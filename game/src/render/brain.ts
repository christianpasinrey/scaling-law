import {
  BufferGeometry,
  Color,
  Float32BufferAttribute,
  InstancedBufferAttribute,
  InstancedMesh,
  Line,
  LineBasicMaterial,
  LineSegments,
  Matrix4,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
  ShaderMaterial,
  Vector2,
} from 'three';
import i18n from '../../data/i18n.es.json';
import type { GameData, GameState } from '../sim/types';
import { lossAt } from '../sim/training';
import { brainGpuIds, brainLayout, brainMode, nodeGpuState, pulseSpeed, waveRate } from './brainLayout';
import type { BrainMode, BrainNode, NodeGpuState } from './brainLayout';
import type { SceneCtx } from './scene';

export interface BrainSelection {
  kind: 'brain';
  blockId: string;
}

export interface BrainEvents {
  select: BrainSelection;
}

type Listener<K extends keyof BrainEvents> = (e: BrainEvents[K]) => void;
type TextKey = keyof typeof i18n;
const T = (k: TextKey): string => i18n[k];

/** Fixed per-GPU palette (Okabe–Ito based, colour-blind friendly; amber/yellow left out: amber means throttling). */
export const GPU_PALETTE: readonly string[] = ['#56B4E9', '#009E73', '#CC79A7', '#0072B2', '#D55E00', '#A08CF0', '#7FD8BE', '#B8C4D6'];

// ---- Layout in brain world units: the normalised layout box is LAYOUT_W × 1 ----
const LAYOUT_W = 1.4;
const PIP_W = 320;
const PIP_H = 220;
const PIP_MARGIN = 16;
const NODE_W = 0.44;
const LAYER_H = 0.072;
const EMBED_H = 0.06;
const HEAD_H = 0.075;
/** Sparkline panel (expanded only), right of the figure. */
const PANEL = { x0: LAYOUT_W + 0.14, x1: LAYOUT_W + 0.95, y0: 0.5, y1: 0.86 };
const PIP_BOUNDS = { x0: -0.05, x1: LAYOUT_W + 0.05, y0: -0.04, y1: 1.12 };
const EXP_BOUNDS = { x0: -0.08, x1: LAYOUT_W + 1.02, y0: -0.06, y1: 1.12 };
const MAX_LOSS_POINTS = 256;
const PULSE_SPACING = 0.34;
const CLICK_MAX_PX = 5;

// Instance kinds (aInfo.x) and GPU states (aInfo.z) shared with the shader.
const K_BG = 0;
const K_FRAME = 1;
const K_PANEL = 2;
const K_EMBED = 3;
const K_ENC = 4;
const K_DEC = 5;
const K_HEAD = 6;
const STATE_CODE: Record<NodeGpuState, number> = { ok: 0, throttled: 1, off: 2, none: 3 };
const MODE_CODE: Record<BrainMode, number> = { idle: 0, inference: 1, training: 2 };
const KIND_CODE: Record<BrainNode['kind'], number> = { embed_in: K_EMBED, embed_out: K_EMBED, enc: K_ENC, dec: K_DEC, head: K_HEAD };

// Instance slots: 0 background, 1–2 stack frames, 3 loss panel, then the 15 nodes.
const I_BG = 0;
const I_FRAME_ENC = 1;
const I_FRAME_DEC = 2;
const I_PANEL = 3;
const I_NODE0 = 4;
const NODE_COUNT = 15;
const INSTANCES = I_NODE0 + NODE_COUNT;

const PULSE_GLSL = /* glsl */ `
uniform float uMode;
uniform float uPhase;
uniform float uReduced;
// Colour added at flow level lv (0 bottom .. 1 top): inference pulses rise; training sends a
// forward wave up and a backward wave down. Reduced motion: a static, mode-coloured highlight.
vec3 pulseAt(float lv) {
  if (uMode < 0.5) return vec3(0.0);
  if (uMode < 1.5) {
    vec3 c = vec3(0.55, 1.0, 0.9);
    if (uReduced > 0.5) return c * 0.22;
    float x = (lv - uPhase) / ${PULSE_SPACING.toFixed(3)};
    float d = abs(fract(x + 0.5) - 0.5) * ${PULSE_SPACING.toFixed(3)};
    return c * exp(-d * d / 0.0018);
  }
  vec3 fw = vec3(0.45, 0.78, 1.0);
  vec3 bw = vec3(1.0, 0.55, 0.9);
  if (uReduced > 0.5) return mix(fw, bw, 0.5) * 0.22;
  bool forward = uPhase < 0.5;
  float front = forward ? mix(-0.12, 1.12, uPhase * 2.0) : mix(1.12, -0.12, (uPhase - 0.5) * 2.0);
  float d = lv - front;
  return (forward ? fw : bw) * exp(-d * d / 0.004);
}
`;

