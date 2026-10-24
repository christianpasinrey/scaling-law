import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import { loadData } from '../src/sim/data';
import { advance, applyCommand, newGame } from '../src/sim';
import { gpuPerfFactor } from '../src/sim/power';
import type { GameState, OwnedGpu } from '../src/sim/types';

const d = loadData(structuredClone({ hardware, world, products }));

function gpuAt(id: number, rigId: string, slot: number): OwnedGpu {
  return { id: `gpu-${id}`, model: 'gtx1080ti', rigId, slot, tempC: 25, perf: 1 };
}

/** Rig `rigModel` with `n` 1080 Tis, all on 'train'. */
function rigWith(n: number, rigModel: 'tower_2017' | 'open_frame'): GameState {
  const s = newGame(d, 1, 'Lab');
  const rigId = rigModel === 'tower_2017' ? 'rig-1' : 'rig-2';
  const rigs = rigModel === 'tower_2017' ? s.rigs : [{ id: 'rig-2', model: rigModel } as const];
  const gpus = Array.from({ length: n }, (_, i) => gpuAt(i + 1, rigId, i));
  return {
    ...s,
    rigs: [...rigs],
    gpus,
    allocation: Object.fromEntries(gpus.map((g) => [g.id, 'train' as const])),
  };
}

describe('thermals', () => {
  it('one GPU at full load never reaches 84 C', () => {
    let s = rigWith(1, 'tower_2017');
    for (let i = 0; i < 48; i++) {
      s = advance(s, d, 1);
      expect(s.gpus[0]!.tempC).toBeLessThan(84);
      expect(s.gpus[0]!.perf).toBe(1);
    }
    expect(s.gpus[0]!.tempC).toBeGreaterThan(79);
  });
  it('three GPUs sharing a tower throttle to 0.7', () => {
    const s = advance(rigWith(3, 'tower_2017'), d, 4);
    expect(s.gpus.some((g) => g.tempC >= 84)).toBe(true);
    expect(s.gpus.every((g) => g.perf === 0.7)).toBe(true);
    expect(gpuPerfFactor(s.gpus[0]!)).toBe(0.7);
  });
  it('three GPUs on the open frame do not throttle', () => {
    const s = advance(rigWith(3, 'open_frame'), d, 48);
    expect(Math.max(...s.gpus.map((g) => g.tempC))).toBeLessThan(84);
    expect(s.gpus.every((g) => g.perf === 1)).toBe(true);
  });
  it('shuts a GPU down at 91 C and recovers it after cooling below 84 C', () => {
    let s = advance(rigWith(3, 'tower_2017'), d, 7);
    expect(s.gpus.every((g) => g.tempC >= 91 && g.perf === 0)).toBe(true);
    expect(gpuPerfFactor(s.gpus[0]!)).toBe(0);
    // Shut down => load 0 => the target drops to 42 C and the GPU cools below 84 C in one step.
    s = advance(s, d, 1);
    expect(s.gpus.every((g) => g.tempC < 84)).toBe(true);
    expect(s.gpus.every((g) => g.perf === 1)).toBe(true);
  });
  it('idle GPUs cool towards the idle target', () => {
    let s = rigWith(1, 'tower_2017');
    s = { ...s, allocation: { 'gpu-1': 'idle' } };
    s = advance(s, d, 24);
    expect(s.gpus[0]!.tempC).toBeCloseTo(30, 0);
    expect(s.power.watts).toBe(150);
  });
});

describe('power and breaker', () => {
  it('draws rig base watts plus GPU watts times load', () => {
    const s = advance(rigWith(2, 'tower_2017'), d, 1);
    expect(s.power.watts).toBe(150 + 2 * 250);
    expect(s.power.breakerTripped).toBe(false);
  });
  it('trips above 1800 W: loads go to 0 and Pulso gets an outage item', () => {
    // open frame (150) + 6 x 250 = 1650 W; add the tower (150) and one more GPU: 1650 + 150 + 250 = 2050 W.
    const a = rigWith(6, 'open_frame');
    const t = rigWith(1, 'tower_2017');
    const s0: GameState = {
      ...a,
      rigs: [...t.rigs, ...a.rigs],
      gpus: [...a.gpus, { ...gpuAt(7, 'rig-1', 0) }],
      allocation: { ...a.allocation, 'gpu-7': 'train' },
    };
    const s = advance(s0, d, 1);
    expect(s.power.breakerTripped).toBe(true);
    expect(s.power.watts).toBe(300);
    const item = s.pulso.find((p) => p.cause === 'outage');
    expect(item?.focus).toEqual({ kind: 'power' });
    const later = advance(s, d, 24);
    expect(later.power.breakerTripped).toBe(true);
    expect(later.pulso.filter((p) => p.cause === 'outage')).toHaveLength(1);
    expect(later.gpus.every((g) => g.tempC < 40)).toBe(true);
  });
  it('reset_breaker clears the flag; still over the limit it trips again next step', () => {
    const a = rigWith(6, 'open_frame');
    const t = rigWith(1, 'tower_2017');
    const s0: GameState = {
      ...a,
      rigs: [...t.rigs, ...a.rigs],
      gpus: [...a.gpus, gpuAt(7, 'rig-1', 0)],
      allocation: { ...a.allocation, 'gpu-7': 'train' },
    };
    const tripped = advance(s0, d, 1);
    const reset = applyCommand(tripped, d, { t: 'reset_breaker' });
    expect(reset.power.breakerTripped).toBe(false);
    expect(advance(reset, d, 1).power.breakerTripped).toBe(true);
    // Deallocating the extra GPU makes the reset stick.
    const fixed = applyCommand(reset, d, { t: 'allocate', gpuId: 'gpu-7', to: 'idle' });
    const ok = advance(fixed, d, 1);
    expect(ok.power.breakerTripped).toBe(false);
    expect(ok.power.watts).toBeLessThanOrEqual(1800);
  });
  it('reset_breaker without a trip warns', () => {
    const s = applyCommand(newGame(d, 1, 'Lab'), d, { t: 'reset_breaker' });
    expect(s.pulso.at(-1)?.cause).toBe('warning');
  });
});

describe('energy cost', () => {
  it('weekly kWh x price enters the ledger and reduces cash', () => {
    const s0 = rigWith(2, 'tower_2017'); // 650 W constant (open-ended temps stay below shutdown? 2 GPUs: target 86, throttled but powered)
    const s = advance(s0, d, 168);
    const entry = s.ledger[0]!;
    const kwh = (168 * 650) / 1000;
    expect(entry.lines.electricity).toBeCloseTo(kwh * 0.13, 6);
    expect(entry.costsUsd).toBeCloseTo(kwh * 0.13, 6);
    expect(s.cashUsd).toBeCloseTo(10000 - kwh * 0.13, 6);
    expect(entry.cashEndUsd).toBeCloseTo(s.cashUsd, 6);
    expect(s.power.weekKwh).toBe(0);
  });
  it('cash may go negative from running costs', () => {
    const s = advance({ ...rigWith(2, 'tower_2017'), cashUsd: 1 }, d, 168);
    expect(s.cashUsd).toBeLessThan(0);
  });
});

describe('advance purity', () => {
  it('does not mutate its input state', () => {
    const s0 = rigWith(3, 'tower_2017');
    const snap = JSON.stringify(s0);
    advance(s0, d, 200);
    expect(JSON.stringify(s0)).toBe(snap);
  });
});
