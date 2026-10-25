import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import { loadData } from '../src/sim/data';
import { advance, applyCommand, newGame } from '../src/sim';
import { restoreRng } from '../src/sim/rng';
import { stepRental } from '../src/sim/economy';
import { offerContracts, offerGrants, settleWeek } from '../src/sim/economy';
import { stepTraining } from '../src/sim/training';
import type { GameState, Grant } from '../src/sim/types';

const raw = () => structuredClone({ hardware, world, products });
const d = loadData(raw());
const dNoFail = (() => {
  const r = raw();
  r.world.failPerGpuDay.value = 0;
  return loadData(r);
})();

const base = () => newGame(d, 1, 'Lab');
/** Game state placed at the end of week `w` (hour = 168 w), ready for settleWeek. */
const atWeek = (w: number, s: GameState = base()): GameState => ({ ...s, hour: w * 168 });
const grant = (over: Partial<Grant> = {}): Grant => ({
  id: 'grant-1',
  p100eq: 2.5,
  hoursLeft: 500,
  weeksLeft: 8,
  status: 'offered',
  ...over,
});

describe('purchases never push cash below 0', () => {
  it('three purchases in the same tick: the ones that do not fit are rejected', () => {
    let s: GameState = { ...base(), cashUsd: 1000, rigs: [{ id: 'rig-1', model: 'open_frame' }] };
    for (let i = 0; i < 3; i++) s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    expect(s.cashUsd).toBe(1000 - 699);
    expect(s.cashUsd).toBeGreaterThanOrEqual(0);
    expect(s.gpus).toHaveLength(2);
    expect(s.pulso.some((p) => p.cause === 'warning')).toBe(true);
  });
});

describe('translation revenue', () => {
  it('settleWeek books weekServedMChars x price as a product line and resets the counter', () => {
    const s0 = atWeek(1);
    const s = settleWeek({ ...s0, product: { ...s0.product, weekServedMChars: 50 } }, d, restoreRng(1));
    const e = s.ledger[0]!;
    expect(e.lines.product).toBe(1000);
    expect(e.revenueUsd).toBe(1000);
    expect(s.product.weekServedMChars).toBe(0);
    expect(s.cashUsd).toBe(10000 + 1000 - e.costsUsd);
  });
});

describe('GPU rental', () => {
  const renting = (): GameState => ({ ...base(), allocation: { 'gpu-1': 'rent' } });
  it('1 GPU on rent for 7 days in June 2017 earns 28 $', () => {
    const s = advance(renting(), d, 168);
    const e = s.ledger[0]!;
    expect(e.lines.rental).toBeCloseTo(28, 6);
    expect(s.weekRentUsd).toBe(0);
  });
  it('after 2018-03-31 the rate falls to 1 $/day', () => {
    const s0 = { ...renting(), hour: 168 * 58 }; // July 2018, on a week boundary
    const s = advance(s0, d, 168);
    expect(s.ledger[0]!.lines.rental).toBeCloseTo(7, 6);
  });
  it('boom rate holds through 2018-03-31 inclusive and drops at 2018-04-01T00:00Z', () => {
    const msAt = (iso: string) => (Date.parse(iso) - Date.parse('2017-06-12T17:57:00Z')) / 3_600_000;
    // Game hours land on :57 past each hour.
    const last = Math.floor(msAt('2018-03-31T23:57:00Z'));
    const first = Math.ceil(msAt('2018-04-01T00:00:00Z'));
    const s = renting();
    expect(stepRental({ ...s, hour: last }, d).weekRentUsd).toBeCloseTo(4 / 24, 10);
    expect(stepRental({ ...s, hour: first }, d).weekRentUsd).toBeCloseTo(1 / 24, 10);
  });
  it('idle GPUs and a tripped breaker earn nothing', () => {
    expect(advance(base(), d, 168).ledger[0]!.lines.rental).toBe(0);
    const tripped = { ...renting(), power: { watts: 0, breakerTripped: true, weekKwh: 0 } };
    expect(advance(tripped, d, 1).weekRentUsd).toBe(0);
  });
});

