// UI shell: mounts the HUD, the four side panels (one open at a time; a bottom sheet on narrow screens),
// learn cards, toasts, banners and keyboard shortcuts. Every module patches its own DOM on update(state).
import type { Command, GameData, GameState, PulsoItem } from '../sim';
import type { Speed } from '../protocol';
import { el, setHidden, setText } from './dom';
import type { PanelDeps } from './dom';
import { conceptsPresent, t } from './format';
import type { TextKey } from './format';
import * as allocation from './allocation';
import * as hud from './hud';
import * as jobs from './jobs';
import * as learn from './learn';
import * as pulso from './pulso';
import * as shop from './shop';
import { confirmDialog } from './dialog';
import type { ConfirmOptions } from './dialog';
import type { LearnCard } from './learn';

export interface UiDeps {
  data: GameData;
  cards: Record<string, LearnCard>;
  send(c: Command): void;
  setSpeed(x: Speed): void;
  toggleBrain(): void;
  /** Highlights a GPU in the 3D garage. */
  highlightGpu(id: string | null): void;
  exportGame(): void;
  importGame(file: File): void;
  newGame(): void;
}

export type PanelId = 'shop' | 'alloc' | 'jobs' | 'pulso';

export interface UiApi {
  update(s: GameState): void;
  showSpeed(x: Speed): void;
  showBrain(expanded: boolean): void;
  openPanel(id: PanelId | null): void;
  /** A GPU was picked (garage click or Pulso): highlight it and open Asignación on its row. */
  selectGpu(id: string, focusRow?: boolean): void;
  openLearn(id: string): void;
  /** Persistent or dismissible notice under the HUD; the same id replaces its text. */
  banner(id: string, text: string, opts?: { dismissible?: boolean; tone?: 'warn' | 'error' | 'info' }): void;
  clearBanner(id: string): void;
  confirm(o: ConfirmOptions): Promise<boolean>;
}

const PANELS: { id: PanelId; key: TextKey }[] = [
  { id: 'shop', key: 'panel.shop' },
  { id: 'alloc', key: 'panel.alloc' },
  { id: 'jobs', key: 'panel.jobs' },
  { id: 'pulso', key: 'panel.pulso' },
];

const isTyping = (e: KeyboardEvent): boolean => {
  const tEl = e.target as HTMLElement | null;
  return !!tEl && (tEl.tagName === 'INPUT' || tEl.tagName === 'TEXTAREA' || tEl.tagName === 'SELECT' || tEl.isContentEditable);
};

