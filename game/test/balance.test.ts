import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { advance, applyCommand, dateOf, newGame } from '../src/sim';
import type { Command } from '../src/sim';
import type { GameData, GameState } from '../src/sim/types';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const WEEK = 168;
const CAP_WEEKS = 120;
const SEEDS = Array.from({ length: 20 }, (_, i) => i + 1);

type Strategy = 'balanced' | 'all_train' | 'all_rent' | 'consulting_heavy';
interface Result {
  outcome: 'seed_round' | 'bankrupt' | null;
  /** Game weeks elapsed when the game ended (or the cap). */
  weeks: number;
  /** True if cash was ever not a finite number. */
  nanCash: boolean;
}

const cmd = (s: GameState, c: Command): GameState => applyCommand(s, d, c);
const job = (s: GameState, id: 'replicate_paper' | 'translation_v2') => s.jobs.find((j) => j.id === id);
const gpuModel = (id: string) => d.gpus.find((g) => g.id === id);
const rigModel = (id: string) => d.rigs.find((r) => r.id === id);
const released = (s: GameState, iso: string) => iso <= dateOf(s);

/** Watts the garage would draw with every GPU loaded: what a careful player checks before plugging one more card in. */
function fullDraw(s: GameState, data: GameData, extraGpuWatts = 0): number {
  const rigs = s.rigs.reduce((sum, r) => sum + (data.rigs.find((m) => m.id === r.model)?.baseWatts ?? 0), 0);
  const gpus = s.gpus.reduce((sum, g) => sum + (data.gpus.find((m) => m.id === g.model)?.watts.value ?? 0), 0);
  return rigs + gpus + extraGpuWatts;
}

/** First rig with a free slot, or undefined. */
function freeRig(s: GameState): string | undefined {
  for (const r of s.rigs) {
    const slots = rigModel(r.model)?.gpuSlots ?? 0;
    if (s.gpus.filter((g) => g.rigId === r.id).length < slots) return r.id;
  }
  return undefined;
}

/**
 * Buys the dearest released GPU it can afford while a slot is free and the garage stays within the circuit,
 * keeping `reserve` dollars untouched. Buys an open frame first when every slot is taken and it is on sale.
 */
function buyGpus(s: GameState, reserve: number, maxGpus: number): GameState {
  let cur = s;
  for (;;) {
    if (cur.gpus.length >= maxGpus) return cur;
    let rig = freeRig(cur);
    if (!rig) {
      const frame = rigModel('open_frame');
      if (!frame || !released(cur, frame.releaseDate) || cur.cashUsd - frame.priceUsd.value < reserve) return cur;
      cur = cmd(cur, { t: 'buy_rig', model: 'open_frame' });
      rig = freeRig(cur);
      if (!rig) return cur;
    }
    const options = [...d.gpus]
      .filter((g) => released(cur, g.releaseDate))
      .filter((g) => cur.cashUsd - g.priceUsd.value >= reserve)
      .filter((g) => fullDraw(cur, d, g.watts.value) <= d.world.circuitWatts)
      .sort((a, b) => b.priceUsd.value - a.priceUsd.value);
    const pick = options[0];
    if (!pick) return cur;
    cur = cmd(cur, { t: 'buy_gpu', model: pick.id, rigId: rig });
  }
}

/** Sets the allocation of every GPU (only issues the commands that change something). */
function allocate(s: GameState, want: (gpuId: string, index: number) => GameState['allocation'][string]): GameState {
  let cur = s;
  cur.gpus.forEach((g, i) => {
    const to = want(g.id, i);
    if (cur.allocation[g.id] !== to) cur = cmd(cur, { t: 'allocate', gpuId: g.id, to });
  });
  return cur;
}

function startReady(s: GameState, id: 'replicate_paper' | 'translation_v2'): GameState {
  return job(s, id)?.status === 'ready' && !s.jobs.some((j) => j.status === 'running') ? cmd(s, { t: 'start_job', jobId: id }) : s;
}

const acceptContracts = (s: GameState): GameState =>
  s.contracts.filter((k) => k.status === 'offered').reduce((cur, k) => cmd(cur, { t: 'accept_contract', contractId: k.id }), s);
const acceptGrants = (s: GameState): GameState =>
  s.grants.filter((g) => g.status === 'offered').reduce((cur, g) => cmd(cur, { t: 'apply_grant', grantId: g.id }), s);

