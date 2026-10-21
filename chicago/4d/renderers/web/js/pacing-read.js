/**
 * T-2732: READ FRAME PACING — the frame governor's moving reading, taken in the
 * visitor's own browser.
 *
 * T-2592 asked whether Adaptive pacing makes a moving frame steadier, and found
 * the steward runner cannot say: with no GPU it draws the town every 0.8 to 3.6 s
 * (T-2591, T-2721), about a hundred times outside the range a governor works in,
 * so Adaptive and Fixed read alike there and any "fall" would be noise. The owner
 * chose (T-2722, answer a) to read it on his own phone — the device the "walking
 * is laggy" report came from, at its own refresh rate — with an action a run
 * builds first. This is that action.
 *
 * It drives the three moves `tools/measure_walk_frames.mjs --live` drives, with
 * the same poses, the same tier (`light`, the phone's) and the same arithmetic:
 * walk, turn and flight through the page's own animation loop, each at Fixed and
 * then at Adaptive, timing only the draws that reach the canvas (the gaze
 * target's one-pixel pick renders too, into a target, and counted as frames
 * those put intervals of a millisecond or two into every reading — T-2721).
 * Then it puts the visitor back: detail, pacing, place and flight as they were.
 *
 * T-2733, after the owner's first reading (1835, 2026-10-19) and his crashed 1904
 * attempt: the poses are now the scene's own (SCENE_POSES — in 1904 the walk had
 * fallen back to the one anchor there and gone due west across Prairie Avenue into
 * the Glessner front), the readout names the scene, the Sharpness stop and the pixel
 * ratio actually drawn, and a longer run (LONG_SECONDS a mode) is offered, so a
 * reading is attributable and less noisy. `tools/test_pacing_read.mjs` walks every
 * scene's poses against that scene's footprints.
 *
 * T-2829: each row also says how often the drawn ratio switched (every switch is a
 * drawing-buffer resize), how many of its draws over 50 ms came on a switch or the
 * draw after it, and what share of its draws were paced to 30 — so a spike like the
 * first reading's 73 ms turn frame is attributed by the readout, not by a guess.
 *
 * DEV ONLY. It is shown on the dev preview (whose banner `#__devpill` the
 * preview script injects, and whose path carries `/dev/`) and anywhere with
 * `?pacing=read`; production without the parameter never shows it. It takes the
 * visitor's camera for about half a minute, which is a tool, not a feature.
 */

export const MOVES = ['walk', 'turn', 'flight'];
export const MODES = ['fixed', 'adaptive'];
export const READ_TIER = 'light';
export const READ_SECONDS = 5;
/** The longer run (T-2733): one 5-second sample a mode was ~160 draws on the owner's
 *  phone, too thin to say whether turn and flight rose for real or by noise. */
export const LONG_SECONDS = 15;
/** The run lengths offered, the longer first: it is the one a repeat should take. */
export const SECONDS_OFFERED = [LONG_SECONDS, READ_SECONDS];
/** Fewer canvas draws than this in either mode and the pair says nothing: the
 *  runner's software rasteriser gets two or three in five seconds (T-2721), a
 *  phone at 60 Hz about three hundred. */
export const MIN_DRAWS = 20;

/** Is the action offered on this page? */
export function pacingReadOffered(loc = globalThis.location, doc = globalThis.document) {
  let param = null;
  try { param = new URLSearchParams(loc?.search ?? '').get('pacing'); } catch { /* no URL */ }
  if (param === 'read') return true;
  if (param === 'off') return false;
  if (doc?.getElementById?.('__devpill')) return true;
  return /\/4d\/dev\//.test(loc?.pathname ?? '');
}

/**
 * Intervals between consecutive draw start times, summarised exactly as
 * `driveLive` in measure_walk_frames.mjs does: population sd, and the p95 read
 * as the floor(0.95 n)-th sorted interval — so a phone's number and a runner's
 * can be set side by side.
 */
