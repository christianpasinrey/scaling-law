import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = join(root, '..', 'blender', 'export');
const dst = join(root, 'public', 'assets');

const files = [
  'rig_01_tower_2017.glb',
  'rig_02_open_frame.glb',
  'gpu_gtx1080ti_fe.glb',
  'gpu_titan_v.glb',
];

mkdirSync(dst, { recursive: true });
for (const f of files) {
  copyFileSync(join(src, f), join(dst, f));
  console.log(`copied ${f}`);
}
