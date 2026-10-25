import { HOURS_PER_WEEK } from './state';
import type { Rng } from './rng';
import type { GameData, GameState } from './types';

const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

/**
 * Hourly: demand, served volume, latency, satisfaction and customer growth for the translation product.
 * Does nothing until the product is launched. The first launched hour seeds the customer base (data).
 * Customers stay fractional internally; the UI rounds. Needs no rng.
 */
export function stepServing(s: GameState, d: GameData, _rng: Rng): GameState {
  const p = s.product;
  if (!p.launched) return s;
  const t = d.products.translation;

  const customersNow = p.customers === 0 ? t.seedCustomers.value : p.customers;

  const demand = customersNow * t.demandMCharsPerCustomerH.value;
  let capacity = 0;
  if (!s.power.breakerTripped) {
    for (const g of s.gpus) {
      if (s.allocation[g.id] !== 'serve') continue;
      const p100eq = d.gpus.find((m) => m.id === g.model)?.p100eq.value ?? 0;
      capacity += p100eq * g.perf * t.capacityMCharsPerP100eqH.value;
    }
  }
  const served = Math.min(demand, capacity);

  const base = t.baseLatencyMs.value;
  const maxLat = t.maxLatencyMs.value;
  let latencyMs: number;
  if (demand <= capacity) latencyMs = base;
  else if (capacity <= 0) latencyMs = maxLat;
  else latencyMs = Math.min(maxLat, (base * demand) / capacity);

  const quality = s.flags.model_v2 ? t.qualityModelV2.value : t.qualityBase.value;
  const satisfaction = clamp(quality * Math.min(1, base / latencyMs), 0, 1);

  const ref = d.products.translation.defaultPriceUsdPerMChars.value;
  const price = Math.max(p.priceUsdPerMChars, 1e-9);
  // R22: the price amplifies the direction satisfaction sets. Happy customers: cheaper ⇒ faster growth.
  // Unhappy customers: dearer ⇒ faster loss (and cheaper ⇒ more forgiving).
  const growthBase = t.weeklyGrowth.value * (2 * satisfaction - 1);
  const ratio = growthBase >= 0 ? ref / price : price / ref;
  const elasticity = Math.min(t.maxElasticityFactor.value, Math.pow(ratio, t.elasticityExponent.value));
  const gMax = t.maxWeeklyGrowthAbs.value;
  const g = clamp(growthBase * elasticity, -gMax, gMax);
  const customers = Math.max(0, customersNow * Math.pow(1 + g, 1 / HOURS_PER_WEEK));

  return {
    ...s,
    product: {
      ...p,
      customers,
      demandMCharsH: demand,
      servedMCharsH: served,
      latencyMs,
      satisfaction,
      weekServedMChars: p.weekServedMChars + served,
    },
  };
}
