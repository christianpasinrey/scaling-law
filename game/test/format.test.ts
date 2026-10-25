import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData, newGame } from '../src/sim';
import type { GameState } from '../src/sim';
import {
  brainCard,
  conceptsPresent,
  formatDate,
  formatDay,
  formatDecimal,
  formatHours,
  formatInt,
  formatUsd,
  fraction,
  freeSlot,
  gpuSlotLabel,
  jobEtaHours,
  lastWeekBalance,
  lossPolyline,
  powerBar,
  powerZone,
  pulsoNewestFirst,
  shopItems,
  shopReasonText,
  t,
  trainingRate,
} from '../src/ui/format';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const fresh = (): GameState => newGame(d, 7, 'Lab');
/** Hours from the start (2017-06-12T17:57Z) to the given UTC date at 17:57. */
const hoursTo = (isoDay: string) => Math.round((Date.parse(`${isoDay}T17:57:00Z`) - Date.parse('2017-06-12T17:57:00Z')) / 3_600_000);
const at = (s: GameState, isoDay: string): GameState => ({ ...s, hour: hoursTo(isoDay) });

describe('t', () => {
  it('fills placeholders and leaves unknown ones', () => {
    expect(t('rig.slot', { n: 2 })).toBe('ranura 2');
    expect(t('rig.slot')).toBe('ranura {n}');
  });
});

describe('numbers and money', () => {
  it('groups thousands with dots, always', () => {
    expect(formatInt(1440)).toBe('1.440');
    expect(formatInt(10000)).toBe('10.000');
    expect(formatInt(1500000)).toBe('1.500.000');
    expect(formatInt(999)).toBe('999');
    expect(formatInt(-1234.6)).toBe('−1.235');
    expect(formatInt(NaN)).toBe('—');
  });
  it('formats dollars, signed when asked', () => {
    expect(formatUsd(10000)).toBe('10.000 $');
    expect(formatUsd(250.4, { signed: true })).toBe('+250 $');
    expect(formatUsd(-50, { signed: true })).toBe('−50 $');
    expect(formatUsd(0, { signed: true })).toBe('0 $');
  });
  it('uses a decimal comma', () => {
    expect(formatDecimal(0.13, 2)).toBe('0,13');
    expect(formatDecimal(1234.5, 1)).toBe('1.234,5');
    expect(formatDecimal(-0.7, 1)).toBe('−0,7');
    expect(formatDecimal(-0.001, 1)).toBe('0,0');
  });
  it('formats durations', () => {
    expect(formatHours(5)).toBe('5 h');
    expect(formatHours(96)).toBe('4 d 0 h');
    expect(formatHours(27.2)).toBe('1 d 4 h');
  });
  it('fraction never NaN', () => {
    expect(fraction(5, 0)).toBe(0);
    expect(fraction(50, 100)).toBe(0.5);
    expect(fraction(150, 100)).toBe(1);
  });
});

describe('dates', () => {
  it('formats the game start as "12 jun 2017 · 17:57"', () => {
    expect(formatDate('2017-06-12T17:57:00.000Z')).toBe('12 jun 2017 · 17:57');
  });
  it('uses UTC and Spanish month abbreviations', () => {
    expect(formatDate('2017-12-31T23:57:00Z')).toBe('31 dic 2017 · 23:57');
    expect(formatDate('2018-01-01T00:57:00Z')).toBe('1 ene 2018 · 00:57');
    expect(formatDay('2017-12-07')).toBe('7 dic 2017');
  });
  it('is safe on garbage', () => {
    expect(formatDate('nope')).toBe('—');
  });
});

describe('power bar zones', () => {
  const w = { circuitSafeWatts: 1440, circuitWatts: 1800 };
  it('ok up to 1.440 W, amber up to 1.800 W, red above', () => {
    expect(powerZone(1440, 1440, 1800, false)).toBe('ok');
    expect(powerZone(1441, 1440, 1800, false)).toBe('amber');
    expect(powerZone(1800, 1440, 1800, false)).toBe('amber');
    expect(powerZone(1801, 1440, 1800, false)).toBe('red');
  });
  it('red while the breaker is tripped, whatever the draw', () => {
    expect(powerZone(150, 1440, 1800, true)).toBe('red');
  });
  it('places both marks inside the bar and clamps the fill', () => {
    const b = powerBar(400, w, false);
    expect(b.safePct).toBeGreaterThan(0);
    expect(b.tripPct).toBeGreaterThan(b.safePct);
    expect(b.tripPct).toBeLessThan(100);
    expect(powerBar(99999, w, false).pct).toBe(100);
    expect(powerBar(NaN, w, false).pct).toBe(0);
    expect(powerBar(-5, w, false).pct).toBe(0);
  });
});

describe('ledger balance', () => {
  it('is null before the first settlement and revenue − costs after', () => {
    const s = fresh();
    expect(lastWeekBalance(s)).toBeNull();
    const withWeeks: GameState = {
      ...s,
      ledger: [
        { week: 1, revenueUsd: 10, costsUsd: 3, cashEndUsd: 0, lines: {} },
        { week: 2, revenueUsd: 100, costsUsd: 140, cashEndUsd: 0, lines: {} },
      ],
    };
    expect(lastWeekBalance(withWeeks)).toEqual({ week: 2, revenueUsd: 100, costsUsd: 140, netUsd: -40 });
  });
});

