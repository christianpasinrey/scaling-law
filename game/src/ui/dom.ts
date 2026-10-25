// Tiny DOM helpers shared by the UI modules (no framework). Modules build their DOM once in mount() and
// patch text/attributes in update(), so keyboard focus survives the ~4 state messages per second.
import type { Command, GameData, PulsoItem } from '../sim';
import { t } from './format';

type Attrs = Record<string, string | number | boolean | null | undefined>;
type Child = Node | string | null | undefined | false;

export function el<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Attrs = {}, ...children: Child[]): HTMLElementTagNameMap[K] {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') n.className = String(v);
    else n.setAttribute(k, v === true ? '' : String(v));
  }
  for (const c of children) if (c !== null && c !== undefined && c !== false) n.append(c);
  return n;
}

/** Sets textContent only when it changed (no layout churn, no screen-reader chatter). */
export function setText(n: Element, text: string): void {
  if (n.textContent !== text) n.textContent = text;
}

export function setAttr(n: Element, name: string, value: string | null): void {
  if (value === null) {
    if (n.hasAttribute(name)) n.removeAttribute(name);
  } else if (n.getAttribute(name) !== value) n.setAttribute(name, value);
}

export function setHidden(n: HTMLElement, hidden: boolean): void {
  if (n.hidden !== hidden) n.hidden = hidden;
}

/** What every panel needs from the shell. */
export interface PanelDeps {
  data: GameData;
  send(c: Command): void;
  /** Opens a learn card; `opener` gets focus back when the card closes. */
  learn(id: string, opener?: HTMLElement): void;
  cardTitle(id: string): string;
}

/** Shell-level callbacks a panel may trigger. */
export interface FocusDeps {
  focus(f: NonNullable<PulsoItem['focus']>): void;
  selectGpu(id: string): void;
}

/** The small "?" button that opens a learn card. */
export function learnButton(deps: PanelDeps, id: string): HTMLButtonElement {
  const b = el('button', { type: 'button', class: 'learn-q', 'aria-label': t('ui.learnMore', { title: deps.cardTitle(id) }), title: deps.cardTitle(id) }, '?');
  b.addEventListener('click', () => deps.learn(id, b));
  return b;
}

/** Panel section heading with an optional learn button. */
export function sectionHead(deps: PanelDeps, text: string, learnId?: string): HTMLElement {
  return el('h3', { class: 'sec-head' }, el('span', {}, text), learnId ? learnButton(deps, learnId) : null);
}
