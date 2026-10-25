// Trabajos: training jobs (progress, checkpoint marker, loss), the translation product and its price,
// consulting offers, compute grants and the seed round.
import type { GameState, TrainingJob } from '../sim';
import { el, learnButton, sectionHead, setAttr, setHidden, setText } from './dom';
import type { PanelDeps } from './dom';
import { confirmDialog } from './dialog';
import { formatDecimal, formatHours, formatInt, formatUsd, fraction, jobEtaHours, lossPolyline, t, trainingRate, weeklyRevenueEstimate } from './format';

export interface JobsApi {
  update(s: GameState): void;
  /** Scrolls to the product and focuses its price input. */
  focusProduct(): void;
}

const LOSS_W = 120;
const LOSS_H = 34;
const SVG_NS = 'http://www.w3.org/2000/svg';

interface JobRow {
  status: HTMLElement;
  fill: HTMLElement;
  ckpt: HTMLElement;
  bar: HTMLElement;
  progress: HTMLElement;
  rate: HTMLElement;
  start: HTMLButtonElement;
  note: HTMLElement;
  lossWrap: HTMLElement;
  line: SVGPolylineElement;
  lossText: HTMLElement;
}

export function mount(root: HTMLElement, deps: PanelDeps, dialogRoot: HTMLElement): JobsApi {
  const d = deps.data;
  const tr = d.products.translation;
  const loss = d.products.training.loss;
  const lossLo = loss.floor.value;
  const lossHi = loss.floor.value + loss.start.value;

  // ---- training jobs
  const jobsList = el('ul', { class: 'cards' });
  const jobRows = new Map<TrainingJob['id'], JobRow>();
  for (const id of ['replicate_paper', 'translation_v2'] as const) {
    const status = el('span', { class: 'badge' });
    const fill = el('div', { class: 'bar-fill' });
    const ckpt = el('div', { class: 'bar-ckpt', title: '' });
    const bar = el('div', { class: 'bar', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-label': t(`jobs.job.${id}`) }, fill, ckpt);
    const progress = el('span', { class: 'num small' });
    const rate = el('p', { class: 'small muted' });
    const note = el('p', { class: 'small warn-text' });
    const start = el('button', { type: 'button', class: 'btn btn-primary' }, t('jobs.start'));
    const title = el('strong', { tabindex: '-1' }, t(`jobs.job.${id}`));
    start.addEventListener('click', () => {
      // The button hides once the job runs: keep keyboard focus in the card instead of dropping it on <body>.
      if (document.activeElement === start) title.focus();
      deps.send({ t: 'start_job', jobId: id });
    });
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('viewBox', `0 0 ${LOSS_W} ${LOSS_H}`);
    svg.setAttribute('width', String(LOSS_W));
    svg.setAttribute('height', String(LOSS_H));
    svg.setAttribute('class', 'loss-svg');
    svg.setAttribute('role', 'img');
    const line = document.createElementNS(SVG_NS, 'polyline');
    svg.append(line);
    const lossText = el('span', { class: 'num small' });
    const lossWrap = el('div', { class: 'loss' }, svg, el('span', { class: 'row' }, lossText, learnButton(deps, 'loss')));
    jobsList.append(
      el(
        'li',
        { class: 'card' },
        el('div', { class: 'card-head' }, title, status),
        el('div', { class: 'row' }, bar, learnButton(deps, 'checkpoint')),
        progress,
        rate,
        lossWrap,
        note,
        el('div', { class: 'card-foot' }, start),
      ),
    );
    jobRows.set(id, { status, fill, ckpt, bar, progress, rate, start, note, lossWrap, line: line as SVGPolylineElement, lossText });
  }

  // ---- product
  const productBox = el('div', { class: 'card', id: 'product' });
  const notLaunched = el('p', { class: 'muted small' }, t('jobs.product.notLaunched'));
  const kv = (label: string): [HTMLElement, HTMLElement] => {
    const v = el('dd', { class: 'num' });
    return [el('div', { class: 'kv' }, el('dt', {}, label), v), v];
  };
  const [kCust, vCust] = kv(t('jobs.product.customers'));
  const [kDem, vDem] = kv(t('jobs.product.demand'));
  const [kLat, vLat] = kv(t('jobs.product.latency'));
  const [kSat, vSat] = kv(t('jobs.product.satisfaction'));
  const stats = el('dl', { class: 'kvs' }, kCust, kDem, kLat, kSat);
  const priceId = 'price-input';
  const priceInput = el('input', {
    id: priceId,
    type: 'number',
    inputmode: 'decimal',
    min: String(tr.minPriceUsdPerMChars.value),
    max: String(tr.maxPriceUsdPerMChars.value),
    step: '0.5',
    class: 'num',
    'aria-describedby': 'price-effect',
  });
  const applyBtn = el('button', { type: 'submit', class: 'btn' }, t('jobs.product.apply'));
  const priceForm = el('form', { class: 'price-form' }, el('label', { for: priceId }, t('jobs.product.price')), el('div', { class: 'row' }, priceInput, applyBtn));
  let editing = false;
  const apply = (): void => {
    const v = Number(priceInput.value.replace(',', '.'));
    deps.send({ t: 'set_price', usdPerMChars: v });
    editing = false;
  };
  priceForm.addEventListener('submit', (e) => {
    e.preventDefault();
    apply();
  });
  priceInput.addEventListener('input', () => {
    editing = true;
  });
  const effect = el(
    'p',
    { id: 'price-effect', class: 'small muted' },
    t('jobs.product.priceEffect', {
      ref: formatInt(tr.defaultPriceUsdPerMChars.value),
      complain: formatInt(tr.defaultPriceUsdPerMChars.value * d.pulso.thresholds.priceFactor.value),
      min: formatInt(tr.minPriceUsdPerMChars.value),
      max: formatInt(tr.maxPriceUsdPerMChars.value),
    }),
  );
  const estimate = el('p', { class: 'small num' });
  const launchedBox = el('div', {}, stats, priceForm, effect, estimate);
  productBox.append(sectionHead(deps, t('jobs.product'), 'translation_api'), notLaunched, launchedBox);

  // ---- consulting, grants, round
  const consultList = el('ul', { class: 'plain' });
  const consultNone = el('p', { class: 'muted small' }, t('jobs.consulting.none'));
  const grantList = el('ul', { class: 'plain' });
  const grantNone = el('p', { class: 'muted small' }, t('jobs.grants.none'));
  const roundBox = el('div', { class: 'card round', hidden: true });

  root.append(
    sectionHead(deps, t('jobs.training'), 'training'),
    jobsList,
    productBox,
    sectionHead(deps, t('jobs.consulting'), 'consulting'),
    consultNone,
    consultList,
    sectionHead(deps, t('jobs.grants'), 'grant'),
    grantNone,
    grantList,
    roundBox,
  );

  let offersKey = '';
  let roundKey = '';

  function renderOffers(s: GameState): void {
    const k = JSON.stringify([s.contracts, s.grants]);
    if (k === offersKey) return;
    offersKey = k;
    const hadFocus = root.contains(document.activeElement) && (consultList.contains(document.activeElement) || grantList.contains(document.activeElement));
    consultList.replaceChildren(
      ...s.contracts
        .filter((c) => c.status !== 'done')
        .map((c) => {
          if (c.status === 'active') return el('li', { class: 'small' }, t('jobs.consulting.active', { usd: formatUsd(c.usd), weeks: c.weeksLeft }));
          const b = el('button', { type: 'button', class: 'btn btn-primary' }, t('jobs.consulting.accept'));
          b.addEventListener('click', () => deps.send({ t: 'accept_contract', contractId: c.id }));
          return el('li', { class: 'offer' }, el('span', { class: 'num' }, t('jobs.consulting.offer', { usd: formatUsd(c.usd), weeks: c.weeksTotal })), b);
        }),
    );
    setHidden(consultNone, consultList.childElementCount > 0);
    grantList.replaceChildren(
      ...s.grants.map((g) => {
        if (g.status === 'active') return el('li', { class: 'small' }, t('jobs.grant.active', { hours: formatInt(g.hoursLeft), weeks: g.weeksLeft }));
        if (g.status === 'expired') return el('li', { class: 'small muted' }, t('jobs.grant.expired'));
        const b = el('button', { type: 'button', class: 'btn btn-primary' }, t('jobs.grant.apply'));
        b.addEventListener('click', () => deps.send({ t: 'apply_grant', grantId: g.id }));
        return el('li', { class: 'offer' }, el('span', {}, t('jobs.grant.offer', { p: formatDecimal(g.p100eq, 1), weeks: g.weeksLeft, hours: formatInt(g.hoursLeft) })), b);
      }),
    );
    setHidden(grantNone, s.grants.length > 0);
    if (hadFocus) (consultList.querySelector('button') ?? grantList.querySelector('button') ?? consultNone)?.focus?.();
  }

  function renderRound(s: GameState): void {
    const k = s.round ? `${s.round.status}:${s.round.offeredHour}` : '';
    if (k === roundKey) return;
    roundKey = k;
    setHidden(roundBox, !s.round);
    if (!s.round) return;
    const sr = d.world.seedRound;
    const vars = { raise: formatUsd(sr.raiseUsd.value), pre: formatUsd(sr.preMoneyUsd.value), dil: formatDecimal(sr.dilution.value * 100, 1), lab: s.labName };
    if (s.round.status === 'declined') {
      roundBox.replaceChildren(sectionHead(deps, t('jobs.round'), 'funding_round'), el('p', { class: 'small muted' }, t('jobs.round.declined')));
      return;
    }
    const accept = el('button', { type: 'button', class: 'btn btn-primary' }, t('jobs.round.accept'));
    const decline = el('button', { type: 'button', class: 'btn' }, t('jobs.round.decline'));
    accept.addEventListener('click', () => {
      void confirmDialog(dialogRoot, { title: t('jobs.round.confirm.title'), body: t('jobs.round.confirm.body', vars) }).then((ok) => {
        if (ok) deps.send({ t: 'accept_round' });
      });
    });
    decline.addEventListener('click', () => deps.send({ t: 'decline_round' }));
    roundBox.replaceChildren(
      sectionHead(deps, t('jobs.round'), 'funding_round'),
      el('p', { class: 'small' }, t('jobs.round.offer', vars), ' ', learnButton(deps, 'dilution')),
      el('div', { class: 'card-foot' }, decline, accept),
    );
  }

  return {
    update(s) {
      const rate = trainingRate(s, d);
      const trainers = s.gpus.some((g) => s.allocation[g.id] === 'train');
      for (const job of s.jobs) {
        const r = jobRows.get(job.id);
        if (!r) continue;
        setText(r.status, t(`jobs.status.${job.status}`));
        r.status.dataset.status = job.status;
        const p = fraction(job.doneP100h, job.workP100h);
        const c = fraction(job.checkpointP100h, job.workP100h);
        r.fill.style.width = `${(p * 100).toFixed(1)}%`;
        r.ckpt.style.left = `${(c * 100).toFixed(1)}%`;
        setHidden(r.ckpt, job.status !== 'running' || c <= 0);
        setAttr(r.ckpt, 'title', t('jobs.checkpoint', { pct: formatInt(c * 100) }));
        setAttr(r.bar, 'aria-valuenow', (p * 100).toFixed(0));
        setAttr(r.bar, 'aria-valuetext', `${formatInt(p * 100)} % · ${t('jobs.checkpoint', { pct: formatInt(c * 100) })}`);
        setText(r.progress, t('jobs.progress', { done: formatDecimal(job.doneP100h, 1), work: formatInt(job.workP100h) }));
        if (job.status === 'running') {
          const eta = jobEtaHours(job, rate);
          setText(r.rate, eta === null ? t('jobs.rate.none') : t('jobs.rate', { rate: formatDecimal(rate, 2), eta: formatHours(eta) }));
        } else setText(r.rate, '');
        setHidden(r.rate, job.status !== 'running');
        setHidden(r.start, job.status !== 'ready');
        const note = job.status === 'locked' ? t('jobs.locked.translation_v2') : (job.status === 'ready' || job.status === 'running') && !trainers ? t('jobs.noTrainers') : '';
        setText(r.note, note);
        setHidden(r.note, note === '');
        r.note.classList.toggle('muted', job.status === 'locked');
        // Loss mini-chart (same didactic curve the brain draws).
        const has = job.lossCurve.length > 0;
        setHidden(r.lossWrap, !has);
        if (has) {
          const pts = lossPolyline(job.lossCurve.length === 1 ? [job.lossCurve[0]!, job.lossCurve[0]!] : job.lossCurve, LOSS_W, LOSS_H, lossLo, lossHi);
          if (r.line.getAttribute('points') !== pts) r.line.setAttribute('points', pts);
          const last = formatDecimal(job.lossCurve[job.lossCurve.length - 1]!, 2);
          setText(r.lossText, t('jobs.loss', { v: last }));
          r.line.parentElement?.setAttribute('aria-label', t('jobs.loss.aria', { n: job.lossCurve.length, v: last }));
        }
      }

      const pr = s.product;
      setHidden(notLaunched, pr.launched);
      setHidden(launchedBox, !pr.launched);
      if (pr.launched) {
        setText(vCust, formatInt(pr.customers));
        setText(vDem, t('jobs.product.demandVal', { demand: formatDecimal(pr.demandMCharsH, 1), served: formatDecimal(pr.servedMCharsH, 1) }));
        setText(vLat, `${formatInt(pr.latencyMs)} ms`);
        vLat.classList.toggle('warn', pr.latencyMs > d.pulso.thresholds.latencyMs.value);
        setText(vSat, `${formatInt(pr.satisfaction * 100)} %`);
        if (!editing && document.activeElement !== priceInput) {
          const v = String(pr.priceUsdPerMChars);
          if (priceInput.value !== v) priceInput.value = v;
        }
        setText(estimate, t('jobs.product.estimate', { usd: formatUsd(weeklyRevenueEstimate(s)) }));
      }
      renderOffers(s);
      renderRound(s);
    },
    focusProduct() {
      productBox.scrollIntoView({ block: 'start' });
      if (!launchedBox.hidden) {
        priceInput.focus();
      } else {
        productBox.setAttribute('tabindex', '-1');
        productBox.focus();
      }
    },
  };
}
