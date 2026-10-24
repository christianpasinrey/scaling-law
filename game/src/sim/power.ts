import type { Rng } from './rng';
import type { GameData, GameState } from './types';

/** Hourly: watts, breaker, temperatures, failures. Filled by a later task. */
export function stepPower(s: GameState, _d: GameData, _rng: Rng): GameState {
  return s;
}
