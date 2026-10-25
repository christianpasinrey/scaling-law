import {
  BufferGeometry,
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
import { brainGpuIds, brainLayout, brainMode, LAST_STEP, lossPanel, nodeGpuState, pulseSpeed, waveRate } from './brainLayout';
import type { BrainMode, BrainNode, LossPanel, NodeGpuState } from './brainLayout';
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
const MAX_GPUS = GPU_PALETTE.length;

/** Figure 1 block-type colours (prototype 01-intro-transformer), shown as a stripe on each block. */
const TYPE_COLOURS = { attention: '#f9d39b', ff: '#bfe0f3', norm: '#f0eea2', embed: '#f6cfcf', lin: '#d8d0f3', soft: '#c6e9c2' } as const;

// ---- Layout in brain world units: the normalised layout box is LAYOUT_W × 1 ----
const LAYOUT_W = 1.4;
const PIP_W = 320;
const PIP_H = 220;
const PIP_MARGIN = 16;
const NODE_W = 0.44;
const LAYER_H = 0.072;
const EMBED_H = 0.06;
const HEAD_H = 0.075;
/** Right-hand column (expanded only): GPU legend, then the loss panel, then the notes. */
const COL_X0 = LAYOUT_W + 0.14;
const COL_X1 = LAYOUT_W + 0.95;
const LEGEND_Y0 = 1.0;
const LEGEND_ROW_PX = 20;
const LEGEND_CHIP_PX = 12;
const PANEL = { x0: COL_X0, x1: COL_X1, y0: 0.3, y1: 0.56 };
const NOTES_Y = 0.25;
const PIP_BOUNDS = { x0: -0.05, x1: LAYOUT_W + 0.05, y0: -0.04, y1: 1.12 };
const EXP_BOUNDS = { x0: -0.08, x1: LAYOUT_W + 1.02, y0: -0.06, y1: 1.14 };
const MAX_LOSS_POINTS = 256;
const CLICK_MAX_PX = 5;

// Instance kinds (aInfo.x), shared with the shader.
const K_BG = 0;
const K_FRAME = 1;
const K_PANEL = 2;
const K_EMBED = 3;
const K_ENC = 4;
const K_DEC = 5;
const K_HEAD = 6;
const K_CHIP = 7;
const STATE_CODE: Record<NodeGpuState, number> = { ok: 0, throttled: 1, off: 2, none: 2 };
const MODE_CODE: Record<BrainMode, number> = { idle: 0, inference: 1, training: 2 };
const KIND_CODE: Record<BrainNode['kind'], number> = { embed_in: K_EMBED, embed_out: K_EMBED, enc: K_ENC, dec: K_DEC, head: K_HEAD };
/** Edge flow levels outside 0..1 (aLevel): feedback of the generated word, all-reduce links. */
const LV_FEEDBACK = 2;
const LV_ALLREDUCE = -1;

// Instance slots: 0 background, 1–2 stack frames, 3 loss panel, 15 nodes, then up to 8 legend chips.
const I_BG = 0;
const I_FRAME_ENC = 1;
const I_FRAME_DEC = 2;
const I_PANEL = 3;
const I_NODE0 = 4;
const NODE_COUNT = 15;
const I_CHIP0 = I_NODE0 + NODE_COUNT;
const INSTANCES = I_CHIP0 + MAX_GPUS;

/** Linear RGB of an sRGB hex, as a GLSL vec3 literal. */
function glslColour(hex: string): string {
  const n = parseInt(hex.slice(1), 16);
  const lin = (c: number): number => {
    const v = c / 255;
    return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  };
  return `vec3(${[(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => lin(c).toFixed(4)).join(', ')})`;
}

/**
 * Timeline of one drawn cycle (uPhase 0..1), by flow level seq = step / LAST_STEP:
 * - inference: the encoder reads the sentence once (first quarter), then the decoder runs three
 *   times, one word each, reading the encoder through cross-attention; the generated word feeds back.
 * - training: forward encoder → decoder, backward decoder → encoder, then (≥ 2 GPUs) an all-reduce flash.
 * Reduced motion: a static, mode-coloured highlight; nothing travels.
 */
const PULSE_GLSL = /* glsl */ `
uniform float uMode;
uniform float uPhase;
uniform float uReduced;
uniform float uGpuCount;
const float ENC_END = 6.0 / ${LAST_STEP.toFixed(1)};
const float DEC_START = 7.0 / ${LAST_STEP.toFixed(1)};
const float TRAIN_SPAN = 0.42;
float bump(float seq, float front) { float d = seq - front; return exp(-d * d / 0.0012); }
vec3 pulseAt(float seq) {
  if (seq < -0.5 || uMode < 0.5) return vec3(0.0);
  bool feedback = seq > 1.5;
  if (uMode < 1.5) {
    vec3 c = vec3(0.55, 1.0, 0.9);
    if (uReduced > 0.5) return c * 0.2;
    if (uPhase < 0.25) {
      if (feedback || seq > ENC_END + 0.01) return vec3(0.0);
      return c * bump(seq, mix(-0.04, ENC_END + 0.04, uPhase / 0.25));
    }
    float front = mix(DEC_START - 0.04, 1.06, fract((uPhase - 0.25) / 0.75 * 3.0));
    if (feedback) return c * bump(1.03, front);
    if (seq < DEC_START - 0.01) return vec3(0.0);
    return c * bump(seq, front);
  }
  if (feedback) return vec3(0.0); // training reads the reference translation: no word-by-word loop
  vec3 fw = vec3(0.45, 0.78, 1.0);
  vec3 bw = vec3(1.0, 0.55, 0.9);
  if (uReduced > 0.5) return mix(fw, bw, 0.5) * 0.2;
  float span = uGpuCount > 1.5 ? TRAIN_SPAN : 0.5;
  if (uPhase < span) return fw * bump(seq, mix(-0.04, 1.04, uPhase / span));
  if (uPhase < 2.0 * span) return bw * bump(seq, mix(1.04, -0.04, (uPhase - span) / span));
  return vec3(0.0);
}
float allReduce() {
  if (uMode < 1.5 || uGpuCount < 1.5) return 0.0;
  if (uReduced > 0.5) return 0.35;
  if (uPhase < 2.0 * TRAIN_SPAN) return 0.0;
  return sin(3.14159 * (uPhase - 2.0 * TRAIN_SPAN) / (1.0 - 2.0 * TRAIN_SPAN));
}
`;

const NODE_VERT = /* glsl */ `
attribute vec4 aInfo;
varying vec2 vUv;
varying vec2 vSize;
varying vec4 vInfo;
void main() {
  vUv = uv;
  vInfo = aInfo;
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
uniform float uChipPx;
uniform vec3 uGpuColor[${MAX_GPUS}];
uniform float uGpuState[${MAX_GPUS}];
uniform float uSelectedStep;
varying vec2 vUv;
varying vec2 vSize;
varying vec4 vInfo;
${PULSE_GLSL}
const vec3 AMBER = vec3(1.0, 0.434, 0.0); // #FFB000
float sdRound(vec2 p, vec2 b, float r) {
  vec2 q = abs(p) - b + r;
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
// Block-type stripe, bottom (t = 0) to top, as in Figure 1.
vec3 typeColour(float kind, float t) {
  vec3 emb = ${glslColour(TYPE_COLOURS.embed)}, mha = ${glslColour(TYPE_COLOURS.attention)};
  vec3 ff = ${glslColour(TYPE_COLOURS.ff)}, nrm = ${glslColour(TYPE_COLOURS.norm)};
  if (kind < 3.5) return emb;
  if (kind < 4.5) return t < 0.4 ? mha : (t < 0.5 ? nrm : (t < 0.9 ? ff : nrm));
  if (kind < 5.5) return t < 0.27 ? mha : (t < 0.33 ? nrm : (t < 0.6 ? mha : (t < 0.66 ? nrm : (t < 0.93 ? ff : nrm))));
  return t < 0.5 ? ${glslColour(TYPE_COLOURS.lin)} : ${glslColour(TYPE_COLOURS.soft)};
}
vec3 gpuChip(int i) {
  vec3 c = uGpuColor[i];
  float st = uGpuState[i];
  if (st > 0.5 && st < 1.5) c = mix(c, AMBER, 0.55);
  if (st > 1.5) c = vec3(0.12);
  return c * (0.55 + 0.45 * uDim) + vec3(0.3) * allReduce() * (st > 1.5 ? 0.0 : 1.0);
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
    gl_FragColor = vec4(vec3(0.42, 0.5, 0.6), a * (0.05 + 0.55 * line));
  } else if (kind > 6.5) {
    // GPU legend chip: palette colour, amber ring when throttled, flashes on all-reduce.
    int gi = int(vInfo.z + 0.5);
    float d = sdRound(p, vSize * 0.5, 3.0 * uPx);
    float a = 1.0 - smoothstep(-uPx, 0.0, d);
    vec3 col = gpuChip(gi);
    float ring = 1.0 - smoothstep(1.5, 2.5, -d / uPx);
    if (uGpuState[gi] > 0.5 && uGpuState[gi] < 1.5) col = mix(col, AMBER, ring);
    gl_FragColor = vec4(col, a);
  } else {
    float d = sdRound(p, vSize * 0.5, 4.0 * uPx);
    float a = 1.0 - smoothstep(-uPx, 0.0, d);
    vec3 col = vec3(0.075, 0.1, 0.14) * (0.5 + 0.5 * uDim) + pulseAt(vInfo.y) * 0.8;
    // Block-type stripe on the left.
    float sx = vUv.x * vSize.x;
    if (sx < max(vSize.x * 0.12, 6.0 * uPx)) col = typeColour(kind, vUv.y) * (0.55 + 0.45 * uDim);
    // One chip per GPU replica at the right end: every GPU holds this whole block.
    float inset = 3.0 * uPx;
    float chipW = uChipPx * uPx;
    float pitch = chipW + max(1.0, uChipPx * 0.35) * uPx;
    float xr = vSize.x * 0.5 - inset - p.x;
    if (uGpuCount > 0.5 && xr > 0.0 && abs(p.y) < vSize.y * 0.5 - inset) {
      float slot = floor(xr / pitch);
      if (slot < uGpuCount && xr - slot * pitch < chipW) col = gpuChip(int(uGpuCount - 1.0 - slot));
    }
    float rim = 1.0 - smoothstep(0.0, 1.0, -d / uPx - 1.2);
    vec3 rimCol = vec3(0.3, 0.38, 0.48);
    if (abs(vInfo.y - uSelectedStep) < 0.001) { rimCol = vec3(1.0); rim = 1.0 - smoothstep(0.0, 1.0, -d / uPx - 2.5); }
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
uniform float uShowLegend;
varying float vLevel;
${PULSE_GLSL}
void main() {
  if (vLevel < -0.5) {
    // All-reduce links between the GPU legend chips (expanded only).
    vec3 col = vec3(0.3, 0.38, 0.48) + vec3(0.7, 1.0, 0.95) * allReduce();
    gl_FragColor = vec4(col, uShowLegend);
  } else {
    gl_FragColor = vec4(vec3(0.36, 0.45, 0.56) * uDim + pulseAt(vLevel), 0.9);
  }
  #include <colorspace_fragment>
}
`;

interface Rect {
  cx: number;
  cy: number;
  w: number;
  h: number;
}

interface LegendRow {
  text: string;
  state: NodeGpuState;
}

/**
 * The brain lens (rulings R18, R19): Figure 1 of the Transformer drawn in the garage's renderer through a
 * scissor viewport — a 320×220 picture-in-picture bottom right, or the full viewport over a dimmed garage.
 * Under data parallelism every GPU holds the whole model, so each block carries one chip per GPU replica.
 * One InstancedMesh (background, frames, blocks, legend chips), one LineSegments (edges, all-reduce links)
 * and, expanded, one Line (loss sparkline): ≤ 4 draw calls. Pulses live in the shaders; the frame loop only
 * advances a phase. `update` is diff-based.
 */
export class BrainView {
  private readonly ctx: SceneCtx;
  private readonly scene = new Scene();
  private readonly camera = new OrthographicCamera(0, 1, 1, 0, -1, 1);
  private readonly mesh: InstancedMesh;
  private readonly info: InstancedBufferAttribute;
  private readonly nodeMat: ShaderMaterial;
  private readonly edges: LineSegments;
  private readonly edgeMat: ShaderMaterial;
  private readonly spark: Line;
  private readonly sparkPos: Float32BufferAttribute;
  private readonly gpuColour = new Float32Array(MAX_GPUS * 3);
  private readonly gpuState = new Float32Array(MAX_GPUS);
  private readonly listeners: { [K in keyof BrainEvents]: Set<Listener<K>> } = { select: new Set() };
  private readonly overlay: HTMLDivElement;
  private readonly titleEl: HTMLDivElement;
  private readonly legendEls: HTMLDivElement[] = [];
  private readonly notesEl: HTMLDivElement;
  private readonly labelEls: HTMLDivElement[] = [];
  private readonly lossEl: HTMLDivElement;
  private readonly allReduceEl: HTMLDivElement;
  private readonly size = new Vector2();
  private readonly lastSize = new Vector2(-1, -1);
  private readonly m4 = new Matrix4();
  private readonly down = new Vector2();
  private readonly hit = new Vector2();
  private readonly offAfter: () => void;
  private readonly ro: ResizeObserver;

  private nodes: BrainNode[] = [];
  private readonly rects: Rect[] = [];
  private gpuIds: string[] = [];
  private gpuKey = '\u0000';
  private mode: BrainMode = 'idle';
  private speed = 0; // drawn cycles per second
  private phase = 0;
  private expanded = false;
  private viewDirty = true;
  private selected: string | null = null;
  private downInBrain = false;
  private loss: LossPanel = { kind: 'hidden' };
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
  private px = 0.003;

  constructor(ctx: SceneCtx) {
    this.ctx = ctx;

    const plane = new PlaneGeometry(1, 1);
    this.info = new InstancedBufferAttribute(new Float32Array(INSTANCES * 4), 4);
    plane.setAttribute('aInfo', this.info);
    const shared = {
      uMode: { value: 0 },
      uPhase: { value: 0 },
      uReduced: { value: ctx.reducedMotion ? 1 : 0 },
      uGpuCount: { value: 0 },
      uDim: { value: 1 },
    };
    this.nodeMat = new ShaderMaterial({
      vertexShader: NODE_VERT,
      fragmentShader: NODE_FRAG,
      uniforms: {
        ...shared,
        uPx: { value: 0.003 },
        uBgAlpha: { value: 0.94 },
        uBgRadius: { value: 8 },
        uBorder: { value: 1 },
        uChipPx: { value: 4 },
        uGpuColor: { value: this.gpuColour },
        uGpuState: { value: this.gpuState },
        uSelectedStep: { value: -1 },
      },
      transparent: true,
      depthTest: false,
      depthWrite: false,
      toneMapped: false,
    });
    this.mesh = new InstancedMesh(plane, this.nodeMat, INSTANCES);
    this.mesh.frustumCulled = false;
    this.scene.add(this.mesh);

    this.edgeMat = new ShaderMaterial({
      vertexShader: EDGE_VERT,
      fragmentShader: EDGE_FRAG,
      uniforms: { ...shared, uShowLegend: { value: 0 } }, // same uniform objects: one phase update drives both
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
    this.notesEl = mk('white-space:normal;color:#9fb0c4');
    this.lossEl = mk('color:#5be7c4');
    this.allReduceEl = mk('color:#7d8da3;font-size:10px');
    for (let i = 0; i < MAX_GPUS; i++) this.legendEls.push(mk('color:#c9d4e0;transform:translateY(-50%)'));
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
  }

  /** Brings the brain in line with `s`. Safe on every state message; only changed data is re-uploaded. */
  update(s: GameState, d: GameData): void {
    this.state = s;
    this.data = d;
    const ids = brainGpuIds(s).slice(0, MAX_GPUS);
    const key = ids.join('|');
    if (key !== this.gpuKey) {
      this.gpuKey = key;
      this.gpuIds = ids;
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
    // Nothing runs (no GPU, breaker out, GPUs off): no pulses, not even the static highlight.
    u.uMode!.value = this.speed > 0 ? MODE_CODE[this.mode] : 0;
    u.uDim!.value = this.mode === 'idle' ? 0.45 : 1;
    u.uGpuCount!.value = ids.length;

    // Per-GPU colour (palette by owned order, so a GPU keeps its colour) and state.
    for (let i = 0; i < ids.length; i++) {
      const owned = s.gpus.findIndex((g) => g.id === ids[i]);
      const hex = parseInt(GPU_PALETTE[owned % MAX_GPUS]!.slice(1), 16);
      this.gpuColour[i * 3] = srgbToLinear((hex >> 16) & 255);
      this.gpuColour[i * 3 + 1] = srgbToLinear((hex >> 8) & 255);
      this.gpuColour[i * 3 + 2] = srgbToLinear(hex & 255);
      this.gpuState[i] = STATE_CODE[nodeGpuState(s, ids[i]!)];
    }
    const sel = this.selected === null ? -1 : (this.nodes.find((n) => n.id === this.selected)?.step ?? -1);
    u.uSelectedStep!.value = sel < 0 ? -1 : sel / LAST_STEP;

    this.loss = lossPanel(s, (f) => lossAt(d, f));
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

  /** Places the blocks and frames. Runs only when the set of model GPUs changes. */
  private layout(ids: string[]): void {
    this.nodes = brainLayout('transformer_2017', ids).nodes;
    this.rects.length = 0;
    for (const n of this.nodes) {
      const h = n.kind === 'enc' || n.kind === 'dec' ? LAYER_H : n.kind === 'head' ? HEAD_H : EMBED_H;
      this.rects.push({ cx: n.x * LAYOUT_W, cy: n.y, w: NODE_W, h });
    }
    const stackFrame = (kind: 'enc' | 'dec'): Rect => {
      const rs = this.rects.filter((_, i) => this.nodes[i]!.kind === kind);
      const top = rs[rs.length - 1]!.cy + LAYER_H / 2 + 0.025;
      const bot = rs[0]!.cy - LAYER_H / 2 - 0.025;
      return { cx: rs[0]!.cx, cy: (top + bot) / 2, w: NODE_W + 0.06, h: top - bot };
    };
    this.setInst(I_FRAME_ENC, stackFrame('enc'), K_FRAME, 0, 0);
    this.setInst(I_FRAME_DEC, stackFrame('dec'), K_FRAME, 0, 0);
    for (let n = 0; n < this.nodes.length; n++) {
      const node = this.nodes[n]!;
      this.setInst(I_NODE0 + n, this.rects[n]!, KIND_CODE[node.kind], node.step / LAST_STEP, 0);
    }
    (this.info.array as Float32Array)[I_BG * 4] = K_BG;
    this.mesh.instanceMatrix.needsUpdate = true;
    this.info.needsUpdate = true;
    this.viewDirty = true; // background, chips and links follow the view
  }

  private setInst(i: number, r: Rect, kind: number, level: number, extra: number): void {
    this.m4.makeScale(r.w, r.h, 1).setPosition(r.cx, r.cy, 0);
    this.mesh.setMatrixAt(i, this.m4);
    const ia = this.info.array as Float32Array;
    ia[i * 4] = kind;
    ia[i * 4 + 1] = level;
    ia[i * 4 + 2] = extra;
  }

  /** World centre of legend chip `i` (expanded column). */
  private chipCentre(i: number): [number, number] {
    return [COL_X0 + (LEGEND_CHIP_PX / 2 + 14) * this.px, LEGEND_Y0 - i * LEGEND_ROW_PX * this.px];
  }

  /** Data-flow edges (by forward step), the generated-word feedback and the all-reduce links. Rebuilt on layout/resize only. */
  private buildEdges(): void {
    const pos: number[] = [];
    const lvl: number[] = [];
    const at = (id: string): [Rect, number] => {
      const i = this.nodes.findIndex((n) => n.id === id);
      return [this.rects[i]!, this.nodes[i]!.step / LAST_STEP];
    };
    const seg = (x0: number, y0: number, l0: number, x1: number, y1: number, l1: number): void => {
      pos.push(x0, y0, 0, x1, y1, 0);
      lvl.push(l0, l1);
    };
    const up = (a: string, b: string): void => {
      const [ra, la] = at(a);
      const [rb, lb] = at(b);
      seg(ra.cx, ra.cy + ra.h / 2, la, rb.cx, rb.cy - rb.h / 2, lb);
    };
    up('embed_in', 'enc_0');
    up('embed_out', 'dec_0');
    for (let l = 1; l < 6; l++) {
      up(`enc_${l - 1}`, `enc_${l}`);
      up(`dec_${l - 1}`, `dec_${l}`);
    }
    up('dec_5', 'head');
    // Encoder output → every decoder layer's cross-attention: lit while that decoder layer runs.
    const [top] = at('enc_5');
    const xOut = top.cx + top.w / 2;
    for (let l = 0; l < 6; l++) {
      const [r, lv] = at(`dec_${l}`);
      seg(xOut, top.cy, lv, r.cx - r.w / 2, r.cy, lv);
    }
    // The generated word goes back in as the next decoder input ("outputs, shifted right").
    const [head] = at('head');
    const [emb] = at('embed_out');
    const xr = head.cx + head.w / 2 + 0.05;
    seg(head.cx + head.w / 2, head.cy, LV_FEEDBACK, xr, head.cy, LV_FEEDBACK);
    seg(xr, head.cy, LV_FEEDBACK, xr, emb.cy, LV_FEEDBACK);
    seg(xr, emb.cy, LV_FEEDBACK, emb.cx + emb.w / 2, emb.cy, LV_FEEDBACK);
    // All-reduce: a bracket joining the legend chips (≥ 2 GPUs).
    const n = this.gpuIds.length;
    if (n >= 2) {
      const bx = COL_X0 + 4 * this.px;
      const [, y0] = this.chipCentre(0);
      const [, y1] = this.chipCentre(n - 1);
      seg(bx, y0, LV_ALLREDUCE, bx, y1, LV_ALLREDUCE);
      for (let i = 0; i < n; i++) {
        const [cx, cy] = this.chipCentre(i);
        seg(bx, cy, LV_ALLREDUCE, cx - (LEGEND_CHIP_PX / 2) * this.px, cy, LV_ALLREDUCE);
      }
    }
    const g = new BufferGeometry();
    g.setAttribute('position', new Float32BufferAttribute(pos, 3));
    g.setAttribute('aLevel', new Float32BufferAttribute(lvl, 1));
    this.edges.geometry.dispose();
    this.edges.geometry = g;
  }

  // ---------------------------------------------------------------- loss + text

  private lossJob(): GameState['jobs'][number] | null {
    const s = this.state;
    if (!s) return null;
    if (this.loss.kind === 'live') return s.jobs.find((j) => j.status === 'running') ?? null;
    if (this.loss.kind === 'final') return [...s.jobs].reverse().find((j) => j.status === 'done' && j.lossCurve.length > 0) ?? null;
    return null;
  }

  private refreshLoss(): void {
    const job = this.lossJob();
    const d = this.data;
    const key = job ? `${job.id}:${job.status}:${job.lossCurve.length}` : '';
    if (key === this.lossKey || !d) return;
    this.lossKey = key;
    const curve = job?.lossCurve ?? [];
    const hi = lossAt(d, 0);
    const lo = lossAt(d, 1);
    const n = Math.min(curve.length, MAX_LOSS_POINTS);
    const a = this.sparkPos.array as Float32Array;
    // x spans the whole job (progress 0..1), so the live line grows left to right.
    const frac = job && job.workP100h > 0 ? Math.min(1, job.doneP100h / job.workP100h) : 0;
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

  /** Legend rows: one per model GPU — each one a full replica. */
  private legend(s: GameState, d: GameData): LegendRow[] {
    return this.gpuIds.map((id) => {
      const i = s.gpus.findIndex((g) => g.id === id);
      const g = s.gpus[i]!;
      const name = d.gpus.find((m) => m.id === g.model)?.shortName ?? g.model;
      return { text: `${T('brain.gpu')} ${i + 1} · ${name} · ${T('brain.replica')}`, state: nodeGpuState(s, id) };
    });
  }

  private refreshText(): void {
    const s = this.state;
    const d = this.data;
    const L = this.loss;
    const lossTxt =
      L.kind === 'live'
        ? `${T('brain.loss')} ${L.loss.toFixed(2)} · ${Math.round(100 * L.fraction)} % — ${T('brain.loss.note')}`
        : L.kind === 'final'
          ? `${T('brain.loss.final')} ${L.loss.toFixed(2)} — ${T('brain.loss.note')}`
          : '';
    const rows = s && d ? this.legend(s, d) : [];
    const key = `${this.expanded}|${this.mode}|${lossTxt}|${rows.map((r) => r.text + r.state).join(',')}|${this.vw}x${this.vh}`;
    if (key === this.textKey) return;
    this.textKey = key;

    this.titleEl.textContent = `${T('brain.title')} · ${T(`brain.mode.${this.mode}`)}${this.expanded ? '' : ' ' + T('brain.hint.pip')}`;
    for (let i = 0; i < this.legendEls.length; i++) {
      const el = this.legendEls[i]!;
      const row = this.expanded ? rows[i] : undefined;
      el.replaceChildren();
      if (!row) continue;
      el.append(row.text);
      if (row.state === 'throttled' || row.state === 'off') {
        const st = document.createElement('span');
        st.style.color = row.state === 'throttled' ? '#ffb000' : '#8a8a8a';
        st.textContent = ` · ${T(row.state === 'throttled' ? 'brain.state.throttled' : 'brain.state.off')}`;
        el.append(st);
      }
    }
    this.notesEl.replaceChildren();
    this.lossEl.textContent = this.expanded ? lossTxt : '';
    this.allReduceEl.textContent = this.expanded && this.mode === 'training' && rows.length >= 2 ? T('brain.allreduce') : '';
    if (this.expanded) {
      const p = (txt: string, css = ''): HTMLDivElement => {
        const el = document.createElement('div');
        el.style.cssText = css;
        el.textContent = txt;
        this.notesEl.appendChild(el);
        return el;
      };
      if (rows.length === 0) p(T('brain.noGpu'), 'margin-bottom:4px');
      p(T(`brain.explain.${this.mode}`), 'color:#d8e3f0;margin-bottom:4px');
      p(T(this.mode === 'inference' ? 'brain.parallel.serve' : 'brain.parallel'), 'margin-bottom:6px');
      const types = p(T('brain.types.title') + ' ', 'margin-bottom:6px');
      const swatches: [string[], TextKey][] = [
        [[TYPE_COLOURS.attention], 'brain.types.attention'],
        [[TYPE_COLOURS.ff], 'brain.types.ff'],
        [[TYPE_COLOURS.norm], 'brain.types.norm'],
        [[TYPE_COLOURS.embed], 'brain.types.embed'],
        [[TYPE_COLOURS.lin, TYPE_COLOURS.soft], 'brain.types.out'],
      ];
      for (const [cols, k] of swatches) {
        const item = document.createElement('span');
        item.style.cssText = 'display:inline-block;margin-right:10px;white-space:nowrap';
        for (const c of cols) {
          const sw = document.createElement('span');
          sw.style.cssText = `display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:3px;vertical-align:-1px;background:${c}`;
          item.append(sw);
        }
        item.append(T(k));
        types.append(item);
      }
      p(T('brain.hint.expanded'), 'color:#7d8da3');
    }
    const labelTexts = [T('brain.node.embed_in'), T('brain.node.enc'), T('brain.node.embed_out'), T('brain.node.dec'), T('brain.node.head')];
    for (let i = 0; i < this.labelEls.length; i++) this.labelEls[i]!.textContent = this.expanded ? labelTexts[i]! : '';
    this.placeText();
  }

  /** World → overlay px. */
  private toPx(wx: number, wy: number, h: number): [number, number] {
    const c = this.camera;
    const left = this.vx;
    const top = h - this.vy - this.vh;
    return [left + ((wx - c.left) / (c.right - c.left)) * this.vw, top + (1 - (wy - c.bottom) / (c.top - c.bottom)) * this.vh];
  }

  /** Positions DOM text from brain world coordinates. */
  private placeText(): void {
    const rect = this.ctx.canvas.getBoundingClientRect();
    const o = this.overlay.style;
    o.left = `${rect.left}px`;
    o.top = `${rect.top}px`;
    o.width = `${rect.width}px`;
    o.height = `${rect.height}px`;
    const h = rect.height;
    const [tx, ty] = this.expanded ? this.toPx(COL_X0, LEGEND_Y0 + 0.1, h) : [this.vx + 10, h - this.vy - this.vh + 7];
    this.titleEl.style.left = `${tx}px`;
    this.titleEl.style.top = `${ty}px`;
    this.titleEl.style.fontSize = this.expanded ? '13px' : '10px';
    for (let i = 0; i < this.legendEls.length; i++) {
      const [cx, cy] = this.chipCentre(i);
      const [x, y] = this.toPx(cx, cy, h);
      this.legendEls[i]!.style.left = `${x + LEGEND_CHIP_PX / 2 + 8}px`;
      this.legendEls[i]!.style.top = `${y}px`;
    }
    const [ax, ay] = this.toPx(COL_X0, this.chipCentre(Math.max(0, this.gpuIds.length - 1))[1], h);
    this.allReduceEl.style.left = `${ax}px`;
    this.allReduceEl.style.top = `${ay + 10}px`;
    const [lx, ly] = this.toPx(PANEL.x0, PANEL.y1, h);
    this.lossEl.style.left = `${lx}px`;
    this.lossEl.style.top = `${ly - 16}px`;
    const [nx, ny] = this.toPx(COL_X0, NOTES_Y, h);
    this.notesEl.style.left = `${nx}px`;
    this.notesEl.style.top = `${ny}px`;
    this.notesEl.style.width = `${Math.max(160, this.toPx(COL_X1, 0, h)[0] - nx)}px`;
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
      // Embeddings and head: label inside the plate; stack titles above the frame.
      const [x, y] = this.toPx(r.cx + (dyw === 0 ? 0.01 : 0), r.cy + dyw, h);
      const el = this.labelEls[i]!.style;
      el.left = `${x}px`;
      el.top = `${y}px`;
      el.color = dyw === 0 ? '#d8e3f0' : '#9fb0c4';
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
    const px = Math.max((b.x1 - b.x0) / Math.max(1, this.vw), (b.y1 - b.y0) / Math.max(1, this.vh)); // world units per CSS px
    this.px = px;
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
    u.uChipPx!.value = this.expanded ? 7 : 3;
    this.edgeMat.uniforms.uShowLegend!.value = this.expanded ? 1 : 0;
    // Background covers the whole brain viewport.
    this.setInst(I_BG, { cx, cy, w: c.right - c.left, h: c.top - c.bottom }, K_BG, 0, 0);
    // Loss panel and legend chips exist only expanded.
    const hidden: Rect = { cx: 0, cy: 0, w: 0, h: 0 };
    const showPanel = this.expanded && this.loss.kind !== 'hidden';
    this.setInst(I_PANEL, showPanel ? { cx: (PANEL.x0 + PANEL.x1) / 2, cy: (PANEL.y0 + PANEL.y1) / 2, w: PANEL.x1 - PANEL.x0, h: PANEL.y1 - PANEL.y0 } : hidden, K_PANEL, 0, 0);
    for (let i = 0; i < MAX_GPUS; i++) {
      const [x, y] = this.chipCentre(i);
      const show = this.expanded && i < this.gpuIds.length;
      this.setInst(I_CHIP0 + i, show ? { cx: x, cy: y, w: LEGEND_CHIP_PX * px, h: LEGEND_CHIP_PX * px } : hidden, K_CHIP, 0, i);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    this.info.needsUpdate = true;
    this.buildEdges();
    this.textKey = '';
    this.refreshText();
  }

  private render(dt: number): void {
    if (this.disposed) return;
    if (this.expanded !== (this.edgeMat.uniforms.uShowLegend!.value === 1)) this.viewDirty = true;
    // The loss panel instance follows the panel state.
    const wantPanel = this.expanded && this.loss.kind !== 'hidden';
    if (wantPanel !== this.panelShown) {
      this.panelShown = wantPanel;
      this.viewDirty = true;
    }
    this.updateView();
    if (!this.ctx.reducedMotion && this.speed > 0) this.phase = (this.phase + this.speed * dt) % 1;
    this.nodeMat.uniforms.uPhase!.value = this.phase;
    this.spark.visible = wantPanel && this.spark.geometry.drawRange.count > 1;

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

  private panelShown = false;

  // ---------------------------------------------------------------- input

  /** Pointer position → brain world coords, or false when outside the brain viewport. */
  private toWorld(e: { clientX: number; clientY: number }, out: Vector2): boolean {
    const rect = this.ctx.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const yUp = rect.bottom - e.clientY;
    if (x < this.vx || x > this.vx + this.vw || yUp < this.vy || yUp > this.vy + this.vh) return false;
    const c = this.camera;
    out.set(c.left + ((x - this.vx) / this.vw) * (c.right - c.left), c.bottom + ((yUp - this.vy) / this.vh) * (c.top - c.bottom));
    return true;
  }

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
    if (this.expanded || this.toWorld(e, this.hit)) e.stopPropagation();
  };

  private readonly onKey = (e: KeyboardEvent): void => {
    if (e.repeat) return; // holding `b` must not flicker the view
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

function srgbToLinear(c: number): number {
  const v = c / 255;
  return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
}
