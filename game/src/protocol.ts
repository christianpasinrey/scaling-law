import type { Command, GameState } from './sim';

export type Speed = 0 | 1 | 2 | 4;
export type ToWorker =
  /** `epoch` grows with every init; states carry it so the main thread can drop replies to an older game (R23). */
  | { t: 'init'; state: GameState; epoch: number }
  | { t: 'cmd'; cmd: Command }
  | { t: 'speed'; x: Speed }
  | { t: 'tick'; realMs: number };
export type FromWorker = { t: 'state'; state: GameState; epoch: number };
