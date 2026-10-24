import { dateOf } from './clock';
import type { Alloc, GameData, GameState, PulsoItem, RigModel } from './types';

export type Command =
  | { t: 'buy_gpu'; model: string; rigId: string }
  | { t: 'buy_rig'; model: RigModel['id'] }
  | { t: 'allocate'; gpuId: string; to: Alloc }
  | { t: 'start_job'; jobId: string }
  | { t: 'accept_contract'; contractId: string }
  | { t: 'apply_grant'; grantId: string }
  | { t: 'set_price'; usdPerMChars: number }
  | { t: 'reset_breaker' }
  | { t: 'accept_round' }
  | { t: 'decline_round' };

const ALLOCS: readonly Alloc[] = ['train', 'serve', 'rent', 'idle'];

/** Next `${prefix}-N` id: one past the highest existing numeric suffix. */
function nextId(prefix: string, ids: string[]): string {
  let max = 0;
  for (const id of ids) {
    const n = Number(id.slice(prefix.length + 1));
    if (id.startsWith(`${prefix}-`) && Number.isInteger(n) && n > max) max = n;
  }
  return `${prefix}-${max + 1}`;
}

/** Invalid command: same state plus a 'warning' Pulso item (repeats of the same warning bump `count`). */
function warn(s: GameState, code: string, text: string): GameState {
  const id = `warn:${code}`;
  const i = s.pulso.findIndex((p) => p.id === id);
  if (i >= 0) {
    const prev = s.pulso[i] as PulsoItem;
    const rest = s.pulso.filter((_, k) => k !== i);
    return { ...s, pulso: [...rest, { ...prev, hour: s.hour, count: prev.count + 1 }] };
  }
  return { ...s, pulso: [...s.pulso, { id, hour: s.hour, cause: 'warning', text, count: 1 }] };
}

function released(releaseDate: string, s: GameState): boolean {
  // ISO strings compare chronologically; a date-only value sorts before any instant on that day.
  return releaseDate <= dateOf(s);
}

function buyGpu(s: GameState, d: GameData, c: Extract<Command, { t: 'buy_gpu' }>): GameState {
  const model = d.gpus.find((g) => g.id === c.model);
  if (!model) return warn(s, 'unknown_gpu_model', `Modelo de GPU desconocido: ${c.model}.`);
  if (!released(model.releaseDate, s)) return warn(s, 'gpu_not_released', `${model.name} aún no ha salido al mercado.`);
  const rig = s.rigs.find((r) => r.id === c.rigId);
  if (!rig) return warn(s, 'unknown_rig', `Bastidor desconocido: ${c.rigId}.`);
  const rigModel = d.rigs.find((r) => r.id === rig.model);
  if (!rigModel) return warn(s, 'unknown_rig', `Bastidor desconocido: ${c.rigId}.`);
  const used = new Set(s.gpus.filter((g) => g.rigId === rig.id).map((g) => g.slot));
  let slot = 0;
  while (used.has(slot)) slot++;
  if (slot >= rigModel.gpuSlots) return warn(s, 'rig_full', `El bastidor ${rig.id} no tiene ranuras libres.`);
  const price = model.priceUsd.value;
  if (s.cashUsd < price) return warn(s, 'no_cash', `Caja insuficiente para comprar ${model.name}.`);
  const id = nextId('gpu', s.gpus.map((g) => g.id));
  return {
    ...s,
    cashUsd: s.cashUsd - price,
    gpus: [...s.gpus, { id, model: model.id, rigId: rig.id, slot, tempC: d.world.ambientC.value, perf: 1 }],
    allocation: { ...s.allocation, [id]: 'idle' },
  };
}

function buyRig(s: GameState, d: GameData, c: Extract<Command, { t: 'buy_rig' }>): GameState {
  const model = d.rigs.find((r) => r.id === c.model);
  if (!model) return warn(s, 'unknown_rig_model', `Modelo de bastidor desconocido: ${String(c.model)}.`);
  if (!released(model.releaseDate, s)) return warn(s, 'rig_not_released', `${model.name} aún no está disponible.`);
  const price = model.priceUsd.value;
  if (s.cashUsd < price) return warn(s, 'no_cash', `Caja insuficiente para comprar ${model.name}.`);
  const id = nextId('rig', s.rigs.map((r) => r.id));
  return { ...s, cashUsd: s.cashUsd - price, rigs: [...s.rigs, { id, model: model.id }] };
}

export function applyCommand(s: GameState, d: GameData, c: Command): GameState {
  if (s.outcome !== null) return s;
  switch (c.t) {
    case 'buy_gpu':
      return buyGpu(s, d, c);
    case 'buy_rig':
      return buyRig(s, d, c);
    case 'allocate': {
      if (!s.gpus.some((g) => g.id === c.gpuId)) return warn(s, 'unknown_gpu', `GPU desconocida: ${c.gpuId}.`);
      if (!ALLOCS.includes(c.to)) return warn(s, 'bad_allocation', `Asignación inválida: ${String(c.to)}.`);
      return { ...s, allocation: { ...s.allocation, [c.gpuId]: c.to } };
    }
    case 'start_job': {
      const job = s.jobs.find((j) => j.id === c.jobId);
      if (!job) return warn(s, 'unknown_job', `Entrenamiento desconocido: ${c.jobId}.`);
      if (job.status !== 'ready') return warn(s, 'job_not_ready', `El entrenamiento ${job.id} no está listo para empezar.`);
      return { ...s, jobs: s.jobs.map((j) => (j.id === job.id ? { ...j, status: 'running' as const } : j)) };
    }
    case 'set_price': {
      if (!Number.isFinite(c.usdPerMChars) || c.usdPerMChars <= 0) {
        return warn(s, 'bad_price', 'El precio debe ser un número mayor que 0.');
      }
      return { ...s, product: { ...s.product, priceUsdPerMChars: c.usdPerMChars } };
    }
    case 'accept_contract':
      return warn(s, 'unknown_contract', `Contrato desconocido: ${c.contractId}.`);
    case 'apply_grant':
      return warn(s, 'unknown_grant', `Beca desconocida: ${c.grantId}.`);
    case 'reset_breaker':
      return warn(s, 'breaker_not_tripped', 'El diferencial no ha saltado.');
    case 'accept_round':
    case 'decline_round':
      return warn(s, 'no_round', 'No hay ninguna ronda abierta.');
  }
}