describe('consulting', () => {
  it('offers only every 4th week; none otherwise', () => {
    const s = settleWeek(atWeek(3), d, restoreRng(7));
    expect(s.contracts).toHaveLength(0);
  });
  it('offers 0-2 contracts within the data ranges, deterministically', () => {
    const counts = new Set<number>();
    for (let seed = 1; seed < 60; seed++) {
      const s = offerContracts(atWeek(4), d, restoreRng(seed));
      counts.add(s.contracts.length);
      for (const c of s.contracts) {
        expect(c.status).toBe('offered');
        expect(c.usd).toBeGreaterThanOrEqual(3000);
        expect(c.usd).toBeLessThanOrEqual(12000);
        expect(c.usd % 100).toBe(0);
        expect(c.weeksTotal).toBeGreaterThanOrEqual(2);
        expect(c.weeksTotal).toBeLessThanOrEqual(6);
        expect(c.weeksLeft).toBe(c.weeksTotal);
      }
      expect(offerContracts(atWeek(4), d, restoreRng(seed))).toEqual(s);
    }
    expect([...counts].sort()).toEqual([0, 1, 2]);
  });
  it('unaccepted offers expire at the next offering; ids keep growing', () => {
    let s: GameState | undefined;
    for (let seed = 1; seed < 100; seed++) {
      const c = offerContracts(atWeek(4), d, restoreRng(seed));
      if (c.contracts.length === 2) {
        s = c;
        break;
      }
    }
    expect(s!.contracts.map((c) => c.id)).toEqual(['contract-1', 'contract-2']);
    const next = offerContracts(atWeek(8, s), d, restoreRng(1));
    expect(next.contracts.some((c) => c.id === 'contract-1' || c.id === 'contract-2')).toBe(false);
    for (const c of next.contracts) expect(Number(c.id.slice(9))).toBeGreaterThan(2);
  });
  it('accept_contract: offered -> active; anything else warns', () => {
    const s0 = { ...base(), contracts: [{ id: 'contract-1', usd: 6000, weeksTotal: 3, weeksLeft: 3, status: 'offered' as const }] };
    const s = applyCommand(s0, d, { t: 'accept_contract', contractId: 'contract-1' });
    expect(s.contracts[0]!.status).toBe('active');
    const again = applyCommand(s, d, { t: 'accept_contract', contractId: 'contract-1' });
    expect(again.pulso.at(-1)?.cause).toBe('warning');
  });
  it('active contract pays usd/weeksTotal per settle and ends done', () => {
    let s: GameState = { ...atWeek(1), contracts: [{ id: 'contract-1', usd: 6000, weeksTotal: 3, weeksLeft: 3, status: 'active' }] };
    for (let w = 1; w <= 3; w++) {
      s = settleWeek({ ...s, hour: w * 168 }, d, restoreRng(1));
      expect(s.ledger.at(-1)!.lines.consulting).toBe(2000);
    }
    expect(s.contracts[0]).toMatchObject({ status: 'done', weeksLeft: 0 });
    s = settleWeek({ ...s, hour: 4 * 168 }, d, restoreRng(1));
    expect(s.ledger.at(-1)!.lines.consulting).toBe(0);
  });
  it('an active contract halves training progress', () => {
    const s0: GameState = {
      ...base(),
      allocation: { 'gpu-1': 'train' },
      jobs: base().jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const } : j)),
      contracts: [{ id: 'contract-1', usd: 6000, weeksTotal: 3, weeksLeft: 3, status: 'active' }],
    };
    const done = (s: GameState) => s.jobs.find((j) => j.id === 'replicate_paper')!.doneP100h;
    expect(done(advance(s0, dNoFail, 10))).toBeCloseTo(5, 10);
    expect(done(advance({ ...s0, contracts: [] }, dNoFail, 10))).toBeCloseTo(10, 10);
  });
});

