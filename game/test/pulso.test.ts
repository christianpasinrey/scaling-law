import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { advance, applyCommand, newGame } from '../src/sim';
import { restoreRng } from '../src/sim/rng';
import { emitPulso } from '../src/sim/pulso';
import { gpuLabel, pushPulso } from '../src/sim/pulsoLog';
import { stepTraining } from '../src/sim/training';
import type { GameState, PulsoItem, PulsoTemplateCause } from '../src/sim/types';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const base = () => newGame(d, 1, 'Lab');
const at = (s: GameState, hour: number): GameState => ({ ...s, hour });
const latencyItem = (hour: number): PulsoItem => ({
  id: `lat:${hour}`,
  hour,
  cause: 'latency',
  text: 'lento',
  count: 1,
  focus: { kind: 'product' },
});
const launched = (over: Partial<GameState['product']> = {}): GameState => {
  const s = base();
  return { ...s, product: { ...s.product, launched: true, customers: 150, ...over } };
};

describe('pushPulso aggregation (R13)', () => {
  it('50 latency events in a day make one item with count 50', () => {
    let s = base();
    for (let i = 0; i < 50; i++) {
      const h = 24 + (i % 23);
      s = pushPulso(at(s, h), d, latencyItem(h));
    }
    const items = s.pulso.filter((p) => p.cause === 'latency');
    expect(items).toHaveLength(1);
    expect(items[0]?.count).toBe(50);
  });

  it('same cause with another focus is a different item', () => {
    let s = base();
    s = pushPulso(s, d, { id: 'a', hour: 0, cause: 'outage', text: 'x', count: 1, focus: { kind: 'gpu', id: 'gpu-1' } });
    s = pushPulso(s, d, { id: 'b', hour: 0, cause: 'outage', text: 'y', count: 1, focus: { kind: 'gpu', id: 'gpu-2' } });
    expect(s.pulso).toHaveLength(2);
  });

  it('an event older than 24 h starts a new item', () => {
    let s = pushPulso(at(base(), 0), d, latencyItem(0));
    s = pushPulso(at(s, 23), d, latencyItem(23));
    expect(s.pulso).toHaveLength(1);
    s = pushPulso(at(s, 23 + 24), d, latencyItem(47));
    expect(s.pulso).toHaveLength(2);
  });

  it('never more than 3 new items per game day; extras merge into the latest of their cause or drop', () => {
    let s = at(base(), 48);
    const causes = ['latency', 'quality', 'price', 'praise', 'latency'] as const;
    causes.forEach((cause, i) => {
      s = pushPulso(s, d, { id: `${cause}:${i}`, hour: 48, cause, text: 't', count: 1, focus: { kind: 'product' } });
    });
    expect(s.pulso).toHaveLength(3);
    // The 4th (praise) had no item of its cause and was dropped; the 5th is the same event as the first.
    expect(s.pulso.find((p) => p.cause === 'latency')?.count).toBe(2);
    expect(s.pulso.some((p) => p.cause === 'praise')).toBe(false);
    // Over the cap with a different focus but an existing cause: merged into the most recent of that cause.
    s = pushPulso(s, d, { id: 'q', hour: 48, cause: 'quality', text: 't', count: 1, focus: { kind: 'gpu', id: 'g' } });
    expect(s.pulso).toHaveLength(3);
    expect(s.pulso.find((p) => p.cause === 'quality')?.count).toBe(2);
    // Next game day the cap resets.
    s = pushPulso(at(s, 72), d, { id: 'n', hour: 72, cause: 'praise', text: 'p', count: 1, focus: { kind: 'product' } });
    expect(s.pulso.some((p) => p.cause === 'praise')).toBe(true);
  });

  it('over many days, never more than 3 new items in any day', () => {
    let s = launched({ latencyMs: 5000, satisfaction: 0.9, priceUsdPerMChars: 100 });
    const createdPerDay = new Map<number, number>();
    const seen = new Set<string>();
    const rng = restoreRng(3);
    for (let h = 0; h < 24 * 20; h++) {
      s = emitPulso(at(s, h), d, rng);
      for (const p of s.pulso) {
        if (!seen.has(p.id)) {
          seen.add(p.id);
          const day = Math.floor(h / 24);
          createdPerDay.set(day, (createdPerDay.get(day) ?? 0) + 1);
        }
      }
    }
    expect(createdPerDay.size).toBeGreaterThan(5);
    for (const n of createdPerDay.values()) expect(n).toBeLessThanOrEqual(3);
  });

  it('keeps only the last 200 items', () => {
    let s = base();
    for (let i = 0; i < 300; i++) {
      s = pushPulso(at(s, i * 48), d, { id: `n:${i}`, hour: i * 48, cause: 'news', text: 'n', count: 1 });
    }
    expect(s.pulso).toHaveLength(200);
    expect(s.pulso.at(-1)?.id).toBe('n:299');
  });

  it('command warnings still appear when the daily cap is reached, and still aggregate', () => {
    let s = at(base(), 10);
    for (const cause of ['latency', 'quality', 'price'] as const) {
      s = pushPulso(s, d, { id: cause, hour: 10, cause, text: 't', count: 1, focus: { kind: 'product' } });
    }
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'nope', to: 'train' });
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'nope', to: 'train' });
    s = applyCommand(s, d, { t: 'start_job', jobId: 'nope' });
    const warnings = s.pulso.filter((p) => p.cause === 'warning');
    expect(warnings).toHaveLength(2);
    expect(warnings.find((w) => w.id === 'warn:unknown_gpu')?.count).toBe(2);
    expect(s.pulso).toHaveLength(5);
  });
});

