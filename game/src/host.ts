import { advance, applyCommand } from './sim';
import type { GameData, GameState } from './sim';
import type { FromWorker, Speed, ToWorker } from './protocol';

export interface SimHost {
  handle(msg: ToWorker): FromWorker | null;
}

/** Pure, DOM-free owner of the GameState and the real-time accumulator (ruling R15). worker.ts only wraps it. */
export function createSimHost(data: GameData): SimHost {
  const msPerHour = data.world.clock.weekRealMs.value / 168;
  const maxTickMs = data.world.clock.maxTickMs.value;
  let state: GameState | null = null;
  let speed: Speed = 0;
  let acc = 0; // fractional game hours

  return {
    handle(msg) {
      switch (msg.t) {
        case 'init':
          state = msg.state;
          acc = 0;
          return null;
        case 'speed':
          speed = msg.x;
          return null;
        case 'cmd':
          if (!state) return null;
          state = applyCommand(state, data, msg.cmd);
          return { t: 'state', state };
        case 'tick': {
          if (!state || state.outcome !== null) return null;
          const eff = state.power.breakerTripped ? Math.min(speed, 1) : speed;
          const ms = Number.isFinite(msg.realMs) ? Math.min(Math.max(msg.realMs, 0), maxTickMs) : 0;
          if (eff === 0 || ms === 0) return null;
          acc += (ms * eff) / msPerHour;
          const hours = Math.floor(acc);
          if (hours < 1) return null;
          acc -= hours;
          state = advance(state, data, hours);
          return { t: 'state', state };
        }
      }
    },
  };
}
