import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { slotFor } from '../src/render/slots';

const d = loadData(structuredClone({ hardware, world, products, pulso }));
const rig = (id: 'tower_2017' | 'open_frame') => {
  const r = d.rigs.find((x) => x.id === id);
  if (!r) throw new Error(`missing rig ${id}`);
  return r;
};

describe('slotFor', () => {
  it('names the tower slots SLOT_gpu_0 and SLOT_gpu_1', () => {
    expect(slotFor(rig('tower_2017'), 0)).toBe('SLOT_gpu_0');
    expect(slotFor(rig('tower_2017'), 1)).toBe('SLOT_gpu_1');
  });

  it('names the open frame slots SLOT_gpu_0 to SLOT_gpu_5', () => {
    const names = [0, 1, 2, 3, 4, 5].map((i) => slotFor(rig('open_frame'), i));
    expect(names).toEqual(['SLOT_gpu_0', 'SLOT_gpu_1', 'SLOT_gpu_2', 'SLOT_gpu_3', 'SLOT_gpu_4', 'SLOT_gpu_5']);
  });

  it('throws past the rig maximum', () => {
    expect(() => slotFor(rig('tower_2017'), 2)).toThrow(/tower_2017/);
    expect(() => slotFor(rig('open_frame'), 6)).toThrow(/open_frame/);
  });

  it('throws on negative or fractional indices', () => {
    expect(() => slotFor(rig('tower_2017'), -1)).toThrow();
    expect(() => slotFor(rig('open_frame'), 1.5)).toThrow();
  });
});
