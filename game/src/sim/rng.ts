// Deterministic PRNG (mulberry32). State is a single uint32 so it can be saved.
export interface Rng {
  /** Uniform float in [0, 1). */
  next(): number;
  /** Uniform integer in [min, max], both inclusive. */
  int(min: number, max: number): number;
  /** Current internal state; pass to restoreRng to resume the sequence. */
  state(): number;
}

export function restoreRng(state: number): Rng {
  let s = state >>> 0;
  const next = (): number => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    next,
    int: (min, max) => min + Math.floor(next() * (max - min + 1)),
    state: () => s,
  };
}

export function createRng(seed: number): Rng {
  return restoreRng(seed);
}
