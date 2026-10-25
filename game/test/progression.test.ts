import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { advance, applyCommand, newGame } from '../src/sim';
import { stepProgression } from '../src/sim/progression';
import type { GameState } from '../src/sim/types';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const WEEK = 168;
/** Hours from the game start (2017-06-12T17:57Z) to the first whole hour on or after 2017-12-07T00:00Z. */
const TITAN_HOUR = Math.ceil((Date.parse('2017-12-07T00:00:00Z') - Date.parse('2017-06-12T17:57:00Z')) / 3_600_000);

const base = (): GameState => newGame(d, 1, 'Lab');
/** All three seed-round conditions true. */
const ready = (over: Partial<GameState> = {}): GameState => {
  const s = base();
  return {
    ...s,
    jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'done' as const } : j)),
    product: { ...s.product, launched: true, customers: 300 },
    reputation: 30,
    ...over,
  };
};

describe('Titan V news', () => {
  const titan = (s: GameState) => s.pulso.filter((p) => p.cause === 'news' && p.text.includes('Titan V'));

  it('appears exactly once, on the first hour whose date reaches 2017-12-07', () => {
    let s = advance(base(), d, TITAN_HOUR);
    // advance runs progression before the hour ticks over: hour TITAN_HOUR - 1 was the last one stepped.
    expect(titan(s)).toHaveLength(0);
    s = advance(s, d, 1);
    expect(titan(s)).toHaveLength(1);
    expect(titan(s)[0]?.text.startsWith('Sale la Titan V')).toBe(true);
    s = advance(s, d, WEEK * 4);
    expect(titan(s)).toHaveLength(1);
  });

  it('is not emitted twice when stepped repeatedly', () => {
    let s: GameState = { ...base(), hour: TITAN_HOUR + 1 };
    for (let i = 0; i < 5; i++) s = stepProgression({ ...s, hour: s.hour + 100 }, d);
    expect(titan(s)).toHaveLength(1);
  });
});

describe('seed round', () => {
  it('is offered only when replicate_paper is done, customers >= 300 and reputation >= 30', () => {
    expect(stepProgression(ready(), d).round?.status).toBe('offered');
    const lowCust = ready({ product: { ...ready().product, customers: 299 } });
    const lowRep = ready({ reputation: 29 });
    const noJob = ready({ jobs: base().jobs });
    for (const s of [noJob, lowCust, lowRep, base()]) expect(stepProgression(s, d).round).toBeUndefined();
  });

  it('records the offer hour and a news item, and does not re-offer while pending', () => {
    let s = stepProgression({ ...ready(), hour: 500 }, d);
    expect(s.round).toEqual({ status: 'offered', offeredHour: 500 });
    expect(s.pulso.filter((p) => p.cause === 'news')).toHaveLength(1);
    s = stepProgression({ ...s, hour: 501 }, d);
    expect(s.round?.offeredHour).toBe(500);
  });

  it('accepting adds the raise and ends the game with seed_round', () => {
    const s = stepProgression({ ...ready(), cashUsd: 1000 }, d);
    const out = applyCommand(s, d, { t: 'accept_round' });
    expect(out.cashUsd).toBe(1000 + d.world.seedRound.raiseUsd.value);
    expect(out.outcome).toBe('seed_round');
  });

  it('accept/decline without an offer only warn', () => {
    for (const t of ['accept_round', 'decline_round'] as const) {
      const out = applyCommand(base(), d, { t });
      expect(out.outcome).toBeNull();
      expect(out.cashUsd).toBe(base().cashUsd);
      expect(out.pulso.at(-1)?.cause).toBe('warning');
    }
  });

  it('declining withdraws it and it is offered again after 8 weeks', () => {
    let s = stepProgression({ ...ready(), hour: 1000 }, d);
    s = applyCommand({ ...s, hour: 1010 }, d, { t: 'decline_round' });
    expect(s.round?.status).toBe('declined');
    expect(s.outcome).toBeNull();
    const declined = s.round?.declinedHour as number;
    expect(declined).toBe(1010);
    expect(stepProgression({ ...s, hour: declined + 8 * WEEK - 1 }, d).round?.status).toBe('declined');
    const again = stepProgression({ ...s, hour: declined + 8 * WEEK }, d);
    expect(again.round).toEqual({ status: 'offered', offeredHour: declined + 8 * WEEK });
  });

  it('a declined round is not re-offered after 8 weeks if the conditions no longer hold', () => {
    let s = stepProgression({ ...ready(), hour: 1000 }, d);
    s = applyCommand(s, d, { t: 'decline_round' });
    const poorer = { ...s, hour: s.hour + 9 * WEEK, reputation: 10 };
    expect(stepProgression(poorer, d).round?.status).toBe('declined');
  });

  it('the offer flows through advance', () => {
    expect(advance(ready(), d, 1).round?.status).toBe('offered');
  });
});
