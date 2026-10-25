import type { GameState } from './sim/types';
import { dateOf } from './sim/time';

export const DB_NAME = 'scaling-law';
export const STORE = 'saves';
export const SLOT_KEY = 'slot-1';

const HOURS_PER_WEEK = 168;

// ---------------------------------------------------------------- shape validation (every non-optional GameState key)

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v);
const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isInt = (v: unknown): v is number => Number.isInteger(v);
const isStr = (v: unknown): v is string => typeof v === 'string';
const isBool = (v: unknown): v is boolean => typeof v === 'boolean';
const oneOf = (v: unknown, xs: readonly unknown[]): boolean => xs.includes(v);
const arrayOf = (v: unknown, ok: (x: unknown) => boolean): boolean => Array.isArray(v) && v.every(ok);
const recordOf = (v: unknown, ok: (x: unknown) => boolean): boolean => isObj(v) && Object.values(v).every(ok);

const isRig = (v: unknown): boolean => isObj(v) && isStr(v.id) && oneOf(v.model, ['tower_2017', 'open_frame']);
const isGpu = (v: unknown): boolean =>
  isObj(v) && isStr(v.id) && isStr(v.model) && isStr(v.rigId) && isInt(v.slot) && isNum(v.tempC) && oneOf(v.perf, [0, 0.7, 1]);
const isPower = (v: unknown): boolean => isObj(v) && isNum(v.watts) && isBool(v.breakerTripped) && isNum(v.weekKwh);
const isJob = (v: unknown): boolean =>
  isObj(v) &&
  oneOf(v.id, ['replicate_paper', 'translation_v2']) &&
  isNum(v.workP100h) &&
  isNum(v.doneP100h) &&
  isNum(v.checkpointP100h) &&
  isInt(v.checkpointEveryH) &&
  arrayOf(v.lossCurve, isNum) &&
  oneOf(v.status, ['locked', 'ready', 'running', 'done']);
const isProduct = (v: unknown): boolean =>
  isObj(v) &&
  isNum(v.priceUsdPerMChars) &&
  isNum(v.customers) &&
  isNum(v.demandMCharsH) &&
  isNum(v.servedMCharsH) &&
  isNum(v.latencyMs) &&
  isNum(v.satisfaction) &&
  isNum(v.weekServedMChars) &&
  isBool(v.launched);
const isContract = (v: unknown): boolean =>
  isObj(v) && isStr(v.id) && isNum(v.usd) && isNum(v.weeksTotal) && isNum(v.weeksLeft) && oneOf(v.status, ['offered', 'active', 'done']);
const isGrant = (v: unknown): boolean =>
  isObj(v) && isStr(v.id) && isNum(v.p100eq) && isNum(v.hoursLeft) && isNum(v.weeksLeft) && oneOf(v.status, ['offered', 'active', 'expired']);
const isLedgerWeek = (v: unknown): boolean =>
  isObj(v) && isNum(v.week) && isNum(v.revenueUsd) && isNum(v.costsUsd) && isNum(v.cashEndUsd) && recordOf(v.lines, isNum);
const isFocus = (v: unknown): boolean => isObj(v) && oneOf(v.kind, ['gpu', 'product', 'power']) && (v.id === undefined || isStr(v.id));
const isPulsoItem = (v: unknown): boolean =>
  isObj(v) &&
  isStr(v.id) &&
  isInt(v.hour) &&
  oneOf(v.cause, ['latency', 'quality', 'price', 'outage', 'praise', 'news', 'warning']) &&
  isStr(v.text) &&
  isNum(v.count) &&
  (v.focus === undefined || isFocus(v.focus));
const isRound = (v: unknown): boolean =>
  isObj(v) && oneOf(v.status, ['offered', 'declined']) && isInt(v.offeredHour) && (v.declinedHour === undefined || isInt(v.declinedHour));

/** True when `o` has every non-optional GameState key with its type (and the optional ones, when present). */
function isGameStateShape(o: Obj): boolean {
  return (
    isNum(o.seed) &&
    isNum(o.rng) &&
    isInt(o.hour) &&
    (o.hour as number) >= 0 &&
    isNum(o.cashUsd) &&
    isStr(o.labName) &&
    arrayOf(o.rigs, isRig) &&
    arrayOf(o.gpus, isGpu) &&
    recordOf(o.allocation, (a) => oneOf(a, ['train', 'serve', 'rent', 'idle'])) &&
    isPower(o.power) &&
    arrayOf(o.jobs, isJob) &&
    isProduct(o.product) &&
    arrayOf(o.contracts, isContract) &&
    arrayOf(o.grants, isGrant) &&
    isNum(o.reputation) &&
    arrayOf(o.ledger, isLedgerWeek) &&
    arrayOf(o.pulso, isPulsoItem) &&
    recordOf(o.flags, isBool) &&
    isNum(o.weekRentUsd) &&
    isInt(o.negativeWeeks) &&
    (o.outcome === null || oneOf(o.outcome, ['seed_round', 'bankrupt'])) &&
    (o.round === undefined || isRound(o.round)) &&
    (o.trainedGpuHours === undefined || isNum(o.trainedGpuHours)) &&
    (o.pulsoDay === undefined || (isObj(o.pulsoDay) && isInt(o.pulsoDay.day) && isInt(o.pulsoDay.created)))
  );
}

export type ImportResult = { ok: true; state: GameState } | { ok: false; reason: 'corrupt' | 'version' };
/** 'none' = store readable and slot-1 empty; 'unavailable' = storage itself failed (never overwrite on this). */
export type LoadResult = ImportResult | { ok: false; reason: 'none' | 'unavailable' };

/** True when the game week index changed between two hours (autosave trigger). */
export function shouldAutosave(prevHour: number, nextHour: number): boolean {
  return Math.floor(nextHour / HOURS_PER_WEEK) !== Math.floor(prevHour / HOURS_PER_WEEK);
}

/**
 * Parses and validates serialized state. Never throws.
 * Order: JSON → an object with a numeric version → version (another version's shape may differ, so it is reported
 * as 'version', not 'corrupt') → the full v1 shape.
 */
function parseSave(text: unknown): ImportResult {
  if (typeof text !== 'string') return { ok: false, reason: 'corrupt' };
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    return { ok: false, reason: 'corrupt' };
  }
  if (!isObj(raw) || !isNum(raw.version)) return { ok: false, reason: 'corrupt' };
  if (raw.version !== 1) return { ok: false, reason: 'version' };
  if (!isGameStateShape(raw)) return { ok: false, reason: 'corrupt' };
  return { ok: true, state: raw as unknown as GameState };
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

export interface StartPolicy {
  /** The loaded game to continue, or null to start a new one. */
  resume: GameState | null;
  /** Ruling R16: false only when storage itself failed, so a real save is never overwritten. */
  canSave: boolean;
  /** What to tell the player: 'unavailable' is a persistent warning, the others a dismissible notice. */
  notice: null | 'unavailable' | 'corrupt' | 'version';
}

/** Decides how the game starts from a load result (pure). */
export function startPolicy(r: LoadResult): StartPolicy {
  if (r.ok) return { resume: r.state, canSave: true, notice: null };
  if (r.reason === 'unavailable') return { resume: null, canSave: false, notice: 'unavailable' };
  return { resume: null, canSave: true, notice: r.reason === 'none' ? null : r.reason };
}
