import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
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

const missing = files.filter((f) => !existsSync(join(src, f)));
if (missing.length > 0) {
  for (const f of missing) {
    console.error(`copy-assets: missing ${f} (expected at ${join(src, f)})`);
  }
  process.exit(1);
}

mkdirSync(dst, { recursive: true });
for (const f of files) {
  copyFileSync(join(src, f), join(dst, f));
  console.log(`copied ${f}`);
}
