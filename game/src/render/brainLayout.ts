// Pure decisions for the brain lens (no three.js, no DOM): Figure 1 layout, pipeline split over GPUs,
// mode, per-node GPU state and pulse rates. Kept pure so the mapping the player learns from is tested.
import type { GameState } from '../sim/types';

export type BrainArch = 'transformer_2017';
export type BrainNodeKind = 'embed_in' | 'enc' | 'dec' | 'embed_out' | 'head';

export interface BrainNode {
  id: string;
  kind: BrainNodeKind;
  /** 0..5 within its stack, for 'enc' and 'dec'. */
  layer?: number;
  /** Normalised layout position of the block centre (0..1, y up). */
  x: number;
  y: number;
  gpuId: string | null;
}

export type BrainMode = 'training' | 'inference' | 'idle';
export type NodeGpuState = 'ok' | 'throttled' | 'off' | 'none';

const LAYERS_PER_STACK = 6;
const TOTAL_LAYERS = LAYERS_PER_STACK * 2;
const ENC_X = 0.27;
const DEC_X = 0.73;
const EMBED_Y = 0.07;
const LAYER_Y0 = 0.22;
const LAYER_DY = 0.1;
const HEAD_Y = 0.91;

/** GPU for pipeline layer `i` of 12 (encoder 0..5, then decoder 0..5): consecutive equal chunks. */
function gpuForLayer(i: number, gpuIds: readonly string[]): string | null {
  const n = Math.min(gpuIds.length, TOTAL_LAYERS);
  if (n === 0) return null;
  return gpuIds[Math.floor((i * n) / TOTAL_LAYERS)] ?? null;
}

/**
 * The blocks of Figure 1 of "Attention Is All You Need" (6 encoder + 6 decoder layers), each with the
 * GPU that runs it under pipeline parallelism: the 12 layers are split in consecutive chunks; the input
 * embedding rides with the first layer, the output embedding and the Linear+Softmax head with the last
 * (the paper ties those weights, §3.4) — ruling R18.
 */
export function brainLayout(arch: BrainArch, gpuIds: readonly string[]): BrainNode[] {
  void arch; // one architecture in M1
  const first = gpuForLayer(0, gpuIds);
  const last = gpuForLayer(TOTAL_LAYERS - 1, gpuIds);
  const nodes: BrainNode[] = [{ id: 'embed_in', kind: 'embed_in', x: ENC_X, y: EMBED_Y, gpuId: first }];
  for (let l = 0; l < LAYERS_PER_STACK; l++) {
    nodes.push({ id: `enc_${l}`, kind: 'enc', layer: l, x: ENC_X, y: LAYER_Y0 + l * LAYER_DY, gpuId: gpuForLayer(l, gpuIds) });
  }
  nodes.push({ id: 'embed_out', kind: 'embed_out', x: DEC_X, y: EMBED_Y, gpuId: last });
  for (let l = 0; l < LAYERS_PER_STACK; l++) {
    nodes.push({
      id: `dec_${l}`,
      kind: 'dec',
      layer: l,
      x: DEC_X,
      y: LAYER_Y0 + l * LAYER_DY,
      gpuId: gpuForLayer(LAYERS_PER_STACK + l, gpuIds),
    });
  }
  nodes.push({ id: 'head', kind: 'head', x: DEC_X, y: HEAD_Y, gpuId: last });
  return nodes;
}

/** Training while a job runs; else inference while characters are served; else idle (R18). */
export function brainMode(s: GameState): BrainMode {
  if (s.jobs.some((j) => j.status === 'running')) return 'training';
  if (s.product.servedMCharsH > 0) return 'inference';
  return 'idle';
}

/** GPUs that hold the model: 'train' ones while a job runs, otherwise 'serve' ones, in owned order. */
export function brainGpuIds(s: GameState): string[] {
  const want = s.jobs.some((j) => j.status === 'running') ? 'train' : 'serve';
  return s.gpus.filter((g) => s.allocation[g.id] === want).map((g) => g.id);
}

/** Visual state of the GPU running a node: breaker out or perf 0 ⇒ off, perf 0.7 ⇒ throttled. */
export function nodeGpuState(s: GameState, gpuId: string | null): NodeGpuState {
  if (gpuId === null) return 'none';
  const g = s.gpus.find((x) => x.id === gpuId);
  if (!g) return 'none';
  if (s.power.breakerTripped || g.perf === 0) return 'off';
  return g.perf < 1 ? 'throttled' : 'ok';
}

// Render pacing (not simulation constants): flow-levels per real second.
const PULSE_SPEED_PER_MCHARS = 0.12;
const PULSE_SPEED_MIN = 0.12;
const PULSE_SPEED_MAX = 1.6;
const WAVE_PER_P100EQ = 0.22;
const WAVE_MIN = 0.12;
const WAVE_MAX = 1.1;

/**
 * Inference: pulses keep a fixed spacing and travel at this speed, so pulses per second ∝ served
 * M chars/h (clamped so the view stays readable). 0 ⇒ no pulses.
 */
export function pulseSpeed(servedMCharsH: number): number {
  if (!(servedMCharsH > 0)) return 0;
  return Math.min(PULSE_SPEED_MAX, Math.max(PULSE_SPEED_MIN, servedMCharsH * PULSE_SPEED_PER_MCHARS));
}

/** Training: forward+backward waves per second ∝ effective throughput (Σ p100eq × perf of training GPUs). */
export function waveRate(effectiveP100eq: number): number {
  if (!(effectiveP100eq > 0)) return 0;
  return Math.min(WAVE_MAX, Math.max(WAVE_MIN, effectiveP100eq * WAVE_PER_P100EQ));
}
