import type { GameData, GameState } from './types';

/** Hourly: unlocks (jobs, hardware, contracts) driven by date and events. Filled by a later task. */
export function stepProgression(s: GameState, _d: GameData): GameState {
  return s;
}
