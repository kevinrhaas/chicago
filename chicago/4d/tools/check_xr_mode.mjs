#!/usr/bin/env node
/**
 * T-3575 — the headset backend (renderers/web/js/controls/xr.js) and its wiring.
 *
 * Holds the pure half to its rules (a headset browser is told apart by its user agent,
 * the framebuffer scale and its override, the dead zone, one push one snap, the stick
 * mapping for one and two controllers), drives the session half against a stand-in
 * renderer and session (the reference space lands its origin on the walker's eye and
 * turns with the snaps; the stick writes only the intent; the session's end hands the
 * controls back), and reads main.js and index.html for the wiring: the key is hidden
 * until the browser offers a headset, a headset boots as a phone, and an XR frame is
 * never skipped by the governor. The browser half (a real session) needs a headset or
 * an emulator and is not claimed here.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const xr = await import(pathToFileURL(path.join(web, 'js/controls/xr.js')).href);
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const { createIntent, createBackendSwitch } = await import(pathToFileURL(path.join(web, 'js/controls/intent.js')).href);
const main = await readFile(path.join(web, 'js/main.js'), 'utf8');
const html = await readFile(path.join(web, 'index.html'), 'utf8');

const checks = [];
function check(name, run) { run(); checks.push(name); }
async function checkAsync(name, run) { await run(); checks.push(name); }
const near = (a, b, eps = 1e-6) => Math.abs(a - b) <= eps;

check('a standalone headset browser is told apart by its user agent', () => {
  assert.ok(xr.isStandaloneHeadset('Mozilla/5.0 (X11; Linux x86_64; Quest 3) AppleWebKit/537.36 (KHTML, like Gecko) OculusBrowser/35.2.0.0.0 SamsungBrowser/4.0 Chrome/128.0 VR Safari/537.36'));
  assert.ok(xr.isStandaloneHeadset('Mozilla/5.0 (Linux; Android 12; Pico 4) AppleWebKit/537.36 PicoBrowser/3.3.22 Chrome/105.0 VR Safari/537.36'));
  assert.ok(!xr.isStandaloneHeadset('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15'));
  assert.ok(!xr.isStandaloneHeadset('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) CriOS/130.0 Mobile/15E148 Safari/604.1'));
  assert.ok(!xr.isStandaloneHeadset(''));
});

check('the framebuffer scale: reduced on a headset, whole on a computer, ?vr-scale= first and clamped', () => {
  assert.equal(xr.vrScale({ headset: true }), xr.VR_SCALE.headset);
  assert.ok(xr.VR_SCALE.headset < 1);
  assert.equal(xr.vrScale({ headset: false }), 1);
  assert.equal(xr.vrScale({ headset: true, search: '?vr-scale=0.8' }), 0.8);
  assert.equal(xr.vrScale({ headset: false, search: '?vr-scale=0.05' }), xr.VR_SCALE.min);
  assert.equal(xr.vrScale({ headset: false, search: '?vr-scale=4' }), xr.VR_SCALE.max);
  assert.equal(xr.vrScale({ headset: true, search: '?vr-scale=nope' }), xr.VR_SCALE.headset);
});

check('the dead zone is taken out and the rest rescaled', () => {
  assert.equal(xr.deadzone(0.1), 0);
  assert.equal(xr.deadzone(-0.15), 0);
  assert.equal(xr.deadzone(1), 1);
  assert.equal(xr.deadzone(-1), -1);
  assert.ok(xr.deadzone(0.5) > 0 && xr.deadzone(0.5) < 0.5);
});

check('one push of the right stick is one snap, right turns right, and it re-arms only near centre', () => {
  const step = xr.SNAP_DEG * Math.PI / 180;
  let s = xr.snapTurn(0.9, true);
  assert.ok(near(s.yaw, -step)); assert.equal(s.armed, false);
  s = xr.snapTurn(0.9, s.armed); assert.equal(s.yaw, 0);
  s = xr.snapTurn(0.45, s.armed); assert.equal(s.yaw, 0); assert.equal(s.armed, false);
  s = xr.snapTurn(0.1, s.armed); assert.equal(s.armed, true);
  s = xr.snapTurn(-0.9, s.armed); assert.ok(near(s.yaw, step));
  assert.ok(near(xr.angleTo(3, -3), 2 * Math.PI - 6));
});

const pad = (x, y, pressed = []) => ({ axes: [0, 0, x, y], buttons: Array.from({ length: 6 }, (_, i) => ({ pressed: pressed.includes(i) })) });
check('two controllers: the left stick walks, the right turns, grip or click runs, A or X flies', () => {
  const r = xr.readPads([{ handedness: 'right', gamepad: pad(1, 0) }, { handedness: 'left', gamepad: pad(0, -1, [1]) }]);
  assert.deepEqual(r.move, [0, -1]);
  assert.equal(r.turn[0], 1);
  assert.equal(r.run, true);
  assert.equal(r.fly, false);
  assert.equal(xr.readPads([{ handedness: 'right', gamepad: pad(0, 0, [4]) }]).fly, true);
});

check('one controller walks whichever hand holds it; a source with no gamepad (a hand) is ignored', () => {
  const r = xr.readPads([{ handedness: 'right', gamepad: pad(0, -1) }, { handedness: 'left' }]);
  assert.deepEqual(r.move, [0, -1]);
  assert.deepEqual(r.turn, [0, 0]);
  assert.deepEqual(xr.readPads([]).move, [0, 0]);
});

// ---- the session half, against stand-ins ------------------------------------ //

class FakeRigid { constructor(position, orientation) { this.position = position; this.orientation = orientation; } }
globalThis.XRRigidTransform = FakeRigid;

function rig() {
  const listeners = {};
  const session = {
    inputSources: [],
    addEventListener: (k, fn) => { listeners[k] = fn; },
    removeEventListener: (k) => { delete listeners[k]; },
    end: async () => { listeners.end?.(); },
    fire: (k, e) => listeners[k]?.(e),
  };
  const spaces = [];
  const base = { getOffsetReferenceSpace: (t) => { spaces.push(t); return { offset: t }; } };
  const head = new THREE.PerspectiveCamera();
  const renderer = { xr: {
    enabled: false, scale: null, type: null, custom: null,
    setReferenceSpaceType(t) { this.type = t; },
    setFramebufferScaleFactor(v) { this.scale = v; },
    async setSession(s) { this.session = s; },
    getReferenceSpace() { return this.custom ?? base; },
    setReferenceSpace(sp) { this.custom = sp; },
    getCamera: () => head,
  } };
  const walker = { state: { e: 120, n: -40, eyeY: 182.5, yaw: 0.7, pitch: 0 } };
  const intent = createIntent();
  const backends = createBackendSwitch(intent);
  const page = { name: 'pointerlock' };
  backends.activate(page);
  const flyCalls = [];
  const changes = [];
  const nav = { xr: {
    isSessionSupported: async (mode) => mode === 'immersive-vr',
    requestSession: async (mode, opts) => { assert.equal(mode, 'immersive-vr'); session.opts = opts; return session; },
  } };
  const mode = xr.createXRMode({ THREE, renderer, walker, intent, backends, fallback: () => page,
    setFly: (on) => { flyCalls.push(on); intent.flying = on; }, onChange: (on) => changes.push(on), scale: 0.6, nav });
  return { mode, renderer, walker, intent, backends, page, session, spaces, head, flyCalls, changes };
}

/** Where the offset space puts a point given in the headset's own space: inverse(offset) · p. */
function toWorld(t, local) {
  const m = new THREE.Matrix4().compose(
    new THREE.Vector3(t.position.x, t.position.y, t.position.z),
    new THREE.Quaternion(t.orientation.x, t.orientation.y, t.orientation.z, t.orientation.w),
    new THREE.Vector3(1, 1, 1)).invert();
  return local.clone().applyMatrix4(m);
}

