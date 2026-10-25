import { dateOf } from './clock';
import { nextId } from './ids';
import { appendPulso } from './pulsoLog';
import type { Rng } from './rng';
import type { Contract, GameData, GameState, Grant, LedgerWeek } from './types';

const HOURS_PER_DAY = 24;
const HOURS_PER_WEEK = 168;

/**
 * Hourly GPU rental accrual. Every GPU allocated to 'rent' that is alive (perf > 0) while the breaker holds
 * earns rate/24 per hour; the rate drops once the crypto boom ends (data). Accrues into `weekRentUsd`.
 */
export function stepRental(s: GameState, d: GameData): GameState {
  if (s.power.breakerTripped) return s;
  const renting = s.gpus.filter((g) => s.allocation[g.id] === 'rent' && g.perf > 0).length;
  if (renting === 0) return s;
  const r = d.world.rentalUsdPerDay;
  // ISO strings compare chronologically; the date-only end sorts before any instant on that day.
  const perDay = dateOf(s) < r.boomEndIso ? r.boom.value : r.after.value;
  return { ...s, weekRentUsd: s.weekRentUsd + (renting * perDay) / HOURS_PER_DAY };
}

/**
 * Consulting offers: expires the previous unaccepted offers, then 0..maxOffers new ones.
 * Money is uniform in [usdMin, usdMax] rounded to usdStep; length uniform in [weeksMin, weeksMax].
 */
export function offerContracts(s: GameState, d: GameData, rng: Rng): GameState {
  const c = d.products.economy.consulting;
  const kept = s.contracts.filter((k) => k.status !== 'offered');
  const count = rng.int(0, c.maxOffers.value);
  const contracts: Contract[] = [...kept];
  for (let i = 0; i < count; i++) {
    const raw = c.usdMin.value + rng.next() * (c.usdMax.value - c.usdMin.value);
    const usd = Math.round(raw / c.usdStep.value) * c.usdStep.value;
    const weeksTotal = rng.int(c.weeksMin.value, c.weeksMax.value);
    // Ids keep growing past expired offers, never reused.
    const id = nextId('contract', [...s.contracts, ...contracts].map((k) => k.id));
    contracts.push({ id, usd, weeksTotal, weeksLeft: weeksTotal, status: 'offered' });
  }
  return { ...s, contracts };
}

/** Compute grant: offered once, when reputation reaches the threshold and no grant has ever existed. */
export function offerGrants(s: GameState, d: GameData): GameState {
  const g = d.products.economy.grant;
  if (s.grants.length > 0 || s.reputation < g.minReputation.value) return s;
  const grant: Grant = {
    id: 'grant-1',
    p100eq: g.p100eq.value,
    hoursLeft: g.hours.value,
    weeksLeft: g.weeks.value,
    status: 'offered',
  };
  return { ...s, grants: [grant] };
}

/**
 * Weekly settlement (called after every 168th hour). Appends exactly one LedgerWeek.
 * Revenue: translation product, consulting installments, GPU rental. Costs: electricity.
 * Then offers (consulting every N weeks, grant), grant ageing and the bankruptcy streak.
 */
export function settleWeek(s: GameState, d: GameData, rng: Rng): GameState {
  const eco = d.products.economy;
  const week = Math.round(s.hour / HOURS_PER_WEEK);

  const electricity = s.power.weekKwh * d.world.electricityUsdPerKwh.value;
  const product = s.product.weekServedMChars * s.product.priceUsdPerMChars;
  const rental = s.weekRentUsd;

  let consulting = 0;
  const contracts = s.contracts.map((k): Contract => {
    if (k.status !== 'active') return k;
    consulting += k.usd / k.weeksTotal;
    const weeksLeft = k.weeksLeft - 1;
    return { ...k, weeksLeft, status: weeksLeft <= 0 ? 'done' : 'active' };
  });

  const grants = s.grants.map((g): Grant => {
    if (g.status !== 'active') return g;
    const weeksLeft = g.weeksLeft - 1;
    return { ...g, weeksLeft, status: weeksLeft <= 0 || g.hoursLeft <= 0 ? 'expired' : 'active' };
  });

  const revenueUsd = product + consulting + rental;
  const cashUsd = s.cashUsd + revenueUsd - electricity;
  const entry: LedgerWeek = {
    week,
    revenueUsd,
    costsUsd: electricity,
    cashEndUsd: cashUsd,
    lines: { product, consulting, rental, electricity },
  };

  let next: GameState = {
    ...s,
    cashUsd,
    contracts,
    grants,
    weekRentUsd: 0,
    product: { ...s.product, weekServedMChars: 0 },
    power: { ...s.power, weekKwh: 0 },
    ledger: [...s.ledger, entry],
  };

  if (week % eco.consulting.everyWeeks.value === 0) next = offerContracts(next, d, rng);
  next = offerGrants(next, d);

  const negativeWeeks = cashUsd < 0 ? s.negativeWeeks + 1 : 0;
  next = { ...next, negativeWeeks };
  if (negativeWeeks >= eco.bankruptcyNegativeWeeks.value) {
    next = {
      ...next,
      outcome: 'bankrupt',
      pulso: appendPulso(next, {
        id: 'news:bankrupt',
        hour: next.hour,
        cause: 'news',
        text: `${next.labName} cierra: cuatro semanas seguidas sin caja y sin salida.`,
        count: 1,
      }),
    };
  }
  return next;
}