describe('compute grants', () => {
  it('offered once reputation >= 15 and only if no grant exists', () => {
    expect(offerGrants({ ...base(), reputation: 14 }, d).grants).toHaveLength(0);
    const s = offerGrants({ ...base(), reputation: 15 }, d);
    expect(s.grants).toEqual([grant()]);
    expect(offerGrants({ ...s, grants: [grant({ status: 'expired' })] }, d).grants).toHaveLength(1);
  });
  it('settleWeek offers the grant', () => {
    const s = settleWeek({ ...atWeek(1), reputation: 15 }, d, restoreRng(1));
    expect(s.grants).toHaveLength(1);
  });
  it('apply_grant: offered -> active', () => {
    const s = applyCommand({ ...base(), grants: [grant()] }, d, { t: 'apply_grant', grantId: 'grant-1' });
    expect(s.grants[0]!.status).toBe('active');
  });
  it('expires after 8 weeks', () => {
    let s: GameState = { ...base(), grants: [grant({ status: 'active' })] };
    for (let w = 1; w <= 7; w++) {
      s = settleWeek({ ...s, hour: w * 168 }, d, restoreRng(1));
      expect(s.grants[0]!.status).toBe('active');
    }
    s = settleWeek({ ...s, hour: 8 * 168 }, d, restoreRng(1));
    expect(s.grants[0]).toMatchObject({ status: 'expired', weeksLeft: 0 });
  });
  it('contributes only while hoursLeft > 0 and burns one hour per contributing hour', () => {
    const s0: GameState = {
      ...base(),
      allocation: { 'gpu-1': 'idle' },
      jobs: base().jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const } : j)),
      grants: [grant({ status: 'active', hoursLeft: 2 })],
    };
    let s = advance(s0, dNoFail, 1);
    expect(s.grants[0]!.hoursLeft).toBe(1);
    s = advance(s, dNoFail, 1);
    expect(s.grants[0]).toMatchObject({ hoursLeft: 0, status: 'expired' });
    const p = s.jobs[0]!.doneP100h;
    expect(p).toBeCloseTo(5, 10);
    expect(advance(s, dNoFail, 1).jobs[0]!.doneP100h).toBeCloseTo(5, 10);
  });
  it('a rolled-back hour does not burn grant hours', () => {
    const s0: GameState = {
      ...base(),
      allocation: { 'gpu-1': 'train' },
      power: { watts: 0, breakerTripped: true, weekKwh: 0 },
      jobs: base().jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const } : j)),
      grants: [grant({ status: 'active', hoursLeft: 5 })],
    };
    const s = stepTraining(s0, dNoFail, restoreRng(1));
    expect(s.grants[0]!.hoursLeft).toBe(5);
  });
});

describe('bankruptcy', () => {
  it('cash < 0 after settling for 4 consecutive weeks => bankrupt, with news in Pulso', () => {
    let s: GameState = { ...base(), cashUsd: -10000 };
    s = advance(s, dNoFail, 3 * 168);
    expect(s.negativeWeeks).toBe(3);
    expect(s.outcome).toBeNull();
    s = advance(s, dNoFail, 168);
    expect(s.negativeWeeks).toBe(4);
    expect(s.outcome).toBe('bankrupt');
    expect(s.pulso.some((p) => p.cause === 'news')).toBe(true);
  });
  it('a non-negative settle resets the streak', () => {
    let s = settleWeek({ ...atWeek(1), cashUsd: -5 }, d, restoreRng(1));
    expect(s.negativeWeeks).toBe(1);
    s = settleWeek({ ...s, hour: 2 * 168, cashUsd: 100 }, d, restoreRng(1));
    expect(s.negativeWeeks).toBe(0);
    expect(s.outcome).toBeNull();
  });
});

describe('ledger', () => {
  it('revenue = product + consulting + rental, costs = electricity, cashEnd = cash after settle', () => {
    const s0: GameState = {
      ...atWeek(1),
      weekRentUsd: 28,
      product: { ...base().product, weekServedMChars: 10 },
      power: { watts: 0, breakerTripped: false, weekKwh: 100 },
      contracts: [{ id: 'contract-1', usd: 4000, weeksTotal: 2, weeksLeft: 2, status: 'active' }],
    };
    const s = settleWeek(s0, d, restoreRng(1));
    const e = s.ledger[0]!;
    expect(e.lines).toMatchObject({ product: 200, consulting: 2000, rental: 28, electricity: 13 });
    expect(e.revenueUsd).toBe(2228);
    expect(e.costsUsd).toBe(13);
    expect(e.cashEndUsd).toBeCloseTo(s.cashUsd, 8);
    expect(s.cashUsd).toBeCloseTo(10000 + 2228 - 13, 8);
  });
});