describe('shop availability', () => {
  const byId = (s: GameState, id: string) => shopItems(s, d).find((i) => i.id === id)!;
  it('at the start: 1080 Ti buyable into tower slot 2, Titan V and frame not released', () => {
    const s = fresh();
    const gtx = byId(s, 'gtx1080ti');
    expect(gtx.reason).toBeNull();
    expect(gtx.target).toEqual({ rigId: 'rig-1', slot: 1 });
    expect(byId(s, 'titan_v').reason).toBe('not_released');
    expect(shopReasonText(byId(s, 'titan_v'))).toBe('Disponible desde el 7 dic 2017');
    expect(byId(s, 'open_frame').reason).toBe('not_released');
  });
  it('Titan V from 2017-12-07, open frame from 2018-01-01', () => {
    expect(byId(at(fresh(), '2017-12-06'), 'titan_v').reason).toBe('not_released');
    expect(byId(at(fresh(), '2017-12-07'), 'titan_v').reason).toBeNull();
    expect(byId(at(fresh(), '2017-12-31'), 'open_frame').reason).toBe('not_released');
    expect(byId(at(fresh(), '2018-01-01'), 'open_frame').reason).toBeNull();
  });
  it('no slot beats no cash; no cash when it does not fit the budget', () => {
    const s = fresh();
    const full: GameState = {
      ...s,
      cashUsd: 100,
      gpus: [...s.gpus, { id: 'gpu-2', model: 'gtx1080ti', rigId: 'rig-1', slot: 1, tempC: 25, perf: 1 }],
    };
    expect(freeSlot(full, d)).toBeNull();
    expect(byId(full, 'gtx1080ti').reason).toBe('no_slot');
    expect(byId({ ...s, cashUsd: 698 }, 'gtx1080ti').reason).toBe('no_cash');
    expect(byId({ ...s, cashUsd: 699 }, 'gtx1080ti').reason).toBeNull();
  });
  it('a bought frame offers its slots', () => {
    const s = at(fresh(), '2018-01-02');
    const full: GameState = {
      ...s,
      rigs: [...s.rigs, { id: 'rig-2', model: 'open_frame' }],
      gpus: [...s.gpus, { id: 'gpu-2', model: 'gtx1080ti', rigId: 'rig-1', slot: 1, tempC: 25, perf: 1 }],
    };
    expect(freeSlot(full, d)).toEqual({ rigId: 'rig-2', slot: 0 });
    expect(gpuSlotLabel(full, d, full.gpus[1]!)).toBe('GTX 1080 Ti · Torre · ranura 2');
  });
});

describe('training rate', () => {
  it('is 0 (not NaN) with no GPU training, and ETA is null', () => {
    const s = fresh();
    expect(trainingRate(s, d)).toBe(0);
    expect(jobEtaHours(s.jobs[0]!, 0)).toBeNull();
  });
  it('sums p100eq × perf, halves under a contract, adds live grants, 0 when tripped', () => {
    const s0 = fresh();
    const s: GameState = {
      ...s0,
      gpus: [...s0.gpus, { id: 'gpu-2', model: 'gtx1080ti', rigId: 'rig-1', slot: 1, tempC: 85, perf: 0.7 }],
      allocation: { 'gpu-1': 'train', 'gpu-2': 'train' },
    };
    expect(trainingRate(s, d)).toBeCloseTo(1.7);
    const k: GameState = { ...s, contracts: [{ id: 'c', usd: 1, weeksTotal: 1, weeksLeft: 1, status: 'active' }] };
    expect(trainingRate(k, d)).toBeCloseTo(0.85);
    const g: GameState = { ...s, grants: [{ id: 'g', p100eq: 2.5, hoursLeft: 10, weeksLeft: 2, status: 'active' }] };
    expect(trainingRate(g, d)).toBeCloseTo(4.2);
    expect(trainingRate({ ...s, power: { ...s.power, breakerTripped: true } }, d)).toBe(0);
    expect(jobEtaHours(s.jobs[0]!, 2)).toBe(48);
  });
});

describe('loss polyline', () => {
  it('needs 2 points and maps lo..hi to bottom..top', () => {
    expect(lossPolyline([], 100, 20, 0, 10)).toBe('');
    expect(lossPolyline([5], 100, 20, 0, 10)).toBe('');
    expect(lossPolyline([10, 0], 100, 20, 0, 10)).toBe('0.0,0.0 100.0,20.0');
  });
  it('never emits NaN for a flat range', () => {
    expect(lossPolyline([2, 2], 10, 10, 2, 2)).not.toContain('NaN');
  });
});

describe('pulso and concepts', () => {
  it('lists the feed newest first', () => {
    const s = fresh();
    const p: GameState = {
      ...s,
      pulso: [
        { id: 'a', hour: 1, cause: 'news', text: 'a', count: 1 },
        { id: 'b', hour: 5, cause: 'news', text: 'b', count: 3 },
      ],
    };
    expect(pulsoNewestFirst(p).map((i) => i.id)).toEqual(['b', 'a']);
  });
  it('introduces concepts as they appear', () => {
    const s = fresh();
    expect(conceptsPresent(s, d)).toEqual(['gpu']);
    const running: GameState = {
      ...s,
      allocation: { 'gpu-1': 'rent' },
      jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const, lossCurve: [9] } : j)),
      power: { ...s.power, breakerTripped: true },
    };
    const c = conceptsPresent(running, d);
    for (const id of ['training', 'p100eq', 'loss', 'checkpoint', 'breaker', 'gpu_rental']) expect(c).toContain(id);
    expect(conceptsPresent(at(fresh(), '2018-01-01'), d)).toEqual(expect.arrayContaining(['gpu_titan_v', 'vram', 'open_frame']));
  });
  it('maps brain blocks to cards', () => {
    expect(brainCard('embed_in')).toBe('embedding');
    expect(brainCard('embed_out')).toBe('embedding');
    expect(brainCard('enc_3')).toBe('encoder');
    expect(brainCard('dec_0')).toBe('decoder');
    expect(brainCard('head')).toBe('softmax');
  });
});
