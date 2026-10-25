import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { advance, newGame } from '../src/sim';
import { restoreRng } from '../src/sim/rng';
import type { Rng } from '../src/sim/rng';
import { lossAt, stepTraining } from '../src/sim/training';
import type { GameData, GameState, OwnedGpu } from '../src/sim/types';

const raw = () => structuredClone({ hardware, world, products, pulso });
const d = loadData(raw());
/** Same data with no hardware failures. */
const dNoFail = (() => {
  const r = raw();
  r.world.failPerGpuDay.value = 0;
  return loadData(r);
})();

function gpu(i: number, rigId = 'rig-2'): OwnedGpu {
  return { id: `gpu-${i}`, model: 'gtx1080ti', rigId, slot: i - 1, tempC: 25, perf: 1 };
}

/** n 1080 Tis on an open frame, all on 'train', replicate_paper running. */
function training(n: number): GameState {
  const s = newGame(d, 1, 'Lab');
  const gpus = Array.from({ length: n }, (_, i) => gpu(i + 1));
  return {
    ...s,
    rigs: [{ id: 'rig-2', model: 'open_frame' }],
    gpus,
    allocation: Object.fromEntries(gpus.map((g) => [g.id, 'train' as const])),
    jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const } : j)),
  };
}

const job = (s: GameState, id = 'replicate_paper') => s.jobs.find((j) => j.id === id)!;
const fakeRng = (...vals: number[]): Rng => {
  let i = 0;
  return { next: () => vals[Math.min(i++, vals.length - 1)]!, int: () => 0, state: () => 0 };
};

describe('lossAt', () => {
  it('follows 9.0 * (1 - f)^1.6 + 1.8', () => {
    expect(lossAt(d, 0)).toBeCloseTo(10.8, 10);
    expect(lossAt(d, 1)).toBeCloseTo(1.8, 10);
    expect(lossAt(d, 0.5)).toBeCloseTo(9 * 0.5 ** 1.6 + 1.8, 10);
  });
});

describe('progress', () => {
  it('one 1080 Ti finishes replicate_paper in 96 h +-1', () => {
    let s = training(1);
    let h = 0;
    while (job(s).status === 'running' && h < 200) {
      s = advance(s, dNoFail, 1);
      h++;
    }
    expect(Math.abs(h - 96)).toBeLessThanOrEqual(1);
    expect(job(s).status).toBe('done');
  });
  it('two GPUs finish in 48 h +-1', () => {
    let s = training(2);
    let h = 0;
    while (job(s).status === 'running' && h < 200) {
      s = advance(s, dNoFail, 1);
      h++;
    }
    expect(Math.abs(h - 48)).toBeLessThanOrEqual(1);
  });
  it('throttled GPUs advance at 0.7', () => {
    const s0 = training(1);
    const s = stepTraining({ ...s0, gpus: [{ ...s0.gpus[0]!, perf: 0.7 }] }, dNoFail, fakeRng(0.99));
    expect(job(s).doneP100h).toBeCloseTo(0.7, 10);
  });
  it('only GPUs on train count and nothing advances unless the job runs', () => {
    const s0 = training(2);
    const mixed = stepTraining({ ...s0, allocation: { 'gpu-1': 'train', 'gpu-2': 'serve' } }, dNoFail, fakeRng(0.99));
    expect(job(mixed).doneP100h).toBe(1);
    const ready = stepTraining(
      { ...s0, jobs: s0.jobs.map((j) => ({ ...j, status: 'ready' as const })) },
      dNoFail,
      fakeRng(0.99),
    );
    expect(ready.jobs.every((j) => j.doneP100h === 0)).toBe(true);
  });
  it('an active research contract halves own progress; active grants add their P100-eq', () => {
    const s0 = training(1);
    const active = { id: 'c1', usd: 1000, weeksTotal: 4, weeksLeft: 4, status: 'active' as const };
    expect(job(stepTraining({ ...s0, contracts: [active] }, dNoFail, fakeRng(0.99))).doneP100h).toBeCloseTo(0.5, 10);
    const offered = { ...active, status: 'offered' as const };
    expect(job(stepTraining({ ...s0, contracts: [offered] }, dNoFail, fakeRng(0.99))).doneP100h).toBe(1);
    const grants = [
      { id: 'g1', p100eq: 2, hoursLeft: 10, weeksLeft: 3, status: 'active' as const },
      { id: 'g2', p100eq: 5, hoursLeft: 10, weeksLeft: 3, status: 'offered' as const },
    ];
    expect(job(stepTraining({ ...s0, grants }, dNoFail, fakeRng(0.99))).doneP100h).toBe(3);
  });
  it('checkpoints every 4 h and records the loss curve', () => {
    let s = training(1);
    s = advance(s, dNoFail, 6); // steps at hours 0..5; checkpoints at hours 0 and 4
    expect(job(s).lossCurve).toHaveLength(2);
    expect(job(s).checkpointP100h).toBe(5);
    expect(job(s).lossCurve[1]).toBeCloseTo(lossAt(d, 5 / 96), 10);
  });
});

