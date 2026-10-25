import type { PulsoData, PulsoTemplateCause, EconomyData, GameData, TrainingData, GpuModel, ProductsData, RigModel, Sourced, WorldData } from './types';

export class DataError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DataError';
  }
}

type Obj = Record<string, unknown>;

function obj(v: unknown, path: string): Obj {
  if (typeof v !== 'object' || v === null || Array.isArray(v)) throw new DataError(`${path}: expected object`);
  return v as Obj;
}
function str(v: unknown, path: string): string {
  if (typeof v !== 'string' || v.length === 0) throw new DataError(`${path}: expected non-empty string`);
  return v;
}
function num(v: unknown, path: string): number {
  if (typeof v !== 'number' || !Number.isFinite(v)) throw new DataError(`${path}: expected finite number`);
  return v;
}
function iso(v: unknown, path: string): string {
  const s = str(v, path);
  if (!/^\d{4}-\d{2}-\d{2}/.test(s)) throw new DataError(`${path}: expected ISO date`);
  return s;
}
function exact<T extends string | number>(v: unknown, expected: T, path: string): T {
  if (v !== expected) throw new DataError(`${path}: expected ${JSON.stringify(expected)}`);
  return expected;
}
function sourced(v: unknown, path: string): Sourced<number> {
  const o = obj(v, path);
  const approx = o.approx;
  if (typeof approx !== 'boolean') throw new DataError(`${path}.approx: expected boolean`);
  return { value: num(o.value, `${path}.value`), source: str(o.source, `${path}.source`), approx };
}
function arr(v: unknown, path: string): unknown[] {
  if (!Array.isArray(v)) throw new DataError(`${path}: expected array`);
  return v;
}

function gpu(v: unknown, path: string): GpuModel {
  const o = obj(v, path);
  return {
    id: str(o.id, `${path}.id`),
    name: str(o.name, `${path}.name`),
    shortName: str(o.shortName, `${path}.shortName`),
    releaseDate: iso(o.releaseDate, `${path}.releaseDate`),
    priceUsd: sourced(o.priceUsd, `${path}.priceUsd`),
    watts: sourced(o.watts, `${path}.watts`),
    memGb: num(o.memGb, `${path}.memGb`),
    p100eq: sourced(o.p100eq, `${path}.p100eq`),
    glb: str(o.glb, `${path}.glb`),
    learnId: str(o.learnId, `${path}.learnId`),
  };
}

function rig(v: unknown, path: string): RigModel {
  const o = obj(v, path);
  const id = o.id;
  if (id !== 'tower_2017' && id !== 'open_frame') {
    throw new DataError(`${path}.id: expected "tower_2017" or "open_frame"`);
  }
  return {
    id,
    name: str(o.name, `${path}.name`),
    releaseDate: iso(o.releaseDate, `${path}.releaseDate`),
    priceUsd: sourced(o.priceUsd, `${path}.priceUsd`),
    gpuSlots: num(o.gpuSlots, `${path}.gpuSlots`),
    psuWatts: num(o.psuWatts, `${path}.psuWatts`),
    baseWatts: num(o.baseWatts, `${path}.baseWatts`),
    glb: str(o.glb, `${path}.glb`),
  };
}

