/** Next `${prefix}-N` id: one past the highest existing numeric suffix. */
export function nextId(prefix: string, ids: string[]): string {
  let max = 0;
  for (const id of ids) {
    const n = Number(id.slice(prefix.length + 1));
    if (id.startsWith(`${prefix}-`) && Number.isInteger(n) && n > max) max = n;
  }
  return `${prefix}-${max + 1}`;
}
