// Pulso: the feed of customers, news and incidents, newest first, aggregated (×N), with its focus.
import type { GameState, PulsoItem } from '../sim';
import { dateOf } from '../sim/time';
import { el, setText } from './dom';
import type { FocusDeps } from './dom';
import { formatDate, pulsoNewestFirst, t } from './format';

export interface PulsoApi {
  update(s: GameState): void;
  /** Items newer than the last time the feed was shown. */
  unseen(): number;
  markSeen(): void;
  /** Another game was loaded (new game, import, resume): nothing of it has been seen yet. */
  reset(): void;
}

/**
 * The last item hour the player has seen, given the newest item hour now in the feed. A feed whose newest item is
 * older than what was seen belongs to another game (a restart or an import), so nothing of it has been seen.
 */
export function seenFloor(seenUpTo: number, latest: number): number {
  return latest < seenUpTo ? -1 : seenUpTo;
}

const SHOWN = 60;
const ICON: Record<PulsoItem['cause'], string> = {
  latency: '⏱',
  quality: '✎',
  price: '$',
  outage: '⚡',
  praise: '♥',
  news: '★',
  warning: '!',
};

export function mount(root: HTMLElement, deps: FocusDeps): PulsoApi {
  const list = el('ol', { class: 'pulso-list', 'aria-live': 'off' });
  const empty = el('p', { class: 'muted' }, t('pulso.empty'));
  root.append(empty, list);
  let key = '';
  let latest = -1;
  let seenUpTo = -1;
  let state: GameState | null = null;

  return {
    update(s) {
      state = s;
      const items = pulsoNewestFirst(s).slice(0, SHOWN);
      latest = s.pulso.reduce((m, p) => Math.max(m, p.hour), -1);
      seenUpTo = seenFloor(seenUpTo, latest);
      const k = items.map((i) => `${i.id}:${i.count}:${i.hour}`).join('|');
      empty.hidden = items.length > 0;
      if (k === key) return;
      key = k;
      const focusedId = (document.activeElement as HTMLElement | null)?.dataset?.pid;
      list.replaceChildren(
        ...items.map((i) => {
          const when = formatDate(dateOf({ ...s, hour: i.hour }));
          const content = [
            el('span', { class: 'p-icon', 'aria-hidden': 'true' }, ICON[i.cause]),
            el('span', { class: 'sr-only' }, `${t(`pulso.cause.${i.cause}`)}: `),
            el('span', { class: 'p-text' }, i.text),
            i.count > 1 ? el('span', { class: 'p-count num', 'aria-label': t('pulso.count.aria', { n: i.count }) }, t('pulso.count', { n: i.count })) : null,
            el('time', { class: 'p-time num', datetime: dateOf({ ...s, hour: i.hour }) }, when),
          ];
          const focus = i.focus;
          if (!focus) return el('li', { class: 'p-item', 'data-cause': i.cause }, el('div', { class: 'p-body' }, ...content));
          const b = el('button', { type: 'button', class: 'p-body p-btn', 'data-pid': i.id, title: t(`pulso.focus.${focus.kind}`) }, ...content);
          b.addEventListener('click', () => deps.focus(focus));
          return el('li', { class: 'p-item', 'data-cause': i.cause }, b);
        }),
      );
      if (focusedId) (list.querySelector(`[data-pid="${CSS.escape(focusedId)}"]`) as HTMLElement | null)?.focus();
    },
    unseen() {
      if (!state) return 0;
      return state.pulso.filter((p) => p.hour > seenUpTo).length;
    },
    markSeen() {
      seenUpTo = latest;
    },
    reset() {
      seenUpTo = -1;
      latest = -1;
    },
  };
}
