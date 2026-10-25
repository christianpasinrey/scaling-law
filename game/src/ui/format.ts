// Pure formatting and derivation helpers for the UI (no DOM). Everything here is unit-tested.
import i18n from '../../data/i18n.es.json';
import { dateOf } from '../sim/time';
import type { GameData, GameState, OwnedGpu, PulsoItem, TrainingJob } from '../sim/types';

export type TextKey = keyof typeof i18n;

/** UI text by key, with {name} placeholders filled from `vars`. */
export function t(k: TextKey, vars?: Record<string, string | number>): string {
  const s: string = i18n[k];
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (m, name: string) => (name in vars ? String(vars[name]) : m));
}

const MINUS = '−';

/** Integer with Spanish thousands dots, always grouped (1.440, 10.000); negatives use a real minus sign. */
export function formatInt(n: number): string {
  if (!Number.isFinite(n)) return '—';
  const r = Math.round(n);
  const digits = String(Math.abs(r)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return (r < 0 ? MINUS : '') + digits;
}

/** Fixed decimals with a decimal comma: 0,13. Integer part grouped like formatInt. */
export function formatDecimal(n: number, digits: number): string {
  if (!Number.isFinite(n)) return '—';
  const fixed = Math.abs(n).toFixed(digits);
  const [int, frac] = fixed.split('.');
  const neg = n < 0 && Number(fixed) !== 0;
  return (neg ? MINUS : '') + formatInt(Number(int)).replace(MINUS, '') + (frac ? ',' + frac : '');
}

/** Money in whole dollars: "10.000 $"; signed adds "+" to positives. */
export function formatUsd(n: number, opts: { signed?: boolean } = {}): string {
  const s = formatInt(n);
  return `${opts.signed && Math.round(n) > 0 ? '+' : ''}${s} $`;
}

export function formatWatts(w: number): string {
  return `${formatInt(w)} W`;
}

function months(): string[] {
  return t('fmt.months').split(',');
}

/** "12 jun 2017 · 17:57" (UTC, the sim's clock). */
export function formatDate(iso: string): string {
  const d = new Date(Date.parse(iso));
  if (Number.isNaN(d.getTime())) return '—';
  const hh = String(d.getUTCHours()).padStart(2, '0');
  const mm = String(d.getUTCMinutes()).padStart(2, '0');
  return `${d.getUTCDate()} ${months()[d.getUTCMonth()]} ${d.getUTCFullYear()} · ${hh}:${mm}`;
}

/** "7 dic 2017" from an ISO date. */
export function formatDay(iso: string): string {
  const d = new Date(Date.parse(iso.length === 10 ? `${iso}T00:00:00Z` : iso));
  if (Number.isNaN(d.getTime())) return '—';
  return `${d.getUTCDate()} ${months()[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

// ---------------------------------------------------------------- power

export type PowerZone = 'ok' | 'amber' | 'red';

/** ok up to the safe continuous limit, amber up to the trip point, red above it or while tripped. */
export function powerZone(watts: number, safe: number, trip: number, tripped: boolean): PowerZone {
  if (tripped || watts > trip) return 'red';
  if (watts > safe) return 'amber';
  return 'ok';
}

export interface PowerBar {
  /** Fill, 0..100. */
  pct: number;
  safePct: number;
  tripPct: number;
  zone: PowerZone;
}

/** The bar spans 0 .. trip × 1.15 so both marks (1.440 and 1.800 W) sit inside it. */
export function powerBar(watts: number, world: { circuitSafeWatts: number; circuitWatts: number }, tripped: boolean): PowerBar {
  const max = world.circuitWatts * 1.15;
  const w = Number.isFinite(watts) ? Math.max(0, watts) : 0;
  return {
    pct: Math.min(100, (w / max) * 100),
    safePct: (world.circuitSafeWatts / max) * 100,
    tripPct: (world.circuitWatts / max) * 100,
    zone: powerZone(w, world.circuitSafeWatts, world.circuitWatts, tripped),
  };
}

// ---------------------------------------------------------------- ledger

export interface WeekBalance {
  week: number;
  revenueUsd: number;
  costsUsd: number;
  netUsd: number;
}

/** Operating balance of the last settled week (purchases are not in the ledger), or null before the first. */
export function lastWeekBalance(s: GameState): WeekBalance | null {
  const w = s.ledger[s.ledger.length - 1];
  if (!w) return null;
  return { week: w.week, revenueUsd: w.revenueUsd, costsUsd: w.costsUsd, netUsd: w.revenueUsd - w.costsUsd };
}

// ---------------------------------------------------------------- hardware labels

/** "Torre" for the 2017 tower; "Bastidor 1", "Bastidor 2"… for open frames in purchase order. */
export function rigLabel(s: GameState, rigId: string): string {
  const rig = s.rigs.find((r) => r.id === rigId);
  if (!rig) return rigId;
  const same = s.rigs.filter((r) => r.model === rig.model);
  const n = same.indexOf(rig) + 1;
  if (rig.model === 'tower_2017') return same.length > 1 ? `${t('rig.tower')} ${n}` : t('rig.tower');
  return `${t('rig.frame')} ${n}`;
}

/** "GTX 1080 Ti · Torre · ranura 1". */
export function gpuSlotLabel(s: GameState, d: GameData, g: OwnedGpu): string {
  const name = d.gpus.find((m) => m.id === g.model)?.shortName ?? g.model;
  return `${name} · ${rigLabel(s, g.rigId)} · ${t('rig.slot', { n: g.slot + 1 })}`;
}

/** First free GPU slot, rigs in purchase order (same rule as the buy_gpu command). */
export function freeSlot(s: GameState, d: GameData): { rigId: string; slot: number } | null {
  for (const rig of s.rigs) {
    const model = d.rigs.find((m) => m.id === rig.model);
    if (!model) continue;
    const used = new Set(s.gpus.filter((g) => g.rigId === rig.id).map((g) => g.slot));
    let slot = 0;
    while (used.has(slot)) slot++;
    if (slot < model.gpuSlots) return { rigId: rig.id, slot };
  }
  return null;
}

// ---------------------------------------------------------------- shop

export type ShopReason = 'not_released' | 'no_slot' | 'no_cash';

export interface ShopItem {
  kind: 'gpu' | 'rig';
  id: string;
  name: string;
  priceUsd: number;
  learnId: string;
  releaseDate: string;
  /** null when it can be bought now. */
  reason: ShopReason | null;
  /** GPUs only: where it would go. */
  target: { rigId: string; slot: number } | null;
}

/** GTX 1080 Ti, Titan V and the open frame with their availability. Reason order: not released, no slot, no cash. */
export function shopItems(s: GameState, d: GameData): ShopItem[] {
  const today = dateOf(s);
  const slot = freeSlot(s, d);
  const out: ShopItem[] = [];
  for (const g of d.gpus) {
    const reason: ShopReason | null =
      g.releaseDate > today ? 'not_released' : slot === null ? 'no_slot' : s.cashUsd < g.priceUsd.value ? 'no_cash' : null;
    out.push({ kind: 'gpu', id: g.id, name: g.name, priceUsd: g.priceUsd.value, learnId: g.learnId, releaseDate: g.releaseDate, reason, target: slot });
  }
  for (const r of d.rigs) {
    if (r.id !== 'open_frame') continue; // the tower is the PC you already own
    const reason: ShopReason | null = r.releaseDate > today ? 'not_released' : s.cashUsd < r.priceUsd.value ? 'no_cash' : null;
    out.push({ kind: 'rig', id: r.id, name: r.name, priceUsd: r.priceUsd.value, learnId: 'open_frame', releaseDate: r.releaseDate, reason, target: null });
  }
  return out;
}

export function shopReasonText(item: ShopItem): string {
  switch (item.reason) {
    case 'not_released':
      return t('shop.reason.not_released', { date: formatDay(item.releaseDate) });
    case 'no_slot':
      return t('shop.reason.no_slot');
    case 'no_cash':
      return t('shop.reason.no_cash');
    default:
      return '';
  }
}

// ---------------------------------------------------------------- training

/** P100-hours per game hour the running job gets right now (own GPUs × perf × contract factor + live grants). Never NaN. */
export function trainingRate(s: GameState, d: GameData): number {
  if (s.power.breakerTripped) return 0;
  const contract = s.contracts.some((c) => c.status === 'active');
  const factor = contract ? d.products.training.researchContractFactor.value : 1;
  let own = 0;
  for (const g of s.gpus) {
    if (s.allocation[g.id] !== 'train') continue;
    own += (d.gpus.find((m) => m.id === g.model)?.p100eq.value ?? 0) * g.perf;
  }
  const grant = s.grants.reduce((sum, g) => sum + (g.status === 'active' && g.hoursLeft > 0 ? g.p100eq : 0), 0);
  return own * factor + grant;
}

/** Game hours left at `rate`, or null when nothing progresses. */
export function jobEtaHours(job: TrainingJob, rate: number): number | null {
  if (!(rate > 0)) return null;
  return Math.max(0, job.workP100h - job.doneP100h) / rate;
}

/** "3 d 4 h" / "5 h". */
export function formatHours(h: number): string {
  const r = Math.ceil(h);
  const days = Math.floor(r / 24);
  const hours = r % 24;
  return days > 0 ? `${days} d ${hours} h` : `${hours} h`;
}

/** Fraction 0..1, safe for workP100h 0. */
export function fraction(done: number, total: number): number {
  if (!(total > 0) || !Number.isFinite(done)) return 0;
  return Math.min(1, Math.max(0, done / total));
}

/** SVG polyline points for a loss curve in a w×h box; y maps lo..hi to bottom..top. Empty string for < 2 points. */
export function lossPolyline(curve: readonly number[], w: number, h: number, lo: number, hi: number): string {
  if (curve.length < 2) return '';
  const span = hi - lo > 0 ? hi - lo : 1;
  return curve
    .map((v, i) => {
      const x = (i / (curve.length - 1)) * w;
      const y = h - Math.min(1, Math.max(0, (v - lo) / span)) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

// ---------------------------------------------------------------- product

/** Revenue per week if the current served rate holds. */
export function weeklyRevenueEstimate(s: GameState): number {
  const v = s.product.servedMCharsH * 168 * s.product.priceUsdPerMChars;
  return Number.isFinite(v) ? v : 0;
}

// ---------------------------------------------------------------- pulso

/** Feed newest first (the log appends and moves refreshed items to the end). */
export function pulsoNewestFirst(s: GameState): PulsoItem[] {
  return [...s.pulso].reverse();
}

// ---------------------------------------------------------------- learn

/** Learn-card ids whose concept is visible in this state (first appearance ⇒ "Nuevo concepto" toast). */
export function conceptsPresent(s: GameState, d: GameData): string[] {
  const out: string[] = [];
  const running = s.jobs.find((j) => j.status === 'running');
  const today = dateOf(s);
  if (s.gpus.length > 0) out.push('gpu');
  if (running || s.jobs.some((j) => j.status === 'done')) out.push('training', 'p100eq');
  if (s.jobs.some((j) => j.lossCurve.length > 0)) out.push('loss', 'checkpoint');
  if (running && s.gpus.filter((g) => s.allocation[g.id] === 'train').length >= 2) out.push('data_parallel');
  if (s.gpus.some((g) => g.perf < 1)) out.push('throttling');
  if (s.power.breakerTripped) out.push('breaker');
  if (s.ledger.length > 0) out.push('kwh');
  if (s.product.launched) out.push('inference', 'translation_api');
  if (s.gpus.some((g) => s.allocation[g.id] === 'rent')) out.push('gpu_rental');
  if (s.contracts.length > 0) out.push('consulting');
  if (s.grants.length > 0) out.push('grant');
  if (s.round) out.push('funding_round', 'dilution');
  const titan = d.gpus.find((g) => g.id === 'titan_v');
  if (titan && titan.releaseDate <= today) out.push(titan.learnId, 'vram');
  const frame = d.rigs.find((r) => r.id === 'open_frame');
  if (frame && frame.releaseDate <= today) out.push('open_frame');
  return out;
}

/** Brain block id → learn card. */
export function brainCard(blockId: string): string {
  if (blockId.startsWith('embed')) return 'embedding';
  if (blockId.startsWith('enc')) return 'encoder';
  if (blockId.startsWith('dec')) return 'decoder';
  return 'softmax';
}
