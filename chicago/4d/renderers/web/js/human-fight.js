// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-fight.js — weapons in the hand and the motions of a fight, for the adults-only jaunts.
 *
 * The owner, 2026-11-15: *"add a jaunt for the 1812 that shows battle of fort Dearborn with more
 * of the actual conflicts in place, the knifing of la lime, people being attacked, tomahawks,
 * this one is targeted at adults and shows everything incredibly graphically"*; *"Both the murder
 * and battle jaunts"*. The student jaunts keep "Build-up and aftermath" (2026-11-14): nothing
 * here is reached from a jaunt that is not `audience: adults` (tools/compile_jaunts.py refuses
 * `arm` and `act` anywhere else).
 *
 * Three parts, each standing alone:
 *
 *   - `weaponGroup(kind)`: the thing in the hand, built in its GRIP frame: the origin where the
 *     fist closes on it, +Y its long axis out of the thumb side of the fist (a haft toward its
 *     head, a blade toward its point, a long gun toward its muzzle), +Z its working face (an
 *     axe's edge, a club's ball, a knife's edge, a gun's top). A pistol is the exception, as a
 *     pistol is held: its barrel runs along the hand (wrist to knuckles) and its butt down
 *     through the fist (`barrelAlongHand`). `muzzle` is the muzzle in that frame.
 *   - `fightTargets(state)`: where each hand is `t` seconds into a motion, from the keyframes in
 *     MOTIONS, in the figure's frame from that side's shoulder joint (+x the figure's left, +y
 *     up, +z ahead): the grip, the weapon's axis and the palm's facing, and an elbow pole. Pure
 *     numbers, for the gate. human-actions.js solves the arms from them.
 *   - `createFightFx(parent)`: a gun's flash and its cloud of powder smoke, which hangs and
 *     drifts as black-powder smoke does.
 *
 * The weapons are those the accounts put in these hands: tomahawks, war clubs and knives, the
 * soldiers' muskets and bayonets, Wells's pistols, Lalime's pistol and his dirk (Kirkland 1893,
 * Helm's and Heald's narratives, the Porthier statement). Their shapes, the motions and the
 * smoke are reconstructed (liberty L-1812-adult-jaunts). Nothing here draws a wound: the fallen
 * fall, and blood follows in its own module.
 */
import * as THREE from 'three';
import { musketGroup } from './human-garrison.js';

export const WEAPON_KINDS = Object.freeze(['none', 'tomahawk', 'club', 'knife', 'pistol', 'musket', 'rifle']);
export const FIGHT_ACTS = Object.freeze(['strike', 'stab', 'fire', 'aim', 'lower', 'struck']);
const TWO_HANDED = new Set(['musket', 'rifle']);
/** Where the right fist closes on a long gun: the small of the stock, metres from the butt plate. */
export const STOCK_WRIST_M = 0.35;
/** How far along a long gun from the right fist the left hand holds it (under the barrel). */
const FORE_GRIP_M = 0.42;

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);

// ── the weapons ───────────────────────────────────────────────────────────────────────────────

const mats = new Map();
function mat(name) {
  if (!mats.has(name)) {
    const def = {
      wood: { color: 0x5e3f24, roughness: 0.78, metalness: 0 },
      dark: { color: 0x3a2716, roughness: 0.7, metalness: 0 },
      iron: { color: 0x4a4b4e, roughness: 0.42, metalness: 0.75 },
      edge: { color: 0x9a9da1, roughness: 0.28, metalness: 0.85 },
      brass: { color: 0x9b7b3a, roughness: 0.4, metalness: 0.8 },
    }[name];
    const m = new THREE.MeshStandardMaterial(def);
    m.name = `fight_${name}`;
    mats.set(name, m);
  }
  return mats.get(name);
}
function mesh(geo, m, at, rot = null) {
  const o = new THREE.Mesh(geo, mat(m));
  o.position.set(...at);
  if (rot) o.rotation.set(...rot);
  o.castShadow = true;
  return o;
}
/** A wedge: a flat blade, thick at its back, from `y0` to `y1` along Y, its edge out along +Z. */
function bladeGeometry(len, back, edge, thick) {
  const s = new THREE.Shape();
  s.moveTo(0, -back / 2); s.lineTo(len, -edge / 2); s.lineTo(len, edge / 2); s.lineTo(0, back / 2); s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: thick, bevelEnabled: false });
  g.translate(0, 0, -thick / 2);
  // shape x -> +Z (the edge out), shape y -> +Y (along the haft), extrusion -> X
  g.applyMatrix4(new THREE.Matrix4().set(0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1));
  return g;
}

