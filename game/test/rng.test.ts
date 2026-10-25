import { describe, expect, it } from 'vitest';
import { createRng, restoreRng } from '../src/sim/rng';

describe('rng', () => {
  it('same seed gives the same 1000 outputs', () => {
    const a = createRng(12345);
    const b = createRng(12345);
    for (let i = 0; i < 1000; i++) expect(a.next()).toBe(b.next());
  });

  it('different seeds diverge', () => {
    expect(createRng(1).next()).not.toBe(createRng(2).next());
  });

  it('next() stays in [0,1)', () => {
    const r = createRng(7);
    for (let i = 0; i < 1000; i++) {
      const v = r.next();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it('restoreRng(state) continues the same sequence', () => {
    const r = createRng(99);
    for (let i = 0; i < 37; i++) r.next();
    const resumed = restoreRng(r.state());
    for (let i = 0; i < 200; i++) expect(resumed.next()).toBe(r.next());
  });

  it('int(1,6) is within [1,6] and covers all faces', () => {
    const r = createRng(2017);
    const seen = new Set<number>();
    for (let i = 0; i < 1000; i++) {
      const v = r.int(1, 6);
      expect(Number.isInteger(v)).toBe(true);
      expect(v).toBeGreaterThanOrEqual(1);
      expect(v).toBeLessThanOrEqual(6);
      seen.add(v);
    }
    expect(seen.size).toBe(6);
  });
});
