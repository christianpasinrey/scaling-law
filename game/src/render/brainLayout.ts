// Pure decisions for the brain lens (no three.js, no DOM): Figure 1 layout, how the model sits on the
// GPUs, mode, per-GPU state and animation rates. Kept pure so what the player learns from is tested.
import brainData from '../../data/brain.json';
import type { GameState } from '../sim/types';

export type BrainArch = 'transformer_2017';
export type BrainNodeKind = 'embed_in' | 'enc' | 'dec' | 'embed_out' | 'head';

/**
 * Ruling R19: in M1 the 2017 base model (~65 M parameters) fits in one GPU, so several GPUs mean data
 * parallelism — each holds a full replica, works on different examples (or requests) and, when
 * training, gradients are averaged (all-reduce). Splitting layers across GPUs is a later unlock.
 */
export type ParallelStrategy = 'data_parallel';

export interface BrainNode {
  id: string;
  kind: BrainNodeKind;
  /** 0..5 within its stack, for 'enc' and 'dec'. */
  layer?: number;
  /** Normalised layout position of the block centre (0..1, y up). */
  x: number;
  y: number;
  /** Order in one forward pass: input embedding, encoder 0..5, output embedding, decoder 0..5, head (0..14). */
  step: number;
  /** Every GPU that holds a replica of this block (all of them, under data parallelism). */
  gpuIds: string[];
}

export interface BrainLayout {
  strategy: ParallelStrategy;
  nodes: BrainNode[];
}

export type BrainMode = 'training' | 'inference' | 'idle';
export type NodeGpuState = 'ok' | 'throttled' | 'off' | 'none';

const LAYERS_PER_STACK = 6;
const ENC_X = 0.27;
const DEC_X = 0.73;
const EMBED_Y = 0.07;
const LAYER_Y0 = 0.22;
const LAYER_DY = 0.1;
const HEAD_Y = 0.91;
/** Highest `step` (the head). */
export const LAST_STEP = 2 * LAYERS_PER_STACK + 2;

/** The blocks of Figure 1 of "Attention Is All You Need" (6 encoder + 6 decoder layers), each replicated on every GPU. */
export function brainLayout(arch: BrainArch, gpuIds: readonly string[]): BrainLayout {
  void arch; // one architecture in M1
  const ids = (): string[] => [...gpuIds];
  const nodes: BrainNode[] = [{ id: 'embed_in', kind: 'embed_in', x: ENC_X, y: EMBED_Y, step: 0, gpuIds: ids() }];
  for (let l = 0; l < LAYERS_PER_STACK; l++) {
    nodes.push({ id: `enc_${l}`, kind: 'enc', layer: l, x: ENC_X, y: LAYER_Y0 + l * LAYER_DY, step: 1 + l, gpuIds: ids() });
  }
  nodes.push({ id: 'embed_out', kind: 'embed_out', x: DEC_X, y: EMBED_Y, step: LAYERS_PER_STACK + 1, gpuIds: ids() });
  for (let l = 0; l < LAYERS_PER_STACK; l++) {
    nodes.push({ id: `dec_${l}`, kind: 'dec', layer: l, x: DEC_X, y: LAYER_Y0 + l * LAYER_DY, step: LAYERS_PER_STACK + 2 + l, gpuIds: ids() });
  }
  nodes.push({ id: 'head', kind: 'head', x: DEC_X, y: HEAD_Y, step: LAST_STEP, gpuIds: ids() });
  return { strategy: 'data_parallel', nodes };
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

/** Visual state of one GPU: breaker out or perf 0 ⇒ off, perf 0.7 ⇒ throttled. */
export function nodeGpuState(s: GameState, gpuId: string | null): NodeGpuState {
  if (gpuId === null) return 'none';
  const g = s.gpus.find((x) => x.id === gpuId);
  if (!g) return 'none';
  if (s.power.breakerTripped || g.perf === 0) return 'off';
  return g.perf < 1 ? 'throttled' : 'ok';
}

/** What the loss panel shows: live while a job runs, the final value after one finished and nothing is served, else nothing. */
export type LossPanel = { kind: 'live'; loss: number; fraction: number } | { kind: 'final'; loss: number } | { kind: 'hidden' };

export function lossPanel(s: GameState, liveLoss: (fraction: number) => number): LossPanel {
  const running = s.jobs.find((j) => j.status === 'running');
  if (running) {
    const fraction = running.workP100h > 0 ? Math.min(1, running.doneP100h / running.workP100h) : 0;
    return { kind: 'live', loss: liveLoss(fraction), fraction };
  }
  if (brainMode(s) === 'inference') return { kind: 'hidden' };
  const done = [...s.jobs].reverse().find((j) => j.status === 'done' && j.lossCurve.length > 0);
  return done ? { kind: 'final', loss: done.lossCurve[done.lossCurve.length - 1]! } : { kind: 'hidden' };
}

const inf = brainData.inference;
const trn = brainData.training;

/**
 * Inference: sentences drawn per real second. Logarithmic in served M chars/h over the game's real
 * range (data/brain.json), strictly increasing inside it; 0 ⇒ no pulses.
 */
export function pulseSpeed(servedMCharsH: number): number {
  if (!(servedMCharsH > 0)) return 0;
  const lo = Math.log10(inf.minMCharsH.value);
  const hi = Math.log10(inf.maxMCharsH.value);
  const t = Math.min(1, Math.max(0, (Math.log10(servedMCharsH) - lo) / (hi - lo)));
  return inf.minCyclesPerS.value + t * (inf.maxCyclesPerS.value - inf.minCyclesPerS.value);
}

/** Training: steps (forward + backward + all-reduce) drawn per second ∝ effective throughput (Σ p100eq × perf). */
export function waveRate(effectiveP100eq: number): number {
  if (!(effectiveP100eq > 0)) return 0;
  return Math.min(trn.maxCyclesPerS.value, Math.max(trn.minCyclesPerS.value, effectiveP100eq * trn.cyclesPerP100eq.value));
}