/** A long blade along +Y from its root to its point, `width` deep, its edge toward +Z, its back flat. */
function longBlade(len, width, thick) {
  const s = new THREE.Shape(); // shape x -> Z (across the blade), shape y -> Y (along it)
  s.moveTo(-width * 0.45, 0); s.lineTo(width * 0.55, 0); s.lineTo(width * 0.5, len * 0.7);
  s.quadraticCurveTo(width * 0.35, len * 0.92, -width * 0.45, len); s.closePath();
  const g = new THREE.ExtrudeGeometry(s, { depth: thick, bevelEnabled: false });
  g.translate(0, 0, -thick / 2);
  g.applyMatrix4(new THREE.Matrix4().set(0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1));
  return g;
}

const BUILD = {
  // A trade tomahawk: a 0.5 m ash haft, the fist 0.1 m up from its end, an iron head with a
  // flaring edge ahead and a small poll behind.
  tomahawk() {
    const g = new THREE.Group();
    g.add(mesh(new THREE.CylinderGeometry(0.0125, 0.0145, 0.5, 8), 'wood', [0, 0.15, 0]));
    g.add(mesh(bladeGeometry(0.13, 0.034, 0.075, 0.011), 'iron', [0, 0.36, 0.012]));
    g.add(mesh(new THREE.BoxGeometry(0.006, 0.075, 0.012), 'edge', [0, 0.36, 0.142]));
    g.add(mesh(new THREE.CylinderGeometry(0.019, 0.016, 0.03, 8), 'iron', [0, 0.36, -0.018], [Math.PI / 2, 0, 0]));
    return g;
  },
  // A ball-headed war club: a curved maple shaft and the ball at its head, ahead of the line.
  club() {
    const g = new THREE.Group();
    g.add(mesh(new THREE.CylinderGeometry(0.014, 0.017, 0.46, 8), 'wood', [0, 0.11, 0]));
    g.add(mesh(new THREE.CylinderGeometry(0.02, 0.016, 0.13, 8), 'wood', [0, 0.38, 0.03], [0.5, 0, 0]));
    g.add(mesh(new THREE.SphereGeometry(0.055, 12, 10), 'dark', [0, 0.45, 0.065]));
    return g;
  },
  // A long knife (a scalping knife, a dirk): a wooden grip and a 0.2 m blade, its edge ahead.
  knife() {
    const g = new THREE.Group();
    g.add(mesh(new THREE.CylinderGeometry(0.012, 0.014, 0.115, 8), 'dark', [0, 0.0, 0]));
    g.add(mesh(new THREE.BoxGeometry(0.03, 0.006, 0.026), 'brass', [0, 0.06, 0]));
    g.add(mesh(longBlade(0.2, 0.026, 0.0035), 'edge', [0, 0.063, 0.0]));
    return g;
  },
  // A flintlock pistol, held as a pistol is: its barrel along the hand, the butt down in the fist.
  // Built with +Y along the barrel (the hand's length) and +Z toward the thumb side (up when aimed).
  pistol() {
    const g = new THREE.Group();
    g.add(mesh(new THREE.CylinderGeometry(0.015, 0.02, 0.12, 8), 'wood', [0, -0.02, -0.02], [0.35, 0, 0]));
    g.add(mesh(new THREE.BoxGeometry(0.026, 0.2, 0.03), 'wood', [0, 0.1, 0.045]));
    g.add(mesh(new THREE.CylinderGeometry(0.009, 0.011, 0.24, 8), 'iron', [0, 0.17, 0.066]));
    g.add(mesh(new THREE.BoxGeometry(0.005, 0.05, 0.022), 'iron', [-0.015, 0.03, 0.058]));
    return g;
  },
  // A long gun: the garrison's musket (human-garrison.js), its small of the stock in the fist.
  musket() {
    const g = new THREE.Group(), m = musketGroup('hi');
    m.position.set(0, -STOCK_WRIST_M, 0);
    g.add(m);
    return g;
  },
};
BUILD.rifle = BUILD.musket;

