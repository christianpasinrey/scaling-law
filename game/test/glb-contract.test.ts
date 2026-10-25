import { describe, expect, it } from 'vitest';
import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from '../src/sim/data';
import { slotFor } from '../src/render/slots';

// Name contract between the Blender exports and the renderer, checked without WebGL:
// read the glTF JSON chunk of each rig GLB and look for the nodes the garage addresses by name.
const d = loadData(structuredClone({ hardware, world, products, pulso }));
// Inlined as base64 data URLs by Vite (the project has no Node typings, so no fs here).
const glbs = import.meta.glob<string>('../../blender/export/rig_*.glb', { query: '?inline', import: 'default', eager: true });
const exported = (file: string): string | undefined => glbs[`../../blender/export/${file}`];

function nodeNames(file: string): Set<string> {
  const url = exported(file);
  if (!url) throw new Error(`missing export ${file}`);
  const bin = atob(url.slice(url.indexOf(',') + 1));
  const b = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  const v = new DataView(b.buffer);
  expect(v.getUint32(0, true)).toBe(0x46546c67); // 'glTF'
  const jsonLen = v.getUint32(12, true);
  expect(v.getUint32(16, true)).toBe(0x4e4f534a); // 'JSON'
  const gltf = JSON.parse(new TextDecoder().decode(b.subarray(20, 20 + jsonLen))) as { nodes: { name?: string }[] };
  return new Set(gltf.nodes.map((n) => n.name ?? ''));
}

describe('rig GLB name contract', () => {
  for (const rig of d.rigs) {
    it(`${rig.glb} has a SLOT_gpu_n and a Cable_GPU_n for every slot of ${rig.id}`, () => {
      expect(exported(rig.glb), `blender/export/${rig.glb}`).toBeDefined();
      const names = nodeNames(rig.glb);
      for (let i = 0; i < rig.gpuSlots; i++) {
        expect(names, `${rig.glb}: ${slotFor(rig, i)}`).toContain(slotFor(rig, i));
        expect(names, `${rig.glb}: Cable_GPU_${i}`).toContain(`Cable_GPU_${i}`);
      }
      expect(names.has('SOCKET_power_in') || names.has('SOCKET_power_in_0')).toBe(true);
    });
  }

  it('the open frame has a riser cable per slot for the PCIe slot-power split', () => {
    const frame = d.rigs.find((r) => r.id === 'open_frame');
    if (!frame) throw new Error('open_frame missing');
    const names = nodeNames(frame.glb);
    for (let i = 0; i < frame.gpuSlots; i++) expect(names).toContain(`Cable_Riser_${i}`);
  });
});
