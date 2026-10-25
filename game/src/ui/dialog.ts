// In-page confirm dialog on a native <dialog> (focus trap and Esc for free). Never window.confirm: browser
// dialogs block the page and automation.
import { el } from './dom';
import { t } from './format';

export interface ConfirmOptions {
  title: string;
  body: string;
  ok?: string;
  cancel?: string;
}

let seq = 0;

/** Resolves true on OK, false on Cancel / Esc. */
export function confirmDialog(root: HTMLElement, o: ConfirmOptions): Promise<boolean> {
  const id = `dlg-${++seq}`;
  const okBtn = el('button', { type: 'submit', value: 'ok', class: 'btn btn-primary' }, o.ok ?? t('dialog.ok'));
  const cancelBtn = el('button', { type: 'submit', value: 'cancel', class: 'btn' }, o.cancel ?? t('dialog.cancel'));
  const form = el(
    'form',
    { method: 'dialog' },
    el('h2', { id: `${id}-t` }, o.title),
    el('p', { id: `${id}-b` }, o.body),
    el('div', { class: 'dialog-actions' }, cancelBtn, okBtn),
  );
  const dlg = el('dialog', { class: 'confirm panel-surface', 'aria-labelledby': `${id}-t`, 'aria-describedby': `${id}-b` }, form);
  root.append(dlg);
  const back = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  return new Promise((resolve) => {
    dlg.addEventListener('close', () => {
      const ok = dlg.returnValue === 'ok';
      dlg.remove();
      if (back && back.isConnected) back.focus();
      resolve(ok);
    });
    dlg.showModal();
    cancelBtn.focus(); // the safe choice has focus
  });
}
