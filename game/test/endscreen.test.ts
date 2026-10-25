import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import reality from '../data/reality.es.json';
import { loadData, newGame } from '../src/sim';
import type { GameState, LedgerWeek } from '../src/sim';
import { diagnose, factsAround, idleAdvice, parseFacts, summarize } from '../src/ui/endscreen';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const week = (n: number, lines: Record<string, number>): LedgerWeek => {
  const revenueUsd = (lines.product ?? 0) + (lines.consulting ?? 0) + (lines.rental ?? 0);
  return { week: n, revenueUsd, costsUsd: lines.electricity ?? 0, cashEndUsd: 0, lines };
};

/** 1 starting 1080 Ti + 2 bought 1080 Ti + 1 Titan V on an open frame; 30 weeks played. */
function played(over: Partial<GameState> = {}): GameState {
  const s = newGame(d, 5, 'Garaje Uno');
  return {
    ...s,
    hour: 30 * 168 + 5,
    cashUsd: 1_234_567.4,
    rigs: [...s.rigs, { id: 'rig-2', model: 'open_frame' }],
    gpus: [
      ...s.gpus,
      { id: 'gpu-2', model: 'gtx1080ti', rigId: 'rig-1', slot: 1, tempC: 40, perf: 1 },
      { id: 'gpu-3', model: 'gtx1080ti', rigId: 'rig-2', slot: 0, tempC: 40, perf: 1 },
      { id: 'gpu-4', model: 'titan_v', rigId: 'rig-2', slot: 1, tempC: 40, perf: 1 },
    ],
    allocation: { 'gpu-1': 'train', 'gpu-2': 'serve', 'gpu-3': 'serve', 'gpu-4': 'idle' },
    product: { ...s.product, launched: true, customers: 312.6 },
    reputation: 30,
    trainedGpuHours: 420,
    ledger: [week(1, { product: 100, consulting: 0, rental: 50, electricity: 20 }), week(2, { product: 300, consulting: 1000, rental: 0, electricity: 30 })],
    outcome: 'seed_round',
    ...over,
  };
}

describe('summarize', () => {
  it('derives the end-of-M1 figures from the state', () => {
    const r = summarize(played(), d);
    expect(r.outcome).toBe('seed_round');
    expect(r.labName).toBe('Garaje Uno');
    expect(r.dateIso).toBe(new Date(Date.parse('2017-06-12T17:57:00Z') + (30 * 168 + 5) * 3_600_000).toISOString());
    expect(r.weeks).toBe(30);
    expect(r.cashUsd).toBeCloseTo(1_234_567.4);
    expect(r.gpus).toEqual([
      { model: 'gtx1080ti', name: 'GTX 1080 Ti', count: 3 },
      { model: 'titan_v', name: 'Titan V', count: 1 },
    ]);
    expect(r.gpuCount).toBe(4);
    expect(r.customers).toBe(313);
    expect(r.gpuHours).toBe(420);
    expect(r.reputation).toBe(30);
    expect(r.revenueUsd).toBe(1450);
  });

  it('lists costs largest first: hardware bought (starting PC excluded) and electricity', () => {
    const r = summarize(played(), d);
    const price = (id: string) => d.gpus.find((g) => g.id === id)!.priceUsd.value;
    const frame = d.rigs.find((x) => x.id === 'open_frame')!.priceUsd.value;
    expect(r.costs).toEqual([
      { key: 'hardware', usd: 2 * price('gtx1080ti') + price('titan_v') + frame },
      { key: 'electricity', usd: 50 },
    ]);
    expect(r.revenue).toEqual([
      { key: 'consulting', usd: 1000 },
      { key: 'product', usd: 400 },
      { key: 'rental', usd: 50 },
    ]);
  });

  it('reads saves without the GPU-hours counter as 0 and never returns NaN', () => {
    const s = played({ ledger: [], trainedGpuHours: undefined, product: { ...played().product, customers: Number.NaN } });
    const r = summarize(s, d);
    expect(r.gpuHours).toBe(0);
    expect(r.customers).toBe(0);
    expect(r.revenueUsd).toBe(0);
    expect(r.costs.find((c) => c.key === 'electricity')?.usd).toBe(0);
  });

  it('a fresh game counts no hardware bought', () => {
    expect(summarize({ ...newGame(d, 1, 'L'), outcome: 'bankrupt' }, d).costs.find((c) => c.key === 'hardware')?.usd).toBe(0);
  });
});

