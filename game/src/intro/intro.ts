// Opening scene, ported from prototypes/01-intro-transformer: the arXiv listing of 1706.03762 → the paper's title
// page (our own summary, not the abstract) → Figure 1 drawn block by block with tokens flowing → an illustrative
// attention matrix → the garage hand-off card, which asks for the lab name. Block notes reuse the learn cards.
import './intro.css';
import { t } from '../ui/format';
import type { TextKey } from '../ui/format';
import type { LearnCard } from '../ui/learn';
import { LAB_NAME_MAX, LAB_NAME_MIN, validateLabName } from './labName';

export interface IntroOptions {
  /** Called once with the validated lab name. */
  onDone(labName: string): void;
  /** Shows «Saltar» and lets Esc jump to the hand-off card. */
  skippable: boolean;
  cards: Record<string, LearnCard>;
  defaultName: string;
}

export interface IntroHandle {
  dispose(): void;
}

type BlockKey = 'emb' | 'pe' | 'mha' | 'mmha' | 'xatt' | 'norm' | 'ff' | 'lin' | 'soft' | 'nx';

/** Block → learn card it explains with (card title/short reused unless the intro has its own note) and links to. */
const CARD: Record<BlockKey, { card: string; own: boolean }> = {
  emb: { card: 'embedding', own: false },
  pe: { card: 'embedding', own: true },
  mha: { card: 'attention', own: false },
  mmha: { card: 'decoder', own: true },
  xatt: { card: 'decoder', own: true },
  norm: { card: 'layer_norm', own: false },
  ff: { card: 'feed_forward', own: false },
  lin: { card: 'softmax', own: true },
  soft: { card: 'softmax', own: false },
  nx: { card: 'encoder', own: true },
};

const AUTHORS: [string, string][] = [
  ['Ashish Vaswani', 'Google Brain'],
  ['Noam Shazeer', 'Google Brain'],
  ['Niki Parmar', 'Google Research'],
  ['Jakob Uszkoreit', 'Google Research'],
  ['Llion Jones', 'Google Research'],
  ['Aidan N. Gomez', 'University of Toronto'],
  ['Łukasz Kaiser', 'Google Brain'],
  ['Illia Polosukhin', ' '],
];
const PAPER_TITLE = 'Attention Is All You Need';
const PAPER_META = 'arXiv:1706.03762 · Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin';
const STAMP = 'arXiv:1706.03762v1 [cs.CL] 12 Jun 2017';

const SRC = ['Attention', 'is', 'all', 'you', 'need'];
const TGT = ['<s>', 'Aufmerksamkeit', 'ist', 'alles'];
const NEXT_WORDS = ['Aufmerksamkeit', 'ist', 'alles', ',', 'was', 'du', 'brauchst', '</s>'];
/** Illustrative weights: rows German output tokens, columns English input tokens. */
const ATT = [
  [0.78, 0.06, 0.05, 0.05, 0.06],
  [0.08, 0.8, 0.04, 0.04, 0.04],
  [0.04, 0.05, 0.82, 0.05, 0.04],
  [0.04, 0.04, 0.06, 0.4, 0.46],
];
const ROWS = ['Aufmerksamkeit', 'ist', 'alles', 'was du brauchst'];

const NS = 'http://www.w3.org/2000/svg';

function h<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, html?: string): HTMLElementTagNameMap[K] {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html !== undefined) n.innerHTML = html;
  return n;
}

