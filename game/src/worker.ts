import hardware from '../data/hardware.json';
import world from '../data/world.json';
import products from '../data/products.json';
import pulso from '../data/pulso.es.json';
import { loadData } from './sim';
import { createSimHost } from './host';
import type { FromWorker, ToWorker } from './protocol';

const host = createSimHost(loadData({ hardware, world, products, pulso }));

self.onmessage = (e: MessageEvent<ToWorker>) => {
  const out = host.handle(e.data);
  if (out) (self as unknown as { postMessage(m: FromWorker): void }).postMessage(out);
};