/** One player decision pass, issued before every simulated hour. */
function decide(name: Strategy, s: GameState): GameState {
  let cur = s;
  if (cur.round?.status === 'offered') return cmd(cur, { t: 'accept_round' });
  if (cur.power.breakerTripped) cur = cmd(cur, { t: 'reset_breaker' });
  const replicated = job(cur, 'replicate_paper')?.status === 'done';
  const v2Done = job(cur, 'translation_v2')?.status === 'done';

  switch (name) {
    case 'balanced': {
      // A second GPU as soon as cash allows, keeping a safety reserve; no more than the tower holds.
      cur = buyGpus(cur, 3000, 2);
      cur = acceptGrants(cur);
      cur = acceptContracts(cur);
      cur = startReady(cur, 'replicate_paper');
      if (replicated) cur = startReady(cur, 'translation_v2');
      if (!replicated) cur = allocate(cur, () => 'train');
      else if (!v2Done) cur = allocate(cur, (_, i) => (i === 0 ? 'serve' : 'train'));
      else cur = allocate(cur, (_, i) => (i === 0 ? 'serve' : 'rent'));
      return cur;
    }
    case 'all_train': {
      // Every dollar into GPUs (within the circuit), every GPU training; never serves, consults or rents.
      cur = buyGpus(cur, 0, Infinity);
      cur = startReady(cur, 'replicate_paper');
      if (replicated) cur = startReady(cur, 'translation_v2');
      return allocate(cur, () => 'train');
    }
    case 'all_rent': {
      // Rents every GPU to miners, buys more while keeping a reserve; never trains.
      cur = buyGpus(cur, 1000, Infinity);
      return allocate(cur, () => 'rent');
    }
    case 'consulting_heavy': {
      // One GPU, accepts every consulting gig, replicates and trains v2 slowly, serves once replicated.
      cur = acceptContracts(cur);
      cur = startReady(cur, 'replicate_paper');
      if (replicated) cur = startReady(cur, 'translation_v2');
      if (!replicated) return allocate(cur, () => 'train');
      return allocate(cur, () => (v2Done ? 'serve' : cur.jobs.some((j) => j.status === 'running') ? 'train' : 'serve'));
    }
  }
}

function simulateStrategy(name: Strategy, seed: number): Result {
  let s = newGame(d, seed, 'Lab');
  let nanCash = false;
  while (s.outcome === null && s.hour < CAP_WEEKS * WEEK) {
    s = decide(name, s);
    if (s.outcome !== null) break;
    s = advance(s, d, 1);
    if (!Number.isFinite(s.cashUsd)) nanCash = true;
  }
  return { outcome: s.outcome, weeks: s.hour / WEEK, nanCash };
}

const runs = new Map<Strategy, Result[]>();
const results = (name: Strategy): Result[] => {
  let r = runs.get(name);
  if (!r) {
    r = SEEDS.map((seed) => simulateStrategy(name, seed));
    runs.set(name, r);
  }
  return r;
};

/** "outcome@week" per seed, attached to failing assertions so a regression shows the whole distribution. */
const summary = (name: Strategy): string =>
  `${name}: ${results(name).map((x) => `${x.outcome ?? 'none'}@${x.weeks.toFixed(1)}`).join(' ')}`;

describe('M1 balance (20 seeds)', () => {
  it('balanced reaches the seed round in weeks 30-60 in at least 17 of 20 seeds', () => {
    const ok = results('balanced').filter((r) => r.outcome === 'seed_round' && r.weeks >= 30 && r.weeks <= 60);
    expect(ok.length, summary('balanced')).toBeGreaterThanOrEqual(17);
  });

  it('all_train goes bankrupt within 40 weeks in at least 18 of 20 seeds', () => {
    const ok = results('all_train').filter((r) => r.outcome === 'bankrupt' && r.weeks <= 40);
    expect(ok.length, summary('all_train')).toBeGreaterThanOrEqual(18);
  });

  it('no strategy reaches the seed round before week 20, for any seed', () => {
    for (const name of ['balanced', 'all_train', 'all_rent', 'consulting_heavy'] as const) {
      for (const r of results(name)) if (r.outcome === 'seed_round') expect(r.weeks, summary(name)).toBeGreaterThanOrEqual(20);
    }
  });

  it.each(['all_rent', 'consulting_heavy'] as const)('%s ends with a defined outcome or reaches week 120 with finite cash', (name) => {
    for (const r of results(name)) {
      expect(r.nanCash).toBe(false);
      if (r.outcome === null) expect(r.weeks).toBe(CAP_WEEKS);
    }
  });
});
