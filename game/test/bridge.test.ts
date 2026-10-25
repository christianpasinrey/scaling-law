import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData, newGame } from '../src/sim';
import type { GameState } from '../src/sim';
import type { FromWorker, ToWorker } from '../src/protocol';
import { createSimHost } from '../src/host';
import { SimBridge } from '../src/bridge';
import type { WorkerLike } from '../src/bridge';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const msPerHour = d.world.clock.weekRealMs.value / 168;
const fresh = () => newGame(d, 42, 'Garage Lab');

function hostWith(speed: 0 | 1 | 2 | 4 = 1, s: GameState = fresh()) {
  const h = createSimHost(d);
  h.handle({ t: 'init', state: s, epoch: 1 });
  h.handle({ t: 'speed', x: speed });
  return h;
}
const hourOf = (m: FromWorker | null) => (m ? m.state.hour : -1);

describe('sim host clock', () => {
  it('clamps a 60 s tick to 1000 ms', () => {
    const a = hostWith(1);
    const b = hostWith(1);
    const big = a.handle({ t: 'tick', realMs: 60000 });
    const ok = b.handle({ t: 'tick', realMs: 1000 });
    expect(hourOf(big)).toBe(Math.floor(1000 / msPerHour));
    expect(big).toEqual(ok);
  });
  it('speed 0 does not advance and posts nothing', () => {
    const h = hostWith(0);
    expect(h.handle({ t: 'tick', realMs: 1000 })).toBeNull();
  });
  it('carries remainders across ticks', () => {
    const h = hostWith(1);
    let last = 0;
    for (let i = 0; i < 10; i++) {
      const m = h.handle({ t: 'tick', realMs: 100 });
      if (m) last = m.state.hour;
    }
    expect(last).toBe(Math.floor(1000 / msPerHour));
  });
  it('x4 advances four times as fast', () => {
    const m = hostWith(4).handle({ t: 'tick', realMs: 1000 });
    expect(hourOf(m)).toBe(Math.floor(4000 / msPerHour));
  });
  it('a tripped breaker caps x4 to x1', () => {
    const s = fresh();
    const tripped: GameState = { ...s, power: { ...s.power, breakerTripped: true } };
    const m = hostWith(4, tripped).handle({ t: 'tick', realMs: 1000 });
    expect(hourOf(m)).toBe(Math.floor(1000 / msPerHour));
  });
  it('applies a command and posts state before the next tick', () => {
    const h = hostWith(0);
    const m = h.handle({ t: 'cmd', cmd: { t: 'set_price', usdPerMChars: 25 } });
    expect(m).not.toBeNull();
    expect(m?.state.product.priceUsdPerMChars).toBe(25);
  });
  it('a speed change between ticks keeps the fractional hour already accumulated', () => {
    const h = hostWith(1);
    // 0.6 h at x1, then 0.6 h more at x2 (0.3 h of real time): 1.2 h ⇒ exactly one hour advanced.
    expect(h.handle({ t: 'tick', realMs: 0.6 * msPerHour })).toBeNull();
    h.handle({ t: 'speed', x: 2 });
    expect(hourOf(h.handle({ t: 'tick', realMs: 0.3 * msPerHour }))).toBe(1);
    // The 0.2 h remainder is still there: 0.8 h more at x2 (0.4 h real) reaches the second hour.
    expect(hourOf(h.handle({ t: 'tick', realMs: 0.4 * msPerHour }))).toBe(2);
  });
  it('replies to init with the state and tags later states with that epoch (R23)', () => {
    const h = createSimHost(d);
    const s = fresh();
    expect(h.handle({ t: 'init', state: s, epoch: 7 })).toEqual({ t: 'state', state: s, epoch: 7 });
    h.handle({ t: 'speed', x: 1 });
    expect(h.handle({ t: 'tick', realMs: 1000 })?.epoch).toBe(7);
    expect(h.handle({ t: 'cmd', cmd: { t: 'set_price', usdPerMChars: 25 } })?.epoch).toBe(7);
  });
  it('init resets the accumulator', () => {
    const h = hostWith(1);
    h.handle({ t: 'tick', realMs: 200 });
    h.handle({ t: 'init', state: fresh(), epoch: 2 });
    const m = h.handle({ t: 'tick', realMs: 200 });
    expect(m).toBeNull();
  });
});

class FakeWorker implements WorkerLike {
  sent: ToWorker[] = [];
  onmessage: ((e: { data: FromWorker }) => void) | null = null;
  postMessage(m: ToWorker) { this.sent.push(m); }
}

