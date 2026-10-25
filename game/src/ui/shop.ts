// Tienda: real hardware of the period at launch price, with the reason when it cannot be bought.
import type { GameState } from '../sim';
import { el, learnButton, setAttr, setHidden, setText } from './dom';
import type { PanelDeps } from './dom';
import { formatDecimal, formatInt, formatUsd, rigLabel, shopItems, shopReasonText, t } from './format';

export interface ShopApi {
  update(s: GameState): void;
}

export function mount(root: HTMLElement, deps: PanelDeps): ShopApi {
  const d = deps.data;
  const list = el('ul', { class: 'cards' });
  root.append(el('p', { class: 'muted intro' }, t('shop.intro')), list);

  interface Row {
    buy: HTMLButtonElement;
    status: HTMLElement;
  }
  const rows = new Map<string, Row>();
  let state: GameState | null = null;

  for (const g of d.gpus) {
    const specs = t('shop.specs.gpu', { w: formatInt(g.watts.value), gb: formatInt(g.memGb), p: formatDecimal(g.p100eq.value, 1) }) + (g.p100eq.approx ? ` (${t('ui.aprox')})` : '');
    addRow(g.id, g.name, g.priceUsd.value, specs, g.learnId, () => {
      const item = state && shopItems(state, d).find((i) => i.id === g.id);
      if (item?.target) deps.send({ t: 'buy_gpu', model: g.id, rigId: item.target.rigId });
    });
  }
  for (const r of d.rigs) {
    if (r.id !== 'open_frame') continue;
    const specs = t('shop.specs.rig', { slots: r.gpuSlots, psu: formatInt(r.psuWatts) });
    addRow(r.id, r.name, r.priceUsd.value, specs, 'open_frame', () => deps.send({ t: 'buy_rig', model: r.id }), r.priceUsd.approx);
  }

  function addRow(id: string, name: string, price: number, specs: string, learnId: string, onBuy: () => void, priceApprox = false): void {
    const statusId = `shop-st-${id}`;
    const buy = el('button', { type: 'button', class: 'btn btn-primary', 'aria-describedby': statusId }, t('shop.buy'));
    buy.addEventListener('click', onBuy);
    const status = el('p', { class: 'item-status', id: statusId, tabindex: '-1' });
    list.append(
      el(
        'li',
        { class: 'card' },
        el('div', { class: 'card-head' }, el('strong', {}, name), learnButton(deps, learnId)),
        el('p', { class: 'muted small' }, specs),
        el('div', { class: 'card-foot' }, el('span', { class: 'num price' }, formatUsd(price) + (priceApprox ? ` ${t('ui.aprox')}` : '')), buy),
        status,
      ),
    );
    rows.set(id, { buy, status });
  }

  return {
    update(s) {
      state = s;
      for (const item of shopItems(s, d)) {
        const row = rows.get(item.id);
        if (!row) continue;
        const ok = item.reason === null;
        if (row.buy.disabled === ok) {
          // A focused button that becomes disabled drops focus on <body>: move it to the reason instead.
          const hadFocus = document.activeElement === row.buy;
          row.buy.disabled = !ok;
          if (hadFocus && !ok) queueMicrotask(() => row.status.focus());
        }
        let text = '';
        if (!ok) text = shopReasonText(item);
        else if (item.target) {
          text = t('shop.target', { where: `${rigLabel(s, item.target.rigId)} · ${t('rig.slot', { n: item.target.slot + 1 })}` });
        }
        setText(row.status, text);
        row.status.classList.toggle('blocked', !ok);
        setHidden(row.status, text === '');
        setAttr(row.buy, 'title', ok ? null : text);
      }
    },
  };
}
