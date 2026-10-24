import type { Rng } from './rng';
import type { GameData, GameState } from './types';

/** Hourly: demand, served volume, latency, satisfaction. Filled by a later task. */
export function stepServing(s: GameState, _d: GameData, _rng: Rng): GameState {
  return s;
}