export function mountUi(app: HTMLElement, deps: UiDeps): UiApi {
  const root = el('div', { class: 'ui' });
  app.append(root);

  const learnApi = learn.mount(root, deps.cards);
  const panelDeps: PanelDeps = {
    data: deps.data,
    send: deps.send,
    learn: (id, opener) => learnApi.open(id, opener),
    cardTitle: (id) => learnApi.title(id),
  };

  const hudApi = hud.mount(root, { ...panelDeps, setSpeed: deps.setSpeed, toggleBrain: deps.toggleBrain, exportGame: deps.exportGame, importGame: deps.importGame, newGame: deps.newGame });
  const banners = el('div', { class: 'banners', role: 'status' });
  root.append(banners);
  // Panels and the learn card start below the HUD and banners, whose height depends on wrapping.
  const hudEl = root.querySelector<HTMLElement>('.hud')!;
  const placeDock = (): void => {
    const bottom = Math.max(hudEl.getBoundingClientRect().bottom, banners.getBoundingClientRect().bottom);
    root.style.setProperty('--dock-top', `${Math.ceil(bottom + 8)}px`);
  };
  const ro = new ResizeObserver(placeDock);
  ro.observe(hudEl);
  ro.observe(banners);
  window.addEventListener('resize', placeDock);

  // ---- dock: tab buttons + panel host
  const tabs = el('nav', { class: 'tabs panel-surface', 'aria-label': t('tabs.label') });
  const host = el('div', { class: 'panel-host' });
  const dock = el('div', { class: 'dock' }, tabs, host);
  root.append(dock);

  const tabBtns = new Map<PanelId, HTMLButtonElement>();
  const panelEls = new Map<PanelId, HTMLElement>();
  const bodies = new Map<PanelId, HTMLElement>();
  let pulsoBadge: HTMLElement | null = null;
  for (const p of PANELS) {
    const btn = el('button', { type: 'button', class: 'tab', 'aria-expanded': 'false', 'aria-controls': `panel-${p.id}`, id: `tab-${p.id}` }, t(p.key));
    if (p.id === 'pulso') {
      pulsoBadge = el('span', { class: 'badge-count num', hidden: true });
      btn.append(pulsoBadge);
    }
    btn.addEventListener('click', () => openPanel(current === p.id ? null : p.id));
    tabs.append(btn);
    tabBtns.set(p.id, btn);
    const close = el('button', { type: 'button', class: 'icon-btn', 'aria-label': `${t('ui.close')} ${t(p.key)}` }, '×');
    close.addEventListener('click', () => openPanel(null, true));
    const body = el('div', { class: 'panel-body' });
    const section = el(
      'section',
      { class: 'panel panel-surface', id: `panel-${p.id}`, 'aria-labelledby': `panel-${p.id}-h`, hidden: true },
      el('header', { class: 'panel-head' }, el('h2', { id: `panel-${p.id}-h`, tabindex: '-1' }, t(p.key)), close),
      body,
    );
    section.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !isTyping(e)) {
        e.stopPropagation();
        openPanel(null, true);
      }
    });
    host.append(section);
    panelEls.set(p.id, section);
    bodies.set(p.id, body);
  }

  let current: PanelId | null = null;

  const focus = (f: NonNullable<PulsoItem['focus']>): void => {
    if (f.kind === 'gpu' && f.id) api.selectGpu(f.id, true);
    else if (f.kind === 'product') {
      openPanel('jobs');
      jobsApi.focusProduct();
    } else if (f.kind === 'power') hudApi.flashPower();
  };

  const shopApi = shop.mount(bodies.get('shop')!, panelDeps);
  const allocApi = allocation.mount(bodies.get('alloc')!, { ...panelDeps, selectGpu: (id) => api.selectGpu(id) });
  const jobsApi = jobs.mount(bodies.get('jobs')!, panelDeps, root);
  const pulsoApi = pulso.mount(bodies.get('pulso')!, { focus, selectGpu: (id) => api.selectGpu(id, true) });

  function openPanel(id: PanelId | null, returnFocus = false): void {
    const prev = current;
    current = id;
    for (const [pid, sec] of panelEls) setHidden(sec, pid !== id);
    for (const [pid, b] of tabBtns) {
      b.setAttribute('aria-expanded', String(pid === id));
      b.classList.toggle('active', pid === id);
    }
    dock.classList.toggle('open', id !== null);
    if (id === 'pulso') {
      pulsoApi.markSeen();
      refreshBadge();
    }
    if (id === null && returnFocus && prev) tabBtns.get(prev)?.focus();
  }

  function refreshBadge(): void {
    if (!pulsoBadge) return;
    if (current === 'pulso') pulsoApi.markSeen();
    const n = pulsoApi.unseen();
    setHidden(pulsoBadge, n === 0);
    setText(pulsoBadge, n > 99 ? '99+' : String(n));
    pulsoBadge.setAttribute('aria-label', t('pulso.unseen', { n }));
  }

  // ---- keyboard: Space toggles pause ↔ last speed, 1/2/3 = ×1/×2/×4 (b and Esc belong to the brain).
  let speed: Speed = 0;
  let lastRunning: Speed = 1;
  window.addEventListener('keydown', (e) => {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey || isTyping(e)) return;
    if (document.querySelector('dialog[open]')) return;
    if (e.key === ' ' || e.code === 'Space') {
      // Space is the game's pause key everywhere except text fields and dialogs (Enter still activates buttons):
      // a keyboard player nearly always has a button focused, so deferring to it would make pause unreachable.
      e.preventDefault();
      if (!e.repeat) deps.setSpeed(speed === 0 ? lastRunning : 0);
    } else if (e.key === '1' || e.key === '2' || e.key === '3') {
      deps.setSpeed(e.key === '1' ? 1 : e.key === '2' ? 2 : 4);
    }
  });

  const api: UiApi = {
    update(s) {
      hudApi.update(s);
      shopApi.update(s);
      allocApi.update(s);
      jobsApi.update(s);
      pulsoApi.update(s);
      refreshBadge();
      learnApi.notice(conceptsPresent(s, deps.data));
      if (s.outcome) banner('outcome', t(s.outcome === 'seed_round' ? 'outcome.seed_round' : 'outcome.bankrupt'), { tone: 'info' });
    },
    showSpeed(x) {
      speed = x;
      if (x !== 0) lastRunning = x;
      hudApi.showSpeed(x);
    },
    showBrain(v) {
      hudApi.showBrain(v);
      if (v) openPanel(null); // the expanded brain needs the room the side panel takes
    },
    openPanel,
    selectGpu(id, focusRow = false) {
      deps.highlightGpu(id);
      openPanel('alloc');
      allocApi.select(id, focusRow);
    },
    openLearn(id) {
      learnApi.open(id);
    },
    banner,
    clearBanner(id) {
      banners.querySelector(`[data-banner="${CSS.escape(id)}"]`)?.remove();
    },
    confirm(o) {
      return confirmDialog(root, o);
    },
  };

  function banner(id: string, text: string, opts: { dismissible?: boolean; tone?: 'warn' | 'error' | 'info' } = {}): void {
    let b = banners.querySelector<HTMLElement>(`[data-banner="${CSS.escape(id)}"]`);
    if (!b) {
      b = el('div', { class: 'banner panel-surface', 'data-banner': id, 'data-tone': opts.tone ?? 'warn' }, el('span', { class: 'banner-text' }));
      if (opts.dismissible) {
        const x = el('button', { type: 'button', class: 'icon-btn', 'aria-label': t('banner.dismiss') }, '×');
        x.addEventListener('click', () => b?.remove());
        b.append(x);
      }
      banners.append(b);
    }
    setText(b.querySelector('.banner-text')!, text);
  }

  return api;
}
