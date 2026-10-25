// Real wiring: data → scene (garage + brain) → Worker + SimBridge → UI; save/load/autosave (ruling R16).
import './ui/ui.css';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import learnData from '../data/learn.es.json';
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

const data = loadData({ hardware, world, products, pulso });
const cards = parseCards(learnData);

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
  prevHour = s.hour;
  render(s);
  if (canSave && shouldAutosave(prev, s.hour)) void persist(s);
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

function begin(s: GameState): void {
  prevHour = s.hour;
  render(s);
  bridge.start(s);
  setSpeed(1);
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
  // An explicit, confirmed replacement: this game becomes the save (R16).
  canSave = true;
  begin(r.state);
  void persist(r.state);
}

async function startNewGame(): Promise<void> {
  const ok = await ui.confirm({ title: t('save.new.title'), body: t('save.new.body') });
  if (!ok) return;
  canSave = true;
  const s = newGame(data, randomSeed(), t('save.defaultLab'));
  begin(s);
  void persist(s);
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
  const p = startPolicy(await loadGame());
  canSave = p.canSave;
  if (p.notice === 'unavailable') ui.banner('storage', t('save.unavailable'), { tone: 'warn' });
  else if (p.notice === 'corrupt') ui.banner('load', t('save.corrupt'), { tone: 'warn', dismissible: true });
  else if (p.notice === 'version') ui.banner('load', t('save.version'), { tone: 'warn', dismissible: true });
  begin(p.resume ?? newGame(data, randomSeed(), t('save.defaultLab')));
}

// Dev only: lets browser checks read the state and freeze the brain's animation phase.
if (import.meta.env.DEV) {
  Object.assign(window as object, { __brain: brain, __state: () => state, __bridge: bridge });
}

void boot();
