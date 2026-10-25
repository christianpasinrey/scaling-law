import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { applyCommand, loadData, newGame } from '../src/sim';
import type { GameState } from '../src/sim';
import { brainGpuIds, brainLayout, brainMode, nodeGpuState, pulseSpeed, waveRate } from '../src/render/brainLayout';

const data = loadData({ hardware, world, products, pulso });
const layers = (ids: string[]) => brainLayout('transformer_2017', ids).filter((n) => n.kind === 'enc' || n.kind === 'dec');

describe('brainLayout', () => {
  it('has Figure 1 blocks: 2 embeddings, 6 encoder + 6 decoder layers, head', () => {
    const nodes = brainLayout('transformer_2017', ['a']);
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
    // Encoder on the left, decoder on the right, both rising bottom to top.
    const enc = nodes.filter((n) => n.kind === 'enc');
    const dec = nodes.filter((n) => n.kind === 'dec');
    expect(Math.max(...enc.map((n) => n.x))).toBeLessThan(Math.min(...dec.map((n) => n.x)));
    for (let i = 1; i < 6; i++) expect(enc[i]!.y).toBeGreaterThan(enc[i - 1]!.y);
  });

  it('1 GPU ⇒ every node on the same GPU', () => {
    const nodes = brainLayout('transformer_2017', ['gpu-1']);
    expect(nodes.every((n) => n.gpuId === 'gpu-1')).toBe(true);
  });

  it('2 GPUs ⇒ encoder on one, decoder on the other', () => {
    const nodes = brainLayout('transformer_2017', ['gpu-1', 'gpu-2']);
    expect(nodes.filter((n) => n.kind === 'enc').every((n) => n.gpuId === 'gpu-1')).toBe(true);
    expect(nodes.filter((n) => n.kind === 'dec').every((n) => n.gpuId === 'gpu-2')).toBe(true);
    expect(nodes.find((n) => n.kind === 'embed_in')!.gpuId).toBe('gpu-1');
    expect(nodes.find((n) => n.kind === 'head')!.gpuId).toBe('gpu-2');
  });

  it('3 GPUs ⇒ 4/4/4 consecutive layers', () => {
    const ls = layers(['a', 'b', 'c']);
    const count = (id: string) => ls.filter((n) => n.gpuId === id).length;
    expect([count('a'), count('b'), count('c')]).toEqual([4, 4, 4]);
    // Consecutive: enc0..3 on a, enc4..5 + dec0..1 on b, dec2..5 on c.
    expect(ls.map((n) => n.gpuId).join('')).toBe('aaaabbbbcccc');
  });

  it('0 GPUs ⇒ gpuId null without throwing', () => {
    const nodes = brainLayout('transformer_2017', []);
    expect(nodes.length).toBe(15);
    expect(nodes.every((n) => n.gpuId === null)).toBe(true);
  });

  it('more GPUs than layers ⇒ every layer still gets one, no throw', () => {
    const ids = Array.from({ length: 14 }, (_, i) => `g${i}`);
    expect(layers(ids).every((n) => n.gpuId !== null)).toBe(true);
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
  it('inference pulse speed grows with served characters, 0 when nothing is served', () => {
    expect(pulseSpeed(0)).toBe(0);
    expect(pulseSpeed(2)).toBeGreaterThan(pulseSpeed(1));
    expect(Number.isFinite(pulseSpeed(1e9))).toBe(true);
    expect(pulseSpeed(Number.NaN)).toBe(0);
  });

  it('training wave rate follows effective throughput, 0 when nothing trains', () => {
    expect(waveRate(0)).toBe(0);
    expect(waveRate(2)).toBeGreaterThan(waveRate(1));
    expect(Number.isFinite(waveRate(1e9))).toBe(true);
  });
});
