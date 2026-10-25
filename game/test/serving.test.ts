import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { advance, newGame } from '../src/sim';
import { restoreRng } from '../src/sim/rng';
import { stepServing } from '../src/sim/serving';
import type { GameState, OwnedGpu } from '../src/sim/types';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const rng = restoreRng(1);

function gpu(i: number): OwnedGpu {
  return { id: `gpu-${i}`, model: 'gtx1080ti', rigId: 'rig-2', slot: i - 1, tempC: 25, perf: 1 };
}

/** Launched product with `customers`, n 1080 Tis on an open frame allocated to 'serve'. */
function serving(n: number, customers: number, price = 20): GameState {
  const s = newGame(d, 1, 'Lab');
  const gpus = Array.from({ length: n }, (_, i) => gpu(i + 1));
  return {
    ...s,
    rigs: [{ id: 'rig-2', model: 'open_frame' }],
    gpus,
    allocation: Object.fromEntries(gpus.map((g) => [g.id, 'serve' as const])),
    product: { ...s.product, launched: true, customers, priceUsdPerMChars: price },
  };
}

const finite = (s: GameState) => Object.values(s.product).every((v) => typeof v !== 'number' || Number.isFinite(v));

describe('stepServing', () => {
  it('does nothing before launch and does not touch rng', () => {
    const s = newGame(d, 1, 'Lab');
    const r = restoreRng(7);
    expect(stepServing(s, d, r)).toBe(s);
    expect(r.state()).toBe(restoreRng(7).state());
  });

  it('seeds 20 customers on the first launched hour', () => {
    const s = serving(1, 0);
    const out = stepServing(s, d, rng);
    expect(out.product.customers).toBeGreaterThan(19.9);
    expect(out.product.demandMCharsH).toBeCloseTo(20 * 0.05, 10);
  });

  it('0 serve GPUs with customers: served 0, latency capped at 30000, no NaN', () => {
    const out = stepServing(serving(0, 100), d, rng);
    expect(out.product.servedMCharsH).toBe(0);
    expect(out.product.latencyMs).toBe(30000);
    expect(finite(out)).toBe(true);
    expect(out.product.satisfaction).toBeGreaterThanOrEqual(0);
  });

  it('0 customers: satisfaction defined; no serve GPUs and ~0 customers stays finite', () => {
    const out = stepServing(serving(1, 0), d, rng);
    expect(Number.isFinite(out.product.satisfaction)).toBe(true);
    const tiny = serving(0, 1e-12);
    expect(finite(stepServing(tiny, d, rng))).toBe(true);
  });

  it('1 GTX 1080 Ti serves 800 customers without saturation (latency 300)', () => {
    const out = stepServing(serving(1, 800), d, rng);
    expect(out.product.demandMCharsH).toBeCloseTo(40, 10);
    expect(out.product.servedMCharsH).toBeCloseTo(40, 10);
    expect(out.product.latencyMs).toBe(300);
    expect(out.product.satisfaction).toBeCloseTo(0.6, 10);
  });

  it('saturation raises latency proportionally and lowers satisfaction', () => {
    const out = stepServing(serving(1, 1600), d, rng);
    expect(out.product.latencyMs).toBeCloseTo(600, 8);
    expect(out.product.servedMCharsH).toBeCloseTo(40, 10);
    expect(out.product.satisfaction).toBeCloseTo(0.3, 8);
  });

  it('model_v2 raises quality to 0.8', () => {
    const s = serving(1, 800);
    const out = stepServing({ ...s, flags: { ...s.flags, model_v2: true } }, d, rng);
    expect(out.product.satisfaction).toBeCloseTo(0.8, 10);
  });

  it('tripped breaker: capacity 0', () => {
    const s = serving(1, 800);
    const out = stepServing({ ...s, power: { ...s.power, breakerTripped: true } }, d, rng);
    expect(out.product.servedMCharsH).toBe(0);
    expect(out.product.latencyMs).toBe(30000);
  });

  it('throttled GPUs (perf 0.7) give proportionally less capacity', () => {
    const s = serving(1, 1000);
    const out = stepServing({ ...s, gpus: s.gpus.map((g) => ({ ...g, perf: 0.7 as const })) }, d, rng);
    expect(out.product.servedMCharsH).toBeCloseTo(28, 10);
  });

  it('price 40 grows slower than price 20; customers never negative', () => {
    const at = (price: number) => {
      let s = serving(2, 1000, price);
      for (let i = 0; i < 168; i++) s = stepServing(s, d, rng);
      return s.product.customers;
    };
    const c20 = at(20);
    const c40 = at(40);
    expect(c20).toBeGreaterThan(1000);
    expect(c40).toBeLessThan(c20);
    const bad = stepServing(serving(0, 1000), d, rng);
    expect(bad.product.customers).toBeGreaterThanOrEqual(0);
  });

  it('weeklyGrowth at reference price and full satisfaction is 3 % per week', () => {
    const s = serving(2, 1000);
    let cur: GameState = { ...s, flags: { ...s.flags, model_v2: true } };
    for (let i = 0; i < 168; i++) cur = stepServing(cur, d, rng);
    // satisfaction 0.8 -> g = 0.03 * 0.6
    expect(cur.product.customers).toBeCloseTo(1000 * (1 + 0.03 * 0.6), 6);
  });
});

