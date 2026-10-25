// Real wiring: data → scene (garage + brain) → Worker + SimBridge → UI; save/load/autosave (ruling R16);
// boot flow: title screen (saved game) or the opening → lab name → garage; end screens once the game has an outcome.
import './ui/ui.css';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import learnData from '../data/learn.es.json';
import reality from '../data/reality.es.json';
import { loadData, newGame } from './sim';
import type { GameState } from './sim';
import type { Speed } from './protocol';
import { SimBridge } from './bridge';
import type { WorkerLike } from './bridge';
import { exportFileName, exportSave, importSave, loadGame, saveGame, shouldAutosave, startPolicy } from './save';
import { createScene } from './render/scene';
import { GarageView } from './render/garage';
import { BrainView } from './render/brain';
import { mountUi } from './ui/ui';
import { parseCards } from './ui/learn';
import { brainCard, formatDate, t } from './ui/format';
import { dateOf } from './sim/time';
import { runIntro } from './intro/intro';
import { openScreen } from './ui/screen';
import type { Screen } from './ui/screen';
import { parseFacts, showEndScreen } from './ui/endscreen';
import { el } from './ui/dom';
import { confirmDialog } from './ui/dialog';

const data = loadData({ hardware, world, products, pulso });
const cards = parseCards(learnData);
const facts = parseFacts(reality);

const app = document.getElementById('app') ?? document.body;
const canvas = document.createElement('canvas');
canvas.className = 'garage-canvas';
canvas.setAttribute('aria-label', t('garage.canvas'));
app.appendChild(canvas);

const ctx = createScene(canvas);
const garage = new GarageView(ctx);
const brain = new BrainView(ctx);

const worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' });
const bridge = new SimBridge(worker as unknown as WorkerLike);
// An uncaught error inside the simulation: stop the clock and tell the player (the last good state can be exported).
const onWorkerError = (e: Event): void => {
  e.preventDefault();
  console.error('simulation worker error', e);
  setSpeed(0);
  ui.banner('worker', t('sim.error'), { tone: 'error' });
};
worker.addEventListener('error', onWorkerError);
worker.addEventListener('messageerror', onWorkerError);

let state: GameState | null = null;
let prevHour = 0;
/** Ruling R16: only a game from a successful load, or one that replaced a missing/broken save, may be written. */
let canSave = false;

const setSpeed = (x: Speed): void => {
  bridge.setSpeed(x);
  ui.showSpeed(x);
};

const ui = mountUi(app, {
  data,
  cards,
  send: (c) => bridge.send(c),
  setSpeed,
  toggleBrain: () => {
    brain.setExpanded(!brain.isExpanded);
    ui.showBrain(brain.isExpanded);
  },
  highlightGpu: (id) => garage.highlight(id),
  exportGame,
  importGame: (f) => void importGame(f),
  newGame: () => void startNewGame(),
});

garage.on('select', (e) => ui.selectGpu(e.id));
brain.on('select', (e) => ui.openLearn(brainCard(e.blockId)));
// The brain also toggles itself (b, Esc, click on the picture-in-picture): keep the HUD button in sync.
let brainShown = brain.isExpanded;
ctx.onFrame(() => {
  if (brain.isExpanded !== brainShown) {
    brainShown = brain.isExpanded;
    ui.showBrain(brainShown);
  }
});

function render(s: GameState): void {
  state = s;
  garage.update(s, data);
  brain.update(s, data);
  ui.update(s);
}

bridge.onState((s) => {
  const prev = prevHour;
  const wasOver = state?.outcome != null;
  prevHour = s.hour;
  render(s);
  if (s.outcome !== null && !wasOver) {
    // The finished game stays the save, so a reload shows the end screen instead of resuming it.
    if (canSave) void persist(s);
    showEnd(s);
  } else if (canSave && shouldAutosave(prev, s.hour)) void persist(s);
});

async function persist(s: GameState): Promise<void> {
  try {
    await saveGame(s);
    ui.clearBanner('save-failed');
    ui.clearBanner('storage');
  } catch {
    ui.banner('save-failed', t('save.failed'), { tone: 'error', dismissible: true });
  }
}

/**
 * Shows and starts a game. Returns false (and puts the previous game back on screen) if the state could not be
 * applied, e.g. an import that passed validation but breaks rendering; the caller tells the player.
 */
function begin(s: GameState): boolean {
  const before = state;
  const beforeHour = prevHour;
  try {
    prevHour = s.hour;
    ui.reset();
    render(s);
    bridge.start(s);
  } catch (err) {
    console.error(err);
    setSpeed(0);
    prevHour = beforeHour;
    state = before;
    if (before) {
      try {
        render(before);
      } catch {
        // the previous view stays as it was
      }
    }
    return false;
  }
  if (s.outcome !== null) {
    setSpeed(0);
    showEnd(s);
  } else if (s.round?.status === 'offered') {
    setSpeed(0); // the investor's offer is open: the player decides before time runs again
  } else setSpeed(1);
  return true;
}

/** begin() for a game read from storage: if it cannot be shown, say so and start a new one instead. */
function beginLoaded(s: GameState): void {
  if (begin(s)) return;
  ui.banner('load', t('save.corrupt'), { tone: 'warn', dismissible: true });
  showIntro((name) => startFresh(name, false));
}

// ---------------------------------------------------------------- full-screen layers

