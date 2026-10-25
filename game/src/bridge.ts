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
  /** Subscribes to visibility changes; returns the unsubscribe function. */
  onVisibilityChange(cb: () => void): () => void;
  /** Runs cb every frame; returns a cancel function. */
  schedule(cb: () => void): () => void;
}

export function browserEnv(): BridgeEnv {
  return {
    now: () => performance.now(),
    isHidden: () => document.visibilityState === 'hidden',
    onVisibilityChange: (cb) => {
      document.addEventListener('visibilitychange', cb);
      return () => document.removeEventListener('visibilitychange', cb);
    },
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
  private epoch = 0;
  private readonly offVisibility: () => void;

  constructor(private worker: WorkerLike, private env: BridgeEnv = browserEnv()) {
    worker.onmessage = (e) => {
      // R23: a state from before the last init belongs to the replaced game (import / new game): drop it.
      if (e.data.t !== 'state' || e.data.epoch < this.epoch) return;
      for (const cb of this.listeners) cb(e.data.state);
    };
    this.offVisibility = env.onVisibilityChange(() => {
      // Hidden pauses the worker; the stored speed is restored when visible again (no catch-up: ticks are clamped).
      this.worker.postMessage({ t: 'speed', x: env.isHidden() ? 0 : this.speed });
      this.last = env.now();
    });
  }

  /** Speed the worker is actually running at from the main thread's view (the breaker cap is the worker's job). */
  private effectiveSpeed(): Speed {
    return this.env.isHidden() ? 0 : this.speed;
  }

  start(s: GameState): void {
    this.epoch++;
    this.worker.postMessage({ t: 'init', state: s, epoch: this.epoch });
    this.last = this.env.now();
    this.cancel?.();
    this.cancel = this.env.schedule(() => {
      const n = this.env.now();
      const realMs = n - this.last;
      this.last = n;
      // Paused or hidden: nothing to advance, so nothing to post; `last` still moves so a resume never carries the pause.
      if (this.effectiveSpeed() === 0) return;
      this.worker.postMessage({ t: 'tick', realMs });
    });
  }

  send(c: Command): void {
    this.worker.postMessage({ t: 'cmd', cmd: c });
  }

  setSpeed(x: Speed): void {
    if (this.speed === 0 && x !== 0) this.last = this.env.now();
    this.speed = x;
    if (!this.env.isHidden()) this.worker.postMessage({ t: 'speed', x });
  }

  getSpeed(): Speed {
    return this.speed;
  }

  onState(cb: (s: GameState) => void): void {
    this.listeners.push(cb);
  }

  /** Stops ticking and detaches from the worker and the page (listeners are dropped). */
  stop(): void {
    this.cancel?.();
    this.cancel = null;
    this.offVisibility();
    this.worker.onmessage = null;
    this.listeners = [];
  }
}