describe('serving through advance', () => {
  it('accumulates weekServedMChars and settleWeek bills it', () => {
    const s = serving(1, 800);
    const fresh = newGame(d, 1, 'Lab');
    // Full week with no failures noise: use a world without failures.
    const r = structuredClone({ hardware, world, products, pulso });
    r.world.failPerGpuDay.value = 0;
    const dn = loadData(r);
    const out = advance({ ...s, power: fresh.power }, dn, 168);
    expect(out.ledger).toHaveLength(1);
    expect(out.ledger[0]!.revenueUsd).toBeGreaterThan(0);
    expect(out.ledger[0]!.revenueUsd).toBeGreaterThanOrEqual(40 * 20 * 100);
    expect(out.product.weekServedMChars).toBe(0);
  });
});

describe('growth bounds (R12)', () => {
  it('price 1 with satisfaction 0.3 for 1000 h: customers finite and >= 0', () => {
    // 2 GPUs, 1600 customers -> saturated?? use 1 GPU and 1600 customers: satisfaction 0.3
    let s = serving(1, 1600, 1);
    for (let i = 0; i < 1000; i++) {
      s = stepServing(s, d, rng);
      expect(Number.isFinite(s.product.customers)).toBe(true);
      expect(s.product.customers).toBeGreaterThanOrEqual(0);
    }
  });
  it('extreme price keeps weekly growth within the cap', () => {
    let s = serving(100, 1000, 0.001);
    s = { ...s, flags: { ...s.flags, model_v2: true } };
    for (let i = 0; i < 168; i++) s = stepServing(s, d, rng);
    expect(s.product.customers).toBeLessThanOrEqual(1000 * 1.5 + 1e-6);
    expect(Number.isFinite(s.product.customers)).toBe(true);
  });
});

describe('price elasticity follows the sign of satisfaction (R22)', () => {
  const after = (n: number, price: number) => stepServing(serving(n, 1000, price), d, rng).product.customers;
  it('unhappy customers (no capacity, s < 0.5): a high price loses them faster, a low price slower', () => {
    expect(stepServing(serving(0, 1000, 20), d, rng).product.satisfaction).toBeLessThan(0.5);
    const ref = after(0, 20);
    expect(ref).toBeLessThan(1000);
    expect(after(0, 40)).toBeLessThan(ref);
    expect(after(0, 1)).toBeGreaterThan(ref);
    expect(after(0, 1)).toBeLessThan(1000);
  });
  it('happy customers (s > 0.5): a low price grows them faster, a high price slower', () => {
    expect(stepServing(serving(100, 1000, 20), d, rng).product.satisfaction).toBeGreaterThan(0.5);
    const ref = after(100, 20);
    expect(ref).toBeGreaterThan(1000);
    expect(after(100, 10)).toBeGreaterThan(ref);
    expect(after(100, 40)).toBeLessThan(ref);
    expect(after(100, 40)).toBeGreaterThan(1000);
  });
});
