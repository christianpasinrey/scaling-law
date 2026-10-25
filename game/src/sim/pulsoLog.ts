import type { GameState, PulsoItem } from './types';

/**
 * Appends a Pulso item directly.
 * TODO(Task 8): replace with the pulso module's aggregation and rate limiting.
 */
export function appendPulso(s: GameState, item: PulsoItem): PulsoItem[] {
  return [...s.pulso, item];
}
