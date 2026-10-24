import type { Rng } from './rng';
import type { GameData, GameState, LedgerWeek } from './types';

/**
 * Weekly settlement (called after every 168th hour). Appends exactly one LedgerWeek.
 * Revenue/costs are filled by a later task.
 */
export function settleWeek(s: GameState, _d: GameData, _rng: Rng): GameState {
  const entry: LedgerWeek = {
    week: Math.round(s.hour / 168),
    revenueUsd: 0,
    costsUsd: 0,
    cashEndUsd: s.cashUsd,
    lines: {},
  };
  return { ...s, ledger: [...s.ledger, entry] };
}
