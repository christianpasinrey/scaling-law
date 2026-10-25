import type { GameData, GameState, OwnedGpu, PulsoItem } from './types';

const HOURS_PER_DAY = 24;

/**
 * Identity of an event for grouping: cause plus focus (kind and id). Warnings (their code) and news (one-off
 * events) also carry their id, because they share a cause and have no focus yet are distinct events.
 */
const keyOf = (i: PulsoItem): string =>
  `${i.cause}|${i.focus?.kind ?? ''}|${i.focus?.id ?? ''}|${i.cause === 'warning' || i.cause === 'news' ? i.id : ''}`;

/** Display label of a GPU for texts: model short name and 1-based slot, e.g. "GTX 1080 Ti (ranura 1)". */
export function gpuLabel(d: GameData, g: OwnedGpu): string {
  const name = d.gpus.find((m) => m.id === g.model)?.shortName ?? g.model;
  return `${name} (ranura ${g.slot + 1})`;
}

/**
 * The single entry point for Pulso items (ruling R13).
 * - Same cause and focus as an item created/refreshed in the last `dedupeHours`: that item gets count + 1 and
 *   hour = now (moved to the end of the feed); no new item.
 * - At most `maxNewPerDay` new items per game day. A further one is merged into the most recent item of its
 *   cause, or dropped if there is none. Command warnings are player feedback: always created, never counted.
 * - Only the last `maxItems` items are kept.
 */
export function pushPulso(s: GameState, d: GameData, item: PulsoItem): GameState {
  const lim = d.pulso.limits;
  const now = s.hour;
  const bump = (idx: number): GameState => {
    const prev = s.pulso[idx] as PulsoItem;
    const rest = s.pulso.filter((_, k) => k !== idx);
    return { ...s, pulso: [...rest, { ...prev, hour: now, count: prev.count + 1 }] };
  };

  const key = keyOf(item);
  for (let i = s.pulso.length - 1; i >= 0; i--) {
    const p = s.pulso[i] as PulsoItem;
    if (now - p.hour < lim.dedupeHours.value && keyOf(p) === key) return bump(i);
  }

  const exempt = item.cause === 'warning';
  const day = Math.floor(now / HOURS_PER_DAY);
  const created = s.pulsoDay?.day === day ? s.pulsoDay.created : 0;
  if (!exempt && created >= lim.maxNewPerDay.value) {
    for (let i = s.pulso.length - 1; i >= 0; i--) {
      if ((s.pulso[i] as PulsoItem).cause === item.cause) return bump(i);
    }
    return s;
  }

  const pulso = [...s.pulso, { ...item, hour: now }].slice(-lim.maxItems.value);
  return exempt ? { ...s, pulso } : { ...s, pulso, pulsoDay: { day, created: created + 1 } };
}
