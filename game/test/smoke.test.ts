import { describe, expect, it } from 'vitest';

describe('smoke', () => {
  it('runs the test runner', () => {
    expect(1 + 1).toBe(2);
  });

  it('imports the sim module without throwing', async () => {
    await expect(import('../src/sim/index')).resolves.toBeDefined();
  });
});
