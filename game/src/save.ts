import type { GameState } from './sim/types';
import { dateOf } from './sim/time';

export const DB_NAME = 'scaling-law';
export const STORE = 'saves';
export const SLOT_KEY = 'slot-1';

const HOURS_PER_WEEK = 168;
const REQUIRED: readonly string[] = [
  'version', 'seed', 'rng', 'hour', 'cashUsd', 'gpus', 'rigs', 'jobs', 'product', 'pulso', 'ledger',
];

export type ImportResult = { ok: true; state: GameState } | { ok: false; reason: 'corrupt' | 'version' };
/** 'none' = store readable and slot-1 empty; 'unavailable' = storage itself failed (never overwrite on this). */
export type LoadResult = ImportResult | { ok: false; reason: 'none' | 'unavailable' };

/** True when the game week index changed between two hours (autosave trigger). */
export function shouldAutosave(prevHour: number, nextHour: number): boolean {
  return Math.floor(nextHour / HOURS_PER_WEEK) !== Math.floor(prevHour / HOURS_PER_WEEK);
}

/** Parses and validates serialized state. Never throws. */
function parseSave(text: unknown): ImportResult {
  if (typeof text !== 'string') return { ok: false, reason: 'corrupt' };
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    return { ok: false, reason: 'corrupt' };
  }
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) return { ok: false, reason: 'corrupt' };
  const o = raw as Record<string, unknown>;
  if (REQUIRED.some((k) => !(k in o))) return { ok: false, reason: 'corrupt' };
  const nums = ['version', 'seed', 'rng', 'hour', 'cashUsd'];
  const arrays = ['gpus', 'rigs', 'jobs', 'pulso', 'ledger'];
  if (nums.some((k) => typeof o[k] !== 'number' || !Number.isFinite(o[k]))) return { ok: false, reason: 'corrupt' };
  if (arrays.some((k) => !Array.isArray(o[k]))) return { ok: false, reason: 'corrupt' };
  if (typeof o.product !== 'object' || o.product === null || Array.isArray(o.product)) return { ok: false, reason: 'corrupt' };
  if (o.version !== 1) return { ok: false, reason: 'version' };
  return { ok: true, state: raw as GameState };
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
    req.onblocked = () => reject(new Error('indexedDB open blocked'));
  });
}

/** Persists the state as a JSON string in slot-1. Rejects on storage failure. */
export async function saveGame(s: GameState): Promise<void> {
  const json = JSON.stringify(s);
  const db = await openDb();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(json, SLOT_KEY);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally {
    db.close();
  }
}

/** Loads slot-1. Never throws: storage failures are reported as 'unavailable'. */
export async function loadGame(): Promise<LoadResult> {
  let stored: unknown;
  try {
    const db = await openDb();
    try {
      stored = await new Promise<unknown>((resolve, reject) => {
        const req = db.transaction(STORE, 'readonly').objectStore(STORE).get(SLOT_KEY);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
    } finally {
      db.close();
    }
  } catch {
    return { ok: false, reason: 'unavailable' };
  }
  if (stored === undefined) return { ok: false, reason: 'none' };
  return parseSave(stored);
}

export function exportSave(s: GameState): Blob {
  return new Blob([JSON.stringify(s)], { type: 'application/json' });
}

/** Suggested file name: scaling-law-<lab-slug>-<YYYY-MM-DD>.json (game date). */
export function exportFileName(s: GameState): string {
  const slug =
    s.labName
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'lab';
  return `scaling-law-${slug}-${dateOf(s).slice(0, 10)}.json`;
}

/** Reads an exported file and validates it like loadGame. Never throws. */
export async function importSave(file: File | Blob): Promise<ImportResult> {
  try {
    return parseSave(await file.text());
  } catch {
    return { ok: false, reason: 'corrupt' };
  }
}
