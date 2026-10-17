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
 * DEV ONLY. It is shown on the dev preview (whose banner `#__devpill` the
 * preview script injects, and whose path carries `/dev/`) and anywhere with
 * `?pacing=read`; production without the parameter never shows it. It takes the
 * visitor's camera for about half a minute, which is a tool, not a feature.
 */

export const MOVES = ['walk', 'turn', 'flight'];
export const MODES = ['fixed', 'adaptive'];
export const READ_TIER = 'light';
export const READ_SECONDS = 5;

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

/** The text the visitor copies back: one block, readable in a chat message. */
export function formatReading(result) {
  const f = (x) => (Number.isFinite(x) ? x.toFixed(1) : '—');
  const lines = [
    `Read frame pacing (T-2733) — ${result.when}`,
    `${result.device.screen} at ratio ${result.device.ratio}, detail ${result.tier}, ${result.seconds} s a mode`,
    `${result.device.ua}`,
    `build ${result.build}`,
    '',
    'move    mode      draws  mean    sd   med   p95   max  >33 >50',
  ];
  for (const move of Object.keys(result.pairs)) {
    for (const mode of MODES) {
      const r = result.pairs[move][mode];
      lines.push(`${move.padEnd(7)} ${mode.padEnd(9)} ${String(r.draws).padStart(5)} ${f(r.mean).padStart(5)}`
        + ` ${f(r.sd).padStart(5)} ${f(r.median).padStart(5)} ${f(r.p95).padStart(5)} ${f(r.max).padStart(5)}`
        + ` ${String(r.over33).padStart(4)}${String(r.over50).padStart(4)}`);
    }
    const p = result.pairs[move];
    lines.push(`  ${fell(p) ? 'FELL' : 'DID NOT FALL'}: sd ${f(p.fixed.sd)} → ${f(p.adaptive.sd)} ms,`
      + ` p95 ${f(p.fixed.p95)} → ${f(p.adaptive.p95)} ms`);
  }
  return lines.join('\n');
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rad = (d) => d * Math.PI / 180;

/** The poses of `driveLive`, move for move. */
function poseFor(a, move) {
  const anchors = new Map((a.scene?.anchors ?? []).map((x) => [x.id, x]));
  const pick = (...ids) => ids.map((id) => anchors.get(id)).find(Boolean) ?? a.scene?.anchors?.[0];
  if (move === 'walk') {
    const v = a.walkBudget?.speed ?? 1.4;
    const s = pick('lake_at_canal', 'spawn');
    const b = s.yaw_deg ?? 90;
    return (t) => {
      const d = Math.min(40, v * t);
      const d2 = Math.max(0, v * t - 40);
      return { local_e: s.local_e + Math.sin(rad(b)) * d + Math.sin(rad(b + 90)) * d2,
        local_n: s.local_n + Math.cos(rad(b)) * d + Math.cos(rad(b + 90)) * d2,
        yaw_deg: d2 > 0 ? b + 90 : b };
    };
  }
  if (move === 'turn') {
    const s = pick('lake_market', 'lake_at_canal', 'spawn');
    return (t) => ({ local_e: s.local_e, local_n: s.local_n, yaw_deg: (s.yaw_deg ?? 0) + 45 * t });
  }
  const s = pick('from_above', 'aerial');
  return (t) => ({ local_e: s.local_e + 12 * t, local_n: s.local_n, yaw_deg: s.yaw_deg ?? 0,
    altitude_m: s.altitude_m ?? 120, pitch_deg: s.pitch_deg ?? -30 });
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
  const render = a.renderer.render;
  a.renderer.render = function timed(...args) {
    if (a.renderer.getRenderTarget() === null) starts.push(performance.now());
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
  return summarise(starts);
}

/**
 * The whole reading. `a` is the page's handle (`window.__chicago4d`).
 * `onStep(label, i, n)` is told before each of the six drives.
 */
export async function readFramePacing(a, { seconds = READ_SECONDS, tier = READ_TIER, onStep = null } = {}) {
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
  try {
    await a.setDetail(tier);
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
    when: new Date().toISOString(), tier, seconds, build: a.version ?? '',
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
  row.hidden = false;
  status.hidden = false;
  const handle = { running: false, result: null, text: '' };
  btn.addEventListener('click', async () => {
    if (handle.running) return;
    handle.running = true;
    btn.disabled = true;
    copy.hidden = true;
    out.hidden = true;
    hud?.setPanel?.(false);
    try {
      handle.result = await readFramePacing(api, {
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
      hud?.setPanel?.(true);
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
