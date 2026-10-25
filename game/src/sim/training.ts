import { appendPulso } from './pulsoLog';
import type { Rng } from './rng';
import type { GameData, GameState, PulsoItem, TrainingJob } from './types';

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
  let pulso = s.pulso;

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
        text: `La GPU ${g.id} se ha caído y el entrenamiento vuelve al último punto de control.`,
        count: 1,
        focus: { kind: 'gpu', id: g.id },
      };
      pulso = appendPulso({ ...s, pulso }, item);
    }
  }

  if (!rolledBack) {
    const contractActive = s.contracts.some((c) => c.status === 'active');
    const factor = contractActive ? d.products.training.researchContractFactor.value : 1;
    const own = trainGpus.reduce((sum, g) => sum + p100eqOf(d, g.model) * g.perf, 0) * factor;
    const grants = s.grants.reduce((sum, g) => sum + (g.status === 'active' ? g.p100eq : 0), 0);
    done = Math.min(job.workP100h, done + own + grants);
  }

  let lossCurve = job.lossCurve;
  if (!rolledBack && s.hour % job.checkpointEveryH === 0) {
    checkpoint = done;
    lossCurve = [...lossCurve, lossAt(d, done / job.workP100h)];
  }

  const finished = done >= job.workP100h;
  const updated: TrainingJob = { ...job, doneP100h: done, checkpointP100h: checkpoint, lossCurve, status: finished ? 'done' : 'running' };
  let next: GameState = {
    ...s,
    pulso,
    jobs: s.jobs.map((j) => (j.id === job.id ? updated : j)),
  };

  if (finished) next = complete(next, job.id);
  return next;
}

/** Rewards and unlocks when a job finishes. */
function complete(s: GameState, id: TrainingJob['id']): GameState {
  if (id === 'replicate_paper') {
    return {
      ...s,
      reputation: s.reputation + 15,
      pulso: appendPulso(s, {
        id: 'praise:replicate_paper',
        hour: s.hour,
        cause: 'praise',
        text: 'Has replicado el paper',
        count: 1,
      }),
      jobs: s.jobs.map((j) => (j.id === 'translation_v2' && j.status === 'locked' ? { ...j, status: 'ready' as const } : j)),
      product: { ...s.product, launched: true },
    };
  }
  return { ...s, reputation: s.reputation + 10, flags: { ...s.flags, model_v2: true } };
}