export function runIntro(root: HTMLElement, opts: IntroOptions): IntroHandle {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const timers: number[] = [];
  const later = (ms: number, fn: () => void): void => {
    timers.push(window.setTimeout(fn, reduced ? 0 : ms));
  };
  let disposed = false;

  // ---------------------------------------------------------------- DOM skeleton
  const wrap = h('div', 'intro');
  const head = h('header', 'intro-head');
  head.append(h('span', 'intro-brand', t('intro.brand')), h('span', 'intro-date', t('intro.clock')), h('span', 'intro-spacer'));
  const replayBtn = h('button', 'intro-btn', t('intro.replay'));
  replayBtn.type = 'button';
  replayBtn.title = t('intro.replay.title');
  const skipBtn = h('button', 'intro-btn', t('intro.skip'));
  skipBtn.type = 'button';
  skipBtn.title = t('intro.skip.title');
  skipBtn.setAttribute('aria-keyshortcuts', 'Escape');
  skipBtn.hidden = !opts.skippable;
  head.append(replayBtn, skipBtn);

  const listing = h('div', 'intro-listing');
  const typed = h('div', 'intro-listing-title');
  const meta = h('div', 'intro-listing-meta');
  listing.append(h('div', 'intro-listing-kicker', t('intro.listing.kicker')), typed, meta);

  const stage = h('main', 'intro-stage');
  const paperWrap = h('section', 'intro-scene intro-paperwrap');
  const paper = h('article', 'intro-paper');
  paper.setAttribute('lang', 'es');
  paper.append(h('div', 'intro-stamp', STAMP));
  const title = h('h1', '', PAPER_TITLE);
  title.setAttribute('lang', 'en');
  paper.append(title);
  const authors = h('div', 'intro-authors');
  for (const [n, a] of AUTHORS) {
    const d = h('div');
    d.append(h('b', '', n), h('span', '', a));
    authors.append(d);
  }
  paper.append(authors, h('h2', '', t('intro.paper.summaryTitle')), h('p', '', t('intro.paper.p1')), h('p', '', t('intro.paper.p2')));
  const facts = h('div', 'intro-facts');
  for (const [big, k] of [['28,4', 'intro.paper.fact1'], ['41,0', 'intro.paper.fact2'], ['8 × P100', 'intro.paper.fact3']] as const) {
    const d = h('div');
    d.append(h('strong', '', big), document.createTextNode(t(k)));
    facts.append(d);
  }
  paper.append(facts, h('div', 'intro-note', t('intro.paper.note')));
  const attn = h('aside', 'intro-attn');
  attn.append(h('h3', '', t('intro.attn.title')), h('small', '', t('intro.attn.note')));
  const attnGrid = h('div', 'intro-attn-grid');
  attnGrid.setAttribute('lang', 'en');
  attn.append(attnGrid);
  paperWrap.append(paper, attn);

  const figWrap = h('section', 'intro-scene intro-figwrap');
  const figCard = h('div', 'intro-figcard');
  const svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('class', 'intro-fig');
  svg.setAttribute('viewBox', '0 0 540 760');
  svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', t('intro.fig.aria'));
  svg.innerHTML =
    '<defs><marker id="intro-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>';
  const layer = (): SVGGElement => {
    const g = document.createElementNS(NS, 'g');
    svg.append(g);
    return g;
  };
  const L = { frames: layer(), wires: layer(), blocks: layer(), labels: layer(), pulses: layer() };
  figCard.append(svg);
  const explainBox = h('div', 'intro-explain');
  explainBox.setAttribute('aria-live', 'polite');
  figWrap.append(figCard, explainBox);
  stage.append(paperWrap, figWrap);

  // ---- hand-off card with the lab-name form
  const garage = h('div', 'intro-garage');
  garage.setAttribute('role', 'region');
  garage.setAttribute('aria-labelledby', 'intro-garage-h');
  const gh = h('h2', '', t('intro.garage.title'));
  gh.id = 'intro-garage-h';
  garage.append(gh, h('p', '', t('intro.garage.body')));
  const cmp = h('div', 'intro-cmp');
  for (const who of ['them', 'you'] as const) {
    const d = h('div');
    d.append(h('b', '', t(`intro.garage.${who}`)), h('div', 'big', t(`intro.garage.${who}.big`)), h('div', 'sub', t(`intro.garage.${who}.sub`)));
    cmp.append(d);
  }
  const form = h('form', 'intro-name');
  form.noValidate = true;
  const nameLabel = h('label', '', t('intro.name.label'));
  nameLabel.htmlFor = 'intro-lab-name';
  const input = h('input');
  input.id = 'intro-lab-name';
  input.type = 'text';
  input.value = opts.defaultName;
  input.maxLength = LAB_NAME_MAX * 2; // code points ≤ 2 units each; the validator counts characters
  input.autocomplete = 'organization';
  input.spellcheck = false;
  input.setAttribute('aria-describedby', 'intro-lab-hint intro-lab-err');
  const hint = h('p', 'intro-hint', t('intro.name.hint', { min: LAB_NAME_MIN, max: LAB_NAME_MAX }));
  hint.id = 'intro-lab-hint';
  const err = h('p', 'intro-err');
  err.id = 'intro-lab-err';
  err.setAttribute('role', 'alert');
  const figureBtn = h('button', 'intro-btn', t('intro.figure'));
  figureBtn.type = 'button';
  const startBtn = h('button', 'intro-btn primary', t('intro.start'));
  startBtn.type = 'submit';
  const row = h('div', 'intro-row');
  row.append(figureBtn, startBtn);
  form.append(nameLabel, input, hint, err, row);
  garage.append(cmp, form);

  wrap.append(head, listing, stage, garage);
  root.replaceChildren(wrap);

  // ---------------------------------------------------------------- explanations
  const explain = (key: BlockKey): void => {
    const m = CARD[key];
    const card = opts.cards[m.card];
    const own = (part: 't' | 'd') => t(`intro.block.${key}.${part}` as TextKey);
    const titleText = m.own ? own('t') : (card?.title ?? key);
    const body = m.own ? own('d') : (card?.short ?? '');
    explainBox.replaceChildren(h('div', 'intro-explain-t'), h('div', 'intro-explain-d'), h('div', 'intro-explain-f'));
    explainBox.children[0]!.textContent = titleText;
    explainBox.children[1]!.textContent = body;
    explainBox.children[2]!.textContent = t(`intro.block.${key}.f` as TextKey);
    if (card) {
      const more = h('details', 'intro-more');
      const sum = h('summary', '', `${t('intro.more')}: ${card.title}`);
      const why = h('p');
      why.textContent = card.why;
      const src = h('p', 'intro-src');
      src.textContent = `${t('learn.source')}: ${card.source}`;
      more.append(sum, why);
      if (card.game) {
        const g = h('p', 'intro-src');
        g.textContent = `${t('learn.game')}: ${card.game}`;
        more.append(g);
      }
      more.append(src);
      explainBox.append(more);
    }
    svg.querySelectorAll<SVGGElement>('.blk').forEach((b) => b.classList.toggle('hot', b.dataset.k === key));
  };
  const explainDefault = (): void => {
    explainBox.replaceChildren(h('div', 'intro-explain-t', t('intro.fig.title')), h('div', 'intro-explain-d', t('intro.fig.hint')));
  };
  explainDefault();

  // ---------------------------------------------------------------- layout of Figure 1 (as in the prototype)
  const el = (tag: string, attrs: Record<string, string | number>, parent?: Element): SVGElement => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, String(attrs[k]));
    parent?.appendChild(n);
    return n;
  };
  const W = 150;
  const Hh = 32;
  const EX = 140;
  const DX = 395;
  interface Block { id: string; cx: number; y: number; text: string; color: string; key: BlockKey; h: number }
  const blocks: Block[] = [];
  const wires: { id: string; d: string }[] = [];
  const frames: { id: string; x: number; y: number; w: number; h: number }[] = [];
  const labels: { id: string; x: number; y: number; text: string; anchor: string; size: number; weight: number }[] = [];
  const block = (id: string, cx: number, y: number, text: string, color: string, key: BlockKey, hh = Hh) => {
    blocks.push({ id, cx, y, text, color, key, h: hh });
    return { cx, top: y - hh / 2, bot: y + hh / 2 };
  };
  const wire = (id: string, d: string): void => {
    wires.push({ id, d });
  };
  const label = (id: string, x: number, y: number, text: string, anchor = 'middle', size = 12, weight = 400): void => {
    labels.push({ id, x, y, text, anchor, size, weight });
  };

  const eEmb = block('eEmb', EX, 650, 'Input Embedding', 'var(--c-emb)', 'emb');
  const eMha = block('eMha', EX, 520, 'Multi-Head Attention', 'var(--c-mha)', 'mha', 40);
  const eN1 = block('eN1', EX, 470, 'Add & Norm', 'var(--c-norm)', 'norm', 24);
  const eFf = block('eFf', EX, 400, 'Feed Forward', 'var(--c-ff)', 'ff', 40);
  const eN2 = block('eN2', EX, 350, 'Add & Norm', 'var(--c-norm)', 'norm', 24);
  frames.push({ id: 'eFrame', x: EX - W / 2 - 18, y: 324, w: W + 36, h: 230 });
  const dEmb = block('dEmb', DX, 650, 'Output Embedding', 'var(--c-emb)', 'emb');
  const dMm = block('dMm', DX, 520, 'Masked Multi-Head Attention', 'var(--c-mha)', 'mmha', 40);
  const dN1 = block('dN1', DX, 470, 'Add & Norm', 'var(--c-norm)', 'norm', 24);
  const dX = block('dX', DX, 400, 'Multi-Head Attention', 'var(--c-mha)', 'xatt', 40);
  const dN2 = block('dN2', DX, 350, 'Add & Norm', 'var(--c-norm)', 'norm', 24);
  const dFf = block('dFf', DX, 280, 'Feed Forward', 'var(--c-ff)', 'ff', 40);
  const dN3 = block('dN3', DX, 230, 'Add & Norm', 'var(--c-norm)', 'norm', 24);
  frames.push({ id: 'dFrame', x: DX - W / 2 - 18, y: 204, w: W + 36, h: 350 });
  const lin = block('lin', DX, 150, 'Linear', 'var(--c-lin)', 'lin', 26);
  const soft = block('soft', DX, 104, 'Softmax', 'var(--c-soft)', 'soft', 26);

  const PE_Y = 595;
  label('eNx', EX - W / 2 - 34, 440, 'N×', 'middle', 15, 700);
  label('dNx', DX + W / 2 + 34, 380, '×N', 'middle', 15, 700);
  label('in', EX, 742, 'Inputs');
  label('out', DX, 742, 'Outputs (shifted right)');
  label('prob', DX, 40, 'Output Probabilities');
  label('pe1', EX - 92, PE_Y + 4, 'Positional', 'end', 11);
  label('pe1b', EX - 92, PE_Y + 18, 'Encoding', 'end', 11);
  label('pe2', DX + 92, PE_Y + 4, 'Positional', 'start', 11);
  label('pe2b', DX + 92, PE_Y + 18, 'Encoding', 'start', 11);

  const v = (x: number, y1: number, y2: number) => `M${x},${y1} L${x},${y2}`;
  wire('w_in', v(EX, 728, eEmb.bot));
  wire('w_e1', v(EX, eEmb.top, PE_Y + 9));
  wire('w_e2', v(EX, PE_Y - 9, eMha.bot));
  wire('w_e3', v(EX, eMha.top, eN1.bot));
  wire('w_e4', v(EX, eN1.top, eFf.bot));
  wire('w_e5', v(EX, eFf.top, eN2.bot));
  wire('w_out', v(DX, 728, dEmb.bot));
  wire('w_d1', v(DX, dEmb.top, PE_Y + 9));
  wire('w_d2', v(DX, PE_Y - 9, dMm.bot));
  wire('w_d3', v(DX, dMm.top, dN1.bot));
  wire('w_d4', v(DX, dN1.top, dX.bot));
  wire('w_d5', v(DX, dX.top, dN2.bot));
  wire('w_d6', v(DX, dN2.top, dFf.bot));
  wire('w_d7', v(DX, dFf.top, dN3.bot));
  wire('w_d8', v(DX, dN3.top, lin.bot));
  wire('w_d9', v(DX, lin.top, soft.bot));
  wire('w_d10', v(DX, soft.top, 52));
  // Q, K, V fan-in into the self-attention blocks.
  const fan = (id: string, b: { bot: number }, srcY: number, x: number) =>
    [-38, 0, 38].forEach((o, i) => wire(`${id}_${i}`, `M${x},${srcY} C${x},${srcY - 14} ${x + o},${b.bot + 16} ${x + o},${b.bot}`));
  fan('f_e', eMha, eMha.bot + 26, EX);
  fan('f_d', dMm, dMm.bot + 26, DX);
  // Residual connections around each sub-layer.
  const res = (id: string, x: number, y1: number, yN: number) => wire(id, `M${x},${y1} L${x - W / 2 - 10},${y1} L${x - W / 2 - 10},${yN} L${x - W / 2},${yN}`);
  res('r_e1', EX, eMha.bot + 12, 470);
  res('r_e2', EX, eFf.bot + 10, 350);
  res('r_d1', DX, dMm.bot + 12, 470);
  res('r_d2', DX, dX.bot + 10, 350);
  res('r_d3', DX, dFf.bot + 10, 230);
  // Encoder output → K, V of the cross-attention; Q from below.
  const MX = (EX + DX) / 2;
  wire('x_enc', `M${EX},${eN2.top} L${EX},300 C${EX},280 ${MX},300 ${MX},360 L${MX},${dX.bot + 22} C${MX},${dX.bot + 4} ${DX - 38},${dX.bot + 22} ${DX - 38},${dX.bot}`);
  wire('x_enc2', `M${MX},${dX.bot + 22} C${MX + 20},${dX.bot + 8} ${DX},${dX.bot + 22} ${DX},${dX.bot}`);
  wire('x_q', `M${DX},${dN1.top} C${DX + 30},${dN1.top - 10} ${DX + 38},${dX.bot + 14} ${DX + 38},${dX.bot}`);

  // ---- draw
  for (const f of frames) {
    const r = el('rect', { x: f.x, y: f.y, width: f.w, height: f.h, rx: 12, class: 'frame', 'data-id': f.id }, L.frames);
    r.addEventListener('click', () => explain('nx'));
  }
  for (const w of wires) el('path', { d: w.d, class: 'wire', 'data-id': w.id }, L.wires);
  for (const b of blocks) {
    const g = el('g', { class: 'blk', 'data-id': b.id, 'data-k': b.key, tabindex: 0, role: 'button', 'aria-label': b.text }, L.blocks);
    el('rect', { x: b.cx - W / 2, y: b.y - b.h / 2, width: W, height: b.h, fill: b.color }, g);
    const words = b.text.length > 22 ? [b.text.split(' ').slice(0, 1).join(' '), b.text.split(' ').slice(1).join(' ')] : [b.text];
    words.forEach((tx, i) => {
      const n = el('text', { x: b.cx, y: b.y + 4 + (i - (words.length - 1) / 2) * 13, 'text-anchor': 'middle', 'font-size': 12 }, g);
      n.textContent = tx;
    });
    g.addEventListener('click', () => explain(b.key));
    g.addEventListener('keydown', (e) => {
      if ((e as KeyboardEvent).key === 'Enter' || (e as KeyboardEvent).key === ' ') {
        e.preventDefault();
        explain(b.key);
      }
    });
  }
  [EX, DX].forEach((x, i) => {
    // ⊕ and the sine glyph of the positional encoding.
    const g = el('g', { class: 'blk', 'data-id': `pe${i}`, 'data-k': 'pe', tabindex: 0, role: 'button', 'aria-label': 'Positional Encoding' }, L.blocks);
    el('circle', { cx: x, cy: PE_Y, r: 9, fill: '#fff', stroke: '#222', 'stroke-width': 1.3 }, g);
    el('path', { d: `M${x - 6},${PE_Y} L${x + 6},${PE_Y} M${x},${PE_Y - 6} L${x},${PE_Y + 6}`, stroke: '#222', 'stroke-width': 1.3 }, g);
    const sx = i === 0 ? x - 52 : x + 52;
    el('circle', { cx: sx, cy: PE_Y, r: 14, fill: '#fff', stroke: '#222', 'stroke-width': 1.2 }, g);
    el('path', { d: `M${sx - 10},${PE_Y} C${sx - 6},${PE_Y - 12} ${sx - 2},${PE_Y - 12} ${sx},${PE_Y} S${sx + 6},${PE_Y + 12} ${sx + 10},${PE_Y}`, fill: 'none', stroke: '#222', 'stroke-width': 1.2 }, g);
    el('path', { d: `M${sx + (i === 0 ? 14 : -14)},${PE_Y} L${x + (i === 0 ? -9 : 9)},${PE_Y}`, class: 'wire on', 'data-id': `pew${i}` }, L.wires);
    g.addEventListener('click', () => explain('pe'));
    g.addEventListener('keydown', (e) => {
      if ((e as KeyboardEvent).key === 'Enter' || (e as KeyboardEvent).key === ' ') {
        e.preventDefault();
        explain('pe');
      }
    });
  });
  for (const l of labels) {
    const n = el('text', { x: l.x, y: l.y, 'text-anchor': l.anchor, 'font-size': l.size, 'font-weight': l.weight, class: 'lbl', 'data-id': l.id }, L.labels);
    n.textContent = l.text;
  }
  const chips = (arr: string[], cx: number, y: number, id: string): void => {
    const g = el('g', { class: 'lbl', 'data-id': id }, L.labels);
    let x = cx - arr.reduce((s, tk) => s + tk.length * 6.2 + 10, 0) / 2;
    for (const tk of arr) {
      const w = tk.length * 6.2 + 6;
      el('rect', { x, y, width: w, height: 15, rx: 3, fill: '#e2f7f1', stroke: '#0a7d63', 'stroke-width': 0.8 }, g);
      const n = el('text', { x: x + w / 2, y: y + 11, 'text-anchor': 'middle', class: 'tok' }, g);
      n.textContent = tk;
      x += w + 4;
    }
  };
  chips(SRC, EX, 700, 'srcTok');
  chips(TGT, DX, 700, 'tgtTok');
  const outTok = el('text', { x: DX, y: 22, 'text-anchor': 'middle', class: 'lbl tok', 'font-size': 13, 'data-id': 'next', fill: '#0a7d63' }, L.labels);

  // ---- reveal order (bottom → top, like reading the figure)
  const order = [
    ['srcTok', 'in', 'w_in', 'eEmb', 'w_e1', 'pe0', 'pew0', 'pe1', 'pe1b'],
    ['w_e2', 'eFrame', 'f_e_0', 'f_e_1', 'f_e_2', 'eMha', 'r_e1', 'w_e3', 'eN1'],
    ['w_e4', 'eFf', 'r_e2', 'w_e5', 'eN2', 'eNx'],
    ['tgtTok', 'out', 'w_out', 'dEmb', 'w_d1', 'pe1', 'pew1', 'pe2', 'pe2b'],
    ['w_d2', 'dFrame', 'f_d_0', 'f_d_1', 'f_d_2', 'dMm', 'r_d1', 'w_d3', 'dN1'],
    ['x_enc', 'x_enc2', 'x_q', 'w_d4', 'dX', 'r_d2', 'w_d5', 'dN2'],
    ['w_d6', 'dFf', 'r_d3', 'w_d7', 'dN3', 'dNx'],
    ['w_d8', 'lin', 'w_d9', 'soft', 'w_d10', 'prob', 'next'],
  ];
  const tellAt: BlockKey[] = ['emb', 'mha', 'ff', 'emb', 'mmha', 'xatt', 'nx', 'soft'];
  const reveal = (i: number, tell = true): void => {
    for (const id of order[i]!) svg.querySelectorAll(`[data-id="${id}"]`).forEach((n) => n.classList.add('on'));
    if (tell) explain(tellAt[i]!);
  };

  // ---- pulses: tokens flowing through the network (decorative; Math.random is fine outside the sim)
  const flowPaths = [
    ['w_in', 'w_e1', 'w_e2', 'w_e3', 'w_e4', 'w_e5', 'x_enc'],
    ['w_out', 'w_d1', 'w_d2', 'w_d3', 'w_d4', 'w_d5', 'w_d6', 'w_d7', 'w_d8', 'w_d9', 'w_d10'],
  ];
  let flowing = false;
  let raf = 0;
  const pulseLoop = (): void => {
    if (reduced) return; // final state only: no moving dots
    flowing = true;
    const live: { segs: SVGPathElement[]; total: number; dot: SVGElement; t0: number }[] = [];
    const spawn = (chain: string[]): void => {
      const segs = chain.map((id) => svg.querySelector<SVGPathElement>(`path[data-id="${id}"]`)).filter((p): p is SVGPathElement => !!p);
      const total = segs.reduce((s, p) => s + p.getTotalLength(), 0);
      const dot = el('circle', { r: 3.4, class: 'pulse' }, L.pulses);
      live.push({ segs, total, dot, t0: performance.now() });
    };
    const loop = (now: number): void => {
      if (!flowing) return;
      if (live.length < 14 && Math.random() < 0.06) spawn(flowPaths[Math.random() < 0.5 ? 0 : 1]!);
      for (let i = live.length - 1; i >= 0; i--) {
        const p = live[i]!;
        let dist = (now - p.t0) * 0.16;
        if (dist < 0) continue;
        if (dist > p.total) {
          p.dot.remove();
          live.splice(i, 1);
          continue;
        }
        let s = 0;
        while (s < p.segs.length && dist > p.segs[s]!.getTotalLength()) {
          dist -= p.segs[s]!.getTotalLength();
          s++;
        }
        const pt = p.segs[Math.min(s, p.segs.length - 1)]!.getPointAtLength(dist);
        p.dot.setAttribute('cx', String(pt.x));
        p.dot.setAttribute('cy', String(pt.y));
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
  };

  const buildAttn = (): void => {
    attnGrid.replaceChildren();
    attnGrid.style.gridTemplateColumns = `92px repeat(${SRC.length}, 1fr)`;
    attnGrid.append(h('div'), ...SRC.map((s) => h('div', 'c-head', s)));
    ATT.forEach((rowW, r) => {
      attnGrid.append(h('div', '', ROWS[r]!));
      for (const w of rowW) {
        const c = h('div', 'c');
        c.style.opacity = String(0.08 + w * 0.92);
        attnGrid.append(c);
      }
    });
  };

  const type = (text: string, speed: number, done: () => void): void => {
    let i = 0;
    const caret = h('span', 'intro-caret');
    const shown = document.createTextNode('');
    typed.replaceChildren(shown, caret);
    const step = (): void => {
      i++;
      shown.data = text.slice(0, i);
      if (i < text.length) timers.push(window.setTimeout(step, reduced ? 0 : speed));
      else done();
    };
    step();
  };

  // ---------------------------------------------------------------- timeline
  const stop = (): void => {
    timers.splice(0).forEach((x) => window.clearTimeout(x));
    flowing = false;
    cancelAnimationFrame(raf);
    L.pulses.replaceChildren();
  };
  const showGarage = (focus: boolean): void => {
    garage.classList.add('on');
    if (focus) startBtn.focus();
  };

  const play = (): void => {
    stop();
    listing.style.opacity = '1';
    paperWrap.classList.remove('on');
    figWrap.classList.remove('on');
    attn.classList.remove('on');
    garage.classList.remove('on');
    svg.querySelectorAll('.on').forEach((n) => {
      if (!n.matches('[data-id^="pew"]')) n.classList.remove('on');
    });
    explainDefault();
    outTok.textContent = '';
    meta.textContent = '';
    type(PAPER_TITLE, 55, () => {
      meta.textContent = PAPER_META;
      later(1700, () => {
        listing.style.opacity = '0';
        paperWrap.classList.add('on');
      });
      later(3600, () => figWrap.classList.add('on'));
      order.forEach((_, i) => later(4200 + i * 1250, () => reveal(i)));
      const end = 4200 + order.length * 1250;
      later(end, () => {
        pulseLoop();
        buildAttn();
        attn.classList.add('on');
        NEXT_WORDS.forEach((w, i) => later(i * 900, () => (outTok.textContent = t('intro.fig.next', { w }))));
      });
      later(end + 9000, () => showGarage(true));
    });
  };

  /** Final state at once: paper, full figure, matrix and the hand-off card. */
  const skip = (): void => {
    stop();
    listing.style.opacity = '0';
    paperWrap.classList.add('on');
    figWrap.classList.add('on');
    order.forEach((_, i) => reveal(i, false));
    explainDefault();
    outTok.textContent = t('intro.fig.next', { w: NEXT_WORDS[0]! });
    buildAttn();
    attn.classList.add('on');
    pulseLoop();
    showGarage(true);
  };

  // ---------------------------------------------------------------- input
  replayBtn.addEventListener('click', play);
  skipBtn.addEventListener('click', skip);
  figureBtn.addEventListener('click', () => {
    garage.classList.remove('on');
    skipBtn.hidden = false; // the way back to the card, even when the intro was not skippable
    skipBtn.focus();
  });
  const onKey = (e: KeyboardEvent): void => {
    if (e.key !== 'Escape' || !opts.skippable) return;
    if (garage.classList.contains('on')) return;
    e.preventDefault();
    skip();
  };
  window.addEventListener('keydown', onKey);

  const showError = (msg: string): void => {
    err.textContent = msg;
    input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  };
  input.addEventListener('input', () => {
    if (err.textContent) showError('');
  });
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const r = validateLabName(input.value);
    if (!r.ok) {
      showError(t(r.reason === 'short' ? 'intro.name.short' : 'intro.name.long', { min: LAB_NAME_MIN, max: LAB_NAME_MAX }));
      input.focus();
      return;
    }
    if (disposed) return;
    handle.dispose();
    opts.onDone(r.name);
  });

  // Reduced motion: the final state straight away (the card still waits for the player).
  if (reduced) skip();
  else play();

  const handle: IntroHandle = {
    dispose() {
      if (disposed) return;
      disposed = true;
      stop();
      window.removeEventListener('keydown', onKey);
      root.replaceChildren();
    },
  };
  return handle;
}
