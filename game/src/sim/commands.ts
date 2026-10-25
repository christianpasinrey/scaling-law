import { dateOf } from './time';
import { nextId } from './ids';
import { pushPulso } from './pulsoLog';
import type { Alloc, GameData, GameState, RigModel } from './types';

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

/** Invalid command: same state plus a 'warning' Pulso item (aggregated by the Pulso log, exempt from the daily cap). */
function warn(s: GameState, d: GameData, code: string, text: string): GameState {
  return pushPulso(s, d, { id: `warn:${code}`, hour: s.hour, cause: 'warning', text, count: 1 });
}

function released(releaseDate: string, s: GameState): boolean {
  // ISO strings compare chronologically; a date-only value sorts before any instant on that day.
  return releaseDate <= dateOf(s);
}

function buyGpu(s: GameState, d: GameData, c: Extract<Command, { t: 'buy_gpu' }>): GameState {
  const model = d.gpus.find((g) => g.id === c.model);
  if (!model) return warn(s, d, 'unknown_gpu_model', `Modelo de GPU desconocido: ${c.model}.`);
  if (!released(model.releaseDate, s)) return warn(s, d, 'gpu_not_released', `${model.name} aún no ha salido al mercado.`);
  const rig = s.rigs.find((r) => r.id === c.rigId);
  if (!rig) return warn(s, d, 'unknown_rig', `Bastidor desconocido: ${c.rigId}.`);
  const rigModel = d.rigs.find((r) => r.id === rig.model);
  if (!rigModel) return warn(s, d, 'unknown_rig', `Bastidor desconocido: ${c.rigId}.`);
  const used = new Set(s.gpus.filter((g) => g.rigId === rig.id).map((g) => g.slot));
  let slot = 0;
  while (used.has(slot)) slot++;
  if (slot >= rigModel.gpuSlots) return warn(s, d, 'rig_full', `El bastidor ${rig.id} no tiene ranuras libres.`);
  const price = model.priceUsd.value;
  if (s.cashUsd < price) return warn(s, d, 'no_cash', `Caja insuficiente para comprar ${model.name}.`);
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
  if (!model) return warn(s, d, 'unknown_rig_model', `Modelo de bastidor desconocido: ${String(c.model)}.`);
  if (!released(model.releaseDate, s)) return warn(s, d, 'rig_not_released', `${model.name} aún no está disponible.`);
  const price = model.priceUsd.value;
  if (s.cashUsd < price) return warn(s, d, 'no_cash', `Caja insuficiente para comprar ${model.name}.`);
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
      if (!s.gpus.some((g) => g.id === c.gpuId)) return warn(s, d, 'unknown_gpu', `GPU desconocida: ${c.gpuId}.`);
      if (!ALLOCS.includes(c.to)) return warn(s, d, 'bad_allocation', `Asignación inválida: ${String(c.to)}.`);
      return { ...s, allocation: { ...s.allocation, [c.gpuId]: c.to } };
    }
    case 'start_job': {
      const job = s.jobs.find((j) => j.id === c.jobId);
      if (!job) return warn(s, d, 'unknown_job', `Entrenamiento desconocido: ${c.jobId}.`);
      if (job.status !== 'ready') return warn(s, d, 'job_not_ready', `El entrenamiento ${job.id} no está listo para empezar.`);
      return { ...s, jobs: s.jobs.map((j) => (j.id === job.id ? { ...j, status: 'running' as const } : j)) };
    }
    case 'set_price': {
      const tr = d.products.translation;
      const lo = tr.minPriceUsdPerMChars.value;
      const hi = tr.maxPriceUsdPerMChars.value;
      if (!Number.isFinite(c.usdPerMChars) || c.usdPerMChars < lo || c.usdPerMChars > hi) {
        return warn(s, d, 'bad_price', `El precio debe estar entre ${lo} y ${hi} $ por millón de caracteres.`);
      }
      return { ...s, product: { ...s.product, priceUsdPerMChars: c.usdPerMChars } };
    }
    case 'accept_contract': {
      const k = s.contracts.find((x) => x.id === c.contractId);
      if (!k) return warn(s, d, 'unknown_contract', `Contrato desconocido: ${c.contractId}.`);
      if (k.status !== 'offered') return warn(s, d, 'contract_not_offered', `El contrato ${k.id} ya no está disponible.`);
      return { ...s, contracts: s.contracts.map((x) => (x.id === k.id ? { ...x, status: 'active' as const } : x)) };
    }
    case 'apply_grant': {
      const g = s.grants.find((x) => x.id === c.grantId);
      if (!g) return warn(s, d, 'unknown_grant', `Beca desconocida: ${c.grantId}.`);
      if (g.status !== 'offered') return warn(s, d, 'grant_not_offered', `La subvención ${g.id} ya no está disponible.`);
      return { ...s, grants: s.grants.map((x) => (x.id === g.id ? { ...x, status: 'active' as const } : x)) };
    }
    case 'reset_breaker':
      // Clears the flag only: if the draw is still over the limit, the next stepPower trips it again.
      if (s.power.breakerTripped) return { ...s, power: { ...s.power, breakerTripped: false } };
      return warn(s, d, 'breaker_not_tripped', 'Los plomos no han saltado.');
    case 'accept_round': {
      if (s.round?.status !== 'offered') return warn(s, d, 'no_round', 'No hay ninguna ronda abierta.');
      const closed: GameState = { ...s, cashUsd: s.cashUsd + d.world.seedRound.raiseUsd.value, outcome: 'seed_round' };
      return pushPulso(closed, d, { id: 'news:seed_round', hour: s.hour, cause: 'news', text: d.pulso.news.seedRoundClosed, count: 1 });
    }
    case 'decline_round':
      if (s.round?.status !== 'offered') return warn(s, d, 'no_round', 'No hay ninguna ronda abierta.');
      return { ...s, round: { ...s.round, status: 'declined', declinedHour: s.hour } };
  }
}
