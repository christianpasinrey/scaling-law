import {
  BoxGeometry,
  CanvasTexture,
  CatmullRomCurve3,
  Color,
  CylinderGeometry,
  Group,
  HemisphereLight,
  Mesh,
  MeshPhysicalMaterial,
  MeshStandardMaterial,
  PlaneGeometry,
  PointLight,
  Raycaster,
  RepeatWrapping,
  SphereGeometry,
  SRGBColorSpace,
  TubeGeometry,
  Vector2,
  Vector3,
} from 'three';
import type { BufferGeometry, Material, Object3D, Texture } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import type { GLTF } from 'three/addons/loaders/GLTFLoader.js';
import type { GameData, GameState, OwnedGpu, RigModel } from '../sim/types';
import { applyFlowMaterials } from './flow';
import type { FlowMode, FlowSet } from './flow';
import type { SceneCtx } from './scene';
import { hddLedOn } from './motion';
import { slotFor } from './slots';

export interface GpuSelection {
  kind: 'gpu';
  id: string;
}

export interface GarageEvents {
  select: GpuSelection;
}

type Listener<K extends keyof GarageEvents> = (e: GarageEvents[K]) => void;

// ---- Layout (metres; Y up, back wall at z = −2.5, left wall at x = −2) ----
const FLOOR_W = 4;
const FLOOR_D = 5;
const WALL_H = 2.6;
const BACK_Z = -FLOOR_D / 2;
const LEFT_X = -FLOOR_W / 2;
const TABLE_H = 0.42;
const TOWER_SPOTS: readonly Vector3[] = [new Vector3(-0.35, 0, -2.05), new Vector3(-0.95, 0, -2.05)];
const FRAME_SPOTS: readonly Vector3[] = [new Vector3(0.5, TABLE_H, -1.95), new Vector3(1.35, 0, -1.6), new Vector3(1.35, 0, -0.8)];
const WALL_SOCKET = new Vector3(-1.1, 0.32, BACK_Z + 0.012);
const STRIP_POS = new Vector3(-0.85, 0.022, -2.3);
const CLICK_MAX_PX = 5;
const CASE_LIGHT_INTENSITY = 0.35;

interface Led {
  mat: MeshStandardMaterial;
  on: Color;
  intensity: number;
}

interface RigView {
  id: string;
  model: RigModel;
  root: Object3D;
  flow: FlowSet;
  cord: { mesh: Mesh; flow: FlowSet; geometry: BufferGeometry } | null;
  /** Watts per flow line name, refreshed on each update. */
  rates: Map<string, number>;
  cordWatts: number;
  ledPower: Led | null;
  ledMobo: Led | null;
  ledHdd: Led | null;
  ledRisers: (Led | null)[];
  hddActive: boolean;
  /** Faint interior light of a closed case (so the cards read through the window); off with the breaker. */
  caseLight: PointLight | null;
}

interface GpuView {
  id: string;
  rigId: string;
  slot: number;
  model: string;
  root: Object3D;
  led: Led | null;
}

const OFF_COLOR = new Color(0x050505);

function makeLed(mesh: Mesh, on: Color, intensity: number): Led {
  const src = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  const mat =
    src instanceof MeshStandardMaterial ? (src.clone() as MeshStandardMaterial) : new MeshStandardMaterial({ roughness: 0.4 });
  mat.color.setRGB(0.02, 0.02, 0.02);
  mesh.material = mat;
  const led = { mat, on: on.clone(), intensity };
  setLed(led, false);
  return led;
}

function setLed(led: Led | null, on: boolean, scale = 1): void {
  if (!led) return;
  if (on) {
    led.mat.emissive.copy(led.on);
    led.mat.emissiveIntensity = led.intensity * scale;
  } else {
    led.mat.emissive.copy(OFF_COLOR);
    led.mat.emissiveIntensity = 0;
  }
}