export function summarise(starts) {
  const iv = [];
  for (let i = 1; i < starts.length; i++) iv.push(starts[i] - starts[i - 1]);
  const sorted = iv.slice().sort((x, y) => x - y);
  const q = (p) => sorted[Math.min(sorted.length - 1, Math.floor(p * sorted.length))] ?? 0;
  const mean = iv.reduce((t, x) => t + x, 0) / Math.max(1, iv.length);
  const sd = Math.sqrt(iv.reduce((t, x) => t + (x - mean) ** 2, 0) / Math.max(1, iv.length));
  return { draws: starts.length, mean, sd, median: q(0.5), p95: q(0.95), max: sorted[sorted.length - 1] ?? 0,
    over33: iv.filter((x) => x > 33.4).length, over50: iv.filter((x) => x > 50).length };
}

/** The pair's verdict, by the rule `--live` applies: both sd AND p95 fall. */
export function fell(pair) {
  return pair.adaptive.sd < pair.fixed.sd && pair.adaptive.p95 < pair.fixed.p95;
}

/** What the copied text says of a pair — and that it cannot say, on too few draws. */
export function verdict(pair) {
  if (Math.min(pair.fixed.draws, pair.adaptive.draws) < MIN_DRAWS) return 'TOO FEW FRAMES TO SAY';
  return fell(pair) ? 'FELL' : 'DID NOT FALL';
}

/** Sharpness's three stops by name (sharpness.js SHARPNESS_STOPS). */
const STOP_NAMES = new Map([[1, 'Low'], [1.5, 'Medium'], [2, 'High']]);
const ratioText = (x) => (Number.isFinite(x) ? String(Math.round(x * 100) / 100) : '?');

/** The line naming the Sharpness ceiling and the ratio drawn when the reading began. */
export function describeSharpness(sh) {
  if (!sh) return 'sharpness unknown';
  const name = STOP_NAMES.get(sh.ceiling);
  return `sharpness ${name ? `${name} (${ratioText(sh.ceiling)})` : `cap ${ratioText(sh.ceiling)}`},`
    + ` drawn at ${ratioText(sh.ratio)} at rest`;
}

/** A drive's pixel ratios as one value, or the range Adaptive scaled across. */
export function ratioRange(r) {
  if (!r || !Number.isFinite(r.min)) return '?';
  return Math.abs(r.max - r.min) < 0.005 ? ratioText(r.min) : `${ratioText(r.min)}-${ratioText(r.max)}`;
}

/** T-2829: a drive's ratio switches, the draws over 50 ms that came on one, and the
 *  share of its draws paced to 30 — nothing when the drive carries no such count.
 *  T-2970: and the driver's draws a frame, where the page could count them. */
export function drawNotes(r) {
  if (!r || !Number.isFinite(r.switches)) return '';
  const parts = [];
  if (r.switches) {
    parts.push(`${r.switches} switch${r.switches === 1 ? '' : 'es'} (${r.slowAtSwitch ?? 0} of the >50 on one)`);
  }
  if (r.paced) parts.push(`paced ${Math.round((100 * r.paced) / Math.max(1, r.draws))} %`);
  // T-2970: what the GPU driver received for a frame, median and worst — the
  // figure the draw budgets read, where three's own counter takes a batch as one.
  if (r.driverDraws) parts.push(`driver draws ${r.driverDraws.median} (max ${r.driverDraws.max})`);
  return parts.length ? `, ${parts.join(', ')}` : '';
}

