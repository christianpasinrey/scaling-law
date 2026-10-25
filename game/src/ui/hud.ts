// Top bar: lab and date, speed, cash, last week's balance, power bar, reputation, breaker reset, brain and menu.
import type { GameState } from '../sim';
import { dateOf } from '../sim/time';
import type { Speed } from '../protocol';
import { el, learnButton, setAttr, setHidden, setText } from './dom';
import type { PanelDeps } from './dom';
import { formatDate, formatInt, formatUsd, formatWatts, lastWeekBalance, powerBar, t } from './format';
import { currentObjective } from './objectives';
import type { Objective } from './objectives';

export interface HudDeps extends PanelDeps {
  setSpeed(x: Speed): void;
  toggleBrain(): void;
  exportGame(): void;
  importGame(file: File): void;
  newGame(): void;
  /** The objective under the date was clicked. */
  openObjective(panel: Objective['panel']): void;
}

export interface HudApi {
  update(s: GameState): void;
  showSpeed(x: Speed): void;
  showBrain(expanded: boolean): void;
  /** Briefly highlights the power bar (Pulso focus 'power'). */
  flashPower(): void;
}

const SPEEDS: { x: Speed; label: string; title: Parameters<typeof t>[0] }[] = [
  { x: 0, label: '❚❚', title: 'hud.speed.pause.title' },
  { x: 1, label: '×1', title: 'hud.speed.x1.title' },
  { x: 2, label: '×2', title: 'hud.speed.x2.title' },
  { x: 4, label: '×4', title: 'hud.speed.x4.title' },
];