/** Deterministic concrete-ish noise (render only; the sim never sees it). */
function concreteTexture(): Texture {
  const size = 256;
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const g = c.getContext('2d');
  if (g) {
    const img = g.createImageData(size, size);
    let seed = 1234567;
    for (let i = 0; i < size * size; i++) {
      seed = (seed * 1103515245 + 12345) >>> 0;
      const n = (seed >>> 16) / 65535;
      const x = i % size;
      const y = (i / size) | 0;
      const blotch = 0.5 + 0.5 * Math.sin(x * 0.045 + Math.sin(y * 0.03) * 2.2) * Math.cos(y * 0.037);
      const v = 78 + n * 22 + blotch * 14;
      img.data[i * 4] = v;
      img.data[i * 4 + 1] = v * 0.97;
      img.data[i * 4 + 2] = v * 0.93;
      img.data[i * 4 + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }
  const t = new CanvasTexture(c);
  t.colorSpace = SRGBColorSpace;
  t.wrapS = t.wrapT = RepeatWrapping;
  t.repeat.set(3, 3.75);
  return t;
}

/**
 * KHR_materials_anisotropy on the frame's aluminium blows out to pure white under the point
 * light (the GLBs carry no tangents). Plain isotropic metal reads correctly here.
 */
function tameMaterials(root: Object3D): void {
  root.traverse((o) => {
    if (!(o instanceof Mesh)) return;
    for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
      if (m instanceof MeshPhysicalMaterial && m.anisotropy > 0) m.anisotropy = 0;
    }
  });
}

function gpuLoad(s: GameState, g: OwnedGpu): number {
  // Same rule as the sim's power step: working or rented GPUs draw full power.
  if (s.power.breakerTripped || g.perf === 0) return 0;
  const a = s.allocation[g.id];
  return a === 'train' || a === 'serve' || a === 'rent' ? 1 : 0;
}

/**
 * The 3D garage: simple room, owned rigs (GLB), every owned GPU mounted at its SLOT_gpu_n,
 * flow shaders on the cables and LEDs driven by the game state. `update` is idempotent and
 * diff-based: GLBs load once and are cloned per instance.
 */
export class GarageView {
  private readonly ctx: SceneCtx;
  private readonly assetBase: string;
  private readonly loader = new GLTFLoader();
  private readonly gltfs = new Map<string, GLTF>();
  private readonly loading = new Set<string>();
  private readonly failed = new Set<string>();
  private readonly rigs = new Map<string, RigView>();
  /** Same views as `rigs`, as an array for the allocation-free per-frame loop. */
  private readonly rigList: RigView[] = [];
  private readonly gpus = new Map<string, GpuView>();
  private readonly gpuRoots: Object3D[] = [];
  private readonly listeners: { [K in keyof GarageEvents]: Set<Listener<K>> } = { select: new Set() };
  private readonly world = new Group();
  private readonly owned: (Material | BufferGeometry | Texture)[] = [];
  private readonly raycaster = new Raycaster();
  private readonly ndc = new Vector2();
  private readonly down = new Vector2();
  private readonly tmp = new Vector3();
  private wallCord: { flow: FlowSet; watts: number } | null = null;
  private state: GameState | null = null;
  private data: GameData | null = null;
  private mode: FlowMode = 'normal';
  private disposed = false;
  private readonly flowOpts: { reducedMotion: boolean };
  private readonly offFrame: () => void;

  constructor(ctx: SceneCtx, assetBase: string = import.meta.env.BASE_URL + 'assets/') {
    this.ctx = ctx;
    this.assetBase = assetBase;
    this.flowOpts = { reducedMotion: ctx.reducedMotion };
    this.world.name = 'Garage';
    ctx.scene.add(this.world);
    this.buildRoom();
    this.offFrame = ctx.onFrame((dt, t) => this.frame(dt, t));
    ctx.canvas.addEventListener('pointerdown', this.onPointerDown);
    ctx.canvas.addEventListener('pointerup', this.onPointerUp);
  }

  on<K extends keyof GarageEvents>(type: K, fn: Listener<K>): () => void {
    const set = this.listeners[type] as Set<Listener<K>>;
    set.add(fn);
    return () => set.delete(fn);
  }

  /** Brings the 3D garage in line with `s`. Safe to call on every state message. */
  update(s: GameState, d: GameData): void {
    this.state = s;
    this.data = d;
    this.sync();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.offFrame();
    this.ctx.canvas.removeEventListener('pointerdown', this.onPointerDown);
    this.ctx.canvas.removeEventListener('pointerup', this.onPointerUp);
    for (const id of [...this.gpus.keys()]) this.removeGpu(id);
    for (const id of [...this.rigs.keys()]) this.removeRig(id);
    this.wallCord?.flow.dispose();
    for (const r of this.owned) r.dispose();
    for (const g of this.gltfs.values()) {
      g.scene.traverse((o) => {
        if (o instanceof Mesh) {
          o.geometry.dispose();
          const ms = Array.isArray(o.material) ? o.material : [o.material];
          for (const m of ms) m.dispose();
        }
      });
    }
    this.ctx.scene.remove(this.world);
  }

  // ---------------------------------------------------------------- sync

  private sync(): void {
    const s = this.state;
    const d = this.data;
    if (!s || !d || this.disposed) return;

    // Rigs: add missing, drop sold ones.
    const spotIdx = { tower_2017: 0, open_frame: 0 };
    for (const r of s.rigs) {
      const model = d.rigs.find((m) => m.id === r.model);
      const spotIndex = spotIdx[r.model]++;
      if (!model || this.rigs.has(r.id)) continue;
      const gltf = this.gltf(model.glb);
      if (gltf) this.addRig(r.id, model, gltf, spotIndex);
    }
    for (const id of [...this.rigs.keys()]) if (!s.rigs.some((r) => r.id === id)) this.removeRig(id);

    // GPUs: mount new ones, re-mount moved ones, drop sold ones.
    for (const g of s.gpus) {
      const v = this.gpus.get(g.id);
      if (v && v.rigId === g.rigId && v.slot === g.slot && v.model === g.model) continue;
      if (v) this.removeGpu(g.id);
      const rig = this.rigs.get(g.rigId);
      const model = d.gpus.find((m) => m.id === g.model);
      if (!rig || !model) continue;
      const gltf = this.gltf(model.glb);
      if (gltf) this.addGpu(g, rig, gltf);
    }
    for (const id of [...this.gpus.keys()]) if (!s.gpus.some((g) => g.id === id)) this.removeGpu(id);

    this.applyState(s, d);
  }

  /** Returns the loaded GLB or starts loading it (sync runs again when it arrives). */
  private gltf(file: string): GLTF | null {
    const got = this.gltfs.get(file);
    if (got) return got;
    if (!this.loading.has(file) && !this.failed.has(file)) {
      this.loading.add(file);
      this.loader
        .loadAsync(this.assetBase + file)
        .then((g) => {
          tameMaterials(g.scene);
          this.gltfs.set(file, g);
          this.sync();
        })
        .catch((err: unknown) => {
          this.failed.add(file);
          console.error(`garage: could not load ${file}`, err);
        })
        .finally(() => this.loading.delete(file));
    }
    return null;
  }

  private addRig(id: string, model: RigModel, gltf: GLTF, spotIndex: number): void {
    const spots = model.id === 'tower_2017' ? TOWER_SPOTS : FRAME_SPOTS;
    const spot = spots[Math.min(spotIndex, spots.length - 1)]!;
    const root = gltf.scene.clone(true);
    root.name = `rig:${id}`;
    root.position.copy(spot);
    if (spotIndex >= spots.length) root.position.x += 0.7 * (spotIndex - spots.length + 1);
    this.world.add(root);
    root.updateMatrixWorld(true);

    const rates = new Map<string, number>();
    const flow = applyFlowMaterials(root, (line) => rates.get(line.name) ?? 0, this.flowOpts);

    const green = new Color(0x2bff5a);
    const blue = new Color(0x3a7bff);
    let ledPower: Led | null = null;
    let ledMobo: Led | null = null;
    let ledHdd: Led | null = null;
    const ledRisers: (Led | null)[] = Array.from({ length: model.gpuSlots }, () => null);
    root.traverse((o) => {
      if (!(o instanceof Mesh) || !o.name.startsWith('LED_')) return;
      if (o.name === 'LED_power') ledPower = makeLed(o, green, 3);
      else if (o.name === 'LED_mobo_status') ledMobo = makeLed(o, green, 2);
      else if (o.name === 'LED_hdd') ledHdd = makeLed(o, new Color(0xffffff), 3);
      else {
        const m = /^LED_riser_(\d+)$/.exec(o.name);
        const i = m ? Number(m[1]) : -1;
        if (i >= 0 && i < ledRisers.length) ledRisers[i] = makeLed(o, blue, 3);
      }
    });

    const view: RigView = {
      id,
      model,
      root,
      flow,
      cord: null,
      rates,
      cordWatts: 0,
      ledPower,
      ledMobo,
      ledHdd,
      ledRisers,
      hddActive: false,
      caseLight: null,
    };
    if (model.id === 'tower_2017') {
      const light = new PointLight(0xcfe0ff, CASE_LIGHT_INTENSITY, 0.9, 2);
      light.position.set(-0.02, 0.3, -0.05);
      root.add(light);
      view.caseLight = light;
    }
    view.cord = this.buildRigCord(view);
    this.rigs.set(id, view);
    this.rigList.push(view);
  }

  private removeRig(id: string): void {
    const v = this.rigs.get(id);
    if (!v) return;
    for (const g of [...this.gpus.values()]) if (g.rigId === id) this.removeGpu(g.id);
    v.flow.dispose();
    if (v.cord) {
      v.cord.flow.dispose();
      v.cord.geometry.dispose();
      this.world.remove(v.cord.mesh);
    }
    for (const led of [v.ledPower, v.ledMobo, v.ledHdd, ...v.ledRisers]) led?.mat.dispose();
    this.world.remove(v.root);
    this.rigs.delete(id);
    this.rigList.splice(this.rigList.indexOf(v), 1);
  }

  private addGpu(g: OwnedGpu, rig: RigView, gltf: GLTF): void {
    let slotName: string;
    try {
      slotName = slotFor(rig.model, g.slot);
    } catch (err) {
      console.error('garage:', err);
      return;
    }
    const slot = rig.root.getObjectByName(slotName);
    if (!slot) {
      console.error(`garage: ${rig.model.glb} has no ${slotName}`);
      return;
    }
    // The SLOT empty encodes the full mount pose: the card's scene root goes at its transform.
    const root = gltf.scene.clone(true);
    root.name = `gpu:${g.id}`;
    root.userData.gpuId = g.id;
    let led: Led | null = null;
    root.traverse((o) => {
      if (o instanceof Mesh && o.name === 'LED_Text') {
        const src = Array.isArray(o.material) ? o.material[0] : o.material;
        const on = src instanceof MeshStandardMaterial ? src.emissive.clone() : new Color(0x76ff00);
        led = makeLed(o, on, 2.5);
      }
    });
    slot.add(root);
    this.gpus.set(g.id, { id: g.id, rigId: g.rigId, slot: g.slot, model: g.model, root, led });
    this.gpuRoots.push(root);
  }

  private removeGpu(id: string): void {
    const v = this.gpus.get(id);
    if (!v) return;
    v.root.removeFromParent();
    v.led?.mat.dispose();
    const i = this.gpuRoots.indexOf(v.root);
    if (i >= 0) this.gpuRoots.splice(i, 1);
    this.gpus.delete(id);
  }

  /** Derived visuals: per-line watts, flow mode, LEDs. Cheap; runs on every update. */
  private applyState(s: GameState, d: GameData): void {
    const tripped = s.power.breakerTripped;
    const anyJobRunning = s.jobs.some((j) => j.status === 'running');
    let total = 0;

    for (const rig of this.rigs.values()) {
      const r = rig.rates;
      r.clear();
      const base = rig.model.baseWatts;
      let rigWatts = base;
      r.set('Cable_ATX24', base);
      r.set('Cable_EPS8', base);
      for (let i = 0; i < rig.model.gpuSlots; i++) r.set(`Data_USB_riser_${i}`, tripped ? 0 : 1);
      const risersOn: boolean[] = Array.from({ length: rig.model.gpuSlots }, () => false);
      for (const g of s.gpus) {
        if (g.rigId !== rig.id) continue;
        const model = d.gpus.find((m) => m.id === g.model);
        const w = (model?.watts.value ?? 0) * gpuLoad(s, g);
        rigWatts += w;
        if (rig.model.id === 'open_frame') {
          // A x16 slot (here the riser feeding it) supplies at most 75 W (PCIe CEM spec,
          // world.pcieSlotWatts); the rest of the card's draw comes over its own PCIe power cable.
          const slotW = d.world.pcieSlotWatts.value;
          r.set(`Cable_Riser_${g.slot}`, Math.min(w, slotW));
          r.set(`Cable_GPU_${g.slot}`, Math.max(w - slotW, 0));
        } else {
          r.set(`Cable_GPU_${g.slot}`, w);
        }
        const alloc = s.allocation[g.id];
        if (g.slot < risersOn.length) risersOn[g.slot] = alloc !== undefined && alloc !== 'idle';
      }
      rig.cordWatts = rigWatts;
      total += rigWatts;
      setLed(rig.ledPower, !tripped);
      setLed(rig.ledMobo, !tripped);
      // Intensity, not visibility: changing the light count would recompile every material.
      if (rig.caseLight) rig.caseLight.intensity = tripped ? 0 : CASE_LIGHT_INTENSITY;
      rig.hddActive = !tripped && anyJobRunning;
      if (!rig.hddActive) setLed(rig.ledHdd, false);
      rig.ledRisers.forEach((led, i) => setLed(led, !tripped && risersOn[i] === true));
    }
    if (this.wallCord) this.wallCord.watts = total;

    for (const g of s.gpus) setLed(this.gpus.get(g.id)?.led ?? null, !tripped && g.perf > 0);

    // Same draw the next power step will see; amber above the safe continuous limit.
    const mode: FlowMode = tripped ? 'off' : total > d.world.circuitSafeWatts ? 'warn' : 'normal';
    this.mode = mode;
    this.wallCord?.flow.setMode(mode);
    for (const rig of this.rigs.values()) {
      rig.flow.setMode(mode);
      rig.cord?.flow.setMode(mode);
    }
  }

  // ---------------------------------------------------------------- per frame

  private frame(dt: number, t: number): void {
    this.wallCord?.flow.tick(dt);
    for (let i = 0; i < this.rigList.length; i++) {
      const rig = this.rigList[i]!;
      rig.flow.tick(dt);
      rig.cord?.flow.tick(dt);
      if (rig.hddActive) {
        const reduced = this.ctx.reducedMotion;
        setLed(rig.ledHdd, hddLedOn(t, true, reduced), reduced ? 0.8 : 0.6 + 0.4 * Math.abs(Math.sin(t * 11.0)));
      }
    }
  }

  // ---------------------------------------------------------------- picking

  private readonly onPointerDown = (e: PointerEvent): void => {
    this.down.set(e.clientX, e.clientY);
  };

  private readonly onPointerUp = (e: PointerEvent): void => {
    if (Math.hypot(e.clientX - this.down.x, e.clientY - this.down.y) > CLICK_MAX_PX) return; // it was an orbit drag
    const rect = this.ctx.canvas.getBoundingClientRect();
    this.ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(this.ndc, this.ctx.camera);
    const hit = this.raycaster.intersectObjects(this.gpuRoots, true)[0];
    let o: Object3D | null = hit ? hit.object : null;
    while (o && typeof o.userData.gpuId !== 'string') o = o.parent;
    if (!o) return;
    const ev: GpuSelection = { kind: 'gpu', id: o.userData.gpuId as string };
    for (const fn of this.listeners.select) fn(ev);
  };

  // ---------------------------------------------------------------- room

  private keep<T extends Material | BufferGeometry | Texture>(r: T): T {
    this.owned.push(r);
    return r;
  }

  private buildRoom(): void {
    const w = this.world;
    const floorTex = this.keep(concreteTexture());
    const floor = new Mesh(
      this.keep(new PlaneGeometry(FLOOR_W, FLOOR_D)),
      this.keep(new MeshStandardMaterial({ map: floorTex, color: 0x9a958e, roughness: 0.92, metalness: 0 })),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.name = 'Floor';
    w.add(floor);

    const wallMat = this.keep(new MeshStandardMaterial({ color: 0x3b3d40, roughness: 0.95 }));
    const back = new Mesh(this.keep(new PlaneGeometry(FLOOR_W, WALL_H)), wallMat);
    back.position.set(0, WALL_H / 2, BACK_Z);
    back.name = 'WallBack';
    w.add(back);
    const left = new Mesh(this.keep(new PlaneGeometry(FLOOR_D, WALL_H)), wallMat);
    left.rotation.y = Math.PI / 2;
    left.position.set(LEFT_X, WALL_H / 2, 0);
    left.name = 'WallLeft';
    w.add(left);
    // Skirting boards keep the wall/floor joint readable in the dark.
    const skirtMat = this.keep(new MeshStandardMaterial({ color: 0x24221f, roughness: 0.8 }));
    const skirtBack = new Mesh(this.keep(new BoxGeometry(FLOOR_W, 0.08, 0.015)), skirtMat);
    skirtBack.position.set(0, 0.04, BACK_Z + 0.0075);
    w.add(skirtBack);
    const skirtLeft = new Mesh(this.keep(new BoxGeometry(0.015, 0.08, FLOOR_D)), skirtMat);
    skirtLeft.position.set(LEFT_X + 0.0075, 0.04, 0);
    w.add(skirtLeft);

    // Workbench for the open frame (first frame spot).
    const woodMat = this.keep(new MeshStandardMaterial({ color: 0x4a3626, roughness: 0.8 }));
    const top = new Mesh(this.keep(new BoxGeometry(0.9, 0.03, 0.6)), woodMat);
    const bench = FRAME_SPOTS[0]!;
    top.position.set(bench.x, TABLE_H - 0.015, bench.z);
    top.name = 'Workbench';
    w.add(top);
    const legGeo = this.keep(new BoxGeometry(0.045, TABLE_H - 0.03, 0.045));
    for (const [dx, dz] of [[-0.41, -0.26], [0.41, -0.26], [-0.41, 0.26], [0.41, 0.26]] as const) {
      const leg = new Mesh(legGeo, woodMat);
      leg.position.set(bench.x + dx, (TABLE_H - 0.03) / 2, bench.z + dz);
      w.add(leg);
    }

    // Hanging bulb: the only warm light in the garage.
    const bulbPos = new Vector3(0.05, 1.95, -1.55);
    const cordMat = this.keep(new MeshStandardMaterial({ color: 0x111111, roughness: 0.6 }));
    const drop = new Mesh(this.keep(new CylinderGeometry(0.004, 0.004, WALL_H - bulbPos.y, 6)), cordMat);
    drop.position.set(bulbPos.x, (WALL_H + bulbPos.y) / 2 + 0.04, bulbPos.z);
    w.add(drop);
    const holder = new Mesh(this.keep(new CylinderGeometry(0.018, 0.018, 0.05, 12)), cordMat);
    holder.position.set(bulbPos.x, bulbPos.y + 0.06, bulbPos.z);
    w.add(holder);
    const bulb = new Mesh(
      this.keep(new SphereGeometry(0.035, 20, 14)),
      this.keep(new MeshStandardMaterial({ color: 0xfff1d6, emissive: 0xffc27a, emissiveIntensity: 6 })),
    );
    bulb.position.copy(bulbPos);
    bulb.name = 'Bulb';
    w.add(bulb);
    const light = new PointLight(0xffb36b, 5.5, 0, 2);
    light.position.copy(bulbPos);
    w.add(light);
    w.add(new HemisphereLight(0x6f7c8c, 0x1a1410, 0.35));

    // Wall socket, power strip and the cord between them.
    const plateMat = this.keep(new MeshStandardMaterial({ color: 0xd8d2c4, roughness: 0.6 }));
    const holeMat = this.keep(new MeshStandardMaterial({ color: 0x0c0c0c, roughness: 0.9 }));
    const plate = new Mesh(this.keep(new BoxGeometry(0.08, 0.12, 0.012)), plateMat);
    plate.position.copy(WALL_SOCKET).setZ(BACK_Z + 0.006);
    plate.name = 'WallSocket';
    w.add(plate);
    const slotGeo = this.keep(new BoxGeometry(0.004, 0.014, 0.004));
    for (const [dx, dy] of [[-0.009, 0.025], [0.009, 0.025], [-0.009, -0.022], [0.009, -0.022]] as const) {
      const h = new Mesh(slotGeo, holeMat);
      h.position.set(WALL_SOCKET.x + dx, WALL_SOCKET.y + dy, BACK_Z + 0.013);
      w.add(h);
    }
    const strip = new Mesh(
      this.keep(new BoxGeometry(0.36, 0.04, 0.065)),
      this.keep(new MeshStandardMaterial({ color: 0xcfcac0, roughness: 0.55 })),
    );
    strip.position.copy(STRIP_POS);
    strip.name = 'PowerStrip';
    w.add(strip);
    const sw = new Mesh(
      this.keep(new BoxGeometry(0.028, 0.012, 0.034)),
      this.keep(new MeshStandardMaterial({ color: 0x8a0e0e, emissive: 0xff2a1a, emissiveIntensity: 0.6 })),
    );
    sw.position.set(STRIP_POS.x - 0.15, STRIP_POS.y + 0.024, STRIP_POS.z);
    w.add(sw);
    const outletGeo = this.keep(new BoxGeometry(0.03, 0.004, 0.034));
    for (let i = 0; i < 4; i++) {
      const o = new Mesh(outletGeo, holeMat);
      o.position.set(STRIP_POS.x - 0.08 + i * 0.065, STRIP_POS.y + 0.021, STRIP_POS.z);
      w.add(o);
    }

    const wall = this.cordMesh([
      new Vector3(WALL_SOCKET.x, WALL_SOCKET.y - 0.03, BACK_Z + 0.03),
      new Vector3(WALL_SOCKET.x, 0.08, BACK_Z + 0.05),
      new Vector3(WALL_SOCKET.x + 0.05, 0.008, BACK_Z + 0.12),
      new Vector3(STRIP_POS.x - 0.19, 0.012, STRIP_POS.z),
    ]);
    w.add(wall.mesh);
    this.wallCord = { watts: 0, flow: applyFlowMaterials(wall.mesh, () => this.wallCord?.watts ?? 0, this.flowOpts) };
  }

  /** A cable built like the GLB ones: UV u = metres along the path, flow extras set. */
  private cordMesh(points: Vector3[]): { mesh: Mesh; geometry: BufferGeometry } {
    const curve = new CatmullRomCurve3(points, false, 'catmullrom', 0.3);
    const length = curve.getLength();
    const geometry = new TubeGeometry(curve, Math.max(16, Math.ceil(length * 60)), 0.0045, 8, false);
    const uv = geometry.getAttribute('uv');
    for (let i = 0; i < uv.count; i++) uv.setX(i, uv.getX(i) * length);
    uv.needsUpdate = true;
    const mesh = new Mesh(geometry, this.keep(new MeshStandardMaterial({ color: 0x101010, roughness: 0.6 })));
    mesh.name = 'Cord';
    mesh.userData = { flow_u_start: 0, flow_u_end: length, flow_kind: 'power' };
    return { mesh, geometry };
  }

  /** Cord from the power strip to the rig's (first) power inlet, carrying the rig's draw. */
  private buildRigCord(rig: RigView): RigView['cord'] {
    const inlet = rig.root.getObjectByName('SOCKET_power_in') ?? rig.root.getObjectByName('SOCKET_power_in_0');
    if (!inlet) return null;
    const end = inlet.getWorldPosition(this.tmp).clone();
    const index = this.rigs.size;
    const start = new Vector3(STRIP_POS.x - 0.08 + Math.min(index, 3) * 0.065, STRIP_POS.y + 0.03, STRIP_POS.z);
    const floorY = 0.008;
    // Leave the inlet outward (away from the rig centre), drop to the floor clear of a workbench edge.
    const out = end.clone().sub(rig.root.position).setY(0);
    if (out.lengthSq() < 1e-6) out.set(0, 0, 1);
    out.normalize();
    const drop = end.clone().addScaledVector(out, rig.root.position.y > 0.05 ? 0.2 : 0.08);
    drop.z = Math.max(drop.z, BACK_Z + 0.03);
    const pts = [
      start,
      new Vector3(start.x, floorY + 0.02, start.z + 0.06),
      new Vector3((start.x + drop.x) / 2, floorY, Math.max((start.z + drop.z) / 2, BACK_Z + 0.03)),
      new Vector3(drop.x, floorY, drop.z),
      new Vector3(drop.x, end.y, drop.z),
      end,
    ];
    const cord = this.cordMesh(pts);
    this.world.add(cord.mesh);
    const flow = applyFlowMaterials(cord.mesh, () => rig.cordWatts, this.flowOpts);
    flow.setMode(this.mode);
    return { mesh: cord.mesh, flow, geometry: cord.geometry };
  }
}
