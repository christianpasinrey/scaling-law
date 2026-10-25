// Seed-round offer: an in-page modal (native <dialog>) that opens when the investor shows up and stays reachable
// from the objective and from Trabajos. Accept / decline send the existing commands; Esc or «Decidir más tarde»
// just closes it (the offer stays open in the sim).
import type { Command, GameData, GameState } from '../sim';
import { el } from './dom';
import { formatDecimal, formatUsd, t } from './format';

export type RoundChoice = 'accept' | 'decline' | 'later' | '';

/** Opens the offer for an 'offered' round; resolves with the choice when the dialog closes ('' if none). No-op otherwise. */
export function openRoundOffer(root: HTMLElement, s: GameState, d: GameData, send: (c: Command) => void): Promise<RoundChoice> {
  if (s.round?.status !== 'offered' || s.outcome !== null) return Promise.resolve('');
  const existing = root.querySelector<HTMLDialogElement>('dialog.round-offer');
  if (existing) {
    existing.querySelector<HTMLButtonElement>('.btn-primary')?.focus();
    return Promise.resolve('');
  }
  const sr = d.world.seedRound;
  const vars = {
    raise: formatUsd(sr.raiseUsd.value),
    pre: formatUsd(sr.preMoneyUsd.value),
    dil: formatDecimal(sr.dilution.value * 100, 1),
    lab: s.labName,
    weeks: d.world.progression.seedReofferWeeks.value,
  };
  const later = el('button', { type: 'submit', value: 'later', class: 'btn' }, t('round.later'));
  const decline = el('button', { type: 'submit', value: 'decline', class: 'btn' }, t('jobs.round.decline'));
  const accept = el('button', { type: 'submit', value: 'accept', class: 'btn btn-primary' }, t('jobs.round.accept'));
  const dlg = el(
    'dialog',
    { class: 'confirm round-offer panel-surface', 'aria-labelledby': 'round-offer-t', 'aria-describedby': 'round-offer-b' },
    el(
      'form',
      { method: 'dialog' },
      el('h2', { id: 'round-offer-t' }, t('round.title')),
      el('p', { id: 'round-offer-b' }, t('round.body', vars)),
      el('p', { class: 'small muted' }, t('round.note', vars)),
      el('div', { class: 'dialog-actions' }, later, decline, accept),
    ),
  );
  root.append(dlg);
  const back = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  return new Promise((resolve) => {
    dlg.addEventListener('close', () => {
      const v = dlg.returnValue;
      dlg.remove();
      if (v === 'accept') send({ t: 'accept_round' });
      else if (v === 'decline') send({ t: 'decline_round' });
      if (back && back.isConnected) back.focus();
      resolve(v === 'accept' || v === 'decline' || v === 'later' ? v : '');
    });
    dlg.showModal();
    later.focus(); // accepting ends the M1: the harmless choice has focus
  });
}
