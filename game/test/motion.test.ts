import { describe, expect, it } from 'vitest';
import { flowPhaseStep, hddLedOn } from '../src/render/motion';

describe('flowPhaseStep', () => {
  it('advances the dash phase by speed × dt, wrapped to the dash spacing', () => {
    expect(flowPhaseStep(0, 0.35, 0.1, 0.07, false)).toBeCloseTo(0.035, 10);
    expect(flowPhaseStep(0.06, 0.35, 0.1, 0.07, false)).toBeCloseTo(0.025, 10);
  });

  it('freezes the phase under reduced motion', () => {
    expect(flowPhaseStep(0.03, 0.35, 0.1, 0.07, true)).toBe(0.03);
  });

  it('does not move when no current flows', () => {
    expect(flowPhaseStep(0.03, 0, 0.1, 0.07, false)).toBe(0.03);
  });
});

describe('hddLedOn', () => {
  it('is off when no job runs, whatever the motion setting', () => {
    for (const t of [0, 0.1, 1.7, 9.3]) {
      expect(hddLedOn(t, false, false)).toBe(false);
      expect(hddLedOn(t, false, true)).toBe(false);
    }
  });

  it('flickers while a job runs', () => {
    const samples = Array.from({ length: 200 }, (_, i) => hddLedOn(i * 0.01, true, false));
    expect(samples).toContain(true);
    expect(samples).toContain(false);
  });

  it('holds steady-on under reduced motion while a job runs', () => {
    for (let i = 0; i < 200; i++) expect(hddLedOn(i * 0.01, true, true)).toBe(true);
  });
});
