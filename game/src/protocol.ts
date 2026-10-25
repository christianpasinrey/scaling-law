import type { Command, GameState } from './sim';

export type Speed = 0 | 1 | 2 | 4;
export type ToWorker =
  | { t: 'init'; state: GameState }
  | { t: 'cmd'; cmd: Command }
  | { t: 'speed'; x: Speed }
  | { t: 'tick'; realMs: number };
export type FromWorker = { t: 'state'; state: GameState };
