import { restoreRng } from './rng';
import { settleWeek, stepRental } from './economy';
import { emitPulso } from './pulso';
import { stepPower } from './power';
import { stepProgression } from './progression';
import { stepServing } from './serving';
import { HOURS_PER_WEEK } from './state';
import { stepTraining } from './training';
import type { GameData, GameState } from './types';

export { dateOf } from './time';

/** Advance whole hours. Order per hour (ruling R2): progression, power, training, serving, pulso; settleWeek every 168 h. */
export function advance(s: GameState, d: GameData, hours: number): GameState {
  if (s.outcome !== null || !Number.isFinite(hours) || hours < 1) return s;
  const n = Math.floor(hours);
  const rng = restoreRng(s.rng);
  let cur = s;
  for (let i = 0; i < n; i++) {
    cur = stepProgression(cur, d);
    cur = stepPower(cur, d, rng);
    cur = stepRental(cur, d);
    cur = stepTraining(cur, d, rng);
    cur = stepServing(cur, d, rng);
    cur = emitPulso(cur, d, rng);
    cur = { ...cur, hour: cur.hour + 1 };
    if (cur.hour % HOURS_PER_WEEK === 0) cur = settleWeek(cur, d, rng);
    if (cur.outcome !== null) break;
  }
  return { ...cur, rng: rng.state() };
}
