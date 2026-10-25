// Asignación: per GPU, what it does (train / serve / rent / idle), with temperature and performance factor.
import type { Alloc, GameState } from '../sim';
import { dateOf } from '../sim/time';
import { GPU_PALETTE } from '../render/brain';
import { el, learnButton, setAttr, setHidden, setText } from './dom';
import type { FocusDeps, PanelDeps } from './dom';
import { formatDecimal, gpuSlotLabel, t } from './format';

export interface AllocationApi {
  update(s: GameState): void;
  /** Marks a GPU row as selected and moves focus to it. */
  select(gpuId: string | null, focus?: boolean): void;
}

const ALLOCS: { to: Alloc; key: Parameters<typeof t>[0] }[] = [
  { to: 'train', key: 'alloc.train' },
  { to: 'serve', key: 'alloc.serve' },
  { to: 'rent', key: 'alloc.rent' },
  { to: 'idle', key: 'alloc.idle' },
];

interface Row {
  li: HTMLLIElement;
  title: HTMLButtonElement;
  temp: HTMLElement;
  perf: HTMLElement;
  btns: Map<Alloc, HTMLButtonElement>;
}

export function mount(root: HTMLElement, deps: PanelDeps & Pick<FocusDeps, 'selectGpu'>): AllocationApi {
  const d = deps.data;
  const throttleC = d.world.throttle.throttleC.value;
  const list = el('ul', { class: 'cards' });
  const empty = el('p', { class: 'muted' }, t('alloc.empty'));
  const hintServe = el('p', { class: 'muted small' });
  const hintRent = el('p', { class: 'muted small' });
  root.append(
    el('p', { class: 'muted intro' }, t('alloc.intro'), ' ', learnButton(deps, 'data_parallel')),
    empty,
    list,
    el('div', { class: 'hints' }, el('p', { class: 'small row' }, hintServe, learnButton(deps, 'inference')), el('p', { class: 'small row' }, hintRent, learnButton(deps, 'gpu_rental'))),
  );

  const rows = new Map<string, Row>();
  let key = '';
  let selected: string | null = null;

  function build(s: GameState): void {
    rows.clear();
    list.replaceChildren();
    s.gpus.forEach((g, i) => {
      const title = el('button', { type: 'button', class: 'gpu-title' });
      title.addEventListener('click', () => {
        deps.selectGpu(g.id);
      });
      const temp = el('span', { class: 'num' });
      const perf = el('span', { class: 'num' });
      const btns = new Map<Alloc, HTMLButtonElement>();
      const group = el('div', { class: 'segs', role: 'group' });
      for (const a of ALLOCS) {
        const b = el('button', { type: 'button', class: 'seg', 'aria-pressed': 'false', 'data-alloc': a.to }, t(a.key));
        b.addEventListener('click', () => deps.send({ t: 'allocate', gpuId: g.id, to: a.to }));
        btns.set(a.to, b);
        group.append(b);
      }
      const li = el(
        'li',
        { class: 'card gpu-row', 'data-gpu': g.id },
        el('div', { class: 'card-head' }, el('span', { class: 'chip-dot', style: `background:${GPU_PALETTE[i % GPU_PALETTE.length]}`, 'aria-hidden': 'true' }), title),
        el(
          'div',
          { class: 'gpu-stats small' },
          el('span', {}, `${t('alloc.temp')}: `, temp),
          el('span', {}, `${t('alloc.perf')}: `, perf, ' ', learnButton(deps, 'throttling')),
        ),
        group,
      );
      list.append(li);
      rows.set(g.id, { li, title, temp, perf, btns });
    });
  }

  function markSelected(): void {
    for (const [id, r] of rows) r.li.classList.toggle('selected', id === selected);
  }

  return {
    update(s) {
      const k = s.gpus.map((g) => `${g.id}@${g.rigId}:${g.slot}`).join('|') + `#${s.rigs.length}`;
      if (k !== key) {
        key = k;
        build(s);
        markSelected();
      }
      setHidden(empty, s.gpus.length > 0);
      for (const g of s.gpus) {
        const r = rows.get(g.id);
        if (!r) continue;
        const label = gpuSlotLabel(s, d, g);
        setText(r.title, label);
        r.li.querySelector('.segs')?.setAttribute('aria-label', t('alloc.group', { gpu: label }));
        setText(r.temp, `${formatDecimal(g.tempC, 0)} °C`);
        r.temp.classList.toggle('warn', g.tempC >= throttleC);
        setText(r.perf, g.perf === 1 ? t('alloc.perf.ok') : g.perf === 0.7 ? t('alloc.perf.throttled') : t('alloc.perf.off'));
        r.perf.classList.toggle('warn', g.perf === 0.7);
        r.perf.classList.toggle('bad', g.perf === 0);
        const cur = s.allocation[g.id] ?? 'idle';
        for (const [a, b] of r.btns) setAttr(b, 'aria-pressed', String(a === cur));
      }
      setText(hintServe, s.product.launched ? '' : t('alloc.hint.serve'));
      setHidden(hintServe.parentElement as HTMLElement, s.product.launched);
      const rent = d.world.rentalUsdPerDay;
      const perDay = dateOf(s).slice(0, 10) <= rent.boomEndIso.slice(0, 10) ? rent.boom.value : rent.after.value;
      setText(hintRent, t('alloc.hint.rent', { usd: formatDecimal(perDay, 0) }) + (rent.boom.approx ? ` (${t('ui.aprox')})` : ''));
    },
    select(id, focus = false) {
      selected = id;
      markSelected();
      if (id && focus) {
        const r = rows.get(id);
        r?.li.scrollIntoView({ block: 'nearest' });
        r?.title.focus();
      }
    },
  };
}
