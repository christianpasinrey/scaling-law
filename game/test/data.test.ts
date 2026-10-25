import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { DataError, loadData } from '../src/sim/data';

const researchFiles = Object.keys(import.meta.glob("../../docs/research/*.md", { query: "?url" })).map((p) => p.replace("../../", ""));
const raw = () => structuredClone({ hardware, world, products, pulso });

describe('loadData', () => {
  const d = loadData(raw());
  const gpu = (id: string) => {
    const g = d.gpus.find((x) => x.id === id);
    if (!g) throw new Error(`missing ${id}`);
    return g;
  };
  const rig = (id: string) => {
    const r = d.rigs.find((x) => x.id === id);
    if (!r) throw new Error(`missing ${id}`);
    return r;
  };

  it('loads the real JSON', () => {
    expect(d.gpus.length).toBeGreaterThanOrEqual(2);
    expect(d.rigs).toHaveLength(2);
  });

  it('every sourced figure has a source', () => {
    for (const g of d.gpus) {
      for (const s of [g.priceUsd, g.watts, g.p100eq]) expect(s.source.length).toBeGreaterThan(0);
    }
    expect(d.world.electricityUsdPerKwh.source.length).toBeGreaterThan(0);
  });

  it('GTX 1080 Ti matches the fixed table', () => {
    const g = gpu('gtx1080ti');
    expect(g.priceUsd.value).toBe(699);
    expect(g.watts.value).toBe(250);
    expect(g.memGb).toBe(11);
    expect(g.p100eq.value).toBe(1.0);
    expect(g.p100eq.approx).toBe(true);
    expect(g.glb).toBe('gpu_gtx1080ti_fe.glb');
  });

  it('Titan V matches the fixed table', () => {
    const g = gpu('titan_v');
    expect(g.releaseDate).toBe('2017-12-07');
    expect(g.priceUsd.value).toBe(2999);
    expect(g.watts.value).toBe(250);
    expect(g.memGb).toBe(12);
    expect(g.p100eq.value).toBe(2.5);
    expect(g.glb).toBe('gpu_titan_v.glb');
  });

  it('rigs match the fixed table', () => {
    const t = rig('tower_2017');
    expect([t.gpuSlots, t.psuWatts, t.baseWatts]).toEqual([2, 1000, 150]);
    const o = rig('open_frame');
    expect(o.releaseDate).toBe('2018-01-01');
    expect(o.priceUsd.value).toBe(350);
    expect([o.gpuSlots, o.psuWatts, o.baseWatts]).toEqual([6, 3200, 150]);
  });

  it('world matches the fixed table', () => {
    const w = d.world;
    expect(w.startIso).toBe('2017-06-12T17:57:00Z');
    expect(w.startCashUsd).toBe(10000);
    expect(w.circuitWatts).toBe(1800);
    expect(w.circuitSafeWatts).toBe(1440);
    expect(w.pcieSlotWatts.value).toBe(75);
    expect(w.electricityUsdPerKwh.value).toBe(0.35); // T15 balance: 0.13 → 0.35
    expect(w.failPerGpuDay.value).toBeCloseTo(4.7e-4 * 3, 10);
    expect(w.throttle.throttleC.value).toBe(84);
    expect(w.throttle.throttleFactor.value).toBe(0.7);
    expect(w.throttle.shutdownC.value).toBe(91);
    expect(w.rentalUsdPerDay.boom.value).toBe(4);
    expect(w.rentalUsdPerDay.after.value).toBe(1);
    expect(w.rentalUsdPerDay.boomEndIso).toBe("2018-03-31");
    expect(w.seedRound.raiseUsd.value).toBe(1_500_000);
    expect(w.seedRound.preMoneyUsd.value).toBe(8_000_000);
    expect(w.seedRound.dilution.value).toBe(0.158);
  });

  it('translation product default price is 20 $/M chars', () => {
    expect(d.products.translation.defaultPriceUsdPerMChars.value).toBe(20);
  });

  it('tolerates extra fields', () => {
    const r = raw() as any;
    r.world.future = 1;
    r.hardware.gpus[0].extra = 'x';
    expect(() => loadData(r)).not.toThrow();
  });

  it('a GPU without source throws DataError naming the path', () => {
    const r = raw() as any;
    delete r.hardware.gpus[0].priceUsd.source;
    expect(() => loadData(r)).toThrow(DataError);
    expect(() => loadData(r)).toThrow(/hardware\.gpus\[0\]\.priceUsd\.source/);
  });

  it('missing field, wrong type and bad rig id throw DataError', () => {
    const a = raw() as any;
    delete a.world.circuitWatts;
    expect(() => loadData(a)).toThrow(/world\.circuitWatts/);
    const b = raw() as any;
    b.hardware.gpus[1].memGb = '12';
    expect(() => loadData(b)).toThrow(/hardware\.gpus\[1\]\.memGb/);
    const c = raw() as any;
    c.hardware.rigs[0].id = 'nope';
    expect(() => loadData(c)).toThrow(DataError);
    expect(() => loadData({ hardware: null, world: {}, products: {}, pulso: {} })).toThrow(DataError);
  });

  it('checkpointEveryH must be exactly 4', () => {
    const a = raw() as any;
    a.products.jobs.checkpointEveryH.value = 6;
    expect(() => loadData(a)).toThrow(/checkpointEveryH.value/);
  });

  it("every docs/research source points to an existing file", () => {
    const found: string[] = [];
    const walk = (v: unknown): void => {
      if (Array.isArray(v)) v.forEach(walk);
      else if (v && typeof v === "object") {
        for (const [k, x] of Object.entries(v)) {
          if (k === "source" && typeof x === "string" && x.startsWith("docs/research/")) found.push(x);
          else walk(x);
        }
      }
    };
    walk({ hardware, world, products, pulso });
    expect(found.length).toBeGreaterThan(0);
    for (const s of found) {
      const file = s.split(/[ ;]/)[0] as string;
      expect(researchFiles, file).toContain(file);
    }
  });
});

describe('data files encoding', () => {
  it('no source string contains mojibake', () => {
    const bad = /Â|Ã|â€/;
    const walk = (v: unknown, path: string): void => {
      if (typeof v === 'string') {
        if (path.endsWith('.source')) expect(v, path).not.toMatch(bad);
      } else if (v && typeof v === 'object') {
        for (const [k, x] of Object.entries(v)) walk(x, `${path}.${k}`);
      }
    };
    walk(raw(), 'data');
  });
});