describe('loss curve', () => {
  it('ends at the final loss lossAt(1) when the job completes', () => {
    let s = training(1);
    while (job(s).status === 'running') s = advance(s, dNoFail, 1);
    const curve = job(s).lossCurve;
    expect(curve.at(-1)).toBeCloseTo(lossAt(d, 1), 10);
    expect(curve.filter((v) => v === lossAt(d, 1))).toHaveLength(1);
  });
  it('adds no point at a checkpoint where nothing trained', () => {
    let s = advance(training(1), dNoFail, 5); // steps at hours 0..4; checkpoints at 0 and 4 hold all progress
    const n = job(s).lossCurve.length;
    s = { ...s, allocation: { 'gpu-1': 'idle' } };
    s = advance(s, dNoFail, 24); // six checkpoints with no trainer
    expect(job(s).lossCurve.length).toBe(n);
    expect(new Set(job(s).lossCurve).size).toBe(job(s).lossCurve.length);
  });
});

describe('completion news', () => {
  it('replicating the paper and finishing v2 each post a Pulso news item from data', () => {
    let s = training(6);
    while (job(s).status === 'running') s = advance(s, dNoFail, 1);
    expect(s.pulso.some((p) => p.cause === 'news' && p.text === d.pulso.news.replicatePaper)).toBe(true);
    expect(d.pulso.news.replicatePaper.endsWith('.')).toBe(true);
    s = { ...s, jobs: s.jobs.map((j) => (j.id === 'translation_v2' ? { ...j, status: 'running' as const } : j)) };
    let h = 0;
    while (job(s, 'translation_v2').status === 'running' && h++ < 5000) s = advance(s, dNoFail, 1);
    expect(job(s, 'translation_v2').status).toBe('done');
    expect(s.flags.model_v2).toBe(true);
    expect(s.pulso.some((p) => p.cause === 'news' && p.text === d.pulso.news.translationV2)).toBe(true);
  });
});

describe('failures', () => {
  it('a forced failure returns progress to the last checkpoint, not to 0', () => {
    let s = training(1);
    s = advance(s, dNoFail, 10); // last checkpoint at hour 8 => 9 P100-h
    const cp = job(s).checkpointP100h;
    expect(cp).toBeGreaterThan(0);
    expect(job(s).doneP100h).toBeGreaterThan(cp);
    const failed = stepTraining(s, d, fakeRng(0)); // 0 < p => failure
    expect(job(failed).doneP100h).toBe(cp);
    expect(job(failed).checkpointP100h).toBe(cp);
    const item = failed.pulso.find((p) => p.cause === 'outage' && p.focus?.kind === 'gpu');
    expect(item?.focus?.id).toBe('gpu-1');
  });
  it('no failure when the draw is above p', () => {
    const s = advance(training(1), dNoFail, 6);
    const ok = stepTraining(s, d, fakeRng(0.5));
    expect(job(ok).doneP100h).toBe(job(s).doneP100h + 1);
    expect(ok.pulso).toHaveLength(s.pulso.length);
  });
  it('failure probability is failPerGpuDay / 24 per hour (not multiplied again)', () => {
    const s = advance(training(1), dNoFail, 6);
    const p = d.world.failPerGpuDay.value / 24;
    expect(job(stepTraining(s, d, fakeRng(p * 0.99))).doneP100h).toBe(job(s).checkpointP100h);
    expect(job(stepTraining(s, d, fakeRng(p * 1.01))).doneP100h).toBe(job(s).doneP100h + 1);
  });
  it('the breaker tripping returns progress to the checkpoint and is idempotent', () => {
    let s = advance(training(1), dNoFail, 10);
    const cp = job(s).checkpointP100h;
    s = { ...s, power: { ...s.power, breakerTripped: true } };
    const a = stepTraining(s, dNoFail, fakeRng(0.99));
    expect(job(a).doneP100h).toBe(cp);
    const b = stepTraining(a, dNoFail, fakeRng(0.99));
    expect(job(b).doneP100h).toBe(cp);
  });
  it('an overloaded circuit mid-training loses only back to the checkpoint', () => {
    let s = training(2);
    s = advance(s, dNoFail, 10);
    const before = job(s).doneP100h;
    expect(before).toBeGreaterThan(0);
    // Add GPUs until the draw exceeds 1800 W: 7 x 250 W plus the rig base.
    const extra = Array.from({ length: 5 }, (_, i) => gpu(i + 3));
    s = {
      ...s,
      gpus: [...s.gpus, ...extra],
      allocation: { ...s.allocation, ...Object.fromEntries(extra.map((g) => [g.id, 'train' as const])) },
    };
    s = advance(s, dNoFail, 1);
    expect(s.power.breakerTripped).toBe(true);
    expect(job(s).doneP100h).toBe(job(s).checkpointP100h);
    expect(job(s).doneP100h).toBeGreaterThan(0);
    expect(job(s).doneP100h).toBeLessThan(before);
  });
});

