// End of M1: the summary of a finished game (seed round or bankruptcy), «mientras tanto en el mundo real» facts
// from data/reality.es.json and the way back into a new game. Derivations are pure and unit-tested.
import type { GameData, GameState } from '../sim/types';
import { dateOf } from '../sim/time';
import { newGame } from '../sim/state';
import { rentalUsdPerDayAt } from '../sim/economy';
import { el } from './dom';
import { formatDay, formatInt, formatUsd, t } from './format';
import type { TextKey } from './format';
import { openScreen } from './screen';
import type { Screen } from './screen';

export interface RealityFact {
  date: string;
  title: string;
  text: string;
  source: string;
  link?: string;
}

export interface MoneyLine {
  key: string;
  usd: number;
}

export interface EndSummary {
  outcome: 'seed_round' | 'bankrupt';
  labName: string;
  dateIso: string;
  weeks: number;
  cashUsd: number;
  gpus: { model: string; name: string; count: number }[];
  gpuCount: number;
  customers: number;
  gpuHours: number;
  reputation: number;
  revenueUsd: number;
  /** Largest first: hardware bought (the starting PC excluded) and electricity. */
  costs: MoneyLine[];
  /** Largest first, from the ledger lines. */
  revenue: MoneyLine[];
}

const HOURS_PER_WEEK = 168;
const REVENUE_LINES = ['product', 'consulting', 'rental'] as const;
const fin = (v: number | undefined): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const byUsd = (a: MoneyLine, b: MoneyLine): number => b.usd - a.usd;

/** Dollars spent on hardware: every GPU and rig not in the starting garage (nothing can be sold in M1). */
function hardwareSpent(s: GameState, d: GameData): number {
  const start = newGame(d, 0, '');
  const startGpus = new Set(start.gpus.map((g) => g.id));
  const startRigs = new Set(start.rigs.map((r) => r.id));
  let usd = 0;
  for (const g of s.gpus) if (!startGpus.has(g.id)) usd += d.gpus.find((m) => m.id === g.model)?.priceUsd.value ?? 0;
  for (const r of s.rigs) if (!startRigs.has(r.id)) usd += d.rigs.find((m) => m.id === r.model)?.priceUsd.value ?? 0;
  return usd;
}

export function summarize(s: GameState, d: GameData): EndSummary {
  const counts = new Map<string, number>();
  for (const g of s.gpus) counts.set(g.model, (counts.get(g.model) ?? 0) + 1);
  // Data order (1080 Ti, then Titan V), not purchase order.
  const gpus = d.gpus.filter((m) => counts.has(m.id)).map((m) => ({ model: m.id, name: m.shortName, count: counts.get(m.id)! }));

  const sum = (line: string): number => s.ledger.reduce((acc, w) => acc + fin(w.lines[line]), 0);
  const revenue = REVENUE_LINES.map((key) => ({ key, usd: sum(key) })).sort(byUsd);
  const costs = [
    { key: 'hardware', usd: hardwareSpent(s, d) },
    { key: 'electricity', usd: sum('electricity') },
  ].sort(byUsd);

  return {
    outcome: s.outcome === 'bankrupt' ? 'bankrupt' : 'seed_round',
    labName: s.labName,
    dateIso: dateOf(s),
    weeks: Math.floor(s.hour / HOURS_PER_WEEK),
    cashUsd: fin(s.cashUsd),
    gpus,
    gpuCount: s.gpus.length,
    customers: Math.round(fin(s.product.customers)),
    gpuHours: fin(s.trainedGpuHours),
    reputation: fin(s.reputation),
    revenueUsd: s.ledger.reduce((acc, w) => acc + fin(w.revenueUsd), 0),
    costs,
    revenue,
  };
}

export type Diagnosis = 'no_paper' | 'no_product_revenue' | 'hardware_over_revenue' | 'idle_gpus_rent' | 'idle_gpus_serve';

