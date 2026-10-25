import type { RigModel } from '../sim/types';

/** Name of the empty that mounts GPU number `index` in a rig GLB (SLOT_gpu_0 … SLOT_gpu_{gpuSlots-1}). Pure, no WebGL. */
export function slotFor(rig: Pick<RigModel, 'id' | 'gpuSlots'>, index: number): string {
  if (!Number.isInteger(index) || index < 0 || index >= rig.gpuSlots) {
    throw new RangeError(`slotFor: ${rig.id} has ${rig.gpuSlots} GPU slots, got index ${index}`);
  }
  return `SLOT_gpu_${index}`;
}