let screen: Screen | null = null;
let disposeIntro: (() => void) | null = null;

function closeScreen(): void {
  disposeIntro?.();
  disposeIntro = null;
  screen?.close();
  screen = null;
}

/** The opening; its hand-off card asks for the lab name, then `start` gets it. */
function showIntro(start: (labName: string) => void): void {
  closeScreen();
  setSpeed(0); // a game behind the opening (menu → Partida nueva) must not run on
  const sc = openScreen('intro-screen', t('intro.label'));
  screen = sc;
  const intro = runIntro(sc.el, {
    skippable: true,
    cards,
    defaultName: t('save.defaultLab'),
    onDone: (name) => {
      closeScreen();
      start(name);
    },
  });
  disposeIntro = () => intro.dispose();
}

/** A new game from the opening. `explicit`: the player chose it, so it may replace the save (R16). */
function startFresh(labName: string, explicit: boolean): void {
  if (explicit) canSave = true;
  const s = newGame(data, randomSeed(), labName);
  begin(s);
  if (canSave) void persist(s);
}

function showTitle(saved: GameState): void {
  closeScreen();
  const sc = openScreen('title-screen', t('title.label'));
  screen = sc;
  const cont = el('button', { type: 'button', class: 'btn btn-primary btn-lg' }, t('title.continue'));
  const fresh = el('button', { type: 'button', class: 'btn btn-lg' }, t('title.new'));
  cont.addEventListener('click', () => {
    closeScreen();
    beginLoaded(saved);
  });
  fresh.addEventListener('click', () => {
    void confirmDialog(sc.el, { title: t('save.new.title'), body: t('save.new.body') }).then((ok) => {
      if (ok) showIntro((name) => startFresh(name, true));
    });
  });
  sc.el.append(
    el(
      'div',
      { class: 'title-card' },
      el('h1', { class: 'title-brand' }, 'SCALING LAW'),
      el('p', { class: 'title-tagline' }, t('title.tagline')),
      el('p', { class: 'title-saved num' }, t('title.saved', { lab: saved.labName, date: formatDate(dateOf(saved)) })),
      el('div', { class: 'title-actions' }, cont, fresh),
    ),
  );
  cont.focus();
}

function showEnd(s: GameState): void {
  if (screen?.el.classList.contains('endscreen')) return;
  closeScreen();
  screen = showEndScreen(s, {
    data,
    facts,
    onRestart: () => {
      screen = null;
      showIntro((name) => startFresh(name, true));
    },
  });
}

function randomSeed(): number {
  return crypto.getRandomValues(new Uint32Array(1))[0]!;
}

function exportGame(): void {
  if (!state) return;
  const url = URL.createObjectURL(exportSave(state));
  const a = document.createElement('a');
  a.href = url;
  a.download = exportFileName(state);
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function importGame(file: File): Promise<void> {
  const r = await importSave(file);
  if (!r.ok) {
    ui.banner('import', t(r.reason === 'version' ? 'save.importVersion' : 'save.importBad'), { tone: 'error', dismissible: true });
    return;
  }
  ui.clearBanner('import');
  const ok = await ui.confirm({
    title: t('save.import.title'),
    body: t('save.import.body', { lab: r.state.labName, date: formatDate(dateOf(r.state)) }),
  });
  if (!ok) return;
  if (!begin(r.state)) {
    ui.banner('import', t('save.importBad'), { tone: 'error', dismissible: true });
    return;
  }
  // An explicit, confirmed replacement: this game becomes the save (R16).
  canSave = true;
  void persist(r.state);
}

async function startNewGame(): Promise<void> {
  const ok = await ui.confirm({ title: t('save.new.title'), body: t('save.new.body') });
  if (!ok) return;
  showIntro((name) => startFresh(name, true));
}

// Best effort: IndexedDB may not finish before the page goes away; hiding the tab is the last reliable moment on mobile.
const saveOnLeave = (): void => {
  if (canSave && state) void saveGame(state).catch(() => undefined);
};
window.addEventListener('pagehide', saveOnLeave);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') saveOnLeave();
});

async function boot(): Promise<void> {
  // Dev only: ?devstate=seed_round|bankrupt opens a finished game (not saved unless &devsave=1).
  if (import.meta.env.DEV) {
    const q = new URLSearchParams(location.search);
    const kind = q.get('devstate');
    if (kind) {
      const { devState } = await import('./dev/devstate');
      const s = devState(kind, data);
      if (s) {
        canSave = q.get('devsave') === '1';
        begin(s);
        if (canSave) void persist(s);
        return;
      }
    }
  }
  const p = startPolicy(await loadGame());
  canSave = p.canSave;
  if (p.notice === 'unavailable') ui.banner('storage', t('save.unavailable'), { tone: 'warn' });
  else if (p.notice === 'corrupt') ui.banner('load', t('save.corrupt'), { tone: 'warn', dismissible: true });
  else if (p.notice === 'version') ui.banner('load', t('save.version'), { tone: 'warn', dismissible: true });
  if (!p.resume) showIntro((name) => startFresh(name, false));
  else if (p.resume.outcome !== null) beginLoaded(p.resume); // a finished game: straight to its end screen
  else showTitle(p.resume);
}

// Dev only: lets browser checks read the state and freeze the brain's animation phase.
if (import.meta.env.DEV) {
  Object.assign(window as object, { __brain: brain, __state: () => state, __bridge: bridge });
}

void boot();
