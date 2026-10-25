// Pure motion decisions for the garage (no three.js, no DOM) so prefers-reduced-motion is testable.

/**
 * Next dash phase of a flow line. Under reduced motion the dashes stay still: level, colour and
 * on/off still convey the state, only the travel stops.
 */
export function flowPhaseStep(phase: number, speedMPerS: number, dtS: number, spacingM: number, reduced: boolean): number {
  if (reduced || speedMPerS <= 0) return phase;
  return (phase + speedMPerS * dtS) % spacingM;
}

/** HDD activity LED: off without a running job; flickers while one runs, or holds steady-on under reduced motion. */
export function hddLedOn(timeS: number, jobRunning: boolean, reduced: boolean): boolean {
  if (!jobRunning) return false;
  if (reduced) return true;
  // Irregular disk-activity flicker from two incommensurate sines.
  return Math.sin(timeS * 37.0) + Math.sin(timeS * 23.3 + 1.7) > 0.2;
}