function world(v: unknown, path: string): WorldData {
  const o = obj(v, path);
  const th = obj(o.throttle, `${path}.throttle`);
  const th2 = obj(o.thermal, `${path}.thermal`);
  const rent = obj(o.rentalUsdPerDay, `${path}.rentalUsdPerDay`);
  const seed = obj(o.seedRound, `${path}.seedRound`);
  const prog = obj(o.progression, `${path}.progression`);
  return {
    startIso: exact(o.startIso, '2017-06-12T17:57:00Z', `${path}.startIso`),
    startCashUsd: exact(o.startCashUsd, 10000, `${path}.startCashUsd`),
    circuitWatts: exact(o.circuitWatts, 1800, `${path}.circuitWatts`),
    circuitSafeWatts: exact(o.circuitSafeWatts, 1440, `${path}.circuitSafeWatts`),
    ambientC: sourced(o.ambientC, `${path}.ambientC`),
    electricityUsdPerKwh: sourced(o.electricityUsdPerKwh, `${path}.electricityUsdPerKwh`),
    failPerGpuDay: sourced(o.failPerGpuDay, `${path}.failPerGpuDay`),
    thermal: {
      baseC: sourced(th2.baseC, `${path}.thermal.baseC`),
      perLoadC: sourced(th2.perLoadC, `${path}.thermal.perLoadC`),
      neighbourTowerC: sourced(th2.neighbourTowerC, `${path}.thermal.neighbourTowerC`),
      neighbourOpenFrameC: sourced(th2.neighbourOpenFrameC, `${path}.thermal.neighbourOpenFrameC`),
      smoothing: sourced(th2.smoothing, `${path}.thermal.smoothing`),
      recoverBelowC: sourced(th2.recoverBelowC, `${path}.thermal.recoverBelowC`),
    },
    throttle: {
      throttleC: sourced(th.throttleC, `${path}.throttle.throttleC`),
      throttleFactor: sourced(th.throttleFactor, `${path}.throttle.throttleFactor`),
      shutdownC: sourced(th.shutdownC, `${path}.throttle.shutdownC`),
    },
    rentalUsdPerDay: {
      boom: sourced(rent.boom, `${path}.rentalUsdPerDay.boom`),
      after: sourced(rent.after, `${path}.rentalUsdPerDay.after`),
      boomEndIso: iso(rent.boomEndIso, `${path}.rentalUsdPerDay.boomEndIso`),
    },
    progression: {
      seedMinCustomers: sourced(prog.seedMinCustomers, `${path}.progression.seedMinCustomers`),
      seedMinReputation: sourced(prog.seedMinReputation, `${path}.progression.seedMinReputation`),
      seedReofferWeeks: sourced(prog.seedReofferWeeks, `${path}.progression.seedReofferWeeks`),
    },
    seedRound: {
      raiseUsd: sourced(seed.raiseUsd, `${path}.seedRound.raiseUsd`),
      preMoneyUsd: sourced(seed.preMoneyUsd, `${path}.seedRound.preMoneyUsd`),
      dilution: sourced(seed.dilution, `${path}.seedRound.dilution`),
    },
  };
}

function economy(v: unknown, path: string): EconomyData {
  const o = obj(v, path);
  const c = obj(o.consulting, `${path}.consulting`);
  const g = obj(o.grant, `${path}.grant`);
  const r = obj(o.reputation, `${path}.reputation`);
  const cs = (k: string) => sourced(c[k], `${path}.consulting.${k}`);
  const gs = (k: string) => sourced(g[k], `${path}.grant.${k}`);
  return {
    consulting: {
      everyWeeks: cs('everyWeeks'),
      maxOffers: cs('maxOffers'),
      usdMin: cs('usdMin'),
      usdMax: cs('usdMax'),
      usdStep: cs('usdStep'),
      weeksMin: cs('weeksMin'),
      weeksMax: cs('weeksMax'),
    },
    grant: { minReputation: gs('minReputation'), p100eq: gs('p100eq'), hours: gs('hours'), weeks: gs('weeks') },
    bankruptcyNegativeWeeks: sourced(o.bankruptcyNegativeWeeks, `${path}.bankruptcyNegativeWeeks`),
    reputation: {
      replicatePaper: sourced(r.replicatePaper, `${path}.reputation.replicatePaper`),
      translationV2: sourced(r.translationV2, `${path}.reputation.translationV2`),
    },
  };
}

