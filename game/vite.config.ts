import { defineConfig } from 'vite';

export default defineConfig({
  base: '/scaling-law/',
  worker: { format: 'es' },
  build: { target: 'es2022' },
});