describe('emitPulso', () => {
  const run = (s: GameState, from: number, to: number): GameState => {
    const rng = restoreRng(7);
    let cur = s;
    for (let h = from; h < to; h++) cur = emitPulso(at(cur, h), d, rng);
    return cur;
  };

  it('does nothing before launch or off the 6 h cadence', () => {
    const notLaunched = { ...base(), product: { ...base().product, latencyMs: 9999 } };
    expect(emitPulso(at(notLaunched, 6), d, restoreRng(1)).pulso).toHaveLength(0);
    expect(emitPulso(at(launched({ latencyMs: 9999 }), 5), d, restoreRng(1)).pulso).toHaveLength(0);
    expect(emitPulso(at(launched({ latencyMs: 9999 }), 6), d, restoreRng(1)).pulso).toHaveLength(1);
  });

  it('every item has a focus coherent with its cause and a template text of that cause', () => {
    const s = run(launched({ latencyMs: 5000, satisfaction: 0.9, priceUsdPerMChars: 100 }), 0, 24 * 40);
    expect(s.pulso.length).toBeGreaterThan(0);
    for (const p of s.pulso) {
      expect(['latency', 'quality', 'price', 'praise']).toContain(p.cause);
      expect(p.focus).toEqual({ kind: 'product' });
      expect(d.pulso.templates[p.cause as PulsoTemplateCause]).toContain(p.text);
    }
    expect(new Set(s.pulso.map((p) => p.cause)).size).toBeGreaterThan(1);
  });

  it('only causes whose condition holds are emitted', () => {
    const only = (s: GameState, cause: string) => {
      const r = run(s, 0, 24 * 10);
      expect(r.pulso.length).toBeGreaterThan(0);
      expect(new Set(r.pulso.map((p) => p.cause))).toEqual(new Set([cause]));
    };
    const quiet = { latencyMs: 300, satisfaction: 0.3, customers: 10, priceUsdPerMChars: 20 };
    only(launched({ ...quiet, latencyMs: 2000 }), 'latency');
    only(launched({ ...quiet, satisfaction: 0.75 }), 'praise');
    only(launched({ ...quiet, priceUsdPerMChars: 41 }), 'price');
    only(launched({ ...quiet, customers: 100 }), 'quality');
    const v2 = { ...launched({ ...quiet, customers: 500 }), flags: { model_v2: true } };
    expect(run(v2, 0, 24 * 10).pulso).toHaveLength(0);
    expect(run(launched({ ...quiet, priceUsdPerMChars: 40 }), 0, 24 * 10).pulso).toHaveLength(0);
  });

  it('has at least 4 distinct templates per cause', () => {
    for (const list of Object.values(d.pulso.templates)) expect(new Set(list).size).toBeGreaterThanOrEqual(4);
  });
});

describe('GPU names in Pulso texts', () => {
  it('uses the model short name and slot, not the internal id', () => {
    const s0 = base();
    expect(gpuLabel(d, s0.gpus[0] as GameState['gpus'][number])).toBe('GTX 1080 Ti (ranura 1)');
    const s: GameState = {
      ...s0,
      allocation: { 'gpu-1': 'train' },
      jobs: s0.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const } : j)),
    };
    const out = stepTraining(s, d, { next: () => 0, int: () => 0, state: () => 0 });
    const item = out.pulso.find((p) => p.cause === 'outage');
    expect(item?.text).toContain('GTX 1080 Ti (ranura 1)');
    expect(item?.text).not.toContain('gpu-1');
    expect(item?.focus).toEqual({ kind: 'gpu', id: 'gpu-1' });
  });
});

describe('integration with advance', () => {
  it('a long saturated run stays within the 200 item limit', () => {
    const s = advance(launched({ latencyMs: 5000 }), d, 24 * 60);
    expect(s.pulso.length).toBeLessThanOrEqual(200);
  });
});
