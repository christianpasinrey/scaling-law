import type { Rng } from './rng';
import type { GameData, GameState } from './types';

/** Hourly: training progress and checkpoints. Filled by a later task. */
export function stepTraining(s: GameState, _d: GameData, _rng: Rng): GameState {
  return s;
}
