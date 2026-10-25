import 'fake-indexeddb/auto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { advance, applyCommand, loadData, newGame } from '../src/sim';
import { DB_NAME, SLOT_KEY, STORE, exportFileName, exportSave, importSave, loadGame, saveGame, shouldAutosave, startPolicy } from '../src/save';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const fresh = () => ({ ...newGame(d, 42, 'Garage Lab'), hour: 200, cashUsd: 8123.45 });

function rawPut(value: unknown): Promise<void> {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open(DB_NAME, 1);
    open.onupgradeneeded = () => open.result.createObjectStore(STORE);
    open.onerror = () => reject(open.error);
    open.onsuccess = () => {
      const db = open.result;
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(value, SLOT_KEY);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    };
  });
}

function wipe(): Promise<void> {
  return new Promise((resolve) => {
    const r = indexedDB.deleteDatabase(DB_NAME);
    r.onsuccess = r.onerror = r.onblocked = () => resolve();
  });
}

beforeEach(wipe);

describe('save/load', () => {
  it('returns none when nothing is stored', async () => {
    expect(await loadGame()).toEqual({ ok: false, reason: 'none' });
  });

  it('save then load returns an identical state', async () => {
    const s = fresh();
    await saveGame(s);
    const r = await loadGame();
    expect(r).toEqual({ ok: true, state: s });
  });

  it('truncated JSON is corrupt', async () => {
    const json = JSON.stringify(fresh());
    await rawPut(json.slice(0, json.length - 20));
    expect(await loadGame()).toEqual({ ok: false, reason: 'corrupt' });
  });

  it('missing required fields is corrupt', async () => {
    const { ledger: _l, ...rest } = fresh();
    await rawPut(JSON.stringify(rest));
    expect(await loadGame()).toEqual({ ok: false, reason: 'corrupt' });
    await rawPut('null');
    expect(await loadGame()).toEqual({ ok: false, reason: 'corrupt' });
    await rawPut(42);
    expect(await loadGame()).toEqual({ ok: false, reason: 'corrupt' });
  });

  it('version 99 is reported as version', async () => {
    await rawPut(JSON.stringify({ ...fresh(), version: 99 }));
    expect(await loadGame()).toEqual({ ok: false, reason: 'version' });
  });
});

describe('storage failure and scalar validation', () => {
  afterEach(() => vi.restoreAllMocks());

  it('reports unavailable when indexedDB.open fails', async () => {
    vi.spyOn(indexedDB, 'open').mockImplementation(() => {
      const req = {} as IDBOpenDBRequest;
      setTimeout(() => req.onerror?.(new Event('error')), 0);
      return req;
    });
    expect(await loadGame()).toEqual({ ok: false, reason: 'unavailable' });
  });

  it('wrong scalar or container types are corrupt', async () => {
    const bad: Record<string, unknown>[] = [
      { hour: '5' }, { seed: null }, { rng: Number.NaN }, { cashUsd: 'x' }, { version: '1' },
      { gpus: {} }, { rigs: 'x' }, { jobs: null }, { pulso: 1 }, { ledger: {} }, { product: [] }, { product: null },
    ];
    for (const patch of bad) {
      await rawPut(JSON.stringify({ ...fresh(), ...patch }));
      expect(await loadGame(), JSON.stringify(patch)).toEqual({ ok: false, reason: 'corrupt' });
    }
  });
});

