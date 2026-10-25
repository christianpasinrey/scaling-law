import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { advance, applyCommand, dateOf, newGame } from '../src/sim';
import type { Command } from '../src/sim';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const fresh = () => newGame(d, 42, 'Garage Lab');

describe('newGame', () => {
  it('starts with one tower, one 1080 Ti and the starting cash', () => {
    const s = fresh();
    expect(s.cashUsd).toBe(10000);
    expect(s.rigs).toEqual([{ id: 'rig-1', model: 'tower_2017' }]);
    expect(s.gpus).toHaveLength(1);
    expect(s.gpus[0]).toMatchObject({ id: 'gpu-1', model: 'gtx1080ti', rigId: 'rig-1', slot: 0 });
    expect(s.allocation['gpu-1']).toBe('idle');
    expect(s.jobs.map((j) => [j.id, j.status, j.workP100h])).toEqual([
      ['replicate_paper', 'ready', 96],
      ['translation_v2', 'locked', 400],
    ]);
    expect(s.product.launched).toBe(false);
    expect(s.product.priceUsdPerMChars).toBe(20);
    expect(s.outcome).toBeNull();
  });
  it('is JSON-serialisable without loss', () => {
    const s = fresh();
    expect(JSON.parse(JSON.stringify(s))).toEqual(s);
  });
});

describe('dateOf', () => {
  it('maps hour 0 to the arXiv publication instant', () => {
    expect(dateOf(fresh())).toBe('2017-06-12T17:57:00.000Z');
  });
  it('adds whole hours', () => {
    expect(dateOf({ ...fresh(), hour: 24 })).toBe('2017-06-13T17:57:00.000Z');
  });
});

describe('advance', () => {
  it('adds exactly one ledger entry per 168 h', () => {
    const s = advance(fresh(), d, 168);
    expect(s.hour).toBe(168);
    expect(s.ledger).toHaveLength(1);
    expect(s.ledger[0]).toMatchObject({ week: 1, cashEndUsd: s.cashUsd });
    expect(advance(s, d, 167).ledger).toHaveLength(1);
    expect(advance(s, d, 168).ledger).toHaveLength(2);
  });
  it('is split-invariant', () => {
    const a = advance(fresh(), d, 400);
    const b = advance(advance(advance(fresh(), d, 100), d, 200), d, 100);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });
  it('hours <= 0 returns the same state', () => {
    const s = fresh();
    expect(advance(s, d, 0)).toBe(s);
    expect(advance(s, d, -5)).toBe(s);
  });
  it('does not change the state once an outcome is set', () => {
    const s = { ...fresh(), outcome: 'bankrupt' as const };
    expect(advance(s, d, 500)).toEqual(s);
    expect(applyCommand(s, d, { t: 'set_price', usdPerMChars: 5 })).toEqual(s);
  });
  it('same seed and commands give identical JSON after 4 weeks', () => {
    const cmds: Command[] = [
      { t: 'allocate', gpuId: 'gpu-1', to: 'train' },
      { t: 'start_job', jobId: 'replicate_paper' },
      { t: 'set_price', usdPerMChars: 25 },
    ];
    const run = () => {
      let s = fresh();
      for (const c of cmds) s = applyCommand(s, d, c);
      return advance(s, d, 168 * 4);
    };
    expect(JSON.stringify(run())).toBe(JSON.stringify(run()));
    expect(run().ledger).toHaveLength(4);
  });
});

