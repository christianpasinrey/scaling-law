import { gpuLabel, pushPulso } from './pulsoLog';
import type { Rng } from './rng';
import type { GameData, GameState, Grant, PulsoItem, TrainingJob } from './types';

/**
 * Didactic loss curve: start * (1 - f)^exponent + floor (parameters in data).
 * Only its shape is meaningful; it is not data from the paper.
 */
export function lossAt(d: GameData, fraction: number): number {
  const { start, exponent, floor } = d.products.training.loss;
  const f = Math.min(1, Math.max(0, fraction));
  return start.value * Math.pow(1 - f, exponent.value) + floor.value;
}

const HOURS_PER_DAY = 24;

function p100eqOf(d: GameData, model: string): number {
  return d.gpus.find((g) => g.id === model)?.p100eq.value ?? 0;
}

/**
 * Hourly: progress, failures, breaker rollback, checkpoints and completion of the running job.
 * Order: breaker rollback, per-GPU failure draws, progress (skipped if either rolled back),
 * checkpoint, completion. Without a running job nothing happens and the rng is not consumed.
 */
export function stepTraining(s: GameState, d: GameData, rng: Rng): GameState {
  const job = s.jobs.find((j) => j.status === 'running');
  if (!job) return s;

  const trainGpus = s.gpus.filter((g) => s.allocation[g.id] === 'train');
  let done = job.doneP100h;
  let checkpoint = job.checkpointP100h;
  let rolledBack = false;
  let cur = s;
  let grants = s.grants;

  // Time spent, whatever happens to the progress below (the end screen reports it).
  const liveTrainers = s.power.breakerTripped ? 0 : trainGpus.filter((g) => g.perf > 0).length;
  const trainedGpuHours = (s.trainedGpuHours ?? 0) + liveTrainers;

  // Breaker out: the garage has no power, anything since the last checkpoint is lost.
  if (s.power.breakerTripped) {
    rolledBack = true;
    done = checkpoint;
  }

  // One failure draw per training GPU per hour.
  const pFail = d.world.failPerGpuDay.value / HOURS_PER_DAY;
  for (const g of trainGpus) {
    if (rng.next() < pFail) {
      rolledBack = true;
      done = checkpoint;
      const item: PulsoItem = {
        id: `outage:gpu:${g.id}:${s.hour}`,
        hour: s.hour,
        cause: 'outage',
        text: `La GPU ${gpuLabel(d, g)} se ha caído y el entrenamiento vuelve al último punto de control.`,
        count: 1,
        focus: { kind: 'gpu', id: g.id },
      };
      cur = pushPulso(cur, d, item);
    }
  }

  if (!rolledBack) {
    const contractActive = s.contracts.some((c) => c.status === 'active');
    const factor = contractActive ? d.products.training.researchContractFactor.value : 1;
    const own = trainGpus.reduce((sum, g) => sum + p100eqOf(d, g.model) * g.perf, 0) * factor;
    // A grant contributes only while it has cloud hours left; each contributing hour burns one.
    const live = (g: Grant) => g.status === 'active' && g.hoursLeft > 0;
    const grantP100 = s.grants.reduce((sum, g) => sum + (live(g) ? g.p100eq : 0), 0);
    grants = s.grants.map((g) => {
      if (!live(g)) return g;
      const hoursLeft = g.hoursLeft - 1;
      return { ...g, hoursLeft, status: hoursLeft > 0 ? g.status : ('expired' as const) };
    });
    done = Math.min(job.workP100h, done + own + grantP100);
  }

  let lossCurve = job.lossCurve;
  if (!rolledBack && s.hour % job.checkpointEveryH === 0) {
    checkpoint = done;
    lossCurve = [...lossCurve, lossAt(d, done / job.workP100h)];
  }

  const finished = done >= job.workP100h;
  const updated: TrainingJob = { ...job, doneP100h: done, checkpointP100h: checkpoint, lossCurve, status: finished ? 'done' : 'running' };
  let next: GameState = {
    ...cur,
    trainedGpuHours,
    grants,
    jobs: s.jobs.map((j) => (j.id === job.id ? updated : j)),
  };

  if (finished) next = complete(next, d, job.id);
  return next;
}

/** Rewards and unlocks when a job finishes. */
function complete(s: GameState, d: GameData, id: TrainingJob['id']): GameState {
  if (id === 'replicate_paper') {
    const next: GameState = {
      ...s,
      reputation: s.reputation + d.products.economy.reputation.replicatePaper.value,
      jobs: s.jobs.map((j) => (j.id === 'translation_v2' && j.status === 'locked' ? { ...j, status: 'ready' as const } : j)),
      product: { ...s.product, launched: true },
    };
    return pushPulso(next, d, {
      id: 'news:replicate_paper',
      hour: s.hour,
      cause: 'news',
      text: 'Has replicado el paper',
      count: 1,
    });
  }
  return { ...s, reputation: s.reputation + d.products.economy.reputation.translationV2.value, flags: { ...s.flags, model_v2: true } };
}
