// The player's lab name: trimmed, inner whitespace collapsed, 2–40 characters (code points, so emoji count as one).
export const LAB_NAME_MIN = 2;
export const LAB_NAME_MAX = 40;

export type LabNameResult = { ok: true; name: string } | { ok: false; reason: 'short' | 'long' };

export function validateLabName(raw: string): LabNameResult {
  const name = raw.replace(/\s+/g, ' ').trim();
  const len = [...name].length;
  if (len < LAB_NAME_MIN) return { ok: false, reason: 'short' };
  if (len > LAB_NAME_MAX) return { ok: false, reason: 'long' };
  return { ok: true, name };
}
