// TEMPORARY DEV HARNESS (Task 11) — Task 13 replaces this file with the real UI wired to the Worker bridge.
// Drives the 3D garage from a local GameState (no worker) with keyboard shortcuts:
//   g      buy a GTX 1080 Ti into the tower
//   t      allocate every GPU to 'train' and start replicate_paper
//   f      buy the open frame (injected if not yet released) + GPUs until there are 7 (> 1,800 W when all train)
//   i      set the last GPU to idle      r  reset the breaker
//   s      allocate every GPU to 'serve' (inference once the paper is replicated)
//   h      dev only: cycle the first GPU's perf 1 → 0.7 → 0 (brain/garage state colours)
//   b      toggle the brain (handled by BrainView)   Esc  close the expanded brain
//   space  advance 24 game hours
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { advance, applyCommand, loadData, newGame } from './sim';
import type { Command, GameState } from './sim';
import { createScene } from './render/scene';
import { GarageView } from './render/garage';
import { BrainView } from './render/brain';

const data = loadData({ hardware, world, products, pulso });
let state: GameState = newGame(data, 1, 'Dev Lab');

const app = document.getElementById('app') ?? document.body;
document.body.style.margin = '0';
document.body.style.background = '#0a0908';
const canvas = document.createElement('canvas');
canvas.style.cssText = 'display:block;width:100vw;height:100vh;touch-action:none';
app.appendChild(canvas);
const hud = document.createElement('pre');
hud.style.cssText =
  'position:fixed;left:12px;top:10px;margin:0;color:#cfd6dc;font:12px/1.45 ui-monospace,monospace;' +
  'background:rgba(0,0,0,.45);padding:8px 10px;border-radius:6px;pointer-events:none';
app.appendChild(hud);

const ctx = createScene(canvas);
const garage = new GarageView(ctx);
garage.on('select', (e) => console.info(`[dev] select ${e.kind} ${e.id}`));
const brain = new BrainView(ctx);
brain.on('select', (e) => console.info(`[dev] select ${e.kind} ${e.blockId}`));
// Dev only: lets browser checks freeze the brain's animation phase for screenshots.
if (import.meta.env.DEV) (window as unknown as { __brain: BrainView }).__brain = brain;

function render(): void {
  garage.update(state, data);
  brain.update(state, data);
  const job = state.jobs.find((j) => j.id === 'replicate_paper');
  hud.textContent =
    `DEV HARNESS (temporal, Tarea 13 lo sustituye)\n` +
    `hora ${state.hour}  caja ${state.cashUsd.toFixed(0)} $\n` +
    `potencia ${state.power.watts.toFixed(0)} W  diferencial ${state.power.breakerTripped ? 'SALTADO' : 'ok'}\n` +
    `GPUs ${state.gpus.length}  ${state.gpus.map((g) => `${g.id}:${state.allocation[g.id]}`).join(' ')}\n` +
    `replicate_paper ${job ? `${job.status} ${job.doneP100h.toFixed(1)}/${job.workP100h}` : '-'}\n` +
    `servido ${state.product.servedMCharsH.toFixed(2)} M car./h  clientes ${state.product.customers.toFixed(0)}
` +
    `[g] GPU torre  [t] entrenar  [s] servir  [f] bastidor+GPUs  [i] idle  [r] diferencial
` +
    `[h] perf GPU 1 (dev)  [b] cerebro  [espacio] +24 h`;
}

const cmd = (c: Command): void => {
  state = applyCommand(state, data, c);
};

function buyOpenFrame(): void {
  const before = state.rigs.length;
  cmd({ t: 'buy_rig', model: 'open_frame' });
  if (state.rigs.length === before) {
    // Dev only: the frame is released 2018-01-01; inject it so the garage can be tested from 2017.
    const n = state.rigs.length + 1;
    state = { ...state, cashUsd: state.cashUsd - 350, rigs: [...state.rigs, { id: `rig-${n}`, model: 'open_frame' }] };
  }
  const frame = state.rigs.find((r) => r.model === 'open_frame');
  if (!frame) return;
  const want = Math.max(4, 7 - state.gpus.length);
  for (let i = 0; i < want; i++) cmd({ t: 'buy_gpu', model: 'gtx1080ti', rigId: frame.id });
}

window.addEventListener('keydown', (e) => {
  switch (e.key) {
    case 'g':
      cmd({ t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
      break;
    case 't':
      for (const g of state.gpus) cmd({ t: 'allocate', gpuId: g.id, to: 'train' });
      if (state.jobs.some((j) => j.id === 'replicate_paper' && j.status === 'ready')) cmd({ t: 'start_job', jobId: 'replicate_paper' });
      break;
    case 'f':
      buyOpenFrame();
      break;
    case 'i': {
      const last = state.gpus[state.gpus.length - 1];
      if (last) cmd({ t: 'allocate', gpuId: last.id, to: 'idle' });
      break;
    }
    case 'r':
      cmd({ t: 'reset_breaker' });
      break;
    case 's':
      for (const g of state.gpus) cmd({ t: 'allocate', gpuId: g.id, to: 'serve' });
      break;
    case 'h': {
      // Dev only: fake a thermal state on the first GPU to check the state colours.
      const next = (p: 0 | 0.7 | 1): 0 | 0.7 | 1 => (p === 1 ? 0.7 : p === 0.7 ? 0 : 1);
      state = { ...state, gpus: state.gpus.map((g, i) => (i === 0 ? { ...g, perf: next(g.perf) } : g)) };
      break;
    }
    case ' ':
      e.preventDefault();
      state = advance(state, data, 24);
      break;
    default:
      return;
  }
  render();
});

render();
