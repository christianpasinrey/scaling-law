import { pushPulso } from './pulsoLog';
import type { Rng } from './rng';
import type { GameData, GameState, PulsoItem, PulsoTemplateCause } from './types';

/**
 * Every `cadenceH` game hours while the product is launched: one customer message, its cause drawn (rng) among
 * the causes whose condition holds, its text a random template of that cause. All focus on the product.
 * Aggregation and the daily cap are applied by pushPulso. No candidate cause: nothing happens, rng untouched.
 */
export function emitPulso(s: GameState, d: GameData, rng: Rng): GameState {
  if (!s.product.launched || s.hour % d.pulso.cadenceH.value !== 0) return s;
  const p = s.product;
  const th = d.pulso.thresholds;
  const ref = d.products.translation.defaultPriceUsdPerMChars.value;

  const causes: PulsoTemplateCause[] = [];
  if (p.latencyMs > th.latencyMs.value) causes.push('latency');
  if (p.satisfaction >= th.praiseSatisfaction.value) causes.push('praise');
  if (p.priceUsdPerMChars > th.priceFactor.value * ref) causes.push('price');
  if (!s.flags.model_v2 && p.customers >= th.qualityMinCustomers.value) causes.push('quality');
  if (causes.length === 0) return s;

  const cause = causes[rng.int(0, causes.length - 1)] as PulsoTemplateCause;
  const templates = d.pulso.templates[cause];
  const text = templates[rng.int(0, templates.length - 1)] as string;
  const item: PulsoItem = { id: `pulso:${cause}:${s.hour}`, hour: s.hour, cause, text, count: 1, focus: { kind: 'product' } };
  return pushPulso(s, d, item);
}
