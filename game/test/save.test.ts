import 'fake-indexeddb/auto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData, newGame } from '../src/sim';
import { DB_NAME, SLOT_KEY, STORE, exportFileName, exportSave, importSave, loadGame, saveGame, shouldAutosave } from '../src/save';

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
