import { restoreRng } from './rng';
import { settleWeek } from './economy';
import { emitPulso } from './pulso';
import { stepPower } from './power';
import { stepProgression } from './progression';
import { stepServing } from './serving';
import { HOURS_PER_WEEK } from './state';
import { stepTraining } from './training';
import type { GameData, GameState, WorldData } from './types';

// Validated as an exact literal by loadData (data/world.json startIso).
const START_ISO: WorldData['startIso'] = '2017-06-12T17:57:00Z';
const START_MS = Date.parse(START_ISO);
const HOUR_MS = 3_600_000;

/** ISO instant of the current game hour. */
export function dateOf(s: GameState): string {
  return new Date(START_MS + s.hour * HOUR_MS).toISOString();
}

/** Advance whole hours. Order per hour (ruling R2): progression, power, training, serving, pulso; settleWeek every 168 h. */
export function advance(s: GameState, d: GameData, hours: number): GameState {
  if (s.outcome !== null || !Number.isFinite(hours) || hours < 1) return s;
  const n = Math.floor(hours);
  const rng = restoreRng(s.rng);
  let cur = s;
  for (let i = 0; i < n; i++) {
    cur = stepProgression(cur, d);
    cur = stepPower(cur, d, rng);
    cur = stepTraining(cur, d, rng);
    cur = stepServing(cur, d, rng);
    cur = emitPulso(cur, d, rng);
    cur = { ...cur, hour: cur.hour + 1 };
    if (cur.hour % HOURS_PER_WEEK === 0) cur = settleWeek(cur, d, rng);
    if (cur.outcome !== null) break;
  }
  return { ...cur, rng: rng.state() };
}
