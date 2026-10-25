import { describe, expect, it } from 'vitest';
import { LAB_NAME_MAX, LAB_NAME_MIN, validateLabName } from '../src/intro/labName';

describe('validateLabName', () => {
  it('trims and accepts 2–40 characters', () => {
    expect(LAB_NAME_MIN).toBe(2);
    expect(LAB_NAME_MAX).toBe(40);
    expect(validateLabName('  Mi laboratorio  ')).toEqual({ ok: true, name: 'Mi laboratorio' });
    expect(validateLabName('AI')).toEqual({ ok: true, name: 'AI' });
    expect(validateLabName('x'.repeat(40))).toEqual({ ok: true, name: 'x'.repeat(40) });
  });
  it('rejects too short (after trimming) and too long', () => {
    expect(validateLabName('   ')).toEqual({ ok: false, reason: 'short' });
    expect(validateLabName(' a ')).toEqual({ ok: false, reason: 'short' });
    expect(validateLabName('x'.repeat(41))).toEqual({ ok: false, reason: 'long' });
  });
  it('collapses inner runs of whitespace and counts characters, not UTF-16 units', () => {
    expect(validateLabName('Lab \n\t  Uno')).toEqual({ ok: true, name: 'Lab Uno' });
    expect(validateLabName('🧪🧪')).toEqual({ ok: true, name: '🧪🧪' });
    expect(validateLabName('🧪'.repeat(40))).toEqual({ ok: true, name: '🧪'.repeat(40) });
  });
});
