import { ACESFilmicToneMapping, PerspectiveCamera, PMREMGenerator, Scene, SRGBColorSpace, Vector3, WebGLRenderer, Color } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export type FrameFn = (dtSeconds: number, timeSeconds: number) => void;

export interface SceneCtx {
  readonly renderer: WebGLRenderer;
  readonly scene: Scene;
  readonly camera: PerspectiveCamera;
  readonly controls: OrbitControls;
  readonly canvas: HTMLCanvasElement;
  /** true when the user asked for reduced motion: no camera auto-motion, no inertia. */
  readonly reducedMotion: boolean;
  /** Registers a per-frame callback; returns its unsubscribe. */
  onFrame(fn: FrameFn): () => void;
  dispose(): void;
}

const IDLE_BEFORE_DRIFT_S = 8;
const DRIFT_AMPLITUDE_RAD = 0.09;
const DRIFT_RATE = 0.12;
const UP = new Vector3(0, 1, 0);

/** Renderer, camera, orbit controls, environment, resize and the single render loop. */
export function createScene(canvas: HTMLCanvasElement): SceneCtx {
  const reducedMotion = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

  const renderer = new WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;

  const scene = new Scene();
  scene.background = new Color(0x0a0908);

  // Dim image-based light so the black hardware still shows its metal and plastic.
  const pmrem = new PMREMGenerator(renderer);
  const envRT = pmrem.fromScene(new RoomEnvironment(), 0.04);
  scene.environment = envRT.texture;
  scene.environmentIntensity = 0.18;
  pmrem.dispose();

  const camera = new PerspectiveCamera(40, 1, 0.05, 30);
  camera.position.set(-1.25, 0.88, -0.8);

  const controls = new OrbitControls(camera, canvas);
  controls.target.set(-0.05, 0.36, -2.05);
  controls.enableDamping = !reducedMotion;
  controls.dampingFactor = 0.08;
  controls.minDistance = 0.45;
  controls.maxDistance = 3.2;
  controls.minPolarAngle = 0.15;
  controls.maxPolarAngle = Math.PI * 0.49; // never below the floor
  controls.minAzimuthAngle = -1.35; // stay in front of the two walls
  controls.maxAzimuthAngle = 1.35;
  controls.enablePan = true;
  controls.screenSpacePanning = true;
  controls.update();

  let idleS = 0;
  let driftApplied = 0;
  const onInteract = (): void => {
    idleS = 0;
    driftApplied = 0; // the user's new pose becomes the drift centre
  };
  controls.addEventListener('start', onInteract);

  const resize = (): void => {
    const w = canvas.clientWidth || window.innerWidth;
    const h = canvas.clientHeight || window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
  };
  const ro = new ResizeObserver(resize);
  ro.observe(canvas);
  resize();

  // Array, not Set: iterating it every frame must not allocate an iterator.
  const frameFns: FrameFn[] = [];
  const offset = new Vector3();
  let last = -1;
  let time = 0;

  renderer.setAnimationLoop((nowMs: number) => {
    const now = nowMs / 1000;
    // Clamp dt so a background tab does not produce a huge jump on return.
    const dt = last < 0 ? 0 : Math.min(now - last, 0.1);
    last = now;
    time += dt;

    if (!reducedMotion) {
      idleS += dt;
      if (idleS > IDLE_BEFORE_DRIFT_S) {
        // Gentle sway around the target, relative to where the user left the camera.
        const want = DRIFT_AMPLITUDE_RAD * Math.sin((idleS - IDLE_BEFORE_DRIFT_S) * DRIFT_RATE);
        offset.copy(camera.position).sub(controls.target).applyAxisAngle(UP, want - driftApplied);
        camera.position.copy(controls.target).add(offset);
        driftApplied = want;
      }
    }
    controls.update();
    for (let i = 0; i < frameFns.length; i++) frameFns[i]!(dt, time);
    renderer.render(scene, camera);
  });

  return {
    renderer,
    scene,
    camera,
    controls,
    canvas,
    reducedMotion,
    onFrame(fn) {
      frameFns.push(fn);
      return () => {
        const i = frameFns.indexOf(fn);
        if (i >= 0) frameFns.splice(i, 1);
      };
    },
    dispose() {
      renderer.setAnimationLoop(null);
      ro.disconnect();
      controls.removeEventListener('start', onInteract);
      controls.dispose();
      envRT.dispose();
      frameFns.length = 0;
      renderer.dispose();
    },
  };
}
