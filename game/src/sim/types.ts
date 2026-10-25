// All simulation state/data shapes live here (ruling R1).

/** A figure with provenance. `approx` figures are shown as "aprox." in the UI. */
export interface Sourced<T> {
  value: T;
  source: string;
  approx: boolean;
}

export interface GpuModel {
  id: string;
  name: string;
  /** ISO date (YYYY-MM-DD). */
  releaseDate: string;
  priceUsd: Sourced<number>;
  watts: Sourced<number>;
  memGb: number;
  /** Throughput in P100-equivalents. */
  p100eq: Sourced<number>;
  /** Filename under assets/. */
  glb: string;
  /** Learn-card id (cards are authored later). */
  learnId: string;
}

export interface RigModel {
  id: 'tower_2017' | 'open_frame';
  name: string;
  releaseDate: string;
  priceUsd: Sourced<number>;
  gpuSlots: number;
  psuWatts: number;
  baseWatts: number;
  glb: string;
}

export interface WorldData {
  startIso: '2017-06-12T17:57:00Z';
  startCashUsd: 10000;
  circuitWatts: 1800;
  circuitSafeWatts: 1440;
  /** Garage ambient temperature; initial GPU temperature. */
  ambientC: Sourced<number>;
  electricityUsdPerKwh: Sourced<number>;
  /** Interruptions per GPU per day (garage multiplier already applied). */
  failPerGpuDay: Sourced<number>;
  throttle: {
    throttleC: Sourced<number>;
    throttleFactor: Sourced<number>;
    shutdownC: Sourced<number>;
  };
  thermal: {
    /** Target temperature at zero load, no neighbours. */
    baseC: Sourced<number>;
    /** Extra degrees at 100 % load. */
    perLoadC: Sourced<number>;
    /** Extra degrees per other GPU in the same closed tower. */
    neighbourTowerC: Sourced<number>;
    /** Extra degrees per other GPU in the same open frame. */
    neighbourOpenFrameC: Sourced<number>;
    /** Fraction of the gap to the target closed per hour. */
    smoothing: Sourced<number>;
    /** A shut-down GPU restarts (perf 1) once cooler than this. */
    recoverBelowC: Sourced<number>;
  };
  rentalUsdPerDay: {
    /** Per 1080 Ti while the 2017-2018 boom lasts. */
    boom: Sourced<number>;
    after: Sourced<number>;
    /** ISO instant at which the boom ends. */
    boomEndIso: string;
  };
  seedRound: {
    raiseUsd: Sourced<number>;
    preMoneyUsd: Sourced<number>;
    dilution: Sourced<number>;
  };
}

export interface TranslationProductData {
  defaultPriceUsdPerMChars: Sourced<number>;
  /** Customers seeded on the first launched hour. */
  seedCustomers: Sourced<number>;
  /** M characters demanded per customer per hour. */
  demandMCharsPerCustomerH: Sourced<number>;
  /** M characters served per hour by one P100-equivalent. */
  capacityMCharsPerP100eqH: Sourced<number>;
  baseLatencyMs: Sourced<number>;
  maxLatencyMs: Sourced<number>;
  qualityBase: Sourced<number>;
  qualityModelV2: Sourced<number>;
  /** Weekly customer growth at satisfaction 1 and the reference price. */
  weeklyGrowth: Sourced<number>;
  elasticityExponent: Sourced<number>;
}

export interface JobData {
  workP100h: Sourced<number>;
}

export interface EconomyData {
  consulting: {
    /** An offering round happens when the week number is a multiple of this. */
    everyWeeks: Sourced<number>;
    maxOffers: Sourced<number>;
    usdMin: Sourced<number>;
    usdMax: Sourced<number>;
    usdStep: Sourced<number>;
    weeksMin: Sourced<number>;
    weeksMax: Sourced<number>;
  };
  grant: {
    minReputation: Sourced<number>;
    p100eq: Sourced<number>;
    hours: Sourced<number>;
    weeks: Sourced<number>;
  };
  /** Consecutive weekly settlements with negative cash that end the game. */
  bankruptcyNegativeWeeks: Sourced<number>;
  reputation: {
    replicatePaper: Sourced<number>;
    translationV2: Sourced<number>;
  };
}

