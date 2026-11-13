/**
 * xr.js — the headset backend (T-3575). WebXR, the browser's own VR mode.
 *
 * The owner, 2026-11-13: *"What would be the least expensive way to try to add VR
 * style headset navigation to this and try a vr headset"*. The cheapest way is the
 * one with no new build and no app store: the page already draws in a browser, and a
 * headset's browser (the Meta Quest's, a Pico's) or a WebXR emulator extension on a
 * computer offers `navigator.xr`. So this is one more input backend, of the kind
 * intent.js describes, plus the few lines that hand the renderer a session.
 *
 * WHAT IT DOES
 *  - The view is the headset's own: three's WebXRManager draws both eyes from the
 *    headset pose, so looking is turning your head. Nothing here writes the camera.
 *  - Where you stand is still the walker's. The reference space is offset each frame
 *    (`sync`) so its origin sits at the walker's eye — `local`, whose origin is the
 *    head where the session began, so a seated and a standing visitor both see the
 *    town from WALK.eyeHeight. Head bob and the step ease are left out: in a headset
 *    a camera that moves without the head moving is what makes people sick.
 *  - The left stick walks where you look (the walker's collision, step-up rule,
 *    doors and decks all unchanged, since it only writes the intent); its click or
 *    the left grip runs. The right stick turns in SNAP_DEG steps (snap turn is the
 *    comfort default in every headset app) and, flying, rises and descends. A or X
 *    toggles Fly. The headset's own exit, or Exit VR on the page, ends it.
 *  - No stick at all (Google Cardboard's one button, or bare hands on a Quest): the
 *    button — the session's `select` from a source with no thumbstick — starts walking
 *    where you look, and the next press stops (`hasStick`). The owner, 2026-11-13:
 *    *"Could I use Google cardboard with this? I need a controller?"*
 *  - The walker's yaw is steered to the head's only while the stick is pushed: it is
 *    only the direction a step goes, and leaving it alone at rest keeps a ride
 *    (travel.js) from being ended by a visitor who merely looked round.
 *
 * WHAT IT COSTS A DEVICE WITHOUT A HEADSET: nothing. `supported()` asks
 * `isSessionSupported('immersive-vr')`; the key stays hidden where that is false
 * (every phone and computer with no headset or emulator), and no session, no
 * reference space and no per-frame work exist until a visitor presses it.
 *
 * THE RESOLUTION. A standalone headset is a phone inside (main.js boots it as one:
 * the phone's tier and memory diet, its people, horses and carriages kept). Both eyes
 * at the headset's recommended size are some fifteen times the pixels a phone draws
 * at Sharpness Low, so the frame is drawn at VR_SCALE.headset of that size and blurs
 * instead of dropping anything; a computer driving a tethered headset gets
 * VR_SCALE.computer. `?vr-scale=0.3..1` overrides both, for trying a headset by hand.
 *
 * Pure helpers are exported for tools/check_xr_mode.mjs; the session half takes THREE
 * from main.js so this file imports nothing and reads in node.
 */

export const SNAP_DEG = 30;
export const STICK_DEAD = 0.15;
/** Snap fires past ON and re-arms below OFF, so one push is one step. */
export const SNAP_ON = 0.6;
export const SNAP_OFF = 0.3;
export const VR_SCALE = Object.freeze({ headset: 0.6, computer: 1, min: 0.3, max: 1 });

/**
 * A standalone headset's browser, by its user agent: the Quest browser says
 * "OculusBrowser" (and "Quest"), Pico's "PicoBrowser", Wolvic and the Vive Focus
 * browser say so too. Their screens report a fine pointer and a desktop width, so
 * without this they would boot as a computer.
 */
export function isStandaloneHeadset(ua) {
  return /OculusBrowser|\bQuest\b|PicoBrowser|\bPico\b|Wolvic|VR Browser|Vive ?Focus/i.test(String(ua || ''));
}

/** The framebuffer scale for this device, `?vr-scale=` first. */
export function vrScale({ headset = false, search = '' } = {}) {
  let asked = null;
  try { asked = Number(new URLSearchParams(search || '').get('vr-scale')); } catch { asked = null; }
  if (Number.isFinite(asked) && asked > 0) return Math.max(VR_SCALE.min, Math.min(VR_SCALE.max, asked));
  return headset ? VR_SCALE.headset : VR_SCALE.computer;
}