export function mount(root: HTMLElement, deps: HudDeps): HudApi {
  const w = deps.data.world;
  const stat = (label: string, value: HTMLElement, ...extra: (Node | null)[]): HTMLElement =>
    el('div', { class: 'stat' }, el('span', { class: 'stat-label' }, label), value, ...extra);

  const lab = el('span', { class: 'lab-name' });
  const date = el('time', { class: 'num date' });
  // Current M1 objective, under the date; clicking it opens the panel (or the offer) that moves it forward.
  const objStep = el('span', { class: 'obj-step' });
  const objText = el('span', { class: 'obj-text' });
  const objProg = el('span', { class: 'obj-prog num' });
  const objBtn = el('button', { type: 'button', class: 'objective' }, objStep, objText, objProg);
  let objPanel: Objective['panel'] = null;
  objBtn.addEventListener('click', () => deps.openObjective(objPanel));
  const ident = el('div', { class: 'stat ident' }, lab, date, objBtn);

  const speedBtns = SPEEDS.map((s) => {
    const b = el('button', { type: 'button', class: 'seg', 'aria-pressed': 'false', title: t(s.title), 'aria-label': t(s.title) }, s.label);
    b.addEventListener('click', () => deps.setSpeed(s.x));
    return { x: s.x, b };
  });
  const speedCap = el('span', { class: 'speed-cap', hidden: true }, t('hud.speed.capped'));
  const speed = el('div', { class: 'speed', role: 'group', 'aria-label': t('hud.speed') }, ...speedBtns.map((s) => s.b), speedCap);

  const cash = el('span', { class: 'num big' });
  const week = el('span', { class: 'num' });

  const fill = el('div', { class: 'pbar-fill' });
  const safeMark = el('div', { class: 'pbar-mark safe' });
  const tripMark = el('div', { class: 'pbar-mark trip' });
  const bar = el('div', { class: 'pbar', role: 'meter', 'aria-valuemin': '0', 'aria-valuemax': String(w.circuitWatts), 'aria-label': t('hud.power') }, fill, safeMark, tripMark);
  const watts = el('span', { class: 'num' });
  const marks = el('span', { class: 'pbar-legend num' }, t('hud.power.marks', { safe: formatWatts(w.circuitSafeWatts), trip: formatWatts(w.circuitWatts) }));
  const power = el(
    'div',
    { class: 'stat power' },
    el('span', { class: 'stat-label' }, t('hud.power'), learnButton(deps, 'breaker')),
    el('div', { class: 'power-row' }, bar, watts),
    marks,
  );

  const rep = el('span', { class: 'num' });
  const reset = el('button', { type: 'button', class: 'btn btn-danger', hidden: true, 'aria-label': t('hud.breaker.reset.aria'), title: t('hud.breaker.reset.aria') }, t('hud.breaker.reset'));
  reset.addEventListener('click', () => deps.send({ t: 'reset_breaker' }));

  const brainBtn = el('button', { type: 'button', class: 'btn', 'aria-pressed': 'false', title: t('hud.brain.title') }, t('hud.brain'));
  brainBtn.addEventListener('click', () => deps.toggleBrain());

  // Game menu: export / import / new game.
  const file = el('input', { type: 'file', accept: '.json,application/json', class: 'sr-only', tabindex: '-1', 'aria-hidden': 'true' });
  file.addEventListener('change', () => {
    const f = file.files?.[0];
    file.value = '';
    if (f) deps.importGame(f);
  });
  const menuBtn = el('button', { type: 'button', class: 'btn', 'aria-haspopup': 'true', 'aria-expanded': 'false', 'aria-controls': 'game-menu' }, t('hud.menu'), ' ▾');
  const item = (label: string, fn: () => void): HTMLButtonElement => {
    const b = el('button', { type: 'button', class: 'menu-item' }, label);
    b.addEventListener('click', () => {
      closeMenu(true); // focus back on the menu button (dialogs return focus there)
      fn();
    });
    return b;
  };
  const menu = el(
    'div',
    { id: 'game-menu', class: 'menu panel-surface', hidden: true },
    item(t('menu.export'), () => deps.exportGame()),
    item(t('menu.import'), () => file.click()),
    item(t('menu.new'), () => deps.newGame()),
  );
  const menuWrap = el('div', { class: 'menu-wrap' }, menuBtn, menu, file);
  const closeMenu = (focusBtn = false): void => {
    menu.hidden = true;
    menuBtn.setAttribute('aria-expanded', 'false');
    if (focusBtn) menuBtn.focus();
  };
  menuBtn.addEventListener('click', () => {
    const open = menu.hidden;
    menu.hidden = !open;
    menuBtn.setAttribute('aria-expanded', String(open));
    if (open) (menu.querySelector('button') as HTMLButtonElement | null)?.focus();
  });
  menu.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      closeMenu(true);
    }
  });
  document.addEventListener('pointerdown', (e) => {
    if (!menu.hidden && !menuWrap.contains(e.target as Node)) closeMenu();
  });
  menuWrap.addEventListener('focusout', (e) => {
    if (!menu.hidden && !menuWrap.contains(e.relatedTarget as Node | null) && e.relatedTarget !== null) closeMenu();
  });

  const bar1 = el(
    'header',
    { class: 'hud panel-surface' },
    ident,
    speed,
    stat(t('hud.cash'), cash),
    stat(t('hud.week'), week),
    power,
    stat(t('hud.rep'), rep),
    el('div', { class: 'hud-actions' }, reset, brainBtn, menuWrap),
  );
  root.append(bar1);

  let flashTimer = 0;
  let shownSpeed: Speed = 0;
  let tripped = false;
  const refreshCap = (): void => setHidden(speedCap, !(tripped && shownSpeed > 1));

  return {
    update(s) {
      setText(lab, s.labName);
      const iso = dateOf(s);
      setText(date, formatDate(iso));
      setAttr(date, 'datetime', iso);
      setText(cash, formatUsd(s.cashUsd));
      cash.classList.toggle('neg', s.cashUsd < 0);

      const wb = lastWeekBalance(s);
      if (wb) {
        setText(week, formatUsd(wb.netUsd, { signed: true }));
        setAttr(week, 'title', t('hud.week.title', { week: wb.week, rev: formatUsd(wb.revenueUsd), costs: formatUsd(wb.costsUsd) }));
      } else {
        setText(week, t('hud.week.none'));
        setAttr(week, 'title', null);
      }
      week.classList.toggle('pos', !!wb && wb.netUsd > 0);
      week.classList.toggle('neg', !!wb && wb.netUsd < 0);

      tripped = s.power.breakerTripped;
      const pb = powerBar(s.power.watts, w, tripped);
      fill.style.width = `${pb.pct.toFixed(1)}%`;
      safeMark.style.left = `${pb.safePct.toFixed(1)}%`;
      tripMark.style.left = `${pb.tripPct.toFixed(1)}%`;
      power.dataset.zone = pb.zone;
      setText(watts, tripped ? t('hud.power.tripped') : formatWatts(s.power.watts));
      setAttr(bar, 'aria-valuenow', String(Math.round(s.power.watts)));
      setAttr(bar, 'aria-valuetext', tripped ? t('hud.power.tripped') : formatWatts(s.power.watts));
      setAttr(power, 'title', t('hud.power.title', { w: formatWatts(s.power.watts), safe: formatWatts(w.circuitSafeWatts), trip: formatWatts(w.circuitWatts) }));
      setHidden(reset, !tripped);
      refreshCap();

      setText(rep, formatInt(s.reputation));

      const o = currentObjective(s, deps.data);
      objPanel = o.panel;
      objBtn.dataset.obj = o.id;
      objBtn.disabled = o.panel === null;
      setText(objStep, o.step <= 4 ? t('obj.label', { step: o.step }) : t('obj.label.done'));
      setText(objText, o.text);
      const prog = (o.progress ?? []).map((p) => `${formatInt(p.done)}/${formatInt(p.total)} ${p.label}`).join(' · ');
      setText(objProg, prog);
      setHidden(objProg, prog === '');
      setAttr(objBtn, 'aria-label', `${o.step <= 4 ? t('obj.label', { step: o.step }) : t('obj.label.done')}: ${o.text}${prog ? ` (${prog})` : ''}`);
      setAttr(objBtn, 'title', o.panel ? t('obj.open', { text: o.text }) : null);
    },
    showSpeed(x) {
      shownSpeed = x;
      for (const s of speedBtns) setAttr(s.b, 'aria-pressed', String(s.x === x));
      refreshCap();
    },
    showBrain(v) {
      setAttr(brainBtn, 'aria-pressed', String(v));
    },
    flashPower() {
      power.classList.remove('flash');
      void power.offsetWidth; // restart the animation
      power.classList.add('flash');
      window.clearTimeout(flashTimer);
      flashTimer = window.setTimeout(() => power.classList.remove('flash'), 2400);
      power.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    },
  };
}
