import { HOURS_PER_WEEK } from './state';
import { dateOf } from './time';
import { pushPulso } from './pulsoLog';
import type { GameData, GameState } from './types';

const TITAN_V_ID = 'titan_v';
const TITAN_V_FLAG = 'news_titan_v';

/** True when the seed-round conditions hold (replicate_paper done, customers and reputation reached). */
function roundConditions(s: GameState, d: GameData): boolean {
  const g = d.world.progression;
  return (
    s.jobs.some((j) => j.id === 'replicate_paper' && j.status === 'done') &&
    s.product.customers >= g.seedMinCustomers.value &&
    s.reputation >= g.seedMinReputation.value
  );
}

/**
 * Hourly: date- and event-driven unlocks. Titan V news once, on the first hour whose date reaches its release
 * date; the seed round is offered when its conditions hold and none is pending (a declined one comes back
 * after `seedReofferWeeks` weeks if the conditions still hold).
 */
export function stepProgression(s: GameState, d: GameData): GameState {
  let cur = s;

  const titan = d.gpus.find((g) => g.id === TITAN_V_ID);
  if (titan && !cur.flags[TITAN_V_FLAG] && titan.releaseDate <= dateOf(cur)) {
    cur = pushPulso({ ...cur, flags: { ...cur.flags, [TITAN_V_FLAG]: true } }, d, {
      id: 'news:titan_v',
      hour: cur.hour,
      cause: 'news',
      text: d.pulso.news.titanV,
      count: 1,
    });
  }

  const r = cur.round;
  const canOffer =
    r === undefined ||
    (r.status === 'declined' &&
      cur.hour >= (r.declinedHour ?? r.offeredHour) + d.world.progression.seedReofferWeeks.value * HOURS_PER_WEEK);
  if (canOffer && roundConditions(cur, d)) {
    cur = pushPulso({ ...cur, round: { status: 'offered', offeredHour: cur.hour } }, d, {
      id: `news:seed_round:${cur.hour}`,
      hour: cur.hour,
      cause: 'news',
      text: d.pulso.news.seedRound,
      count: 1,
    });
  }
  return cur;
}