/** A stick axis with its dead zone taken out and the rest rescaled to 0..1. */
export function deadzone(v, dead = STICK_DEAD) {
  const a = Math.abs(Number(v) || 0);
  if (a <= dead) return 0;
  return Math.sign(v) * Math.min(1, (a - dead) / (1 - dead));
}

/**
 * One snap-turn decision. `x` is the right stick's sideways axis (+ right), `armed`
 * whether it has come back to centre since the last step. Returns the yaw to turn
 * (radians, + is left, as the intent has it) and whether the stick is armed after.
 */
export function snapTurn(x, armed, stepDeg = SNAP_DEG) {
  const a = Math.abs(Number(x) || 0);
  if (!armed) return { yaw: 0, armed: a < SNAP_OFF };
  if (a < SNAP_ON) return { yaw: 0, armed: true };
  return { yaw: -Math.sign(x) * stepDeg * (Math.PI / 180), armed: false };
}

/** The smallest signed angle from `from` to `to`, radians. */
export function angleTo(from, to) {
  let d = (to - from) % (2 * Math.PI);
  if (d > Math.PI) d -= 2 * Math.PI;
  if (d < -Math.PI) d += 2 * Math.PI;
  return d;
}

/**
 * Read the controllers into one plain object. xr-standard mapping: axes 2/3 are the
 * thumbstick (the touchpad's 0/1 stand in when there is no stick), buttons 1 squeeze,
 * 3 stick click, 4 A or X, 5 B or Y. With one controller, or one with no handedness,
 * its stick walks.
 */
export function readPads(sources) {
  const out = { move: [0, 0], turn: [0, 0], run: false, fly: false };
  const list = [...(sources || [])].filter((s) => s?.gamepad);
  const left = list.find((s) => s.handedness === 'left') ?? (list.length === 1 ? list[0] : null)
    ?? list.find((s) => s.handedness !== 'right') ?? null;
  const right = list.find((s) => s.handedness === 'right' && s !== left) ?? null;
  const stick = (pad) => {
    const ax = pad?.axes || [];
    const x = ax.length >= 4 ? ax[2] : ax[0];
    const y = ax.length >= 4 ? ax[3] : ax[1];
    return [deadzone(x), deadzone(y)];
  };
  const pressed = (pad, i) => !!pad?.buttons?.[i]?.pressed;
  if (left) {
    out.move = stick(left.gamepad);
    out.run = pressed(left.gamepad, 1) || pressed(left.gamepad, 3);
    out.fly ||= pressed(left.gamepad, 4);
  }
  if (right) {
    out.turn = stick(right.gamepad);
    out.fly ||= pressed(right.gamepad, 4);
  }
  return out;
}

/** Whether an input source has a thumbstick (or touchpad) to walk with. */
export function hasStick(source) {
  return (source?.gamepad?.axes?.length ?? 0) >= 2;
}

/**
 * The headset session and its backend.
 * @param {object} o
 * @param {object} o.THREE      three, from main.js
 * @param {object} o.renderer   the WebGLRenderer
 * @param {object} o.walker     walker.js — `state` is read, never written
 * @param {object} o.intent     the shared intent
 * @param {object} o.backends   intent.js's switch
 * @param {Function} o.fallback the backend to hand back to when the session ends
 * @param {Function} o.setFly   hud.setFly
 * @param {Function} [o.onChange] called with true/false as the session starts and ends
 * @param {number} [o.scale]    the framebuffer scale (vrScale)
 */
