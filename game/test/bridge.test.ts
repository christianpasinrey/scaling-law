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
  h.handle({ t: 'init', state: s });
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
  it('init resets the accumulator', () => {
    const h = hostWith(1);
    h.handle({ t: 'tick', realMs: 200 });
    h.handle({ t: 'init', state: fresh() });
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
      onVisibilityChange: (cb) => { visCb = cb; },
      schedule: (cb) => { loop = cb; return () => { loop = null; }; },
    });
    return {
      w, b,
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
    t.b.send({ t: 'set_price', usdPerMChars: 25 });
    t.frame(10);
    const kinds = t.w.sent.map((m) => m.t);
    expect(kinds.indexOf('cmd')).toBeLessThan(kinds.lastIndexOf('tick'));
    t.w.onmessage?.({ data: { t: 'state', state: fresh() } });
    expect(got).toHaveLength(1);
  });
});