describe('diagnose (bankruptcy)', () => {
  it('names what went wrong', () => {
    const s = newGame(d, 1, 'L');
    const keys = diagnose({ ...s, outcome: 'bankrupt', allocation: { 'gpu-1': 'idle' } }, d);
    expect(keys).toEqual(['no_paper', 'idle_gpus_rent']);
    const shopper = played({ outcome: 'bankrupt', ledger: [week(1, { product: 0, consulting: 0, rental: 0, electricity: 40 })], allocation: { 'gpu-1': 'train', 'gpu-2': 'train', 'gpu-3': 'train', 'gpu-4': 'train' } });
    const done = { ...shopper, jobs: shopper.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'done' as const } : j)) };
    expect(diagnose(done, d)).toEqual(['no_product_revenue', 'hardware_over_revenue']);
  });
});

describe('idleAdvice (only advice that is true on the end date)', () => {
  const HOUR_2018_04_02 = Math.ceil((Date.parse('2018-04-02T00:00:00Z') - Date.parse('2017-06-12T17:57:00Z')) / 3_600_000);
  const base = (over: Partial<GameState> = {}): GameState => ({ ...newGame(d, 1, 'L'), outcome: 'bankrupt', allocation: { 'gpu-1': 'idle' }, ...over });
  it('suggests renting during the boom (4 $/day > 250 W × 24 h × 0,35 $/kWh ≈ 2,10 $/day)', () => {
    expect(idleAdvice(base(), d)).toEqual(['idle_gpus_rent']);
  });
  it('does not suggest renting after the boom (1 $/day < 2,10 $/day of electricity)', () => {
    expect(idleAdvice(base({ hour: HOUR_2018_04_02 }), d)).toEqual([]);
  });
  it('suggests serving only when the API was launched and demand went unserved', () => {
    const s = base({ hour: HOUR_2018_04_02 });
    expect(idleAdvice({ ...s, product: { ...s.product, launched: false, demandMCharsH: 5, servedMCharsH: 0 } }, d)).toEqual([]);
    expect(idleAdvice({ ...s, product: { ...s.product, launched: true, demandMCharsH: 5, servedMCharsH: 5 } }, d)).toEqual([]);
    expect(idleAdvice({ ...s, product: { ...s.product, launched: true, demandMCharsH: 5, servedMCharsH: 2 } }, d)).toEqual(['idle_gpus_serve']);
  });
  it('says nothing when no GPU is idle', () => {
    expect(idleAdvice(base({ allocation: { 'gpu-1': 'train' } }), d)).toEqual([]);
  });
});

describe('real-world facts', () => {
  const facts = parseFacts(reality);
  it('every fact has a date, a text and a source', () => {
    expect(facts.length).toBeGreaterThanOrEqual(3);
    for (const f of facts) {
      expect(f.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(f.text.length).toBeGreaterThan(20);
      expect(f.source.length).toBeGreaterThan(5);
    }
    expect(() => parseFacts({ facts: [{ date: 'x', text: 'y', source: '' }] })).toThrow();
  });
  it('splits facts into those before the reached date and those after it', () => {
    const r = factsAround(facts, '2018-06-11T09:00:00.000Z');
    expect(r.before.map((f) => f.title)).toEqual(['ELMo', 'GPT']);
    expect(r.after.map((f) => f.title)).toEqual(['BERT']);
    expect(factsAround(facts, '2017-09-01T00:00:00.000Z').before).toEqual([]);
  });
});
