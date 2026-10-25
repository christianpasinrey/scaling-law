// Dev only (loaded behind import.meta.env.DEV): builds finished games for checking the end screens with
// ?devstate=seed_round | bankrupt. Runs the real sim; the seed round patches customers and reputation in, since
// reaching it by play is the balance pass's job (Task 15).
import { advance, applyCommand, newGame } from '../sim';
import type { GameData, GameState } from '../sim';

const WEEK = 168;

function replicate(d: GameData, seed: number): GameState {
  let s = newGame(d, seed, 'Laboratorio de pruebas');
  s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-1', to: 'train' });
  s = applyCommand(s, d, { t: 'start_job', jobId: 'replicate_paper' });
  for (let i = 0; i < 400 && s.jobs[0]!.status !== 'done'; i++) s = advance(s, d, 1);
  return s;
}

export function devState(kind: string, d: GameData): GameState | null {
  if (kind === 'seed_round') {
    let s = replicate(d, 11);
    s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-1', to: 'serve' });
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-2', to: 'serve' });
    s = advance(s, d, 30 * WEEK);
    s = { ...s, product: { ...s.product, customers: Math.max(s.product.customers, 312) }, reputation: Math.max(s.reputation, 30) };
    s = advance(s, d, 1); // the investor shows up
    return applyCommand(s, d, { t: 'accept_round' });
  }
  if (kind === 'bankrupt') {
    // Only buys GPUs and trains: no income at all.
    let s = newGame(d, 12, 'Garaje sin ingresos');
    s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-1' });
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-1', to: 'train' });
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-2', to: 'idle' });
    s = applyCommand(s, d, { t: 'start_job', jobId: 'replicate_paper' });
    s = advance(s, d, 30 * WEEK); // the open frame comes out on 2018-01-01
    s = applyCommand(s, d, { t: 'buy_rig', model: 'open_frame' });
    for (let i = 0; i < 3; i++) s = applyCommand(s, d, { t: 'buy_gpu', model: 'gtx1080ti', rigId: 'rig-2' });
    for (const g of s.gpus) s = applyCommand(s, d, { t: 'allocate', gpuId: g.id, to: 'train' });
    // Without income this takes years at garage electricity prices: start the slide with the savings spent.
    s = { ...s, cashUsd: Math.min(s.cashUsd, 40) };
    for (let w = 0; w < 400 && s.outcome === null; w++) s = advance(s, d, WEEK);
    return s;
  }
  return null;
}
