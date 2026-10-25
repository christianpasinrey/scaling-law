import { pushPulso } from './pulsoLog';
import type { Rng } from './rng';
import type { GameData, GameState, OwnedGpu } from './types';

/** Performance multiplier of a GPU: 1 (normal), 0.7 (throttled) or 0 (shut down). */
export function gpuPerfFactor(g: OwnedGpu): number {
  return g.perf;
}

/** Fraction of full power a GPU draws: 1 when working or rented, 0 when idle, shut down or the breaker is out. */
function loadOf(s: GameState, g: OwnedGpu): number {
  if (s.power.breakerTripped || g.perf === 0) return 0;
  const a = s.allocation[g.id];
  return a === 'train' || a === 'serve' || a === 'rent' ? 1 : 0;
}

/**
 * Hourly: power draw, circuit breaker, GPU temperatures and throttling.
 * Loads come from the current allocation and perf; if the draw exceeds the circuit the
 * breaker trips and this very step already runs with every load at 0.
 */
export function stepPower(s: GameState, d: GameData, _rng: Rng): GameState {
  const w = d.world;
  const rigBase = (rigId: string): number => {
    const owned = s.rigs.find((r) => r.id === rigId);
    return d.rigs.find((r) => r.id === owned?.model)?.baseWatts ?? 0;
  };
  const gpuWatts = (g: OwnedGpu): number => d.gpus.find((m) => m.id === g.model)?.watts.value ?? 0;
  const draw = (cur: GameState): number =>
    cur.rigs.reduce((sum, r) => sum + rigBase(r.id), 0) +
    cur.gpus.reduce((sum, g) => sum + gpuWatts(g) * loadOf(cur, g), 0);

  let cur = s;
  let watts = draw(cur);
  if (!cur.power.breakerTripped && watts > w.circuitWatts) {
    cur = pushPulso({ ...cur, power: { ...cur.power, breakerTripped: true } }, d, {
      id: `outage:power:${cur.hour}`,
      hour: cur.hour,
      cause: 'outage',
      text: 'Han saltado los plomos (magnetotérmico): el garaje pidió más de lo que aguanta el circuito.',
      count: 1,
      focus: { kind: 'power' },
    });
    watts = draw(cur);
  }

  const t = w.thermal;
  const gpus = cur.gpus.map((g): OwnedGpu => {
    const rigModel = d.rigs.find((r) => r.id === cur.rigs.find((x) => x.id === g.rigId)?.model);
    const neighbours = cur.gpus.filter((o) => o.rigId === g.rigId).length - 1;
    const perNeighbour = rigModel?.id === 'open_frame' ? t.neighbourOpenFrameC.value : t.neighbourTowerC.value;
    const target = t.baseC.value + t.perLoadC.value * loadOf(cur, g) + perNeighbour * neighbours;
    const tempC = g.tempC + (target - g.tempC) * t.smoothing.value;
    let perf: OwnedGpu['perf'];
    if (g.perf === 0) perf = tempC < t.recoverBelowC.value ? 1 : 0;
    else if (tempC >= w.throttle.shutdownC.value) perf = 0;
    else if (tempC >= w.throttle.throttleC.value) perf = 0.7;
    else perf = 1;
    return { ...g, tempC, perf };
  });

  return { ...cur, gpus, power: { ...cur.power, watts, weekKwh: cur.power.weekKwh + watts / 1000 } };
}
