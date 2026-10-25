// Learn cards ("saber más"): three levels per card (sentence · why · formula/paper), opened on "?" and,
// the first time a concept appears, offered through a non-blocking "Nuevo concepto" toast.
import { el } from './dom';
import { t } from './format';

export interface LearnCard {
  title: string;
  short: string;
  why: string;
  deep: string;
  /** Where the game simplifies, said explicitly ("En el juego…"). */
  game?: string;
  link?: string;
  source: string;
  related: string[];
}

/** Validates data/learn.es.json. Throws naming the bad path. */
export function parseCards(raw: unknown): Record<string, LearnCard> {
  const root = raw as { cards?: unknown };
  if (typeof root !== 'object' || root === null || typeof root.cards !== 'object' || root.cards === null) throw new Error('learn: expected { cards: {...} }');
  const src = root.cards as Record<string, Record<string, unknown>>;
  const out: Record<string, LearnCard> = {};
  const str = (id: string, o: Record<string, unknown>, k: string, optional = false): string | undefined => {
    const v = o[k];
    if (v === undefined && optional) return undefined;
    if (typeof v !== 'string' || v.trim() === '') throw new Error(`learn: ${id}.${k} must be a non-empty string`);
    return v;
  };
  for (const [id, o] of Object.entries(src)) {
    const related = o.related ?? [];
    if (!Array.isArray(related) || related.some((r) => typeof r !== 'string')) throw new Error(`learn: ${id}.related must be a string array`);
    out[id] = {
      title: str(id, o, 'title')!,
      short: str(id, o, 'short')!,
      why: str(id, o, 'why')!,
      deep: str(id, o, 'deep')!,
      game: str(id, o, 'game', true),
      link: str(id, o, 'link', true),
      source: str(id, o, 'source')!,
      related: related as string[],
    };
  }
  for (const [id, c] of Object.entries(out)) {
    for (const r of c.related) if (!out[r]) throw new Error(`learn: ${id}.related references unknown card ${r}`);
  }
  return out;
}

const SEEN_KEY = 'scaling-law:learn-seen';
const TOAST_MS = 9000;

function readSeen(): Set<string> {
  try {
    const raw = localStorage.getItem(SEEN_KEY);
    const arr: unknown = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(arr) ? arr.filter((x): x is string => typeof x === 'string') : []);
  } catch {
    return new Set();
  }
}

function writeSeen(seen: Set<string>): void {
  try {
    localStorage.setItem(SEEN_KEY, JSON.stringify([...seen]));
  } catch {
    // Private mode or blocked storage: the toasts may repeat next session, nothing else breaks.
  }
}

export interface LearnApi {
  open(id: string, opener?: HTMLElement): void;
  close(): void;
  title(id: string): string;
  isOpen(): boolean;
  /** Offers a toast for every id not seen before (queued, one at a time). */
  notice(ids: readonly string[]): void;
}

export function mount(root: HTMLElement, cards: Record<string, LearnCard>): LearnApi {
  const seen = readSeen();
  const queue: string[] = [];
  let toastTimer = 0;
  let opener: HTMLElement | null = null;
  let openId: string | null = null;

  const heading = el('h2', { id: 'learn-title', tabindex: '-1' });
  const body = el('div', { class: 'learn-body' });
  const closeBtn = el('button', { type: 'button', class: 'icon-btn', 'aria-label': t('ui.close') }, '×');
  const card = el(
    'aside',
    { class: 'learn-card panel-surface', role: 'dialog', 'aria-modal': 'false', 'aria-labelledby': 'learn-title', hidden: true },
    el('header', { class: 'learn-head' }, heading, closeBtn),
    body,
  );
  const toastHost = el('div', { class: 'toast-host', 'aria-live': 'polite' });
  root.append(card, toastHost);

  const close = (): void => {
    if (card.hidden) return;
    card.hidden = true;
    openId = null;
    const back = opener;
    opener = null;
    if (back && back.isConnected) back.focus();
  };
  closeBtn.addEventListener('click', close);
  card.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      close();
    }
  });

  const open = (id: string, from?: HTMLElement): void => {
    const c = cards[id];
    if (!c) return;
    if (!seen.has(id)) {
      seen.add(id);
      writeSeen(seen);
    }
    if (card.hidden || from) opener = from ?? (document.activeElement instanceof HTMLElement ? document.activeElement : null);
    openId = id;
    heading.textContent = c.title;
    const details = (label: string, ...content: (Node | string)[]): HTMLDetailsElement =>
      el('details', { class: 'learn-level' }, el('summary', {}, label), ...content);
    const relatedRow =
      c.related.length > 0
        ? el(
            'div',
            { class: 'learn-related' },
            el('span', { class: 'muted' }, `${t('learn.related')}: `),
            ...c.related.map((r) => {
              const b = el('button', { type: 'button', class: 'chip' }, cards[r]?.title ?? r);
              b.addEventListener('click', () => open(r));
              return b;
            }),
          )
        : null;
    body.replaceChildren(
      el('p', { class: 'learn-short' }, c.short),
      details(t('learn.why'), el('p', {}, c.why)),
      details(
        t('learn.deep'),
        el('p', { class: 'learn-formula' }, c.deep),
        el('p', { class: 'learn-source' }, el('strong', {}, `${t('learn.source')}: `), c.source),
        c.link ? el('p', {}, el('a', { href: c.link, target: '_blank', rel: 'noopener noreferrer' }, t('learn.link'))) : '',
      ),
      c.game ? el('p', { class: 'learn-game' }, el('strong', {}, `${t('learn.game')}: `), c.game) : '',
      relatedRow ?? '',
    );
    card.hidden = false;
    heading.focus();
  };

  const showNextToast = (): void => {
    if (toastHost.firstChild || queue.length === 0) return;
    const id = queue.shift()!;
    const c = cards[id];
    if (!c) return showNextToast();
    const b = el('button', { type: 'button', class: 'toast' }, el('strong', {}, t('learn.toast', { title: c.title })), el('span', { class: 'muted' }, t('learn.toast.hint')));
    const done = (): void => {
      window.clearTimeout(toastTimer);
      b.remove();
      showNextToast();
    };
    b.addEventListener('click', () => {
      done();
      open(id, undefined);
    });
    toastHost.append(b);
    const arm = (): void => {
      window.clearTimeout(toastTimer);
      toastTimer = window.setTimeout(() => {
        // Never yank a toast from under the keyboard or the pointer.
        if (b.matches(':focus, :hover')) arm();
        else done();
      }, TOAST_MS);
    };
    arm();
  };

  return {
    open,
    close,
    title: (id) => cards[id]?.title ?? id,
    isOpen: () => openId !== null,
    notice(ids) {
      let added = false;
      for (const id of ids) {
        if (seen.has(id) || !cards[id]) continue;
        seen.add(id);
        queue.push(id);
        added = true;
      }
      if (added) {
        writeSeen(seen);
        showNextToast();
      }
    },
  };
}