const NODE_VERT = /* glsl */ `
attribute vec4 aInfo;
attribute vec3 aColor;
varying vec2 vUv;
varying vec2 vSize;
varying vec4 vInfo;
varying vec3 vColor;
void main() {
  vUv = uv;
  vInfo = aInfo;
  vColor = aColor;
  vSize = vec2(length(instanceMatrix[0].xyz), length(instanceMatrix[1].xyz));
  gl_Position = projectionMatrix * viewMatrix * modelMatrix * instanceMatrix * vec4(position, 1.0);
}
`;

const NODE_FRAG = /* glsl */ `
uniform float uPx;
uniform float uBgAlpha;
uniform float uBgRadius;
uniform float uBorder;
uniform float uDim;
varying vec2 vUv;
varying vec2 vSize;
varying vec4 vInfo;
varying vec3 vColor;
${PULSE_GLSL}
float sdRound(vec2 p, vec2 b, float r) {
  vec2 q = abs(p) - b + r;
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
// Figure 1 block-type colours (prototype palette), shown as a stripe on each plate.
vec3 typeColour(float kind, float t) {
  vec3 emb = vec3(0.965, 0.812, 0.812), mha = vec3(0.976, 0.827, 0.608), ff = vec3(0.749, 0.878, 0.953);
  vec3 lin = vec3(0.847, 0.816, 0.953), soft = vec3(0.776, 0.914, 0.761);
  if (kind < 3.5) return emb;
  if (kind < 4.5) return t < 0.5 ? mha : ff;
  if (kind < 5.5) return t < 0.33 ? mha * 0.92 : (t < 0.66 ? mha : ff);
  return t < 0.5 ? lin : soft;
}
void main() {
  float kind = vInfo.x;
  vec2 p = (vUv - 0.5) * vSize;
  if (kind < 0.5) {
    float d = sdRound(p, vSize * 0.5, uBgRadius * uPx);
    float a = 1.0 - smoothstep(-uPx, 0.0, d);
    float edge = uBorder * (1.0 - smoothstep(1.5 * uPx, 2.5 * uPx, -d));
    vec3 col = mix(vec3(0.004, 0.007, 0.013), vec3(0.1, 0.16, 0.25), edge);
    gl_FragColor = vec4(col, a * max(uBgAlpha, edge));
  } else if (kind < 2.5) {
    float d = sdRound(p, vSize * 0.5, 6.0 * uPx);
    float a = 1.0 - smoothstep(-uPx, 0.0, d);
    float line = 1.0 - smoothstep(0.5 * uPx, 1.5 * uPx, abs(d + uPx));
    vec3 col = vec3(0.42, 0.5, 0.6);
    gl_FragColor = vec4(col, a * (0.05 + 0.55 * line));
  } else {
    float st = vInfo.z;
    float d = sdRound(p, vSize * 0.5, 4.0 * uPx);
    float a = 1.0 - smoothstep(-uPx, 0.0, d);
    vec3 base = vColor;
    vec3 amber = vec3(1.0, 0.434, 0.0); // #FFB000 in linear
    if (st > 0.5 && st < 1.5) base = mix(base, amber, 0.18);
    if (st > 1.5 && st < 2.5) base = vec3(0.3);
    if (st > 2.5) base = vec3(0.22, 0.25, 0.3);
    base *= uDim;
    // Block-type stripe on the left fifth.
    float sx = vUv.x * vSize.x;
    float stripeW = max(vSize.x * 0.12, 6.0 * uPx);
    vec3 col = sx < stripeW ? typeColour(kind, vUv.y) * (0.55 + 0.45 * uDim) : base;
    // Pulses light the plate (not on GPUs that are off).
    if (st < 1.5 || st > 2.5) col += pulseAt(vInfo.y) * 0.75;
    // Outline: amber (throttled), white (selected), else a darker rim.
    float rim = 1.0 - smoothstep(0.0, 1.0, (-d) / uPx - (st > 0.5 && st < 1.5 ? 2.5 : 1.2));
    vec3 rimCol = vInfo.w > 0.5 ? vec3(1.0) : (st > 0.5 && st < 1.5 ? amber : base * 0.45);
    if (vInfo.w > 0.5) rim = 1.0 - smoothstep(0.0, 1.0, (-d) / uPx - 2.5);
    col = mix(col, rimCol, rim);
    gl_FragColor = vec4(col, a);
  }
  #include <colorspace_fragment>
}
`;

const EDGE_VERT = /* glsl */ `
attribute float aLevel;
varying float vLevel;
void main() {
  vLevel = aLevel;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const EDGE_FRAG = /* glsl */ `