describe('SimBridge', () => {
  function setup() {
    const w = new FakeWorker();
    let now = 0;
    let hidden = false;
    let visCb: (() => void) | null = null;
    let loop: (() => void) | null = null;
    const b = new SimBridge(w, {
      now: () => now,
      isHidden: () => hidden,
      onVisibilityChange: (cb) => { visCb = cb; return () => { visCb = null; }; },
      schedule: (cb) => { loop = cb; return () => { loop = null; }; },
    });
    return {
      w, b,
      hasVisibilityListener: () => visCb !== null,
      hasLoop: () => loop !== null,
      frame: (ms: number) => { now += ms; loop?.(); },
      hide: (v: boolean) => { hidden = v; visCb?.(); },
    };
  }
  it('sends init, and ticks with real elapsed ms', () => {
    const t = setup();
    t.b.start(fresh());
    t.b.setSpeed(1);
    t.frame(16);
    expect(t.w.sent[0]?.t).toBe('init');
    expect(t.w.sent.at(-1)).toEqual({ t: 'tick', realMs: 16 });
  });
  it('hidden sets speed 0 and visible restores the previous speed', () => {
    const t = setup();
    t.b.start(fresh());
    t.b.setSpeed(2);
    t.hide(true);
    expect(t.w.sent.at(-1)).toEqual({ t: 'speed', x: 0 });
    t.hide(false);
    expect(t.w.sent.at(-1)).toEqual({ t: 'speed', x: 2 });
  });
  it('sends commands in order and forwards state to listeners', () => {
    const t = setup();
    const got: GameState[] = [];
    t.b.onState((s) => got.push(s));
    t.b.start(fresh());
    t.b.setSpeed(1);
    t.b.send({ t: 'set_price', usdPerMChars: 25 });
    t.frame(10);
    const kinds = t.w.sent.map((m) => m.t);
    expect(kinds.indexOf('cmd')).toBeLessThan(kinds.lastIndexOf('tick'));
    t.w.onmessage?.({ data: { t: 'state', state: fresh(), epoch: 1 } });
    expect(got).toHaveLength(1);
  });
  it('posts no ticks while paused, and the first tick after resuming does not include the pause', () => {
    const t = setup();
    t.b.start(fresh());
    t.frame(16);
    t.frame(500);
    expect(t.w.sent.filter((m) => m.t === 'tick')).toHaveLength(0);
    t.b.setSpeed(1);
    t.frame(20);
    expect(t.w.sent.at(-1)).toEqual({ t: 'tick', realMs: 20 });
  });
  it('posts no ticks while hidden', () => {
    const t = setup();
    t.b.start(fresh());
    t.b.setSpeed(1);
    t.hide(true);
    const before = t.w.sent.length;
    t.frame(16);
    t.frame(16);
    expect(t.w.sent.slice(before).some((m) => m.t === 'tick')).toBe(false);
    t.hide(false);
    t.frame(16);
    expect(t.w.sent.at(-1)).toEqual({ t: 'tick', realMs: 16 });
  });
  it('setSpeed while hidden is remembered and sent when visible again', () => {
    const t = setup();
    t.b.start(fresh());
    t.b.setSpeed(1);
    t.hide(true);
    const before = t.w.sent.length;
    t.b.setSpeed(4);
    expect(t.w.sent.slice(before)).toEqual([]);
    t.hide(false);
    expect(t.w.sent.at(-1)).toEqual({ t: 'speed', x: 4 });
  });
  it('stop() cancels the loop, unsubscribes visibility and detaches the worker', () => {
    const t = setup();
    const got: GameState[] = [];
    t.b.onState((s) => got.push(s));
    t.b.start(fresh());
    t.b.setSpeed(1);
    t.b.stop();
    expect(t.hasLoop()).toBe(false);
    expect(t.hasVisibilityListener()).toBe(false);
    expect(t.w.onmessage).toBeNull();
    const before = t.w.sent.length;
    t.frame(16);
    t.hide(true);
    expect(t.w.sent.length).toBe(before);
    expect(got).toHaveLength(0);
  });
  it('drops a stale state posted by the previous game before the new init reply (R23)', () => {
    const t = setup();
    const got: GameState[] = [];
    t.b.onState((s) => got.push(s));
    const a = fresh();
    const b: GameState = { ...newGame(d, 99, 'Imported'), hour: 500 };
    t.b.start(a);
    const epochA = (t.w.sent[0] as Extract<ToWorker, { t: 'init' }>).epoch;
    t.b.start(b);
    const initB = t.w.sent.filter((m) => m.t === 'init')[1] as Extract<ToWorker, { t: 'init' }>;
    expect(initB.epoch).toBeGreaterThan(epochA);
    // The worker had already posted a tick of game A when B's init went out.
    t.w.onmessage?.({ data: { t: 'state', state: { ...a, hour: 3 }, epoch: epochA } });
    expect(got).toEqual([]);
    t.w.onmessage?.({ data: { t: 'state', state: b, epoch: initB.epoch } });
    expect(got).toEqual([b]);
  });
  it('an autosave listener never sees (so never persists) a stale state (R23)', () => {
    const t = setup();
    const saved: GameState[] = [];
    let prev = 0;
    t.b.onState((s) => {
      // Same rule main.ts uses: save when the game week changes.
      if (Math.floor(s.hour / 168) !== Math.floor(prev / 168)) saved.push(s);
      prev = s.hour;
    });
    const old: GameState = { ...fresh(), labName: 'Old', hour: 167 };
    t.b.start(old);
    const e1 = (t.w.sent[0] as Extract<ToWorker, { t: 'init' }>).epoch;
    t.b.start({ ...fresh(), labName: 'New' });
    t.w.onmessage?.({ data: { t: 'state', state: { ...old, hour: 168 }, epoch: e1 } }); // would cross a week
    expect(saved).toEqual([]);
  });
});