/** The muzzle, grip frame (null for a weapon that is not a gun). */
export const MUZZLE = Object.freeze({ pistol: [0, 0.29, 0.066], musket: [0, 1.51 - STOCK_WRIST_M, 0.006], rifle: [0, 1.51 - STOCK_WRIST_M, 0.006] });

/** The weapon of `kind` as a group in its grip frame, or null for none. */
export function weaponGroup(kind) {
  const make = BUILD[kind];
  if (!make) return null;
  const g = make();
  g.name = `fight_${kind}`;
  g.userData.fightWeapon = kind;
  g.userData.barrelAlongHand = kind === 'pistol';
  g.userData.muzzle = MUZZLE[kind] ? v3(MUZZLE[kind]) : null;
  return g;
}

// ── the motions ───────────────────────────────────────────────────────────────────────────────
//
// A key: `t` seconds, and for the right hand `r` (and the left `l` where both hands hold): `at`
// the grip, metres from that side's shoulder joint in the figure's frame (+x its left, +y up,
// +z ahead); `axis` the weapon's long axis out of the fist (for a pistol, its barrel); `palm`
// the palm's facing; `pole` where the elbow points. Between keys each is eased. The numbers are
// read off how a person swings an axe, thrusts, presents a musket and levels a pistol: a
// reconstruction, not a measurement.

const R = (at, axis, palm, pole = [-0.9, -0.4, -0.2]) => ({ at, axis, palm, pole });
const READY = {
  tomahawk: R([0.02, -0.4, 0.2], [0, 0.6, 0.8], [1, 0, 0]),
  club: R([0.02, -0.42, 0.18], [0, 0.65, 0.76], [1, 0, 0]),
  knife: R([0.0, -0.42, 0.2], [0, 0.35, 0.94], [1, 0, 0]),
  pistol: R([0.0, -0.46, 0.12], [0, -0.75, 0.66], [1, 0, 0]),
  // At the port: the right fist low before the right hip, the gun across the body up to the left.
  musket: { r: R([0.1, -0.36, 0.2], [0.52, 0.8, 0.3], [0.2, -0.3, -0.93]), l: 'fore' },
};
READY.rifle = READY.musket;

const AIMED = {
  // The arm out straight at the shoulder's height, the pistol level.
  pistol: R([0.04, -0.03, 0.6], [0, 0.02, 1], [1, 0, 0], [-0.9, -0.5, 0]),
  // The butt in the hollow of the right shoulder, the cheek down on the stock, the left hand under
  // the barrel: the fist at the small of the stock, a hand ahead of the shoulder.
  musket: { r: R([0.06, -0.06, 0.16], [0, 0.03, 1], [1, 0, 0], [-0.95, -0.15, -0.1]), l: 'fore' },
};
AIMED.rifle = AIMED.musket;

