import type { GameState, WorldData } from './types';

// Validated as an exact literal by loadData (data/world.json startIso).
const START_ISO: WorldData['startIso'] = '2017-06-12T17:57:00Z';
const START_MS = Date.parse(START_ISO);
const HOUR_MS = 3_600_000;

/** ISO instant of the current game hour. */
export function dateOf(s: GameState): string {
  return new Date(START_MS + s.hour * HOUR_MS).toISOString();
}
