import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { applyCommand, loadData, newGame } from '../src/sim';
import type { GameState } from '../src/sim';
import { brainGpuIds, brainLayout, brainMode, lossPanel, nodeGpuState, pulseSpeed, waveRate } from '../src/render/brainLayout';

const data = loadData({ hardware, world, products, pulso });
const nodesOf = (ids: string[]) => brainLayout('transformer_2017', ids).nodes;

describe('brainLayout (ruling R19: data parallelism)', () => {
  it('has Figure 1 blocks: 2 embeddings, 6 encoder + 6 decoder layers, head', () => {
    const nodes = nodesOf(['a']);
    expect(nodes.filter((n) => n.kind === 'enc').map((n) => n.layer)).toEqual([0, 1, 2, 3, 4, 5]);
    expect(nodes.filter((n) => n.kind === 'dec').map((n) => n.layer)).toEqual([0, 1, 2, 3, 4, 5]);
    expect(nodes.filter((n) => n.kind === 'embed_in')).toHaveLength(1);
    expect(nodes.filter((n) => n.kind === 'embed_out')).toHaveLength(1);
    expect(nodes.filter((n) => n.kind === 'head')).toHaveLength(1);
    expect(new Set(nodes.map((n) => n.id)).size).toBe(nodes.length);
    for (const n of nodes) {
      expect(n.x).toBeGreaterThanOrEqual(0);
      expect(n.x).toBeLessThanOrEqual(1);
      expect(n.y).toBeGreaterThanOrEqual(0);
      expect(n.y).toBeLessThanOrEqual(1);
    }
    const enc = nodes.filter((n) => n.kind === 'enc');
    const dec = nodes.filter((n) => n.kind === 'dec');
    expect(Math.max(...enc.map((n) => n.x))).toBeLessThan(Math.min(...dec.map((n) => n.x)));
    for (let i = 1; i < 6; i++) expect(enc[i]!.y).toBeGreaterThan(enc[i - 1]!.y);
  });

  it('declares data parallelism', () => {
    expect(brainLayout('transformer_2017', ['a', 'b']).strategy).toBe('data_parallel');
  });

  it('forward pass order: input embedding, encoder, output embedding, decoder, head', () => {
    const nodes = nodesOf([]);
    const step = (id: string) => nodes.find((n) => n.id === id)!.step;
    const order = ['embed_in', 'enc_0', 'enc_1', 'enc_2', 'enc_3', 'enc_4', 'enc_5', 'embed_out', 'dec_0', 'dec_1', 'dec_2', 'dec_3', 'dec_4', 'dec_5', 'head'];
    expect(order.map(step)).toEqual(order.map((_, i) => i));
  });

  it('1 GPU ⇒ every node on that GPU', () => {
    expect(nodesOf(['gpu-1']).every((n) => n.gpuIds.join() === 'gpu-1')).toBe(true);
  });

  it('2 GPUs ⇒ every node replicated on both (no layer split)', () => {
    expect(nodesOf(['gpu-1', 'gpu-2']).every((n) => n.gpuIds.join() === 'gpu-1,gpu-2')).toBe(true);
  });

  it('3 GPUs ⇒ every node replicated on all three', () => {
    expect(nodesOf(['a', 'b', 'c']).every((n) => n.gpuIds.length === 3)).toBe(true);
  });

  it('0 GPUs ⇒ empty gpuIds without throwing', () => {
    const nodes = nodesOf([]);
    expect(nodes.length).toBe(15);
    expect(nodes.every((n) => n.gpuIds.length === 0)).toBe(true);
  });

  it('nodes do not share the caller array', () => {
    const ids = ['a'];
    const nodes = nodesOf(ids);
    ids.push('b');
    expect(nodes[0]!.gpuIds).toEqual(['a']);
  });
});

describe('brain mode and GPU selection', () => {
  const two = (): GameState => {
    let s = newGame(data, 1, 'T');
    s = applyCommand(s, data, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    s = applyCommand(s, data, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    return s;
  };

  it('idle without job or served traffic', () => {
    expect(brainMode(two())).toBe('idle');
  });

  it('training GPUs are used while a job runs; serve GPUs otherwise', () => {
    let s = two();
    const [a, b] = s.gpus.map((g) => g.id) as [string, string];
    s = applyCommand(s, data, { t: 'allocate', gpuId: a, to: 'train' });
    s = applyCommand(s, data, { t: 'allocate', gpuId: b, to: 'serve' });
    expect(brainGpuIds(s)).toEqual([b]); // no job running yet
    s = applyCommand(s, data, { t: 'start_job', jobId: 'replicate_paper' });
    expect(brainMode(s)).toBe('training');
    expect(brainGpuIds(s)).toEqual([a]);
  });

  it('inference when the product serves characters', () => {
    const s = two();
    expect(brainMode({ ...s, product: { ...s.product, servedMCharsH: 2 } })).toBe('inference');
  });

  it('node GPU state: throttled, off, breaker, unassigned', () => {
    const s = two();
    const [a, b] = s.gpus.map((g) => g.id) as [string, string];
    const t = { ...s, gpus: s.gpus.map((g) => (g.id === a ? { ...g, perf: 0.7 as const } : { ...g, perf: 0 as const })) };
    expect(nodeGpuState(t, a)).toBe('throttled');
    expect(nodeGpuState(t, b)).toBe('off');
    expect(nodeGpuState(s, a)).toBe('ok');
    expect(nodeGpuState({ ...s, power: { ...s.power, breakerTripped: true } }, a)).toBe('off');
    expect(nodeGpuState(s, null)).toBe('none');
    expect(nodeGpuState(s, 'missing')).toBe('none');
  });
});

describe('pulse rates', () => {
  it('inference pulse rate strictly increases over the real served range (log scale), 0 when nothing is served', () => {
    expect(pulseSpeed(0)).toBe(0);
    expect(pulseSpeed(Number.NaN)).toBe(0);
    const v = [0.05, 0.5, 5, 50].map(pulseSpeed);
    for (let i = 1; i < v.length; i++) expect(v[i]!).toBeGreaterThan(v[i - 1]!);
    expect(v[0]!).toBeGreaterThan(0);
    expect(Number.isFinite(pulseSpeed(1e9))).toBe(true);
  });

  it('training step rate follows effective throughput, 0 when nothing trains', () => {
    expect(waveRate(0)).toBe(0);
    expect(waveRate(2)).toBeGreaterThan(waveRate(1));
    expect(Number.isFinite(waveRate(1e9))).toBe(true);
  });
});

describe('loss panel', () => {
  const live = (f: number) => 10 - f;
  const base = () => newGame(data, 1, 'T');

  it('live while a job runs', () => {
    const s = base();
    const t = { ...s, jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const, doneP100h: j.workP100h / 2 } : j)) };
    expect(lossPanel(t, live)).toEqual({ kind: 'live', loss: 9.5, fraction: 0.5 });
  });

  it('final value (last curve point) after completion when not serving; hidden while serving', () => {
    const s = base();
    const done = { ...s, jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'done' as const, lossCurve: [9, 4, 2.25] } : j)) };
    expect(lossPanel(done, live)).toEqual({ kind: 'final', loss: 2.25 });
    expect(lossPanel({ ...done, product: { ...done.product, servedMCharsH: 1 } }, live)).toEqual({ kind: 'hidden' });
  });

  it('hidden before any training', () => {
    expect(lossPanel(base(), live)).toEqual({ kind: 'hidden' });
  });
});
