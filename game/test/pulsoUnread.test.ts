import { describe, expect, it } from 'vitest';
import { seenFloor } from '../src/ui/pulso';

describe('Pulso unread after a restart or import', () => {
  it('keeps what was seen while the same game moves forward', () => {
    expect(seenFloor(120, 120)).toBe(120);
    expect(seenFloor(120, 300)).toBe(120);
  });
  it('forgets it when the newest item is older than what was seen (another game)', () => {
    expect(seenFloor(5000, 0)).toBe(-1);
    expect(seenFloor(5000, -1)).toBe(-1);
  });
});
