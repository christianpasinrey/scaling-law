import type { Command, GameState } from './sim';
import type { FromWorker, Speed, ToWorker } from './protocol';

export interface WorkerLike {
  postMessage(m: ToWorker): void;
  onmessage: ((e: { data: FromWorker }) => void) | null;
}

/** Injectable environment so the bridge needs no DOM in tests. */
export interface BridgeEnv {
  now(): number;
  isHidden(): boolean;
  onVisibilityChange(cb: () => void): void;
  /** Runs cb every frame; returns a cancel function. */
  schedule(cb: () => void): () => void;
}

export function browserEnv(): BridgeEnv {
  return {
    now: () => performance.now(),
    isHidden: () => document.visibilityState === 'hidden',
    onVisibilityChange: (cb) => document.addEventListener('visibilitychange', cb),
    schedule: (cb) => {
      let id = 0;
      const loop = () => { cb(); id = requestAnimationFrame(loop); };
      id = requestAnimationFrame(loop);
      return () => cancelAnimationFrame(id);
    },
  };
}

export class SimBridge {
  private listeners: Array<(s: GameState) => void> = [];
  private speed: Speed = 0;
  private last = 0;
  private cancel: (() => void) | null = null;

  constructor(private worker: WorkerLike, private env: BridgeEnv = browserEnv()) {
    worker.onmessage = (e) => {
      if (e.data.t === 'state') for (const cb of this.listeners) cb(e.data.state);
    };
    env.onVisibilityChange(() => {
      // Hidden pauses the worker; the stored speed is restored when visible again (no catch-up: ticks are clamped).
      this.worker.postMessage({ t: 'speed', x: env.isHidden() ? 0 : this.speed });
      this.last = env.now();
    });
  }

  start(s: GameState): void {
    this.worker.postMessage({ t: 'init', state: s });
    this.last = this.env.now();
    this.cancel?.();
    this.cancel = this.env.schedule(() => {
      const n = this.env.now();
      const realMs = n - this.last;
      this.last = n;
      this.worker.postMessage({ t: 'tick', realMs });
    });
  }

  send(c: Command): void {
    this.worker.postMessage({ t: 'cmd', cmd: c });
  }

  setSpeed(x: Speed): void {
    this.speed = x;
    if (!this.env.isHidden()) this.worker.postMessage({ t: 'speed', x });
  }

  onState(cb: (s: GameState) => void): void {
    this.listeners.push(cb);
  }

  stop(): void {
    this.cancel?.();
    this.cancel = null;
  }
}