await checkAsync('no headset, no key: supported() is false without navigator.xr and never throws', async () => {
  const r = rig();
  assert.equal(await r.mode.supported(), true);
  const none = xr.createXRMode({ THREE, renderer: r.renderer, walker: r.walker, intent: r.intent, backends: r.backends,
    fallback: () => null, setFly: () => {}, nav: {} });
  assert.equal(await none.supported(), false);
  const throws = xr.createXRMode({ THREE, renderer: r.renderer, walker: r.walker, intent: r.intent, backends: r.backends,
    fallback: () => null, setFly: () => {}, nav: { xr: { isSessionSupported: () => { throw new Error('denied'); } } } });
  assert.equal(await throws.supported(), false);
  assert.equal(await none.enter(), false);
});

await checkAsync('entering: local space, the scale asked for, the headset backend live, facing the way the walker faced', async () => {
  const r = rig();
  assert.equal(await r.mode.enter(), true);
  assert.equal(r.renderer.xr.enabled, true);
  assert.equal(r.renderer.xr.type, 'local');
  assert.equal(r.renderer.xr.scale, 0.6);
  assert.equal(r.backends.name, 'xr');
  assert.equal(r.mode.presenting, true);
  assert.equal(r.mode.rigYaw, 0.7);
  assert.deepEqual(r.changes, [true]);
});