describe('commands', () => {
  it('does not mutate the input state', () => {
    const s = fresh();
    const snap = JSON.stringify(s);
    applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    expect(JSON.stringify(s)).toBe(snap);
  });
  it('buy_gpu fills the free slot, charges cash, allocates idle', () => {
    const s = applyCommand(fresh(), d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    expect(s.gpus).toHaveLength(2);
    expect(s.gpus[1]).toMatchObject({ id: 'gpu-2', slot: 1, rigId: 'rig-1' });
    expect(s.cashUsd).toBe(10000 - 699);
    expect(s.allocation['gpu-2']).toBe('idle');
  });
  it('buy_gpu rejects a full rig with a warning', () => {
    let s = applyCommand(fresh(), d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    const before = s;
    s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    expect(s.gpus).toHaveLength(2);
    expect(s.cashUsd).toBe(before.cashUsd);
    expect(s.pulso.at(-1)?.cause).toBe('warning');
  });
  it('buy_gpu rejects unknown model, unknown rig and unreleased model', () => {
    for (const c of [
      { t: 'buy_gpu', model: 'nope', rigId: 'rig-1' },
      { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-9' },
      { t: 'buy_gpu', model: 'titan_v', rigId: 'rig-1' },
    ] as Command[]) {
      const s = applyCommand(fresh(), d, c);
      expect(s.gpus).toHaveLength(1);
      expect(s.cashUsd).toBe(10000);
      expect(s.pulso.at(-1)?.cause).toBe('warning');
    }
  });
  it('buy_gpu works once the release date has passed', () => {
    const late = { ...fresh(), hour: 24 * 200 };
    const s = applyCommand(late, d, { t: 'buy_gpu', model: 'titan_v', rigId: 'rig-1' });
    expect(s.gpus).toHaveLength(2);
  });
  it('buy_rig respects the release date and cash', () => {
    expect(applyCommand(fresh(), d, { t: 'buy_rig', model: 'open_frame' }).rigs).toHaveLength(1);
    const late = { ...fresh(), hour: 24 * 250 };
    const s = applyCommand(late, d, { t: 'buy_rig', model: 'open_frame' });
    expect(s.rigs.map((r) => r.id)).toEqual(['rig-1', 'rig-2']);
    expect(s.cashUsd).toBe(10000 - 350);
  });
  it('purchases never take cash below 0', () => {
    let s = { ...fresh(), cashUsd: 1000, hour: 24 * 250 };
    s = applyCommand(s, d, { t: 'buy_rig', model: 'open_frame' });
    expect(s.cashUsd).toBe(650);
    s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-2' });
    s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-2' });
    expect(s.cashUsd).toBe(650);
    expect(s.gpus).toHaveLength(1);
    expect(s.pulso.some((p) => p.cause === 'warning')).toBe(true);
  });
  it('allocate changes allocation and rejects unknown gpus', () => {
    let s = applyCommand(fresh(), d, { t: 'allocate', gpuId: 'gpu-1', to: 'serve' });
    expect(s.allocation['gpu-1']).toBe('serve');
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-9', to: 'train' });
    expect(s.allocation['gpu-9']).toBeUndefined();
    expect(s.pulso.at(-1)?.cause).toBe('warning');
  });
  it('start_job runs a ready job; locked or unknown jobs warn', () => {
    let s = applyCommand(fresh(), d, { t: 'start_job', jobId: 'replicate_paper' });
    expect(s.jobs[0]?.status).toBe('running');
    s = applyCommand(fresh(), d, { t: 'start_job', jobId: 'translation_v2' });
    expect(s.jobs[1]?.status).toBe('locked');
    expect(s.pulso.at(-1)?.cause).toBe('warning');
    s = applyCommand(fresh(), d, { t: 'start_job', jobId: 'x' });
    expect(s.pulso.at(-1)?.cause).toBe('warning');
  });
  it('set_price validates and sets', () => {
    expect(applyCommand(fresh(), d, { t: 'set_price', usdPerMChars: 12.5 }).product.priceUsdPerMChars).toBe(12.5);
    for (const v of [0, -1, NaN, Infinity, 0.5, 500]) {
      const s = applyCommand(fresh(), d, { t: 'set_price', usdPerMChars: v });
      expect(s.product.priceUsdPerMChars).toBe(20);
      expect(s.pulso.at(-1)?.cause).toBe('warning');
    }
  });
  it('not-yet-implemented commands warn and leave the rest unchanged', () => {
    const base = fresh();
    for (const c of [
      { t: 'accept_contract', contractId: 'c' },
      { t: 'apply_grant', grantId: 'g' },
      { t: 'reset_breaker' },
      { t: 'accept_round' },
      { t: 'decline_round' },
    ] as Command[]) {
      const s = applyCommand(base, d, c);
      expect({ ...s, pulso: [] }).toEqual({ ...base, pulso: [] });
      expect(s.pulso.at(-1)?.cause).toBe('warning');
    }
  });
});