export function createXRMode({ THREE, renderer, walker, intent, backends, fallback, setFly, onChange = () => {}, scale = 1, nav = globalThis.navigator }) {
  const xr = nav?.xr ?? null;
  let session = null;
  let base = null;
  let rigYaw = 0;
  let armed = true;
  let flyHeld = false;
  let starting = false;
  let autoWalk = false;
  // T-3575: a stickless source's button (Cardboard, hands) toggles walking on and off.
  const onSelect = (event) => { if (!hasStick(event?.inputSource)) autoWalk = !autoWalk; };
  const last = { x: NaN, y: NaN, z: NaN, yaw: NaN };
  const m = new THREE.Matrix4();
  const p = new THREE.Vector3();
  const q = new THREE.Quaternion();
  const s = new THREE.Vector3();
  const euler = new THREE.Euler(0, 0, 0, 'YXZ');

  const backend = {
    name: 'xr',
    enable() { armed = true; flyHeld = false; autoWalk = false; },
    disable() { intent.clear(); },
    update() {
      if (!session) return;
      const pads = readPads(session.inputSources);
      const head = renderer.xr.getCamera();
      euler.setFromQuaternion(head.quaternion, 'YXZ');
      const [mx, sy] = pads.move;
      if (sy || mx) autoWalk = false;
      const my = sy || (autoWalk ? -1 : 0);
      intent.forward = my ? -my : 0;
      intent.strafe = mx;
      intent.sprint = pads.run;
      if (mx || my) {
        // Steps go where the head faces (the walker clamps its own pitch).
        intent.yawDelta = angleTo(walker.state.yaw, euler.y);
        intent.pitchDelta = euler.x - walker.state.pitch;
      }
      const [tx, ty] = pads.turn;
      const turning = Math.abs(tx) >= Math.abs(ty);
      const snap = snapTurn(turning ? tx : 0, armed);
      armed = snap.armed;
      if (snap.yaw) rigYaw += snap.yaw;
      intent.rise = intent.flying && !turning && ty ? -ty : 0;
      if (pads.fly && !flyHeld) setFly(!intent.flying);
      flyHeld = pads.fly;
    },
  };

  function onEnd() {
    session?.removeEventListener('end', onEnd);
    session?.removeEventListener('select', onSelect);
    autoWalk = false;
    session = null;
    base = null;
    renderer.xr.enabled = false;
    if (backends.active === backend) backends.activate(fallback());
    onChange(false);
  }

  return {
    backend,
    get presenting() { return !!session; },
    get rigYaw() { return rigYaw; },
    get autoWalk() { return autoWalk; },

    /** Whether this browser offers a headset at all. Never rejects. */
    async supported() {
      try { return !!(xr && await xr.isSessionSupported('immersive-vr')); } catch { return false; }
    },

    /**
     * Start the session. Call it from the click itself: requestSession needs the
     * user's gesture, so nothing is awaited before it.
     */
    async enter() {
      if (session || starting || !xr) return false;
      starting = true;
      try {
        const next = await xr.requestSession('immersive-vr', { optionalFeatures: ['local-floor'] });
        renderer.xr.enabled = true;
        renderer.xr.setReferenceSpaceType('local');
        renderer.xr.setFramebufferScaleFactor(scale);
        await renderer.xr.setSession(next);
        session = next;
        base = renderer.xr.getReferenceSpace();
        rigYaw = walker.state.yaw;
        last.x = NaN;
        session.addEventListener('end', onEnd);
        session.addEventListener('select', onSelect);
        if (globalThis.document?.pointerLockElement) globalThis.document.exitPointerLock?.();
        backends.activate(backend);
        onChange(true);
        return true;
      } catch (err) {
        renderer.xr.enabled = false;
        console.warn('[4D Chicago] VR could not start', err);
        return false;
      } finally {
        starting = false;
      }
    },

    exit() { return session?.end().catch(() => {}); },

    /**
     * Before the render, after the walker: put the reference space's origin at the
     * walker's eye, turned by the snap turns. Only when either moved; the pose a
     * frame is drawn with was read before this frame's callback, so it takes effect
     * on the next frame (a step of a couple of centimetres, never seen).
     */
    sync() {
      if (!session || !base || typeof XRRigidTransform === 'undefined') return;
      const st = walker.state;
      const x = st.e, y = st.eyeY, z = -st.n;
      if (x === last.x && y === last.y && z === last.z && rigYaw === last.yaw) return;
      last.x = x; last.y = y; last.z = z; last.yaw = rigYaw;
      // world-from-reference is T(eye) * Ry(rigYaw); the offset space takes its inverse.
      m.makeRotationY(rigYaw).setPosition(x, y, z).invert();
      m.decompose(p, q, s);
      renderer.xr.setReferenceSpace(base.getOffsetReferenceSpace(
        new XRRigidTransform({ x: p.x, y: p.y, z: p.z, w: 1 }, { x: q.x, y: q.y, z: q.z, w: q.w })));
    },
  };
}