await checkAsync('sync: the space\'s origin is the walker\'s eye, turned by the rig, and only rebuilt when either moved', async () => {
  const r = rig();
  await r.mode.enter();
  r.mode.sync();
  assert.equal(r.spaces.length, 1);
  const eye = toWorld(r.spaces[0], new THREE.Vector3(0, 0, 0));
  assert.ok(near(eye.x, 120) && near(eye.y, 182.5) && near(eye.z, 40), `eye at ${eye.toArray()}`);
  // A metre ahead in the headset's space (-z) is a metre along the walker's facing.
  const ahead = toWorld(r.spaces[0], new THREE.Vector3(0, 0, -1)).sub(eye);
  assert.ok(near(ahead.x, -Math.sin(0.7)) && near(ahead.z, -Math.cos(0.7)), `ahead ${ahead.toArray()}`);
  r.mode.sync();
  assert.equal(r.spaces.length, 1, 'standing still builds no new space');
  r.walker.state.e += 0.5;
  r.mode.sync();
  assert.equal(r.spaces.length, 2);
});

await checkAsync('the stick writes the intent and steers the step to the head; at rest the walker\'s yaw is left alone', async () => {
  const r = rig();
  await r.mode.enter();
  r.head.quaternion.setFromEuler(new THREE.Euler(0.2, 1.5, 0, 'YXZ'));
  r.session.inputSources = [{ handedness: 'left', gamepad: pad(0, -1) }];
  r.mode.backend.update(0.016);
  assert.equal(r.intent.forward, 1);
  assert.ok(near(r.intent.yawDelta, 1.5 - 0.7));
  assert.ok(near(r.intent.pitchDelta, 0.2));
  r.intent.clearLook();
  r.session.inputSources = [{ handedness: 'left', gamepad: pad(0, 0) }];
  r.mode.backend.update(0.016);
  assert.equal(r.intent.forward, 0);
  assert.equal(r.intent.yawDelta, 0);
});

await checkAsync('the right stick snaps the rig, and flying, rises; A or X toggles fly once per press', async () => {
  const r = rig();
  await r.mode.enter();
  r.session.inputSources = [{ handedness: 'left', gamepad: pad(0, 0) }, { handedness: 'right', gamepad: pad(1, 0) }];
  r.mode.backend.update(0.016);
  r.mode.backend.update(0.016);
  assert.ok(near(r.mode.rigYaw, 0.7 - xr.SNAP_DEG * Math.PI / 180), 'one step per push');
  r.session.inputSources = [{ handedness: 'right', gamepad: pad(0, 0, [4]) }, { handedness: 'left', gamepad: pad(0, 0) }];
  r.mode.backend.update(0.016);
  r.mode.backend.update(0.016);
  assert.deepEqual(r.flyCalls, [true]);
  r.session.inputSources = [{ handedness: 'right', gamepad: pad(0, -1) }, { handedness: 'left', gamepad: pad(0, 0) }];
  r.mode.backend.update(0.016);
  assert.equal(r.intent.rise, 1);
});