/** One motion: its keys and how long it takes; `hold` keeps its last key until another. */
export const MOTIONS = Object.freeze({
  // Overhand: up and back behind the head, over, and down into the blow; back to the ready.
  strike: {
    for: ['tomahawk', 'club'],
    keys: (w) => [
      { t: 0, r: READY[w] },
      { t: 0.38, r: R([0.0, 0.24, -0.06], [0, -0.25, -0.97], [1, 0, 0], [-0.7, 0.5, 0.4]) },
      { t: 0.5, r: R([0.02, 0.18, 0.28], [0, 0.95, 0.3], [1, 0, 0], [-0.8, 0.2, 0.5]) },
      { t: 0.62, r: R([0.06, -0.26, 0.5], [0, -0.3, 0.95], [1, 0, 0], [-0.9, -0.3, 0.2]) },
      { t: 1.15, r: READY[w] },
    ],
    hit: 0.6,
  },
  // A thrust: drawn back low at the hip, then driven forward and up; a bayonet with both hands.
  stab: {
    for: ['knife', 'musket', 'rifle'],
    keys: (w) => (TWO_HANDED.has(w)
      ? [
        { t: 0, r: READY[w].r, l: 'fore' },
        { t: 0.3, r: R([0.08, -0.34, -0.02], [0.05, 0.12, 1], [1, 0, 0]), l: 'fore' },
        { t: 0.5, r: R([0.1, -0.3, 0.42], [0.05, 0.1, 1], [1, 0, 0]), l: 'fore' },
        { t: 1.1, r: READY[w].r, l: 'fore' },
      ]
      : [
        { t: 0, r: READY[w] },
        { t: 0.28, r: R([-0.04, -0.36, 0.0], [0, 0.15, 1], [1, 0, 0]) },
        { t: 0.45, r: R([0.06, -0.2, 0.6], [0, 0.1, 1], [1, 0, 0], [-0.9, -0.4, 0]) },
        { t: 0.9, r: READY[w] },
      ]),
    hit: 0.44,
  },
  // Brought up to the aim and held there.
  aim: {
    for: ['pistol', 'musket', 'rifle'],
    keys: (w) => (TWO_HANDED.has(w)
      ? [{ t: 0, r: READY[w].r, l: 'fore' }, { t: 0.55, r: AIMED[w].r, l: 'fore' }]
      : [{ t: 0, r: READY[w] }, { t: 0.45, r: AIMED[w] }]),
    hold: true,
  },
  // Brought up, a breath, the shot (`shot`), the kick, and held at the aim.
  fire: {
    for: ['pistol', 'musket', 'rifle'],
    keys: (w) => {
      const a = TWO_HANDED.has(w) ? AIMED[w].r : AIMED[w];
      const kick = R([a.at[0], a.at[1] + 0.04, a.at[2] - 0.05], [a.axis[0], a.axis[1] + 0.18, a.axis[2]], a.palm, a.pole);
      const k = TWO_HANDED.has(w)
        ? [{ t: 0, r: READY[w].r }, { t: 0.55, r: a }, { t: 0.8, r: a }, { t: 0.86, r: kick }, { t: 1.2, r: a }]
        : [{ t: 0, r: READY[w] }, { t: 0.45, r: a }, { t: 0.7, r: a }, { t: 0.75, r: kick }, { t: 1.05, r: a }];
      return TWO_HANDED.has(w) ? k.map((x) => ({ ...x, l: 'fore' })) : k;
    },
    shot: (w) => (TWO_HANDED.has(w) ? 0.8 : 0.7),
    hold: true,
  },
  // Back down to the ready.
  lower: {
    for: ['pistol', 'musket', 'rifle', 'tomahawk', 'club', 'knife'],
    keys: (w, from) => [{ t: 0, r: from?.r ?? READY[w]?.r ?? READY[w], ...(TWO_HANDED.has(w) ? { l: 'fore' } : {}) },
      { t: 0.5, r: TWO_HANDED.has(w) ? READY[w].r : READY[w], ...(TWO_HANDED.has(w) ? { l: 'fore' } : {}) }],
  },
  // Hit: both hands go to the body where the blow or the ball went in, and stay there.
  struck: {
    for: null,
    keys: () => {
      const clutch = { r: R([0.15, -0.3, 0.17], [0, 1, 0], [0, 0, -1], [-0.8, -0.5, 0.2]), l: R([-0.12, -0.24, 0.17], [0, 1, 0], [0, 0, -1], [0.8, -0.5, 0.2]) };
      return [{ t: 0, r: null, l: null }, { t: 0.18, ...clutch }];
    },
    hold: true,
    empty: true,
  },
});

/** A long gun's fore grip: the left hand under the barrel, FORE_GRIP_M along it from the right fist. */
function foreGrip(r, rShoulder, lShoulder) {
  const axis = v3(r.axis).normalize();
  const at = v3(r.at).add(rShoulder).addScaledVector(axis, FORE_GRIP_M).add(new THREE.Vector3(0, -0.03, 0)).sub(lShoulder);
  return { at: at.toArray(), axis: r.axis, palm: [0, 1, 0], pole: [0.9, -0.5, -0.1] };
}

