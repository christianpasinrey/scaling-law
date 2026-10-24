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
  electricityUsdPerKwh: Sourced<number>;
  /** Interruptions per GPU per day (garage multiplier already applied). */
  failPerGpuDay: Sourced<number>;
  throttle: {
    throttleC: Sourced<number>;
    throttleFactor: Sourced<number>;
    shutdownC: Sourced<number>;
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
}

export interface ProductsData {
  translation: TranslationProductData;
}

export interface GameData {
  gpus: GpuModel[];
  rigs: RigModel[];
  world: WorldData;
  products: ProductsData;
}