await checkAsync('no stick (Cardboard, hands): the button starts walking where you look, the next press stops, a stick takes over', async () => {
  const r = rig();
  await r.mode.enter();
  assert.ok(xr.hasStick({ gamepad: pad(0, 0) }));
  assert.ok(!xr.hasStick({ targetRayMode: 'gaze' }));
  r.head.quaternion.setFromEuler(new THREE.Euler(0, 1.5, 0, 'YXZ'));
  r.session.fire('select', { inputSource: { handedness: 'none', targetRayMode: 'gaze' } });
  assert.equal(r.mode.autoWalk, true);
  r.mode.backend.update(0.016);
  assert.equal(r.intent.forward, 1);
  assert.ok(near(r.intent.yawDelta, 1.5 - 0.7));
  r.session.fire('select', { inputSource: { handedness: 'right', gamepad: pad(0, 0) } });
  assert.equal(r.mode.autoWalk, true, 'a controller\'s trigger is not the walk button');
  r.session.fire('select', { inputSource: { handedness: 'none', targetRayMode: 'gaze' } });
  r.intent.clearLook();
  r.mode.backend.update(0.016);
  assert.equal(r.intent.forward, 0);
  r.session.fire('select', { inputSource: { targetRayMode: 'gaze' } });
  r.session.inputSources = [{ handedness: 'left', gamepad: pad(0, 1) }];
  r.mode.backend.update(0.016);
  assert.equal(r.mode.autoWalk, false, 'pushing a stick ends the hands-free walk');
  assert.equal(r.intent.forward, -1);
});

await checkAsync('the session ending hands the controls back and turns XR off', async () => {
  const r = rig();
  await r.mode.enter();
  await r.mode.exit();
  assert.equal(r.mode.presenting, false);
  assert.equal(r.renderer.xr.enabled, false);
  assert.equal(r.backends.active, r.page);
  assert.deepEqual(r.changes, [true, false]);
});

// ---- the wiring --------------------------------------------------------------- //

check('the key ships hidden and is shown only when the browser offers a headset', () => {
  assert.match(html, /<button[^>]*id="btn-vr"[^>]*hidden/);
  assert.match(main, /xrMode\.supported\(\)\.then\(\(ok\) => \{ if \(vrKey\) vrKey\.hidden = !ok; \}\)/);
});

check('a headset boots as a phone: the phone\'s choices and memory diet', () => {
  assert.match(main, /const headset = isStandaloneHeadset\(navigator\.userAgent\)/);
  assert.match(main, /profileDevice\(\{ touch: coarse \|\| headset,/);
});

check('the governor never skips or rescales a headset frame, and the space follows the walker before the draw', () => {
  assert.match(main, /renderer\.xr\.isPresenting\) governor\.rest\(\)/);
  const sync = main.indexOf('if (xrMode.presenting) xrMode.sync();');
  const draw = main.indexOf('confidence.render(renderer, scene3d, camera);');
  assert.ok(sync > 0 && draw > sync, 'sync runs before the render');
});

check('the page\'s own keys and pointer do not take the controls from a headset session', () => {
  assert.match(main, /pointerdown', \(e\) => \{\n\s*if \(gateOpen \|\| xrMode\?\.presenting/);
  assert.match(main, /if \(gateOpen \|\| xrMode\?\.presenting \|\| isTyping\(e\.target\)/);
});

for (const name of checks) console.log(`ok - ${name}`);
console.log(`check_xr_mode: ${checks.length} checks passed`);