/** The text the visitor copies back: one block, readable in a chat message. */
export function formatReading(result) {
  const f = (x) => (Number.isFinite(x) ? x.toFixed(1) : '—');
  const lines = [
    `Read frame pacing (T-2733) — ${result.when}`,
    `${result.device.screen} at ratio ${result.device.ratio}, detail ${result.tier}, ${result.seconds} s a mode`,
    `scene ${result.scene ?? '?'}, ${describeSharpness(result.sharpness)}`,
    `${result.device.ua}`,
    `build ${result.build}`,
    '',
    'move    mode      draws  mean    sd   med   p95   max  >33 >50  drawn at',
  ];
  for (const move of Object.keys(result.pairs)) {
    for (const mode of MODES) {
      const r = result.pairs[move][mode];
      lines.push(`${move.padEnd(7)} ${mode.padEnd(9)} ${String(r.draws).padStart(5)} ${f(r.mean).padStart(5)}`
        + ` ${f(r.sd).padStart(5)} ${f(r.median).padStart(5)} ${f(r.p95).padStart(5)} ${f(r.max).padStart(5)}`
        + ` ${String(r.over33).padStart(4)}${String(r.over50).padStart(4)}  ${ratioRange(r.ratio)}${drawNotes(r)}`);
    }
    const p = result.pairs[move];
    lines.push(`  ${verdict(p)}: sd ${f(p.fixed.sd)} → ${f(p.adaptive.sd)} ms,`
      + ` p95 ${f(p.fixed.p95)} → ${f(p.adaptive.p95)} ms`);
  }
  return lines.join('\n');
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rad = (d) => d * Math.PI / 180;

/**
 * T-2733: each scene's three poses, in local ENU metres. A walk is a path of legs
 * (bearing, metres) walked at the visitor's pace and held at its end; a turn stands
 * at one place and turns 45 degrees a second; a flight crosses east at 12 m/s at
 * its altitude, looking along its yaw. `tools/test_pacing_read.mjs` holds every walk
 * and stand outside every structure footprint of its scene (with a shoulder's
 * clearance and more), and every walk long enough for LONG_SECONDS at a jog.
 *
 * 1835 is `driveLive`'s, move for move (measure_walk_frames.mjs): the walk from
 * `lake_at_canal` east 40 m and then south, the turn at `lake_market`, the flight
 * from `from_above` — so the owner's first reading and a repeat compare.
 */
export const SCENE_POSES = Object.freeze({
  1812: {
    // From the spawn west of the fort, east along the open ground south of its
    // pickets and north of the officers' garden.
    walk: { from: [1112, 180], legs: [[90, 100]] },
    turn: { at: [1112, 180], yaw_deg: 45 },
    flight: { from: [1152, 60], yaw_deg: 0, altitude_m: 120, pitch_deg: -35 }, // first_fort_from_above
  },
  1835: {
    walk: { from: [-159.7, -108.4], legs: [[90, 40], [180, 60]] }, // lake_at_canal
    turn: { at: [89.2, -110.4], yaw_deg: 135 }, // lake_market
    flight: { from: [60, -330], yaw_deg: 0, altitude_m: 175, pitch_deg: -30 }, // from_above
  },
  1904: {
    // Prairie Avenue's east walk, south from 18th Street along the middle of the
    // walk band (data/street_grid/1904.json, face prairie__prairie_calumet_18_20),
    // parallel to the street: the visitor's own first steps from the spawn, with
    // Glessner across the street — never across the street into its front.
    walk: { from: [1410.67, -3218.2], legs: [[179.42, 240]] },
    turn: { at: [1410.12, -3218.01], yaw_deg: 264.94 }, // the spawn, glessner_house
    flight: { from: [1330, -3330], yaw_deg: 0, altitude_m: 120, pitch_deg: -30 },
  },
});

/** The scene the page is showing, as SCENE_POSES keys it. */
export function sceneOf(a) {
  return String(a?.scene?.id ?? a?.year ?? '');
}

/** Where a walk stands `d` metres along its legs, and which way it faces; held at the end. */
export function walkAt(walk, d) {
  let [e, n] = walk.from;
  let yaw = walk.legs[0][0];
  let left = Math.max(0, d);
  for (const [bearing, len] of walk.legs) {
    yaw = bearing;
    const step = Math.min(left, len);
    e += Math.sin(rad(bearing)) * step;
    n += Math.cos(rad(bearing)) * step;
    left -= step;
    if (left <= 0) break;
  }
  return { local_e: e, local_n: n, yaw_deg: yaw };
}

/** A move's pose as a function of seconds, for the scene `poses` describes. */
export function poseFrom(poses, move, speed = 1.4) {
  if (move === 'walk') return (t) => walkAt(poses.walk, speed * t);
  if (move === 'turn') {
    const s = poses.turn;
    return (t) => ({ local_e: s.at[0], local_n: s.at[1], yaw_deg: s.yaw_deg + 45 * t });
  }
  const s = poses.flight;
  return (t) => ({ local_e: s.from[0] + 12 * t, local_n: s.from[1], yaw_deg: s.yaw_deg,
    altitude_m: s.altitude_m, pitch_deg: s.pitch_deg });
}

function poseFor(a, move) {
  const poses = SCENE_POSES[sceneOf(a)];
  // A scene with no poses of its own gets no reading: a fallback is how 1904's walk
  // ended inside a house (T-2828).
  if (!poses) throw new Error(`no reading poses for scene ${sceneOf(a) || '?'}`);
  return poseFrom(poses, move, a.walkBudget?.speed ?? 1.4);
}

/** One move at one mode, through the animation loop, for `seconds`. */
async function driveOne(a, move, mode, seconds) {
  a.setGovernor(mode === 'adaptive');
  const pose = poseFor(a, move);
  a.setFly(move === 'flight');
  a.walker.teleport(pose(0));
  // At rest first, so both modes start from the same neutral state.
  await sleep(800);
  const starts = [];
  const ratio = { min: Infinity, max: -Infinity };
  // T-2829: the ratio is set before the frame's work, so a resize's cost falls in
  // the interval that ends at the first draw at the new ratio, or the one after.
  const notes = { switches: 0, slowAtSwitch: 0, paced: 0 };
  let lastRatio = null;
  let sinceSwitch = Infinity;
  const driver = [];
  const render = a.renderer.render;
  a.renderer.render = function timed(...args) {
    if (a.renderer.getRenderTarget() === null) {
      const now = performance.now();
      const r = a.renderer.getPixelRatio();
      if (lastRatio !== null && Math.abs(r - lastRatio) > 1e-9) { notes.switches += 1; sinceSwitch = 0; } else sinceSwitch += 1;
      if (starts.length && now - starts[starts.length - 1] > 50 && sinceSwitch <= 1) notes.slowAtSwitch += 1;
      if (a.governor?.pace === 2) notes.paced += 1;
      lastRatio = r;
      starts.push(now);
      if (r < ratio.min) ratio.min = r;
      if (r > ratio.max) ratio.max = r;
      const out = render.apply(this, args);
      const n = a.driverDraws?.draws;
      if (Number.isFinite(n)) driver.push(n);
      return out;
    }
    return render.apply(this, args);
  };
  const t0 = performance.now();
  try {
    await new Promise((resolve) => {
      const frame = () => {
        const el = (performance.now() - t0) / 1000;
        if (el >= seconds) { resolve(); return; }
        a.walker.teleport(pose(el));
        requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
    });
  } finally {
    a.renderer.render = render;
  }
  driver.sort((x, y) => x - y);
  const driverDraws = driver.length ? { median: driver[Math.floor(driver.length / 2)], max: driver[driver.length - 1] } : null;
  return { ...summarise(starts), ratio, ...notes, driverDraws };
}

/**
 * The whole reading. `a` is the page's handle (`window.__chicago4d`).
 * `onStep(label, i, n)` is told before each of the six drives.
 */
export async function readFramePacing(a, { seconds = READ_SECONDS, tier = READ_TIER, onStep = null } = {}) {
  if (!SCENE_POSES[sceneOf(a)]) throw new Error(`no reading poses for scene ${sceneOf(a) || '?'}`);
  const welcome = a.welcome;
  // Under the welcome the loop draws only a frame that changed (T-2113) and the
  // governor is held at rest, so nothing live can be read there.
  const deadline = Date.now() + 60_000;
  while (welcome && welcome.state !== 'world' && Date.now() < deadline) {
    if (welcome.state === 'welcome') welcome.enter('spawn');
    await sleep(100);
  }
  const p = a.player;
  const before = { detail: a.detail, adaptive: a.governor.mode === 'adaptive', flying: !!p.flying,
    pose: { local_e: p.e, local_n: p.n, yaw_deg: p.bearingDeg, pitch_deg: p.pitchDeg,
      altitude_m: p.flying ? p.altitude : null } };
  const pairs = {};
  let sharpness = null;
  try {
    await a.setDetail(tier);
    // The ceiling is the visitor's Sharpness capped by the device; the ratio is
    // what the canvas draws at rest, before any move scales it.
    const g = a.governor;
    sharpness = { ceiling: g?.ceiling, ratio: a.renderer?.getPixelRatio?.() ?? g?.ratio };
    let i = 0;
    for (const move of MOVES) {
      pairs[move] = {};
      for (const mode of MODES) {
        onStep?.(`${move}, ${mode === 'fixed' ? 'Fixed' : 'Adaptive'}`, i++, MOVES.length * MODES.length);
        pairs[move][mode] = await driveOne(a, move, mode, seconds);
      }
    }
  } finally {
    await a.setDetail(before.detail);
    a.setGovernor(before.adaptive);
    a.walker.teleport(before.pose);
    a.setFly(before.flying);
  }
  const s = globalThis.screen;
  return {
    when: new Date().toISOString(), tier, seconds, build: a.version ?? '', scene: sceneOf(a), sharpness,
    device: { screen: `${innerWidth}x${innerHeight}${s ? ` (screen ${s.width}x${s.height})` : ''}`,
      ratio: devicePixelRatio, ua: navigator.userAgent },
    pairs,
  };
}

/**
 * Mounts the button under Settings → Performance, when it is offered.
 * `hud` closes the panel for the reading so the canvas is what is drawn.
 */
export function mountPacingRead({ api, hud, doc = document }) {
  const row = doc.getElementById('pacing-read');
  if (!row || !pacingReadOffered(doc.location, doc)) return null;
  const btn = doc.getElementById('s-pacing-read');
  const status = doc.getElementById('pacing-read-status');
  const out = doc.getElementById('pacing-read-out');
  const copy = doc.getElementById('s-pacing-copy');
  const length = doc.getElementById('pacing-read-length');
  const lengthSelect = doc.getElementById('s-pacing-seconds');
  row.hidden = false;
  status.hidden = false;
  if (length) length.hidden = false;
  // `seconds` is a mode's drive; a harness on a slow rasteriser may shorten it.
  const chosen = () => {
    const n = Number(lengthSelect?.value);
    return SECONDS_OFFERED.includes(n) ? n : LONG_SECONDS;
  };
  const handle = { running: false, result: null, text: '', seconds: chosen() };
  const describe = () => {
    // Six drives, each with its moment at rest first, and the detail switch.
    const total = MOVES.length * MODES.length * (handle.seconds + 0.8) + 3;
    status.textContent = `Walks, turns and flies for about ${total < 60 ? `${Math.round(total / 5) * 5} seconds`
      : `${Math.round(total / 30) / 2} minutes`} at Light, Fixed then Adaptive, and puts you back where you were.`;
  };
  lengthSelect?.addEventListener('change', () => {
    handle.seconds = chosen();
    if (!handle.running) describe();
  });
  describe();
  btn.addEventListener('click', async () => {
    if (handle.running) return;
    handle.running = true;
    btn.disabled = true;
    if (lengthSelect) lengthSelect.disabled = true;
    copy.hidden = true;
    out.hidden = true;
    hud?.setPanel?.(false);
    try {
      handle.result = await readFramePacing(api, { seconds: handle.seconds,
        onStep: (label, i, n) => { status.textContent = `Reading ${i + 1} of ${n}: ${label}…`; },
      });
      handle.text = formatReading(handle.result);
      out.value = handle.text;
      out.hidden = false;
      copy.hidden = false;
      status.textContent = 'Done. Copy the result and send it back (T-2733).';
    } catch (e) {
      status.textContent = `The reading stopped: ${e?.message ?? e}`;
    } finally {
      handle.running = false;
      btn.disabled = false;
      if (lengthSelect) lengthSelect.disabled = false;
      hud?.setPanel?.(true);
      out.hidden ? status.scrollIntoView?.({ block: 'nearest' }) : out.scrollIntoView?.({ block: 'nearest' });
    }
  });
  copy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(out.value);
      status.textContent = 'Copied.';
    } catch {
      // No clipboard permission: select it so a long press copies it.
      out.focus();
      out.select();
      status.textContent = 'Selected — copy it from the box.';
    }
  });
  api.pacingRead = handle;
  return handle;
}