describe('full shape validation', () => {
  const without = (k: string): Record<string, unknown> => {
    const o: Record<string, unknown> = { ...fresh() };
    delete o[k];
    return o;
  };
  const imp = (o: unknown) => importSave(new Blob([JSON.stringify(o)]));

  it('missing power is rejected', async () => {
    expect(await imp(without('power'))).toEqual({ ok: false, reason: 'corrupt' });
  });
  it('a non-integer hour is rejected', async () => {
    expect(await imp({ ...fresh(), hour: 12.5 })).toEqual({ ok: false, reason: 'corrupt' });
  });
  it('missing flags is rejected', async () => {
    expect(await imp(without('flags'))).toEqual({ ok: false, reason: 'corrupt' });
  });
  it('every non-optional key is required', async () => {
    const keys = ['seed', 'rng', 'hour', 'cashUsd', 'labName', 'rigs', 'gpus', 'allocation', 'power', 'jobs', 'product',
      'contracts', 'grants', 'reputation', 'ledger', 'pulso', 'flags', 'weekRentUsd', 'negativeWeeks', 'outcome'];
    for (const k of keys) expect(await imp(without(k)), k).toEqual({ ok: false, reason: 'corrupt' });
  });
  it('rejects wrong field types and element shapes', async () => {
    const s = fresh();
    const bad: Record<string, unknown>[] = [
      { labName: 7 },
      { allocation: [] },
      { allocation: { 'gpu-1': 'mine' } },
      { flags: { model_v2: 'yes' } },
      { power: { ...s.power, watts: 'x' } },
      { power: { ...s.power, breakerTripped: 1 } },
      { product: { ...s.product, launched: 'no' } },
      { product: { ...s.product, customers: null } },
      { gpus: [{ ...s.gpus[0]!, perf: 0.5 }] },
      { gpus: [null] },
      { rigs: [{ id: 'rig-1', model: 'shed' }] },
      { jobs: [{ ...s.jobs[0]!, lossCurve: ['a'] }] },
      { contracts: [{ id: 'c', usd: 1 }] },
      { pulso: [{ id: 'p', hour: 1.5, cause: 'news', text: 't', count: 1 }] },
      { reputation: '5' },
      { negativeWeeks: 1.5 },
      { weekRentUsd: null },
      { outcome: 'won' },
      { round: { status: 'offered' } },
    ];
    for (const patch of bad) expect(await imp({ ...s, ...patch }), JSON.stringify(patch)).toEqual({ ok: false, reason: 'corrupt' });
  });
  it('accepts optional fields when present and well-formed', async () => {
    const s = { ...fresh(), round: { status: 'offered' as const, offeredHour: 100 }, trainedGpuHours: 4, pulsoDay: { day: 3, created: 1 } };
    expect(await imp(s)).toEqual({ ok: true, state: s });
  });
  it('a played game (ledger, Pulso, jobs, allocation) round-trips', async () => {
    let s = applyCommand(newGame(d, 7, 'Lab'), d, { t: 'start_job', jobId: 'replicate_paper' });
    s = applyCommand(s, d, { t: 'allocate', gpuId: 'gpu-1', to: 'train' });
    s = advance(s, d, 3 * 168 + 5);
    expect(s.ledger.length).toBeGreaterThan(0);
    expect(s.jobs.find((j) => j.id === 'replicate_paper')!.lossCurve.length).toBeGreaterThan(0);
    expect(await imp(s)).toEqual({ ok: true, state: s });
  });
  it('another version is reported as version even if its shape differs', async () => {
    expect(await imp({ version: 2, somethingNew: true })).toEqual({ ok: false, reason: 'version' });
  });
});

describe('export/import', () => {
  it('imports an exported blob and round-trips', async () => {
    const s = fresh();
    const blob = exportSave(s);
    expect(blob.type).toBe('application/json');
    expect(await importSave(blob)).toEqual({ ok: true, state: s });
  });

  it('import validates like load', async () => {
    const json = JSON.stringify(fresh());
    expect(await importSave(new Blob([json.slice(0, 50)]))).toEqual({ ok: false, reason: 'corrupt' });
    expect(await importSave(new Blob([JSON.stringify({ ...fresh(), version: 2 })]))).toEqual({
      ok: false,
      reason: 'version',
    });
  });

  it('builds a file name from lab name and game date', () => {
    const s = { ...fresh(), labName: 'Ñandú Lab: Åbo!', hour: 0 };
    expect(exportFileName(s)).toBe('scaling-law-nandu-lab-abo-2017-06-12.json');
    expect(exportFileName({ ...s, labName: '***' })).toBe('scaling-law-lab-2017-06-12.json');
  });
});

describe('shouldAutosave', () => {
  it('fires only when the week index changes', () => {
    expect(shouldAutosave(0, 167)).toBe(false);
    expect(shouldAutosave(167, 168)).toBe(true);
    expect(shouldAutosave(168, 335)).toBe(false);
    expect(shouldAutosave(100, 400)).toBe(true);
    expect(shouldAutosave(168, 168)).toBe(false);
  });
});

describe('startPolicy (R16)', () => {
  const s = newGame(loadData(structuredClone({ hardware, world, products, pulso })), 1, 'Lab');
  it('continues a loaded game and may save it', () => {
    expect(startPolicy({ ok: true, state: s })).toEqual({ resume: s, canSave: true, notice: null });
  });
  it('a missing save starts a new game that may save, silently', () => {
    expect(startPolicy({ ok: false, reason: 'none' })).toEqual({ resume: null, canSave: true, notice: null });
  });
  it('a corrupt or other-version save starts a new game that replaces it, with a notice', () => {
    expect(startPolicy({ ok: false, reason: 'corrupt' })).toEqual({ resume: null, canSave: true, notice: 'corrupt' });
    expect(startPolicy({ ok: false, reason: 'version' })).toEqual({ resume: null, canSave: true, notice: 'version' });
  });
  it('unavailable storage starts a new game that never saves, with a persistent warning', () => {
    expect(startPolicy({ ok: false, reason: 'unavailable' })).toEqual({ resume: null, canSave: false, notice: 'unavailable' });
  });
});
