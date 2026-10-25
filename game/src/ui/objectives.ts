// M1 objective tracker: a pure derivation of the current goal from the state (shown under the date in the HUD).
import type { GameData, GameState } from '../sim/types';
import { t } from './format';

export type ObjectiveId = 'replicate' | 'launch' | 'grow' | 'round' | 'done';

export interface ObjectiveProgress {
  label: string;
  done: number;
  total: number;
}

export interface Objective {
  id: ObjectiveId;
  /** 1–4 for the M1 goals, 5 once the game has an outcome. */
  step: number;
  text: string;
  /** Usually one value; «grow» has two (customers and reputation). */
  progress?: ObjectiveProgress[];
  /** What clicking the objective opens: a side panel, the seed-round offer, or nothing. */
  panel: 'jobs' | 'alloc' | 'round' | null;
}

const capped = (v: number, total: number): number => Math.min(total, Math.max(0, Number.isFinite(v) ? v : 0));

/** Replicate the paper → launch the translation API → 300 customers and reputation 30 → decide the seed round. */
export function currentObjective(s: GameState, d: GameData): Objective {
  if (s.outcome !== null) return { id: 'done', step: 5, text: t(s.outcome === 'seed_round' ? 'obj.done.seed_round' : 'obj.done.bankrupt'), panel: null };
  if (s.round?.status === 'offered') return { id: 'round', step: 4, text: t('obj.round'), panel: 'round' };

  const job = s.jobs.find((j) => j.id === 'replicate_paper');
  if (job && job.status !== 'done') {
    return {
      id: 'replicate',
      step: 1,
      text: t('obj.replicate'),
      progress: [{ label: t('obj.replicate.unit'), done: capped(job.doneP100h, job.workP100h), total: job.workP100h }],
      panel: 'jobs',
    };
  }

  const serving = s.gpus.some((g) => s.allocation[g.id] === 'serve');
  if (!s.product.launched || !serving) return { id: 'launch', step: 2, text: t('obj.launch'), panel: 'alloc' };

  const g = d.world.progression;
  const minC = g.seedMinCustomers.value;
  const minR = g.seedMinReputation.value;
  if (s.product.customers < minC || s.reputation < minR) {
    return {
      id: 'grow',
      step: 3,
      text: t('obj.grow', { customers: minC, rep: minR }),
      progress: [
        { label: t('obj.grow.customers'), done: Math.floor(capped(s.product.customers, minC)), total: minC },
        { label: t('obj.grow.rep'), done: Math.floor(capped(s.reputation, minR)), total: minR },
      ],
      panel: 'jobs',
    };
  }

  // Conditions met: the offer arrives on the next hour, or it was declined and may come back.
  return { id: 'round', step: 4, text: t(s.round?.status === 'declined' ? 'obj.round.declined' : 'obj.round'), panel: 'jobs' };
}