/** What went wrong, in the order the player can act on it. */
export function diagnose(s: GameState, d: GameData): Diagnosis[] {
  const r = summarize(s, d);
  const out: Diagnosis[] = [];
  const paper = s.jobs.find((j) => j.id === 'replicate_paper')?.status === 'done';
  if (!paper) out.push('no_paper');
  else if ((r.revenue.find((l) => l.key === 'product')?.usd ?? 0) <= 0) out.push('no_product_revenue');
  const hw = r.costs.find((c) => c.key === 'hardware')?.usd ?? 0;
  if (hw > 0 && hw > r.revenueUsd) out.push('hardware_over_revenue');
  out.push(...idleAdvice(s, d));
  return out;
}

/**
 * What idle GPUs could have earned, only when it is true on the end date:
 * renting, if the rate beats that GPU's full-load electricity per day (watts/1000 × 24 × $/kWh);
 * serving, if the API was launched and demand was going unserved.
 */
export function idleAdvice(s: GameState, d: GameData): Diagnosis[] {
  const idle = s.gpus.filter((g) => (s.allocation[g.id] ?? 'idle') === 'idle');
  if (idle.length === 0) return [];
  const out: Diagnosis[] = [];
  const rent = rentalUsdPerDayAt(s, d);
  const kwh = d.world.electricityUsdPerKwh.value;
  const powerPerDay = (model: string): number => ((d.gpus.find((m) => m.id === model)?.watts.value ?? 0) / 1000) * 24 * kwh;
  if (idle.some((g) => rent > powerPerDay(g.model))) out.push('idle_gpus_rent');
  if (s.product.launched && fin(s.product.demandMCharsH) > fin(s.product.servedMCharsH)) out.push('idle_gpus_serve');
  return out;
}

/** Validates data/reality.es.json. Throws naming the bad entry. */
export function parseFacts(raw: unknown): RealityFact[] {
  const list = (raw as { facts?: unknown })?.facts;
  if (!Array.isArray(list)) throw new Error('reality: expected { facts: [...] }');
  return list.map((f: Record<string, unknown>, i) => {
    const str = (k: string, optional = false): string | undefined => {
      const v = f[k];
      if (v === undefined && optional) return undefined;
      if (typeof v !== 'string' || v.trim() === '') throw new Error(`reality: facts[${i}].${k} must be a non-empty string`);
      return v;
    };
    const date = str('date')!;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error(`reality: facts[${i}].date must be YYYY-MM-DD`);
    return { date, title: str('title')!, text: str('text')!, source: str('source')!, link: str('link', true) };
  });
}

/** Facts already true on the reached date, and those that came soon after. */
export function factsAround(facts: readonly RealityFact[], iso: string): { before: RealityFact[]; after: RealityFact[] } {
  const day = iso.slice(0, 10);
  const sorted = [...facts].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  return { before: sorted.filter((f) => f.date <= day), after: sorted.filter((f) => f.date > day) };
}

// ---------------------------------------------------------------- DOM

export interface EndScreenDeps {
  data: GameData;
  facts: readonly RealityFact[];
  /** «Jugar otra vez» / «Volver a intentarlo». */
  onRestart(): void;
}

function factList(facts: readonly RealityFact[]): HTMLElement {
  return el(
    'ul',
    { class: 'facts-list' },
    ...facts.map((f) =>
      el(
        'li',
        {},
        el('time', { class: 'num', datetime: f.date }, formatDay(f.date)),
        el('p', {}, f.text),
        el(
          'p',
          { class: 'small muted' },
          `${t('learn.source')}: `,
          f.link ? el('a', { href: f.link, target: '_blank', rel: 'noopener noreferrer' }, f.source) : f.source,
        ),
      ),
    ),
  );
}