export interface ProductsData {
  translation: TranslationProductData;
  economy: EconomyData;
  jobs: {
    replicate_paper: JobData;
    translation_v2: JobData;
    /** Hours between training checkpoints. */
    checkpointEveryH: Sourced<4>;
  };
  training: TrainingData;
}

export interface TrainingData {
  /** Multiplier on own-GPU progress while a research contract is active. */
  researchContractFactor: Sourced<number>;
  /** Didactic loss curve: start * (1 - f)^exponent + floor. */
  loss: { start: Sourced<number>; exponent: Sourced<number>; floor: Sourced<number> };
}

export interface GameData {
  gpus: GpuModel[];
  rigs: RigModel[];
  world: WorldData;
  products: ProductsData;
}

// ---- Game state shapes (ruling R1: shapes now, behaviour in later tasks) ----

export type Alloc = 'train' | 'serve' | 'rent' | 'idle';

export interface OwnedRig {
  id: string;
  model: 'tower_2017' | 'open_frame';
}

export interface OwnedGpu {
  id: string;
  model: string;
  rigId: string;
  slot: number;
  tempC: number;
  perf: 0 | 0.7 | 1;
}

export interface PowerState {
  watts: number;
  breakerTripped: boolean;
  weekKwh: number;
}

export interface TrainingJob {
  id: 'replicate_paper' | 'translation_v2';
  workP100h: number;
  doneP100h: number;
  checkpointP100h: number;
  checkpointEveryH: 4;
  lossCurve: number[];
  status: 'locked' | 'ready' | 'running' | 'done';
}

export interface ProductState {
  priceUsdPerMChars: number;
  customers: number;
  demandMCharsH: number;
  servedMCharsH: number;
  latencyMs: number;
  satisfaction: number;
  weekServedMChars: number;
  launched: boolean;
}

export interface Contract {
  id: string;
  usd: number;
  weeksTotal: number;
  weeksLeft: number;
  status: 'offered' | 'active' | 'done';
}

export interface Grant {
  id: string;
  p100eq: number;
  /** Cloud hours still available; the grant only contributes while this is above 0. */
  hoursLeft: number;
  weeksLeft: number;
  status: 'offered' | 'active' | 'expired';
}

export interface LedgerWeek {
  week: number;
  revenueUsd: number;
  costsUsd: number;
  cashEndUsd: number;
  lines: Record<string, number>;
}

export interface PulsoItem {
  id: string;
  hour: number;
  cause: 'latency' | 'quality' | 'price' | 'outage' | 'praise' | 'news' | 'warning';
  text: string;
  count: number;
  focus?: { kind: 'gpu' | 'product' | 'power'; id?: string };
}

export interface GameState {
  version: 1;
  seed: number;
  rng: number;
  /** Whole hours since the start of the game. */
  hour: number;
  cashUsd: number;
  labName: string;
  rigs: OwnedRig[];
  gpus: OwnedGpu[];
  allocation: Record<string, Alloc>;
  power: PowerState;
  jobs: TrainingJob[];
  product: ProductState;
  contracts: Contract[];
  grants: Grant[];
  reputation: number;
  ledger: LedgerWeek[];
  pulso: PulsoItem[];
  flags: Record<string, boolean>;
  /** GPU rental income accrued this week; settled into the ledger. */
  weekRentUsd: number;
  /** Consecutive weekly settlements that ended with negative cash. */
  negativeWeeks: number;
  outcome: null | 'seed_round' | 'bankrupt';
  round?: { status: 'offered' | 'declined'; offeredHour: number };
}
