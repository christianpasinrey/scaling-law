// Full-screen layers (intro, title, end of M1) that own the page while open: everything else in <body> is made
// inert, and the game's global key handlers stand down while a [data-screen] element exists (like dialog[open]).
// Not a native <dialog>: the intro uses Esc to skip, and a modal dialog may be force-closed by repeated Esc.

export interface Screen {
  el: HTMLElement;
  close(): void;
}

export const SCREEN_SELECTOR = '[data-screen]';

/** True when a full-screen layer or a modal dialog owns the keyboard. */
export function keyboardOwned(): boolean {
  return document.querySelector(`dialog[open], ${SCREEN_SELECTOR}`) !== null;
}

export function openScreen(className: string, label: string): Screen {
  const el = document.createElement('div');
  el.className = `screen ${className}`;
  el.setAttribute('role', 'dialog');
  el.setAttribute('aria-modal', 'true');
  el.setAttribute('aria-label', label);
  el.dataset.screen = '';
  const madeInert: Element[] = [];
  for (const c of Array.from(document.body.children)) {
    if (c instanceof HTMLElement && !c.inert && c.tagName !== 'SCRIPT') {
      c.inert = true;
      madeInert.push(c);
    }
  }
  document.body.append(el);
  let open = true;
  return {
    el,
    close() {
      if (!open) return;
      open = false;
      el.remove();
      for (const c of madeInert) (c as HTMLElement).inert = false;
    },
  };
}
