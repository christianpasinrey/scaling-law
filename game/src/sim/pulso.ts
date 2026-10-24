import type { Rng } from './rng';
import type { GameData, GameState } from './types';

/** Hourly: turns state changes into Pulso feed items. Filled by a later task. */
export function emitPulso(s: GameState, _d: GameData, _rng: Rng): GameState {
  return s;
}
