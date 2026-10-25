import { Color, Mesh, MeshStandardMaterial, ShaderMaterial, Vector2 } from 'three';
import type { Material, Object3D } from 'three';

/** What a flow mesh carries (glTF extra `flow_kind`). */
export type FlowKind = 'power' | 'data';

/** 'normal' = cyan pulses; 'warn' = amber (draw above the safe continuous limit); 'off' = breaker tripped, no motion. */
export type FlowMode = 'normal' | 'warn' | 'off';

export interface FlowLine {
  readonly mesh: Mesh;
  readonly name: string;
  readonly kind: FlowKind;
  /** Path length in metres (flow_u_end − flow_u_start). */
  readonly length: number;
}

export interface FlowSet {
  readonly lines: readonly FlowLine[];
  setMode(mode: FlowMode): void;
  /** Advances the pulses; call once per frame. Allocation-free. */
  tick(dtSeconds: number): void;
  dispose(): void;
}

/**
 * Watts carried by a line right now. For 'data' lines any value > 0 means "link active"
 * (they run at a fixed rate and colour).
 */
export type FlowRate = (line: FlowLine) => number;

// Visual tuning (render-only, not simulation constants).
const SPEED_M_PER_S_PER_W = 0.0014; // 250 W ⇒ 0.35 m/s
const MAX_SPEED_M_PER_S = 0.6;
const DATA_SPEED_M_PER_S = 0.18;
const REF_WATTS = 250;
const DASH_SPACING_M = 0.07;
const COLOR_POWER = new Color(0x33e6ff);
const COLOR_WARN = new Color(0xffa424);
const COLOR_DATA = new Color(0xb68cff);

const vertexShader = /* glsl */ `
varying float vU;
varying vec3 vN;
varying vec3 vV;
void main() {
  vU = uv.x;
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  vV = -mv.xyz;
  vN = normalize(normalMatrix * normal);
  gl_Position = projectionMatrix * mv;
}
`;

const fragmentShader = /* glsl */ `
uniform vec3 uBase;
uniform vec3 uColor;
uniform float uPhase;
uniform float uLevel;
uniform float uSpacing;
uniform vec2 uRange;
varying float vU;
varying vec3 vN;
varying vec3 vV;
void main() {
  vec3 n = normalize(vN);
  vec3 v = normalize(vV);
  float diff = 0.3 + 0.7 * max(dot(n, normalize(vec3(0.3, 0.8, 0.5))), 0.0);
  float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0);
  vec3 col = uBase * (diff + 0.6 * rim);
  float inRange = step(uRange.x, vU) * step(vU, uRange.y);
  float d = fract((vU - uPhase) / uSpacing);
  float dash = smoothstep(0.0, 0.1, d) * (1.0 - smoothstep(0.2, 0.42, d));
  col += uColor * inRange * uLevel * (0.08 + 2.4 * dash);
  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;

interface LineState {
  line: FlowLine;
  material: ShaderMaterial;
  previous: Material | Material[];
  phase: number;
}

function baseColorOf(m: Material | Material[]): Color {
  const first = Array.isArray(m) ? m[0] : m;
  const c = first instanceof MeshStandardMaterial ? first.color.clone() : new Color(0x0b0b0c);
  // The sleeve is near black; lift it a little so the cable still reads when no current flows.
  c.r = Math.max(c.r, 0.035);
  c.g = Math.max(c.g, 0.035);
  c.b = Math.max(c.b, 0.04);
  return c;
}

function makeMaterial(base: Color, uStart: number, uEnd: number): ShaderMaterial {
  return new ShaderMaterial({
    name: 'FlowPulse',
    vertexShader,
    fragmentShader,
    uniforms: {
      uBase: { value: base },
      uColor: { value: COLOR_POWER.clone() },
      uPhase: { value: 0 },
      uLevel: { value: 0 },
      uSpacing: { value: DASH_SPACING_M },
      uRange: { value: new Vector2(uStart, uEnd) },
    },
  });
}

/**
 * Replaces the material of every mesh under `root` that carries the glTF extras
 * flow_u_start / flow_u_end (UV u = metres along the path) with an animated pulse shader.
 * Pulse speed ∝ watts reported by `getRate`; colour by mode and kind.
 */
export function applyFlowMaterials(root: Object3D, getRate: FlowRate): FlowSet {
  const states: LineState[] = [];
  root.traverse((o) => {
    if (!(o instanceof Mesh)) return;
    const ud = o.userData as Record<string, unknown>;
    const uStart = ud.flow_u_start;
    const uEnd = ud.flow_u_end;
    if (typeof uStart !== 'number' || typeof uEnd !== 'number') return;
    const kind: FlowKind = ud.flow_kind === 'data' ? 'data' : 'power';
    const previous = o.material;
    const material = makeMaterial(baseColorOf(previous), uStart, uEnd);
    o.material = material;
    states.push({ line: { mesh: o, name: o.name, kind, length: uEnd - uStart }, material, previous, phase: 0 });
  });

  let mode: FlowMode = 'normal';
  const applyColours = (): void => {
    for (const st of states) {
      const target = st.line.kind === 'data' ? COLOR_DATA : mode === 'warn' ? COLOR_WARN : COLOR_POWER;
      (st.material.uniforms.uColor!.value as Color).copy(target);
    }
  };
  applyColours();

  return {
    lines: states.map((s) => s.line),
    setMode(m) {
      if (m === mode) return;
      mode = m;
      applyColours();
    },
    tick(dt) {
      for (let i = 0; i < states.length; i++) {
        const st = states[i]!;
        const u = st.material.uniforms;
        const w = mode === 'off' ? 0 : getRate(st.line);
        let speed = 0;
        let level = 0;
        if (w > 0) {
          if (st.line.kind === 'data') {
            speed = DATA_SPEED_M_PER_S;
            level = 0.8;
          } else {
            speed = Math.min(w * SPEED_M_PER_S_PER_W, MAX_SPEED_M_PER_S);
            level = Math.min(0.35 + (0.65 * w) / REF_WATTS, 1.6);
          }
        }
        st.phase = (st.phase + speed * dt) % DASH_SPACING_M;
        u.uPhase!.value = st.phase;
        u.uLevel!.value = level;
      }
    },
    dispose() {
      for (const st of states) {
        st.line.mesh.material = st.previous;
        st.material.dispose();
      }
      states.length = 0;
    },
  };
}