function lerpKey(a, b, k) {
  if (!a) return b; if (!b) return a;
  const mix = (x, y) => x.map((v, i) => v + (y[i] - v) * k);
  return { at: mix(a.at, b.at), axis: mix(a.axis, b.axis), palm: mix(a.palm, b.palm), pole: mix(a.pole, b.pole) };
}

/**
 * The hands `state.t` seconds into `state.act` for weapon `state.arm` (no act: the weapon's
 * ready). `shoulders` { l, r } are the shoulder joints in the figure's frame, for a long gun's
 * fore grip. Returns { r, l, empty } (each hand null when it is not asked) or null.
 */
export function fightTargets({ arm = 'none', act = null, t = 0, from = null } = {}, shoulders = null) {
  const sh = shoulders ?? { r: new THREE.Vector3(-0.18, 1.42, 0), l: new THREE.Vector3(0.18, 1.42, 0) };
  const motion = act ? MOTIONS[act] : null;
  const usable = motion && (motion.for === null || motion.for.includes(arm));
  let r = null, l = null;
  if (usable) {
    const keys = motion.keys(arm, from);
    let i = 0;
    while (i < keys.length - 1 && keys[i + 1].t <= t) i++;
    const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)];
    const k = b === a || b.t <= a.t ? 1 : smooth((t - a.t) / (b.t - a.t));
    r = lerpKey(a.r, b.r, t >= b.t ? 1 : k);
    if (a.l === 'fore' || b.l === 'fore') l = 'fore';
    else l = lerpKey(a.l, b.l, t >= b.t ? 1 : k);
    if (t >= keys[keys.length - 1].t && !motion.hold && act !== 'struck') r = keys[keys.length - 1].r;
  } else if (READY[arm]) {
    const ready = READY[arm];
    r = ready.r ?? ready; l = ready.l ?? null;
  }
  if (r && r.r) r = r.r; // a two-handed ready
  if (l === 'fore') l = r ? foreGrip(r, sh.r, sh.l) : null;
  if (!r && !l) return null;
  return { r, l, empty: !!motion?.empty };
}

/** How long a motion lasts before it holds or ends. */
export function motionLength(act, arm) {
  const m = MOTIONS[act];
  if (!m) return 0;
  const keys = m.keys(arm, null);
  return keys[keys.length - 1].t;
}

/** When a motion's shot goes off (null for one that does not shoot). */
export function shotTime(act, arm) {
  const m = MOTIONS[act];
  return m?.shot ? m.shot(arm) : null;
}

// ── the flash and the smoke ───────────────────────────────────────────────────────────────────

