// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-motions.js — T-3553. Getting up off the ground and getting down onto it, as people do.
 *
 * The owner, 2026-11-27, of the warriors rising from the grass behind the sand bank in the 1812
 * battle jaunts: "they just rise like a plank, that is not how someone would jump up to attack
 * from a prone position". A held posture (human-life.js POSTURES) was eased in and out as one
 * weight, and a lying one is tipped whole about the feet (humans.js `place`), so a man lying
 * face down came up stiff and straight, pivoting on his toes. Here the way up is a short run of
 * key poses the body passes through: the hands come back under the shoulders, the arms push the
 * chest up, a knee comes in under the hips, the foot comes through to a crouch, and he drives up
 * off it, already leaning into his first stride when the run takes him. Some go up through both
 * knees, on all fours, first; each has his own side, speed and lean (drawn from his id), so no
 * two get up alike (the owner's rule that the Native people must not look identical). Going down
 * is the same road the other way: a crouch, the hands to the ground, the knees, the legs out
 * behind. A kneeling or crouching man who is about to run drives up off his front foot leaning
 * forward, where a calm one still just stands.
 *
 * A key says where the hip joint is (x forward, y up, metres, in the ground frame of the spot the
 * figure stands on once up), how far the trunk is tipped forward from upright (`tip`, degrees,
 * the whole figure pitched as a lying posture is), each leg's ankle and the foot's own pitch in
 * the world (`foot`: 0 flat, negative toes down), the spine's extra lean (negative forward) and
 * the head's look, and the wrists planted on the ground (`hands`: [x forward, y up, out from the
 * body]) with the way the elbow points (`pole`: [out, up, forward]). Leg `a` is the one that comes
 * through first. Between keys every number eases (smoothstep); the legs are solved to their
 * ankles on this body's own thigh and shin (human-life.js), the arms reach the planted wrists in
 * human-actions.js. The poses are reconstructed (liberty L-human-gait-3472), from how people get
 * up off the ground (push up, a knee in, a foot through, up), not from a measured dataset.
 */