function products(v: unknown, path: string): ProductsData {
  const o = obj(v, path);
  const tr = obj(o.translation, `${path}.translation`);
  const jobs = obj(o.jobs, `${path}.jobs`);
  const job = (k: string): { workP100h: Sourced<number> } => ({
    workP100h: sourced(obj(jobs[k], `${path}.jobs.${k}`).workP100h, `${path}.jobs.${k}.workP100h`),
  });
  const tr2 = obj(o.training, `${path}.training`);
  const loss = obj(tr2.loss, `${path}.training.loss`);
  const training: TrainingData = {
    researchContractFactor: sourced(tr2.researchContractFactor, `${path}.training.researchContractFactor`),
    loss: {
      start: sourced(loss.start, `${path}.training.loss.start`),
      exponent: sourced(loss.exponent, `${path}.training.loss.exponent`),
      floor: sourced(loss.floor, `${path}.training.loss.floor`),
    },
  };
  return {
    training,
    economy: economy(o.economy, `${path}.economy`),
    translation: {
      defaultPriceUsdPerMChars: sourced(tr.defaultPriceUsdPerMChars, `${path}.translation.defaultPriceUsdPerMChars`),
      seedCustomers: sourced(tr.seedCustomers, `${path}.translation.seedCustomers`),
      demandMCharsPerCustomerH: sourced(tr.demandMCharsPerCustomerH, `${path}.translation.demandMCharsPerCustomerH`),
      capacityMCharsPerP100eqH: sourced(tr.capacityMCharsPerP100eqH, `${path}.translation.capacityMCharsPerP100eqH`),
      baseLatencyMs: sourced(tr.baseLatencyMs, `${path}.translation.baseLatencyMs`),
      maxLatencyMs: sourced(tr.maxLatencyMs, `${path}.translation.maxLatencyMs`),
      qualityBase: sourced(tr.qualityBase, `${path}.translation.qualityBase`),
      qualityModelV2: sourced(tr.qualityModelV2, `${path}.translation.qualityModelV2`),
      weeklyGrowth: sourced(tr.weeklyGrowth, `${path}.translation.weeklyGrowth`),
      elasticityExponent: sourced(tr.elasticityExponent, `${path}.translation.elasticityExponent`),
      maxElasticityFactor: sourced(tr.maxElasticityFactor, `${path}.translation.maxElasticityFactor`),
      maxWeeklyGrowthAbs: sourced(tr.maxWeeklyGrowthAbs, `${path}.translation.maxWeeklyGrowthAbs`),
      minPriceUsdPerMChars: sourced(tr.minPriceUsdPerMChars, `${path}.translation.minPriceUsdPerMChars`),
      maxPriceUsdPerMChars: sourced(tr.maxPriceUsdPerMChars, `${path}.translation.maxPriceUsdPerMChars`),
    },
    jobs: {
      replicate_paper: job('replicate_paper'),
      translation_v2: job('translation_v2'),
      checkpointEveryH: {
        ...sourced(jobs.checkpointEveryH, `${path}.jobs.checkpointEveryH`),
        value: exact(obj(jobs.checkpointEveryH, `${path}.jobs.checkpointEveryH`).value, 4, `${path}.jobs.checkpointEveryH.value`),
      },
    },
  };
}

function pulsoData(v: unknown, path: string): PulsoData {
  const o = obj(v, path);
  const th = obj(o.thresholds, `${path}.thresholds`);
  const lim = obj(o.limits, `${path}.limits`);
  const tpl = obj(o.templates, `${path}.templates`);
  const news = obj(o.news, `${path}.news`);
  const causes: PulsoTemplateCause[] = ['latency', 'quality', 'price', 'praise'];
  const templates = {} as Record<PulsoTemplateCause, string[]>;
  for (const c of causes) {
    const list = arr(tpl[c], `${path}.templates.${c}`).map((x, i) => str(x, `${path}.templates.${c}[${i}]`));
    if (list.length < 4) throw new DataError(`${path}.templates.${c}: expected at least 4 templates`);
    templates[c] = list;
  }
  return {
    cadenceH: sourced(o.cadenceH, `${path}.cadenceH`),
    thresholds: {
      latencyMs: sourced(th.latencyMs, `${path}.thresholds.latencyMs`),
      praiseSatisfaction: sourced(th.praiseSatisfaction, `${path}.thresholds.praiseSatisfaction`),
      priceFactor: sourced(th.priceFactor, `${path}.thresholds.priceFactor`),
      qualityMinCustomers: sourced(th.qualityMinCustomers, `${path}.thresholds.qualityMinCustomers`),
    },
    limits: {
      dedupeHours: sourced(lim.dedupeHours, `${path}.limits.dedupeHours`),
      maxNewPerDay: sourced(lim.maxNewPerDay, `${path}.limits.maxNewPerDay`),
      maxItems: sourced(lim.maxItems, `${path}.limits.maxItems`),
    },
    templates,
    news: {
      titanV: str(news.titanV, `${path}.news.titanV`),
      seedRound: str(news.seedRound, `${path}.news.seedRound`),
      seedRoundClosed: str(news.seedRoundClosed, `${path}.news.seedRoundClosed`),
    },
  };
}

/** Validates raw JSON (extra fields tolerated, defined ones strict). Throws DataError naming the path. */
export function loadData(raw: { hardware: unknown; world: unknown; products: unknown; pulso: unknown }): GameData {
  const hw = obj(raw.hardware, 'hardware');
  return {
    gpus: arr(hw.gpus, 'hardware.gpus').map((g, i) => gpu(g, `hardware.gpus[${i}]`)),
    rigs: arr(hw.rigs, 'hardware.rigs').map((r, i) => rig(r, `hardware.rigs[${i}]`)),
    world: world(raw.world, 'world'),
    products: products(raw.products, 'products'),
    pulso: pulsoData(raw.pulso, 'pulso'),
  };
}