let puffTexture = null, flashTexture = null, puffGeometry = null;
function radialTexture(stops) {
  if (typeof document === 'undefined') return null;
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  for (const [o, col] of stops) grad.addColorStop(o, col);
  g.fillStyle = grad; g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * Gun flashes and powder smoke under `parent`. `shoot(at, dir)` (world): a flash at the muzzle
 * for a few hundredths of a second, and a white-grey cloud that billows out along the shot,
 * hangs, swells and drifts down the wind over some seconds. `update(dt)` each frame.
 */
export function createFightFx(parent, { wind = [0.35, 0.05, 0.15], max = 60 } = {}) {
  puffTexture ??= radialTexture([[0, 'rgba(236,234,228,0.9)'], [0.45, 'rgba(214,212,206,0.55)'], [1, 'rgba(200,198,192,0)']]);
  flashTexture ??= radialTexture([[0, 'rgba(255,250,220,1)'], [0.25, 'rgba(255,200,90,0.9)'], [1, 'rgba(255,120,20,0)']]);
  const live = [];
  const drift = v3(wind);
  // The flash is light and glows; the smoke is lit by the scene like anything else (a card that
  // turns to face the eye), so at dusk it is a dusk grey and not a glowing ball (the town's
  // exposure lifts anything unlit).
  function sprite(tex, additive) {
    let s;
    if (additive) {
      s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 1 }));
    } else {
      puffGeometry ??= new THREE.PlaneGeometry(1, 1);
      s = new THREE.Mesh(puffGeometry, new THREE.MeshLambertMaterial({ map: tex, color: 0xcfccc4, transparent: true, depthWrite: false, side: THREE.DoubleSide, opacity: 1 }));
      s.onBeforeRender = (r, sc, camera) => { s.quaternion.copy(camera.quaternion); s.updateMatrixWorld(); };
    }
    s.renderOrder = 3;
    parent?.add?.(s);
    return s;
  }
  function drop(p) { parent?.remove?.(p.s); p.s.material.dispose(); }
  return {
    shoot(at, dir) {
      if (!parent || !at) return;
      const d = (dir ?? new THREE.Vector3(0, 0, 1)).clone().normalize();
      const flash = sprite(flashTexture, true);
      flash.position.copy(at).addScaledVector(d, 0.12); flash.scale.setScalar(0.55);
      live.push({ s: flash, age: 0, life: 0.07, flash: true });
      for (let i = 0; i < 7; i++) {
        const s = sprite(puffTexture, false);
        const out = 0.25 + i * 0.22;
        s.position.copy(at).addScaledVector(d, out * 0.6);
        const vel = d.clone().multiplyScalar(2.4 - i * 0.28).add(new THREE.Vector3((Math.sin(i * 2.1) * 0.3), 0.15 + i * 0.03, Math.cos(i * 1.7) * 0.3));
        live.push({ s, age: 0, life: 6 + i * 0.6, vel, size: 0.35 + i * 0.05, grow: 0.5 + i * 0.07 });
      }
      while (live.length > max) drop(live.shift());
    },
    update(dt) {
      if (!(dt > 0)) return;
      for (let i = live.length - 1; i >= 0; i--) {
        const p = live[i];
        p.age += dt;
        if (p.age >= p.life) { drop(p); live.splice(i, 1); continue; }
        const k = p.age / p.life;
        if (p.flash) { p.s.material.opacity = 1 - k; continue; }
        p.vel.multiplyScalar(Math.exp(-2.2 * dt));
        p.s.position.addScaledVector(p.vel, dt).addScaledVector(drift, dt);
        p.s.scale.setScalar(p.size + p.grow * Math.sqrt(p.age) * 1.6);
        p.s.material.opacity = 0.5 * (k < 0.08 ? k / 0.08 : 1 - smooth((k - 0.35) / 0.65));
      }
    },
    get count() { return live.length; },
    clear() { for (const p of live) drop(p); live.length = 0; },
  };
}

const basis = new THREE.Matrix4(), world = new THREE.Matrix4(), inv = new THREE.Matrix4();
const X = new THREE.Vector3(), Y = new THREE.Vector3(), Z = new THREE.Vector3(), S = new THREE.Vector3();
/**
 * Lay `group` (a weaponGroup) in the hand whose grip is `frame` (human-actions.js gripFrame:
 * world `pos`, `a` out of the thumb side, `f` along the hand, `p` the palm's facing, `scale`),
 * under its parent's own transform. A pistol's barrel runs along the hand and its top is the
 * thumb side; a long gun's top is the back of the hand's line turned up (its lock to the right);
 * anything else has its working face where the knuckles go.
 */
export function placeWeapon(group, frame) {
  if (!group || !frame) return;
  const kind = group.userData.fightWeapon;
  if (kind === 'pistol') { X.copy(frame.p).negate(); Y.copy(frame.f); Z.copy(frame.a); }
  else if (kind === 'musket' || kind === 'rifle') { X.copy(frame.p).negate(); Y.copy(frame.a); Z.copy(frame.f).negate(); }
  else { X.copy(frame.p); Y.copy(frame.a); Z.copy(frame.f); }
  basis.makeBasis(X, Y, Z).setPosition(frame.pos);
  world.copy(basis).scale(S.setScalar(frame.scale || 1));
  const parent = group.parent;
  if (parent) { parent.updateWorldMatrix(true, false); world.premultiply(inv.copy(parent.matrixWorld).invert()); }
  world.decompose(group.position, group.quaternion, group.scale);
}

/** A gun's muzzle in the world and the way it points, or null. */
export function muzzleOf(group) {
  const m = group?.userData?.muzzle;
  if (!m) return null;
  group.updateWorldMatrix(true, false);
  const at = m.clone().applyMatrix4(group.matrixWorld);
  const dir = new THREE.Vector3(0, 1, 0).transformDirection(group.matrixWorld);
  return { at, dir };
}
