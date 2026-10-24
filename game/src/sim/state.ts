import type { GameData, GameState, TrainingJob } from './types';

export const HOURS_PER_WEEK = 168;

export function newGame(d: GameData, seed: number, labName: string): GameState {
  const j = d.products.jobs;
  const checkpointEveryH = j.checkpointEveryH.value as 4;
  const job = (id: TrainingJob['id'], work: number, status: TrainingJob['status']): TrainingJob => ({
    id,
    workP100h: work,
    doneP100h: 0,
    checkpointP100h: 0,
    checkpointEveryH,
    lossCurve: [],
    status,
  });
  return {
    version: 1,
    seed,
    rng: seed >>> 0,
    hour: 0,
    // Starting hardware is already owned: not charged.
    cashUsd: d.world.startCashUsd,
    labName,
    rigs: [{ id: 'rig-1', model: 'tower_2017' }],
    gpus: [{ id: 'gpu-1', model: 'gtx1080ti', rigId: 'rig-1', slot: 0, tempC: d.world.ambientC.value, perf: 1 }],
    allocation: { 'gpu-1': 'idle' },
    power: { watts: 0, breakerTripped: false, weekKwh: 0 },
    jobs: [
      job('replicate_paper', j.replicate_paper.workP100h.value, 'ready'),
      job('translation_v2', j.translation_v2.workP100h.value, 'locked'),
    ],
    product: {
      priceUsdPerMChars: d.products.translation.defaultPriceUsdPerMChars.value,
      customers: 0,
      demandMCharsH: 0,
      servedMCharsH: 0,
      latencyMs: 0,
      satisfaction: 0,
      weekServedMChars: 0,
      launched: false,
    },
    contracts: [],
    grants: [],
    reputation: 0,
    ledger: [],
    pulso: [],
    flags: {},
    outcome: null,
  };
}