/** Opens the end screen for a finished game; focus lands on the primary button. */
export function showEndScreen(s: GameState, deps: EndScreenDeps): Screen {
  const r = summarize(s, deps.data);
  const won = r.outcome === 'seed_round';
  const screen = openScreen(`endscreen ${won ? 'won' : 'lost'}`, t(won ? 'end.title.seed_round' : 'end.title.bankrupt', { lab: r.labName }));

  const stat = (label: string, value: string): HTMLElement => el('div', { class: 'end-stat' }, el('dt', {}, label), el('dd', { class: 'num' }, value));
  const gpuText = r.gpus.map((g) => `${g.count} × ${g.name}`).join(' · ') || '—';
  const stats = el(
    'dl',
    { class: 'end-stats' },
    stat(t('end.date'), formatDay(r.dateIso)),
    stat(t('end.weeks'), formatInt(r.weeks)),
    stat(t('end.cash'), formatUsd(r.cashUsd)),
    stat(t('end.gpus', { n: r.gpuCount }), gpuText),
    stat(t('end.customers'), formatInt(r.customers)),
    stat(t('end.gpuHours'), formatInt(r.gpuHours)),
    stat(t('end.rep'), formatInt(r.reputation)),
  );

  const primary = el('button', { type: 'button', class: 'btn btn-primary btn-lg' }, t(won ? 'end.again' : 'end.retry'));
  primary.addEventListener('click', () => {
    screen.close();
    deps.onRestart();
  });

  const sections: HTMLElement[] = [];
  if (won) {
    const { before, after } = factsAround(deps.facts, r.dateIso);
    const reality = el('section', { class: 'end-section reality', 'aria-labelledby': 'end-reality-h' }, el('h2', { id: 'end-reality-h' }, t('end.reality')));
    reality.append(el('p', { class: 'muted' }, t(before.length > 0 ? 'end.reality.before' : 'end.reality.none', { date: formatDay(r.dateIso) })));
    if (before.length > 0) reality.append(factList(before));
    if (after.length > 0) reality.append(...(before.length > 0 ? [el('h3', {}, t('end.reality.after'))] : []), factList(after));
    sections.push(reality, el('p', { class: 'end-next' }, t('end.next')));
  } else {
    const wrong = el('section', { class: 'end-section wrong', 'aria-labelledby': 'end-wrong-h' }, el('h2', { id: 'end-wrong-h' }, t('end.wrong')));
    wrong.append(
      el(
        'dl',
        { class: 'end-money' },
        ...r.costs.map((c) => el('div', { class: 'kv' }, el('dt', {}, t(`end.cost.${c.key}` as TextKey)), el('dd', { class: 'num neg' }, `−${formatUsd(c.usd)}`))),
        el('div', { class: 'kv' }, el('dt', {}, t('end.revenue')), el('dd', { class: 'num pos' }, formatUsd(r.revenueUsd, { signed: true }))),
      ),
    );
    const causes = diagnose(s, deps.data);
    if (causes.length > 0) wrong.append(el('ul', { class: 'end-causes' }, ...causes.map((c) => el('li', {}, t(`end.why.${c}` as TextKey)))));
    sections.push(wrong);
  }

  screen.el.append(
    el(
      'div',
      { class: 'end-card panel-surface' },
      el('p', { class: 'end-kicker num' }, t('end.kicker', { date: formatDay(r.dateIso) })),
      el('h1', {}, t(won ? 'end.title.seed_round' : 'end.title.bankrupt', { lab: r.labName })),
      el(
        'p',
        { class: 'end-lead' },
        t(won ? 'end.lead.seed_round' : 'end.lead.bankrupt', {
          raise: formatUsd(deps.data.world.seedRound.raiseUsd.value),
          pre: formatUsd(deps.data.world.seedRound.preMoneyUsd.value),
          weeks: deps.data.products.economy.bankruptcyNegativeWeeks.value,
        }),
      ),
      stats,
      ...sections,
      el('div', { class: 'end-actions' }, primary),
    ),
  );
  primary.focus({ preventScroll: true }); // keyboard on the primary action, the summary read from the top
  screen.el.scrollTop = 0;
  return screen;
}