describe('completion', () => {
  it('replicate_paper: done, +15 reputation, praise in Pulso, translation_v2 ready, API launched', () => {
    let s = training(2);
    s = advance(s, dNoFail, 60);
    expect(job(s).status).toBe('done');
    expect(job(s).doneP100h).toBe(96);
    expect(s.reputation).toBe(15);
    expect(s.pulso.some((p) => p.cause === 'news' && p.text === 'Has replicado el paper.')).toBe(true);
    expect(job(s, 'translation_v2').status).toBe('ready');
    expect(s.product.launched).toBe(true);
  });
  it('translation_v2: +15 reputation and the model_v2 flag', () => {
    let s = training(2);
    s = advance(s, dNoFail, 60);
    s = { ...s, jobs: s.jobs.map((j) => (j.id === 'translation_v2' ? { ...j, status: 'running' as const } : j)) };
    s = advance(s, dNoFail, 250);
    expect(job(s, 'translation_v2').status).toBe('done');
    expect(s.reputation).toBe(30);
    expect(s.flags.model_v2).toBe(true);
  });
});

describe('determinism with the rng consumed', () => {
  const highFail = (v: number): GameData => {
    const r = raw();
    r.world.failPerGpuDay.value = v;
    return loadData(r);
  };
  const run = (seed: number, data: GameData) => advance({ ...training(2), seed, rng: seed }, data, 336);
  it('same seed and allocation give identical JSON over 2 weeks', () => {
    const dd = highFail(2);
    expect(JSON.stringify(run(7, dd))).toBe(JSON.stringify(run(7, dd)));
    const s = run(7, dd);
    expect(s.pulso.some((p) => p.cause === 'outage' && p.focus?.kind === 'gpu')).toBe(true);
    expect(s.rng).not.toBe(7);
  });
  it('a different seed gives a different failure history', () => {
    const dd = highFail(2);
    const hist = (s: GameState) => JSON.stringify(s.pulso.filter((p) => p.focus?.kind === 'gpu').map((p) => p.id));
    expect(hist(run(7, dd))).not.toBe(hist(run(8, dd)));
  });
  it('splitting the run does not change the outcome (rng state is carried)', () => {
    const dd = highFail(2);
    const a = advance(advance({ ...training(2), seed: 3, rng: 3 }, dd, 100), dd, 100);
    const b = advance({ ...training(2), seed: 3, rng: 3 }, dd, 200);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
    expect(restoreRng(a.rng).next()).toBe(restoreRng(b.rng).next());
  });
});

describe('trained GPU-hours counter', () => {
  it('counts one hour per live training GPU while a job runs', () => {
    const s = stepTraining(training(3), dNoFail, fakeRng(0.99));
    expect(s.trainedGpuHours).toBe(3);
    const s2 = stepTraining(s, dNoFail, fakeRng(0.99));
    expect(s2.trainedGpuHours).toBe(6);
  });
  it('skips GPUs shut down by heat and counts nothing while the breaker is out or no job runs', () => {
    const s0 = training(2);
    const off = stepTraining({ ...s0, gpus: [{ ...s0.gpus[0]!, perf: 0 }, s0.gpus[1]!] }, dNoFail, fakeRng(0.99));
    expect(off.trainedGpuHours).toBe(1);
    const tripped = stepTraining({ ...s0, power: { ...s0.power, breakerTripped: true } }, dNoFail, fakeRng(0.99));
    expect(tripped.trainedGpuHours ?? 0).toBe(0);
    const idle = newGame(d, 1, 'Lab');
    expect(stepTraining({ ...idle, allocation: { 'gpu-1': 'train' } }, dNoFail, fakeRng(0.99)).trainedGpuHours ?? 0).toBe(0);
  });
  it('still counts the hour a GPU fails (the time was spent)', () => {
    const s = stepTraining(training(1), d, fakeRng(0));
    expect(s.trainedGpuHours).toBe(1);
  });
  it('accumulates over a full replication with one GPU (≈ 96 h)', () => {
    let s = training(1);
    let h = 0;
    while (job(s).status === 'running' && h < 200) {
      s = advance(s, dNoFail, 1);
      h++;
    }
    expect(s.trainedGpuHours).toBe(h);
  });
});
