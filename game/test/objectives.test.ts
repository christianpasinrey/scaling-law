import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData, newGame } from '../src/sim';
import type { GameState } from '../src/sim';
import { currentObjective } from '../src/ui/objectives';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const fresh = (): GameState => newGame(d, 3, 'Lab');
const replicated = (s: GameState): GameState => ({
  ...s,
  jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'done' as const, doneP100h: j.workP100h } : j)),
  product: { ...s.product, launched: true },
  reputation: 15,
});
const serving = (s: GameState): GameState => ({ ...s, allocation: { ...s.allocation, 'gpu-1': 'serve' } });

describe('currentObjective', () => {
  it('1 · replicate the paper, with the job progress', () => {
    const s = fresh();
    const o = currentObjective({ ...s, jobs: s.jobs.map((j) => (j.id === 'replicate_paper' ? { ...j, status: 'running' as const, doneP100h: 24 } : j)) }, d);
    expect(o.id).toBe('replicate');
    expect(o.step).toBe(1);
    expect(o.text).toBe('Replicar el paper');
    expect(o.progress).toEqual([{ label: 'P100-h', done: 24, total: 96 }]);
    expect(o.panel).toBe('jobs');
  });

  it('2 · launch the API until it is launched and at least one GPU serves', () => {
    const o = currentObjective(replicated(fresh()), d);
    expect(o.id).toBe('launch');
    expect(o.text).toBe('Lanzar tu API de traducción');
    expect(o.progress).toBeUndefined();
    expect(o.panel).toBe('alloc');
  });

  it('3 · 300 customers and reputation 30, two progress values from data', () => {
    const s = serving(replicated(fresh()));
    const o = currentObjective({ ...s, product: { ...s.product, customers: 123.7 } }, d);
    expect(o.id).toBe('grow');
    expect(o.text).toBe('Conseguir 300 clientes y reputación 30');
    expect(o.progress).toEqual([
      { label: 'clientes', done: 123, total: 300 },
      { label: 'reputación', done: 15, total: 30 },
    ]);
    expect(o.panel).toBe('jobs');
  });

  it('3 · progress is capped at the target and survives NaN-free when only one goal is met', () => {
    const s = serving(replicated(fresh()));
    const o = currentObjective({ ...s, product: { ...s.product, customers: 450 }, reputation: 25 }, d);
    expect(o.id).toBe('grow');
    expect(o.progress?.[0]).toEqual({ label: 'clientes', done: 300, total: 300 });
  });

  it('4 · decide the seed round when it is offered (even if a GPU stopped serving)', () => {
    const s = replicated(fresh());
    const o = currentObjective({ ...s, product: { ...s.product, customers: 320 }, reputation: 30, round: { status: 'offered', offeredHour: 900 } }, d);
    expect(o.id).toBe('round');
    expect(o.step).toBe(4);
    expect(o.text).toBe('Decidir la ronda semilla');
    expect(o.panel).toBe('round');
  });

  it('4 · after declining, waits for the investor to come back', () => {
    const s = serving(replicated(fresh()));
    const o = currentObjective(
      { ...s, product: { ...s.product, customers: 320 }, reputation: 30, round: { status: 'declined', offeredHour: 900, declinedHour: 950 } },
      d,
    );
    expect(o.id).toBe('round');
    expect(o.text).toBe('Ronda rechazada: el inversor puede volver dentro de unas semanas');
    expect(o.panel).toBe('jobs');
  });

  it('done once the game has an outcome', () => {
    expect(currentObjective({ ...fresh(), outcome: 'seed_round' }, d)).toMatchObject({ id: 'done', step: 5, panel: null });
    expect(currentObjective({ ...fresh(), outcome: 'bankrupt' }, d).id).toBe('done');
  });
});
