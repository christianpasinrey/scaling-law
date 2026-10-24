import type { Rng } from './rng';
import type { GameData, GameState, LedgerWeek } from './types';

/**
 * Weekly settlement (called after every 168th hour). Appends exactly one LedgerWeek.
 * Running costs (electricity) are charged to cash, which may go negative; revenue is filled by a later task.
 */
export function settleWeek(s: GameState, d: GameData, _rng: Rng): GameState {
  const electricity = s.power.weekKwh * d.world.electricityUsdPerKwh.value;
  const cashUsd = s.cashUsd - electricity;
  const entry: LedgerWeek = {
    week: Math.round(s.hour / 168),
    revenueUsd: 0,
    costsUsd: electricity,
    cashEndUsd: cashUsd,
    lines: { electricity },
  };
  return { ...s, cashUsd, power: { ...s.power, weekKwh: 0 }, ledger: [...s.ledger, entry] };
}