uniform float uDim;
varying float vLevel;
${PULSE_GLSL}
void main() {
  vec3 col = vec3(0.36, 0.45, 0.56) * uDim + pulseAt(vLevel);
  gl_FragColor = vec4(col, 0.9);
  #include <colorspace_fragment>
}
`;

interface LegendRow {
  swatch: string;
  text: string;
  state: NodeGpuState;
}

interface Rect {
  cx: number;
  cy: number;
  w: number;
  h: number;
}

/**
 * The brain lens (ruling R18): Figure 1 of the Transformer, each block coloured by the GPU that runs
 * it, drawn in the garage's own renderer through a scissor viewport — a 320×220 picture-in-picture
 * bottom right, or the full viewport over a dimmed garage. One InstancedMesh (background, frames,
 * blocks), one LineSegments (edges) and, expanded, one Line (loss sparkline): ≤ 4 draw calls.
 * Pulses live in the shaders; the frame loop only advances a phase. `update` is diff-based.
 */
export class BrainView {
  private readonly ctx: SceneCtx;
  private readonly scene = new Scene();
  private readonly camera = new OrthographicCamera(0, 1, 1, 0, -1, 1);
  private readonly mesh: InstancedMesh;
  private readonly info: InstancedBufferAttribute;
  private readonly color: InstancedBufferAttribute;
  private readonly nodeMat: ShaderMaterial;
  private readonly edges: LineSegments;
  private readonly edgeMat: ShaderMaterial;
  private readonly spark: Line;
  private readonly sparkPos: Float32BufferAttribute;
  private readonly listeners: { [K in keyof BrainEvents]: Set<Listener<K>> } = { select: new Set() };
  private readonly overlay: HTMLDivElement;
  private readonly titleEl: HTMLDivElement;
  private readonly detailEl: HTMLDivElement;
  private readonly labelEls: HTMLDivElement[] = [];
  private readonly lossEl: HTMLDivElement;
  private readonly size = new Vector2();
  private readonly lastSize = new Vector2(-1, -1);
  private readonly m4 = new Matrix4();
  private readonly tmpColor = new Color();
  private readonly down = new Vector2();
  private readonly offAfter: () => void;
  private readonly ro: ResizeObserver;

  private nodes: BrainNode[] = [];
  private readonly rects: Rect[] = [];
  private gpuKey = '\u0000';
  private mode: BrainMode = 'idle';
  private speed = 0; // flow-levels/s (inference) or cycles/s (training)
  private phase = 0;
  private expanded = false;
  private viewDirty = true;
  private selected: string | null = null;
  private downInBrain = false;
  private lossKey = '';
  private textKey = '';
  private state: GameState | null = null;
  private data: GameData | null = null;
  private disposed = false;
  /** Brain viewport in CSS px, origin bottom-left (three's convention). */
  private vx = 0;
  private vy = 0;
  private vw = PIP_W;
  private vh = PIP_H;

  constructor(ctx: SceneCtx) {
    this.ctx = ctx;

    const plane = new PlaneGeometry(1, 1);
    this.info = new InstancedBufferAttribute(new Float32Array(INSTANCES * 4), 4);
    this.color = new InstancedBufferAttribute(new Float32Array(INSTANCES * 3), 3);
    plane.setAttribute('aInfo', this.info);
    plane.setAttribute('aColor', this.color);
    const shared = {
      uMode: { value: 0 },
      uPhase: { value: 0 },
      uReduced: { value: ctx.reducedMotion ? 1 : 0 },
      uDim: { value: 1 },
    };
    this.nodeMat = new ShaderMaterial({
      vertexShader: NODE_VERT,
      fragmentShader: NODE_FRAG,
      uniforms: { ...shared, uPx: { value: 0.003 }, uBgAlpha: { value: 0.94 }, uBgRadius: { value: 8 }, uBorder: { value: 1 } },
      transparent: true,
      depthTest: false,
      depthWrite: false,
      toneMapped: false,
    });
    this.mesh = new InstancedMesh(plane, this.nodeMat, INSTANCES);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 0;
    this.scene.add(this.mesh);

    this.edgeMat = new ShaderMaterial({
      vertexShader: EDGE_VERT,
      fragmentShader: EDGE_FRAG,
      uniforms: shared, // same uniform objects: one phase update drives both
      transparent: true,
      depthTest: false,
      depthWrite: false,
      toneMapped: false,
    });
    this.edges = new LineSegments(new BufferGeometry(), this.edgeMat);
    this.edges.frustumCulled = false;
    this.edges.renderOrder = 1;
    this.scene.add(this.edges);

    const sparkGeo = new BufferGeometry();
    this.sparkPos = new Float32BufferAttribute(new Float32Array(MAX_LOSS_POINTS * 3), 3);
    sparkGeo.setAttribute('position', this.sparkPos);
    sparkGeo.setDrawRange(0, 0);
    this.spark = new Line(sparkGeo, new LineBasicMaterial({ color: 0x5be7c4, toneMapped: false, transparent: true, depthTest: false }));
    this.spark.frustumCulled = false;
    this.spark.renderOrder = 2;
    this.spark.visible = false;
    this.scene.add(this.spark);

    // DOM text layer (labels only; never takes pointer events).
    this.overlay = document.createElement('div');
    this.overlay.style.cssText =
      'position:fixed;pointer-events:none;overflow:hidden;font:11px/1.35 ui-sans-serif,system-ui,sans-serif;color:#d8e3f0;z-index:2';
    const mk = (css: string): HTMLDivElement => {
      const el = document.createElement('div');
      el.style.cssText = 'position:absolute;white-space:nowrap;' + css;
      this.overlay.appendChild(el);
      return el;
    };
    this.titleEl = mk('font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:10px;color:#5be7c4');
    this.detailEl = mk('white-space:normal;color:#9fb0c4');
    this.lossEl = mk('color:#5be7c4');
    for (let i = 0; i < 5; i++) this.labelEls.push(mk('color:#9fb0c4;font-size:10px;transform:translate(-50%,-50%)'));
    document.body.appendChild(this.overlay);

    this.layout([]);
    this.offAfter = ctx.onAfterRender((dt) => this.render(dt));
    this.ro = new ResizeObserver(() => {
      this.viewDirty = true;
    });
    this.ro.observe(ctx.canvas);
    window.addEventListener('pointerdown', this.onPointerDown, true);
    window.addEventListener('pointerup', this.onPointerUp, true);
    window.addEventListener('wheel', this.onWheel, { capture: true, passive: false });
    window.addEventListener('keydown', this.onKey);
  }

  on<K extends keyof BrainEvents>(type: K, fn: Listener<K>): () => void {
    const set = this.listeners[type] as Set<Listener<K>>;
    set.add(fn);
    return () => set.delete(fn);
  }

  get isExpanded(): boolean {
    return this.expanded;
  }

  /** Picture-in-picture (false) or full viewport over a dimmed garage (true). */
  setExpanded(v: boolean): void {
    if (v === this.expanded) return;
    this.expanded = v;
    this.ctx.controls.enabled = !v; // no orbiting the garage behind the expanded brain
    this.viewDirty = true;
    this.textKey = '';
    this.refreshText();
  }

  /** Brings the brain in line with `s`. Safe on every state message; only changed data is re-uploaded. */
  update(s: GameState, d: GameData): void {
    this.state = s;
    this.data = d;
    const ids = brainGpuIds(s);
    const key = ids.join('|');
    if (key !== this.gpuKey) {
      this.gpuKey = key;
      this.layout(ids);
    }

    this.mode = brainMode(s);
    if (this.mode === 'training') {
      let eff = 0;
      if (!s.power.breakerTripped) {
        for (const g of s.gpus) {
          if (s.allocation[g.id] !== 'train') continue;
          eff += (d.gpus.find((m) => m.id === g.model)?.p100eq.value ?? 0) * g.perf;
        }
      }
      this.speed = waveRate(eff);
    } else if (this.mode === 'inference') {
      this.speed = pulseSpeed(s.product.servedMCharsH);
    } else {
      this.speed = 0;
    }
    const u = this.nodeMat.uniforms;
    u.uMode!.value = MODE_CODE[this.mode];
    u.uDim!.value = this.mode === 'idle' ? 0.45 : 1;

    // Per-node colour and state: write only what changed.
    let colourDirty = false;
    let infoDirty = false;
    const ca = this.color.array as Float32Array;
    const ia = this.info.array as Float32Array;
    for (let n = 0; n < this.nodes.length; n++) {
      const node = this.nodes[n]!;
      const i = I_NODE0 + n;
      const st = STATE_CODE[nodeGpuState(s, node.gpuId)];
      const sel = node.id === this.selected ? 1 : 0;
      if (ia[i * 4 + 2] !== st || ia[i * 4 + 3] !== sel) {
        ia[i * 4 + 2] = st;
        ia[i * 4 + 3] = sel;
        infoDirty = true;
      }
      this.gpuColour(s, node.gpuId);
      if (ca[i * 3] !== this.tmpColor.r || ca[i * 3 + 1] !== this.tmpColor.g || ca[i * 3 + 2] !== this.tmpColor.b) {
        ca[i * 3] = this.tmpColor.r;
        ca[i * 3 + 1] = this.tmpColor.g;
        ca[i * 3 + 2] = this.tmpColor.b;
        colourDirty = true;
      }
    }
    if (infoDirty) this.info.needsUpdate = true;
    if (colourDirty) this.color.needsUpdate = true;

    this.refreshLoss();
    this.refreshText();
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.offAfter();
    this.ro.disconnect();
    window.removeEventListener('pointerdown', this.onPointerDown, true);
    window.removeEventListener('pointerup', this.onPointerUp, true);
    window.removeEventListener('wheel', this.onWheel, true);
    window.removeEventListener('keydown', this.onKey);
    this.ctx.controls.enabled = true;
    this.mesh.geometry.dispose();
    this.mesh.dispose();
    this.nodeMat.dispose();
    this.edges.geometry.dispose();
    this.edgeMat.dispose();
    this.spark.geometry.dispose();
    (this.spark.material as LineBasicMaterial).dispose();
    this.overlay.remove();
  }

  // ---------------------------------------------------------------- layout

  /** Places the static instances and edges for a GPU split. Runs only when the set of model GPUs changes. */
  private layout(ids: string[]): void {
    this.nodes = brainLayout('transformer_2017', ids);
    this.rects.length = 0;
    const ia = this.info.array as Float32Array;
    const setInst = (i: number, r: Rect, kind: number, level: number): void => {
      this.m4.makeScale(r.w, r.h, 1).setPosition(r.cx, r.cy, 0);
      this.mesh.setMatrixAt(i, this.m4);
      ia[i * 4] = kind;
      ia[i * 4 + 1] = level;
    };
    for (const n of this.nodes) {
      const h = n.kind === 'enc' || n.kind === 'dec' ? LAYER_H : n.kind === 'head' ? HEAD_H : EMBED_H;
      this.rects.push({ cx: n.x * LAYOUT_W, cy: n.y, w: NODE_W, h });
    }
    const stackFrame = (kind: 'enc' | 'dec'): Rect => {
      const rs = this.nodes.map((n, i) => (n.kind === kind ? this.rects[i]! : null)).filter((r): r is Rect => r !== null);
      const top = rs[rs.length - 1]!.cy + LAYER_H / 2 + 0.025;
      const bot = rs[0]!.cy - LAYER_H / 2 - 0.025;
      return { cx: rs[0]!.cx, cy: (top + bot) / 2, w: NODE_W + 0.06, h: top - bot };
    };
    setInst(I_FRAME_ENC, stackFrame('enc'), K_FRAME, 0);
    setInst(I_FRAME_DEC, stackFrame('dec'), K_FRAME, 0);
    setInst(I_PANEL, { cx: (PANEL.x0 + PANEL.x1) / 2, cy: (PANEL.y0 + PANEL.y1) / 2, w: PANEL.x1 - PANEL.x0, h: PANEL.y1 - PANEL.y0 }, K_PANEL, 0);
    for (let n = 0; n < this.nodes.length; n++) setInst(I_NODE0 + n, this.rects[n]!, KIND_CODE[this.nodes[n]!.kind], this.nodes[n]!.y);
    ia[I_BG * 4] = K_BG;
    this.mesh.instanceMatrix.needsUpdate = true;
    this.info.needsUpdate = true;
    this.buildEdges();
    this.viewDirty = true; // background instance follows the view
    this.textKey = '';
  }

  private buildEdges(): void {
    const pos: number[] = [];
    const lvl: number[] = [];
    const idx = (id: string): number => this.nodes.findIndex((n) => n.id === id);
    const seg = (x0: number, y0: number, l0: number, x1: number, y1: number, l1: number): void => {
      pos.push(x0, y0, 0, x1, y1, 0);
      lvl.push(l0, l1);
    };
    const up = (a: string, b: string): void => {
      const ra = this.rects[idx(a)]!;
      const rb = this.rects[idx(b)]!;
      seg(ra.cx, ra.cy + ra.h / 2, ra.cy, rb.cx, rb.cy - rb.h / 2, rb.cy);
    };
    up('embed_in', 'enc_0');
    up('embed_out', 'dec_0');
    for (let l = 1; l < 6; l++) {
      up(`enc_${l - 1}`, `enc_${l}`);
      up(`dec_${l - 1}`, `dec_${l}`);
    }
    up('dec_5', 'head');
    // The encoder's output feeds every decoder layer's cross-attention: lit together when the pulse leaves the encoder.
    const top = this.rects[idx('enc_5')]!;
    const xOut = top.cx + top.w / 2;
    for (let l = 0; l < 6; l++) {
      const r = this.rects[idx(`dec_${l}`)]!;
      seg(xOut, top.cy, top.cy, r.cx - r.w / 2, r.cy, top.cy);
    }
    // Fresh geometry so the old GPU buffers are released (runs only when the GPU split changes).
    const g = new BufferGeometry();
    g.setAttribute('position', new Float32BufferAttribute(pos, 3));
    g.setAttribute('aLevel', new Float32BufferAttribute(lvl, 1));
    this.edges.geometry.dispose();
    this.edges.geometry = g;
  }

  /** Colour of the GPU running a node, into tmpColor (palette by owned-GPU order, so a GPU keeps its colour). */
  private gpuColour(s: GameState, gpuId: string | null): void {
    const i = gpuId === null ? -1 : s.gpus.findIndex((g) => g.id === gpuId);
    this.tmpColor.set(i < 0 ? '#3a4250' : GPU_PALETTE[i % GPU_PALETTE.length]!);
  }

  // ---------------------------------------------------------------- loss + text

  private lossJob(): GameState['jobs'][number] | null {
    const s = this.state;
    if (!s) return null;
    return s.jobs.find((j) => j.status === 'running') ?? [...s.jobs].reverse().find((j) => j.lossCurve.length > 0) ?? null;
  }

  private refreshLoss(): void {
    const job = this.lossJob();
    const d = this.data;
    const key = job ? `${job.id}:${job.lossCurve.length}` : '';
    if (key === this.lossKey || !d) return;
    this.lossKey = key;
    const curve = job?.lossCurve ?? [];
    const hi = lossAt(d, 0);
    const lo = lossAt(d, 1);
    const n = Math.min(curve.length, MAX_LOSS_POINTS);
    const a = this.sparkPos.array as Float32Array;
    // x spans the whole job (progress 0..1), so the line grows left to right as training advances.
    const frac = job && job.workP100h > 0 ? job.doneP100h / job.workP100h : 0;
    const span = frac > 0 ? Math.max(n, n / frac) : n;
    for (let i = 0; i < n; i++) {
      const src = curve.length <= MAX_LOSS_POINTS ? i : Math.round((i * (curve.length - 1)) / (n - 1));
      const t = Math.min(1, i / Math.max(1, span - 1));
      const v = (curve[src]! - lo) / Math.max(1e-9, hi - lo);
      a[i * 3] = PANEL.x0 + 0.03 + t * (PANEL.x1 - PANEL.x0 - 0.06);
      a[i * 3 + 1] = PANEL.y0 + 0.03 + Math.min(1, Math.max(0, v)) * (PANEL.y1 - PANEL.y0 - 0.06);
      a[i * 3 + 2] = 0;
    }
    this.sparkPos.needsUpdate = true;
    this.spark.geometry.setDrawRange(0, n);
  }

  private refreshText(): void {
    const s = this.state;
    const d = this.data;
    const job = this.lossJob();
    const lossTxt = job && d ? `${T('brain.loss')} ${lossAt(d, job.doneP100h / Math.max(1e-9, job.workP100h)).toFixed(2)} · ${Math.round((100 * job.doneP100h) / Math.max(1e-9, job.workP100h))} %` : '';
    const rows = s && d ? this.legend(s, d) : [];
    const key = `${this.expanded}|${this.mode}|${lossTxt}|${rows.map((r) => r.text + r.state).join(',')}|${this.vw}x${this.vh}`;
    if (key === this.textKey) return;
    this.textKey = key;

    this.titleEl.textContent = `${T('brain.title')} · ${T(`brain.mode.${this.mode}`)}${this.expanded ? '' : ' ' + T('brain.hint.pip')}`;
    if (this.expanded) {
      this.detailEl.replaceChildren();
      const p = (txt: string, css = ''): void => {
        const el = document.createElement('div');
        el.style.cssText = css;
        el.textContent = txt;
        this.detailEl.appendChild(el);
      };
      p(T(`brain.explain.${this.mode}`), 'color:#d8e3f0;margin-bottom:4px');
      p(T('brain.split'), 'margin-bottom:6px');
      if (rows.length === 0) p(T('brain.noGpu'));
      for (const row of rows) {
        const el = document.createElement('div');
        const sw = document.createElement('span');
        sw.style.cssText = `display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px;background:${row.swatch}`;
        el.append(sw, row.text);
        if (row.state === 'throttled' || row.state === 'off') {
          const st = document.createElement('span');
          st.style.color = row.state === 'throttled' ? '#ffb000' : '#8a8a8a';
          st.textContent = ` · ${T(row.state === 'throttled' ? 'brain.state.throttled' : 'brain.state.off')}`;
          el.append(st);
        }
        this.detailEl.appendChild(el);
      }
      p(T('brain.hint.expanded'), 'margin-top:8px;color:#7d8da3');
      this.lossEl.textContent = lossTxt ? `${lossTxt} — ${T('brain.loss.note')}` : '';
    } else {
      this.detailEl.textContent = '';
      this.lossEl.textContent = '';
    }
    const labelTexts = [T('brain.node.embed_in'), T('brain.node.enc'), T('brain.node.embed_out'), T('brain.node.dec'), T('brain.node.head')];
    for (let i = 0; i < this.labelEls.length; i++) this.labelEls[i]!.textContent = this.expanded ? labelTexts[i]! : '';
    this.placeText();
  }

  /** Legend rows: one per model GPU, with its palette colour, layer count and state. */
  private legend(s: GameState, d: GameData): LegendRow[] {
    return brainGpuIds(s).map((id) => {
      const i = s.gpus.findIndex((g) => g.id === id);
      const g = s.gpus[i]!;
      const name = d.gpus.find((m) => m.id === g.model)?.shortName ?? g.model;
      const layers = this.nodes.filter((n) => n.gpuId === id && (n.kind === 'enc' || n.kind === 'dec')).length;
      return { swatch: GPU_PALETTE[i % GPU_PALETTE.length]!, text: `${T('brain.gpu')} ${i + 1} · ${name} · ${layers} capas`, state: nodeGpuState(s, id) };
    });
  }

  /** Positions DOM labels from brain world coordinates. */
  private placeText(): void {
    const rect = this.ctx.canvas.getBoundingClientRect();
    const o = this.overlay.style;
    o.left = `${rect.left}px`;
    o.top = `${rect.top}px`;
    o.width = `${rect.width}px`;
    o.height = `${rect.height}px`;
    const h = rect.height;
    // Brain viewport top-left in overlay px.
    const left = this.vx;
    const top = h - this.vy - this.vh;
    const toPx = (wx: number, wy: number): [number, number] => {
      const c = this.camera;
      const fx = (wx - c.left) / (c.right - c.left);
      const fy = (wy - c.bottom) / (c.top - c.bottom);
      return [left + fx * this.vw, top + (1 - fy) * this.vh];
    };
    // Expanded: title heads the right-hand column (the top-left corner belongs to the HUD).
    const [tx, ty] = this.expanded ? toPx(PANEL.x0, PANEL.y1 + 0.2) : [left + 10, top + 7];
    this.titleEl.style.left = `${tx}px`;
    this.titleEl.style.top = `${ty}px`;
    this.titleEl.style.fontSize = this.expanded ? '13px' : '10px';
    const [dx, dy] = toPx(PANEL.x0, 1.02);
    this.detailEl.style.left = `${dx}px`;
    this.detailEl.style.top = `${toPx(0, 0.47)[1]}px`;
    this.detailEl.style.width = `${Math.max(160, toPx(PANEL.x1, 0)[0] - dx)}px`;
    void dy;
    const [lx, ly] = toPx(PANEL.x0, PANEL.y1);
    this.lossEl.style.left = `${lx}px`;
    this.lossEl.style.top = `${ly - 16}px`;
    if (!this.expanded || this.nodes.length === 0) return;
    const at = (id: string): Rect => this.rects[this.nodes.findIndex((n) => n.id === id)]!;
    const spots: [Rect, number][] = [
      [at('embed_in'), 0],
      [at('enc_5'), LAYER_H / 2 + 0.05],
      [at('embed_out'), 0],
      [at('dec_5'), LAYER_H / 2 + 0.05],
      [at('head'), 0],
    ];
    for (let i = 0; i < spots.length; i++) {
      const [r, dyw] = spots[i]!;
      // Embeddings and head: label inside the plate (right of the stripe); stack titles above the frame.
      const [px, py] = toPx(r.cx + (dyw === 0 ? 0.03 : 0), r.cy + dyw);
      const el = this.labelEls[i]!.style;
      el.left = `${px}px`;
      el.top = `${py}px`;
      el.color = dyw === 0 ? '#0b0f16' : '#9fb0c4';
      el.fontWeight = dyw === 0 ? '600' : '400';
    }
  }

  // ---------------------------------------------------------------- frame

  private updateView(): void {
    const r = this.ctx.renderer;
    r.getSize(this.size);
    if (!this.viewDirty && this.size.equals(this.lastSize)) return;
    this.viewDirty = false;
    this.lastSize.copy(this.size);
    const W = this.size.x;
    const H = this.size.y;
    if (this.expanded) {
      this.vx = 0;
      this.vy = 0;
      this.vw = W;
      this.vh = H;
    } else {
      this.vw = Math.min(PIP_W, W - 2 * PIP_MARGIN);
      this.vh = Math.min(PIP_H, H - 2 * PIP_MARGIN);
      this.vx = W - this.vw - PIP_MARGIN;
      this.vy = PIP_MARGIN;
    }
    const b = this.expanded ? EXP_BOUNDS : PIP_BOUNDS;
    const bw = b.x1 - b.x0;
    const bh = b.y1 - b.y0;
    const px = Math.max(bw / Math.max(1, this.vw), bh / Math.max(1, this.vh)); // world units per CSS px
    const cx = (b.x0 + b.x1) / 2;
    const cy = (b.y0 + b.y1) / 2;
    const c = this.camera;
    c.left = cx - (this.vw * px) / 2;
    c.right = cx + (this.vw * px) / 2;
    c.bottom = cy - (this.vh * px) / 2;
    c.top = cy + (this.vh * px) / 2;
    c.updateProjectionMatrix();
    const u = this.nodeMat.uniforms;
    u.uPx!.value = px;
    u.uBgAlpha!.value = this.expanded ? 0.82 : 0.94;
    u.uBgRadius!.value = this.expanded ? 0 : 8;
    u.uBorder!.value = this.expanded ? 0 : 1;
    // Background covers the whole brain viewport.
    this.m4.makeScale(c.right - c.left, c.top - c.bottom, 1).setPosition(cx, cy, 0);
    this.mesh.setMatrixAt(I_BG, this.m4);
    // The loss panel only exists expanded.
    if (this.expanded) {
      this.m4.makeScale(PANEL.x1 - PANEL.x0, PANEL.y1 - PANEL.y0, 1).setPosition((PANEL.x0 + PANEL.x1) / 2, (PANEL.y0 + PANEL.y1) / 2, 0);
    } else {
      this.m4.makeScale(0, 0, 1);
    }
    this.mesh.setMatrixAt(I_PANEL, this.m4);
    this.mesh.instanceMatrix.needsUpdate = true;
    this.textKey = '';
    this.refreshText();
  }

  private render(dt: number): void {
    if (this.disposed) return;
    this.updateView();
    if (!this.ctx.reducedMotion && this.speed > 0) {
      const period = this.mode === 'inference' ? PULSE_SPACING : 1;
      this.phase = (this.phase + this.speed * dt) % period;
    }
    this.nodeMat.uniforms.uPhase!.value = this.phase;
    this.spark.visible = this.expanded && this.spark.geometry.drawRange.count > 1;

    const r = this.ctx.renderer;
    const autoClear = r.autoClear;
    r.autoClear = false;
    r.setViewport(this.vx, this.vy, this.vw, this.vh);
    r.setScissor(this.vx, this.vy, this.vw, this.vh);
    r.setScissorTest(true);
    r.clearDepth();
    r.render(this.scene, this.camera);
    r.setScissorTest(false);
    r.setViewport(0, 0, this.size.x, this.size.y);
    r.autoClear = autoClear;
  }

  // ---------------------------------------------------------------- input

  /** Pointer position → brain world coords, or false when outside the brain viewport. */
  private toWorld(e: PointerEvent | WheelEvent, out: Vector2): boolean {
    const rect = this.ctx.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const yUp = rect.bottom - e.clientY;
    if (x < this.vx || x > this.vx + this.vw || yUp < this.vy || yUp > this.vy + this.vh) return false;
    const c = this.camera;
    out.set(c.left + ((x - this.vx) / this.vw) * (c.right - c.left), c.bottom + ((yUp - this.vy) / this.vh) * (c.top - c.bottom));
    return true;
  }

  private readonly hit = new Vector2();

  private readonly onPointerDown = (e: PointerEvent): void => {
    if (e.target !== this.ctx.canvas) return;
    this.downInBrain = this.expanded || this.toWorld(e, this.hit);
    if (!this.downInBrain) return;
    this.down.set(e.clientX, e.clientY);
    e.stopPropagation(); // the garage (orbit + GPU picking) never sees clicks on the brain
  };

  private readonly onPointerUp = (e: PointerEvent): void => {
    if (!this.downInBrain) return;
    this.downInBrain = false;
    e.stopPropagation();
    if (Math.hypot(e.clientX - this.down.x, e.clientY - this.down.y) > CLICK_MAX_PX) return;
    if (!this.toWorld(e, this.hit)) return;
    const n = this.pick(this.hit.x, this.hit.y);
    if (n === null) {
      if (!this.expanded) this.setExpanded(true);
      return;
    }
    this.select(n.id);
  };

  private readonly onWheel = (e: WheelEvent): void => {
    if (e.target !== this.ctx.canvas) return;
    if (this.expanded || this.toWorld(e as unknown as PointerEvent, this.hit)) e.stopPropagation();
  };

  private readonly onKey = (e: KeyboardEvent): void => {
    const t = e.target as HTMLElement | null;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === 'b' || e.key === 'B') this.setExpanded(!this.expanded);
    else if (e.key === 'Escape' && this.expanded) this.setExpanded(false);
  };

  private pick(wx: number, wy: number): BrainNode | null {
    for (let i = 0; i < this.nodes.length; i++) {
      const r = this.rects[i]!;
      if (Math.abs(wx - r.cx) <= r.w / 2 && Math.abs(wy - r.cy) <= r.h / 2) return this.nodes[i]!;
    }
    return null;
  }

  private select(id: string): void {
    this.selected = id;
    if (this.state && this.data) this.update(this.state, this.data); // refresh the selected outline
    const ev: BrainSelection = { kind: 'brain', blockId: id };
    for (const fn of this.listeners.select) fn(ev);
  }
}