// The figure's own draws (driver-life.js seededRandom's recipe, here so this module imports nothing
// and runs under node for tools/test_human_motions.mjs).
function seededRandom(id) {
  let h = 2166136261;
  for (const ch of String(id)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  let a = h >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const smooth = (u) => u * u * (3 - 2 * u);
const lerp = (a, b, u) => a + (b - a) * u;

// The pieces the keys are made of. Prone: lying face down, the hip 0.12 m off the ground (the
// prone posture's lift), the legs out straight behind on the toes, the forearms on the ground
// before the head, elbows out. Its root (its toes) lies PRONE_BACK behind the standing spot.
export const PRONE_BACK = 1.25;
const PRONE_HANDS = { pos: [0.37, 0.05, 0.16], pole: [1, -0.25, 0.35] };
const SET_HANDS = { pos: [0.15, 0.05, 0.27], pole: [0.35, 0.55, -0.75] };
const prone = (at, hands = PRONE_HANDS, look = 52) => ({
  at, tip: 90, hip: [-0.3, 0.12], a: { ankle: [-1.18, 0.12], foot: -90 }, b: { ankle: [-1.18, 0.12], foot: -90 },
  spread: 8, look, hands: { a: hands, b: hands },
});
// Up on straight arms, the chest high and the hips still low, on the toes.
const push = (at) => ({ at, tip: 58, lean: 12, hip: [-0.32, 0.22], a: { ankle: [-1.18, 0.14], foot: -80 }, b: { ankle: [-1.18, 0.14], foot: -80 },
  spread: 4, look: 18, hands: { a: SET_HANDS, b: SET_HANDS } });
// The leading knee in under the hips on the ground, the trailing leg out behind on its toes.
const kneeIn = (at) => ({ at, tip: 85, hip: [-0.4, 0.53], a: { ankle: [-0.85, 0.11], foot: -68 }, b: { ankle: [-1.16, 0.14], foot: -70 },
  look: 22, hands: { a: SET_HANDS, b: SET_HANDS } });
// On all fours: both knees under the hips.
const fours = (at) => ({ at, tip: 85, hip: [-0.4, 0.53], a: { ankle: [-0.85, 0.11], foot: -68 }, b: { ankle: [-0.85, 0.11], foot: -68 },
  look: 22, hands: { a: SET_HANDS, b: SET_HANDS } });
// Standing, the feet under the hip.
const upright = (at) => ({ at, tip: 0, hip: [0, 0.95], a: { ankle: [0, 0.07], foot: 0 }, b: { ankle: [0, 0.07], foot: 0 } });
// Driving up off the leading foot into the first stride, leaning into it: the trailing knee
// coming through high. The run (humans.js walkPath) takes over from here.
const stride = (at, lean = 22) => ({ at, tip: lean, hip: [0, 0.9], a: { ankle: [-0.15, 0.1], foot: -28 }, b: { ankle: [0.14, 0.4], foot: 8 }, look: 6 });

/**
 * The motions, each a list of keys over a nominal time (seconds), the time the run may start
 * (`release`: the walk asked for while getting up waits for it), what the figure is in at the
 * end (`ends`), and how far the spot it stands on moves (`shift`, metres along its heading:
 * a man lying face down gets up where his knees were, not where his toes were).
 */
export const MOTIONS = Object.freeze({
  // Push up, a knee in under, the foot through to a crouch, up and away.
  rise_prone_knee: { from: 'prone', ends: 'stand', shift: PRONE_BACK, keys: [
    prone(0), prone(0.2, SET_HANDS, 44), push(0.45), kneeIn(0.78),
    { at: 1.05, tip: 50, hip: [-0.3, 0.62], a: { ankle: [-0.15, 0.08], foot: 0 }, b: { ankle: [-1.0, 0.12], foot: -70 }, look: 14, hands: { a: null, b: null } },
    stride(1.3)] },
  // Up through both knees on all fours, then a foot through, up and away.
  rise_prone_fours: { from: 'prone', ends: 'stand', shift: PRONE_BACK, keys: [
    prone(0), prone(0.22, SET_HANDS, 44), push(0.5), fours(0.85),
    { at: 1.15, tip: 68, hip: [-0.35, 0.54], a: { ankle: [-0.15, 0.08], foot: 0 }, b: { ankle: [-0.8, 0.11], foot: -68 }, look: 16, hands: { a: null, b: null } },
    { at: 1.42, tip: 36, hip: [-0.16, 0.72], a: { ankle: [-0.15, 0.08], foot: 0 }, b: { ankle: [-0.74, 0.14], foot: -60 }, look: 10 },
    stride(1.68, 20)] },
  // The same up, standing still at the end (getting up with no run after it).
  rise_prone_calm: { from: 'prone', ends: 'stand', shift: PRONE_BACK, keys: [
    prone(0), prone(0.25, SET_HANDS, 44), push(0.6), kneeIn(1.0),
    { at: 1.4, tip: 42, hip: [-0.22, 0.6], a: { ankle: [-0.05, 0.08], foot: 0 }, b: { ankle: [-0.62, 0.1], foot: -75 }, look: 12, hands: { a: null, b: null } },
    { at: 1.8, tip: 10, hip: [-0.02, 0.9], a: { ankle: [-0.05, 0.08], foot: 0 }, b: { ankle: [-0.12, 0.12], foot: -20 }, look: 4 },
    upright(2.1)] },
  // Down into the grass: a crouch, the hands to the ground ahead, the knees, the legs out behind.
  down_prone: { from: 'stand', ends: 'prone', shift: -PRONE_BACK, keys: [
    upright(0),
    { at: 0.3, tip: 40, hip: [-0.04, 0.6], a: { ankle: [0.02, 0.08], foot: 0 }, b: { ankle: [-0.14, 0.1], foot: -20 }, look: 8,
      hands: { a: { pos: [0.3, 0.12, 0.25], pole: SET_HANDS.pole }, b: { pos: [0.3, 0.12, 0.25], pole: SET_HANDS.pole } }, handsW: 0.6 },
    { ...fours(0.6), hip: [-0.25, 0.53], a: { ankle: [-0.7, 0.11], foot: -68 }, b: { ankle: [-0.72, 0.11], foot: -68 },
      hands: { a: { pos: [0.22, 0.05, 0.26], pole: SET_HANDS.pole }, b: { pos: [0.22, 0.05, 0.26], pole: SET_HANDS.pole } } },
    { ...push(0.9), lean: 6, tip: 66, hip: [-0.3, 0.2], a: { ankle: [-1.16, 0.14], foot: -80 }, b: { ankle: [-1.16, 0.14], foot: -80 } },
    prone(1.15, SET_HANDS, 44), prone(1.4)] },
  // Off the front foot of a kneel, leaning in, the back knee coming through: the kneel posture's
  // own legs to start (human-life.js POSTURES.kneel: left foot planted, right knee down).
  rise_kneel: { from: 'kneel', ends: 'stand', shift: 0.57, fixedSide: 'l', keys: [
    { at: 0, tip: 0, lean: -6, hip: [-0.57, 0.445], a: { ankle: [-0.15, 0.07], foot: 0 }, b: { ankle: [-1.2, 0.09], foot: -170 }, look: 4 },
    { at: 0.3, tip: 30, hip: [-0.35, 0.56], a: { ankle: [-0.15, 0.07], foot: 0 }, b: { ankle: [-1.1, 0.12], foot: -62 }, look: 8 },
    stride(0.62, 20)] },
  // From the crouch: weight forward over the feet and up, one foot stepping through.
  rise_crouch: { from: 'crouch', ends: 'stand', shift: 0.405, keys: [
    { at: 0, tip: 0, lean: -24, hip: [-0.405, 0.36], a: { ankle: [-0.15, 0.07], foot: 0 }, b: { ankle: [-0.125, 0.07], foot: 0 }, look: 14 },
    { at: 0.25, tip: 32, hip: [-0.25, 0.55], a: { ankle: [-0.15, 0.07], foot: 0 }, b: { ankle: [-0.14, 0.12], foot: -35 }, look: 10 },
    stride(0.55, 22)] },
  // Off both knees: one foot forward to a kneel, then up off it.
  rise_kneel2: { from: 'kneel2', ends: 'stand', shift: 0.45, keys: [
    { at: 0, tip: 0, lean: -3, hip: [-0.45, 0.5], a: { ankle: [-0.9, 0.09], foot: -170 }, b: { ankle: [-0.9, 0.09], foot: -170 }, look: 2 },
    { at: 0.32, tip: 12, hip: [-0.48, 0.47], a: { ankle: [-0.2, 0.1], foot: 0 }, b: { ankle: [-1.0, 0.09], foot: -170 }, look: 6 },
    { at: 0.62, tip: 30, hip: [-0.3, 0.58], a: { ankle: [-0.15, 0.07], foot: 0 }, b: { ankle: [-0.95, 0.12], foot: -62 }, look: 8 },
    stride(0.92, 20)] },
});

/**
 * Which motion takes a figure from posture `from` to `to` (or null: the plain blend), and how
 * it goes for this figure: the leading side, the speed and a little of its own in the poses.
 * `spring`: a run follows at once (jaunt-stage.js looks ahead to the next beat).
 */
export function chooseMotion(from, to, { id = 'human', spring = false, seconds = 0.9 } = {}) {
  const rand = seededRandom(`motion:${id}`);
  let name = null;
  if (from === 'prone' && to === 'stand') name = !spring ? 'rise_prone_calm' : rand() < 0.62 ? 'rise_prone_knee' : 'rise_prone_fours';
  else if (from === 'stand' && to === 'prone') name = 'down_prone';
  else if (spring && to === 'stand' && (from === 'kneel' || from === 'crouch' || from === 'kneel2')) name = `rise_${from}`;
  if (!name) return null;
  const def = MOTIONS[name];
  // A man's own pace: about a fifth either side, and the beat's ease asks a little of it.
  const tempo = (0.82 + 0.4 * rand()) * Math.min(1.25, Math.max(0.85, (Number.isFinite(seconds) ? seconds : 1) / 1.1));
  const side = def.fixedSide ?? (rand() < 0.5 ? 'l' : 'r');
  const own = { tip: (rand() - 0.5) * 10, hip: (rand() - 0.5) * 0.06, look: rand() * 12, out: (rand() - 0.5) * 0.06 };
  const keys = def.keys;
  const end = keys.at(-1).at * tempo;
  return { name, def, keys, tempo, side, own, t: 0, end, release: end, out: def.ends === 'stand' ? 0.35 : 0, shift: def.shift, ends: def.ends, queued: null, released: false };
}

/** The pose at the motion's time now: the keys either side, eased. Numbers only, in the ground
 *  frame; humans.js turns it into the root's tip and place, human-life.js into the legs,
 *  human-actions.js into the hands. `w`: how much of it is on the body (1, falling to 0 over `out`
 *  after the end of a rise, as the run takes over). */
export function motionFrame(m) {
  const T = m.t / m.tempo, keys = m.keys;
  let i = 0;
  while (i < keys.length - 2 && T >= keys[i + 1].at) i++;
  const k0 = keys[i], k1 = keys[Math.min(i + 1, keys.length - 1)];
  const span = k1.at - k0.at;
  const u = span > 1e-6 ? smooth(Math.min(1, Math.max(0, (T - k0.at) / span))) : 1;
  const num = (f, d = 0) => lerp(k0[f] ?? d, k1[f] ?? d, u);
  const inner = (k) => (k === 0 || k === keys.length - 1 ? 0 : 1); // the figure's own touch, off at the ends
  const ownK = lerp(inner(i), inner(Math.min(i + 1, keys.length - 1)), u);
  const leg = (s) => ({
    ankle: [lerp(k0[s].ankle[0], k1[s].ankle[0], u), lerp(k0[s].ankle[1], k1[s].ankle[1], u)],
    foot: lerp(k0[s].foot, k1[s].foot, u),
  });
  const hand = (s) => {
    const h0 = k0.hands?.[s] ?? null, h1 = k1.hands?.[s] ?? null;
    const w0 = h0 ? (k0.handsW ?? 1) : 0, w1 = h1 ? (k1.handsW ?? 1) : 0;
    const p0 = h0 ?? h1, p1 = h1 ?? h0;
    if (!p0) return null;
    const w = lerp(w0, w1, u);
    if (!(w > 1e-3)) return null;
    return { pos: p0.pos.map((v, j) => lerp(v, p1.pos[j], u) + (j === 2 ? m.own.out * ownK : 0)), pole: p0.pole.map((v, j) => lerp(v, p1.pole[j], u)), w };
  };
  const after = m.t - m.release;
  const w = m.out > 0 && after > 0 ? 1 - smooth(Math.min(1, after / m.out)) : 1;
  return {
    w, side: m.side,
    tip: num('tip') + m.own.tip * ownK,
    hip: [lerp(k0.hip[0], k1.hip[0], u), lerp(k0.hip[1], k1.hip[1], u) + m.own.hip * ownK],
    a: leg('a'), b: leg('b'),
    lean: num('lean'), look: num('look') + m.own.look * ownK, spread: num('spread'),
    hands: { a: hand('a'), b: hand('b') },
  };
}
