import { describe, expect, it } from 'vitest';
import learn from '../data/learn.es.json';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData, newGame } from '../src/sim';
import type { GameState } from '../src/sim';
import { brainCard, conceptsPresent } from '../src/ui/format';
import { parseCards } from '../src/ui/learn';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const cards = parseCards(learn);

const REQUIRED = [
  'gpu', 'vram', 'p100eq', 'training', 'loss', 'checkpoint', 'inference', 'throttling', 'breaker', 'kwh',
  'gpu_rental', 'funding_round', 'dilution', 'data_parallel', 'attention', 'feed_forward', 'layer_norm',
  'embedding', 'softmax', 'translation_api',
];

describe('learn cards', () => {
  it('has every required card', () => {
    for (const id of REQUIRED) expect(cards[id], id).toBeDefined();
  });
  it('every card has the three levels and a source', () => {
    for (const [id, c] of Object.entries(cards)) {
      for (const k of ['title', 'short', 'why', 'deep', 'source'] as const) expect(c[k].trim().length, `${id}.${k}`).toBeGreaterThan(0);
      if (c.link !== undefined) expect(c.link, `${id}.link`).toMatch(/^https:\/\//);
      if (c.game !== undefined) expect(c.game, `${id}.game`).toMatch(/^(En el juego|El juego|La curva del juego|La ronda del juego|Las |Clientes|Cifras)/);
    }
  });
  it('related ids, hardware learn ids, concept triggers and brain blocks all resolve to cards', () => {
    for (const [id, c] of Object.entries(cards)) for (const r of c.related) expect(cards[r], `${id} → ${r}`).toBeDefined();
    for (const g of d.gpus) expect(cards[g.learnId], g.learnId).toBeDefined();
    const s0 = newGame(d, 1, 'Lab');
    const busy: GameState = {
      ...s0,
      hour: 24 * 400, // mid 2018: Titan V and the open frame are out
      gpus: [...s0.gpus, { id: 'gpu-2', model: 'gtx1080ti', rigId: 'rig-1', slot: 1, tempC: 86, perf: 0.7 }],
      allocation: { 'gpu-1': 'train', 'gpu-2': 'train' },
      jobs: s0.jobs.map((j) => ({ ...j, status: 'running' as const, lossCurve: [9, 8] })),
      power: { ...s0.power, breakerTripped: true },
      ledger: [{ week: 1, revenueUsd: 0, costsUsd: 0, cashEndUsd: 0, lines: {} }],
      product: { ...s0.product, launched: true },
      contracts: [{ id: 'c', usd: 1, weeksTotal: 1, weeksLeft: 1, status: 'offered' }],
      grants: [{ id: 'g', p100eq: 1, hoursLeft: 1, weeksLeft: 1, status: 'offered' }],
      round: { status: 'offered', offeredHour: 0 },
    };
    const ids = conceptsPresent(busy, d);
    expect(ids.length).toBeGreaterThan(15);
    for (const id of ids) expect(cards[id], `concept ${id}`).toBeDefined();
    for (const b of ['embed_in', 'enc_0', 'dec_5', 'embed_out', 'head']) expect(cards[brainCard(b)], b).toBeDefined();
  });
  it('the paper is the source of every model-part card', () => {
    for (const id of ['attention', 'feed_forward', 'embedding', 'encoder', 'decoder', 'layer_norm']) {
      expect(cards[id]!.source, id).toContain('1706.03762');
    }
  });
  it('rejects malformed data', () => {
    expect(() => parseCards({ cards: { x: { title: 'x' } } })).toThrow(/x\.short/);
    expect(() => parseCards({ cards: { x: { title: 'x', short: 's', why: 'w', deep: 'd', source: 's', related: ['nope'] } } })).toThrow(/nope/);
  });
});
