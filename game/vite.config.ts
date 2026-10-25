import { defineConfig } from 'vite';

export default defineConfig({
  base: '/scaling-law/',
  // GLBs are served from public/; listing them here lets tests import blender exports with ?inline.
  assetsInclude: ['**/*.glb'],
  worker: { format: 'es' },
  build: { target: 'es2022' },
});
