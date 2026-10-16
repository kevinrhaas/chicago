/**
 * THE FRAME GOVERNOR — T-2555.
 *
 * "Jittery" is often not a slow frame but an UNEVEN one: a phone alternating
 * 16 ms and 33 ms frames reads as stutter, and the same phone held at a steady
 * 33 ms reads as smooth. Until this, nothing in the renderer adapted to the
 * device: the pixel ratio was the Sharpness setting (T-2110), the sun's shadow
 * map re-rendered every frame, and the loop drew as fast as rAF fired.
 *
 * This decides three things for the frame about to be drawn, from the
 * intervals between the frames already drawn (rAF timestamps — the one clock
 * every device has):
 *
 *   scale   a multiple of the visitor's Sharpness ratio, between FLOOR and 1.
 *           Sharpness is the CEILING: the governor only ever draws fewer pixels
 *           than the visitor chose, never more.
 *   pace    1 = draw on every rAF, 2 = a steady 30 fps (draw when 1/30 s has
 *           passed), taken only by a device that cannot hold 60 at the floor
 *           and can hold 30.
 *   shadow  whether the sun's shadow map is re-rendered this frame. On `light`
 *           while moving it is re-rendered every second drawn frame: the sun
 *           does not move during a walk, only the eye does.
 *
 * At rest — the camera has not moved for `restFrames` drawn frames, which is a
 * twentieth of a second at 60 and short of the frame a mouse look skips an
 * event on — all three go back to neutral at once: scale 1, pace 1, a shadow every frame. That is what keeps
 * every still frame, and so every capture, exactly what it was before the
 * governor existed. `Fixed` in Settings holds them neutral always.
 *
 * Pure logic, no three.js and no DOM, so `tools/test_frame_governor.mjs` drives
 * it with synthetic frame times in Node.
 */

export const GOVERNOR = Object.freeze({
  /** The lowest multiple of the Sharpness ratio a moving frame is drawn at. */
  floor: 0.67,
  /** Drawn moving frames read per decision; one decision per window, so a
   *  change is always followed by a full window of frames drawn under it. */
  window: 10,
  /** p80 of a window above this (ms) is a device not holding 60: 1/60 s plus
   *  10 %, so ordinary rAF jitter on a device that holds 60 is not a breach. */
  budget60: 18.3,
  /** At or below this (ms) a moving window holds 60. rAF never reports a frame
   *  faster than the display's own interval, so "holds 60" is all a window can
   *  say about headroom; the step back up is therefore earned over `upAfter`
   *  windows in a row, and a step up that fails at once doubles that wait (up
   *  to `upAfterMax`) — the hysteresis that stops a ratio see-sawing on a
   *  device that sits on the boundary. */
  headroom60: 17.5,
  upAfter: 3,
  upAfterMax: 48,
  /** At the floor and still over budget, a p80 at or under this (ms) can hold
   *  a steady 30, so the governor paces there. Above it a device cannot hold 30
   *  either, and pacing would only add an idle rAF to an already slow frame. */
  hold30: 33.5,
  /** Paced and still above this (ms): 30 is not holding either — unpace. */
  fail30: 38,
  /** Paced for this long while moving (ms), try 60 again for one window. At the
   *  floor a device that still cannot hold 60 paces again on that window. */
  probeMs: 8000,
  /** A drawn-frame interval longer than this (ms) is a gap — a hidden tab, a
   *  long task, a ride arriving — and not a frame time. */
  gapMs: 250,
  /** Still drawn frames in a row that are a rest, not a pause between inputs. */
  restFrames: 3,
  /** One step down never cuts more than this much ratio at once, nor less. */
  stepDownMin: 0.85,
  stepDownMax: 0.95,
  /** One step up. */
  stepUp: 1 / 0.9,
  /** A paced frame is drawn once this much of 1/30 s has passed, so a 60 Hz
   *  display draws every other rAF and a 120 Hz one every fourth. */
  paceSlackMs: 4,
});

const quantile = (xs, p) => {
  const s = xs.slice().sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor(p * s.length))];
};

/**
 * @param {object} [o]
 * @param {boolean} [o.enabled=true]  false = Fixed
 * @param {string} [o.tier='full']    the scene-detail level in force
 * @param {(state) => void} [o.onChange]  called when scale, pace or mode changes
 */
export function createFrameGovernor({ enabled = true, tier = 'full', onChange = null } = {}) {
  const G = GOVERNOR;
  let on = !!enabled;
  let level = tier;
  let scale = 1;
  let pace = 1;
  let moving = false;
  let still = 0;
  let lastDrawT = null;
  let samples = [];
  let pacedMs = 0;
  let drawn = 0;
  let shadowFresh = true;
  let decisions = 0;
  let lastP80 = null;
  let good = 0;
  let upAfter = G.upAfter;
  let sinceUp = Infinity;

  const snapshot = () => ({
    mode: on ? 'adaptive' : 'fixed', scale, pace, fps: pace === 2 ? 30 : 60,
    moving, shadowEvery: on && moving && level === 'light' ? 2 : 1,
    decisions, p80: lastP80, tier: level,
  });
  let told = '';
  const tell = () => {
    const key = `${on}|${scale}|${pace}|${moving}`;
    if (key === told) return;
    told = key;
    onChange?.(snapshot());
  };

  /** Neutral: what the renderer drew before this module existed. */
  function rest() {
    scale = 1;
    pace = 1;
    samples = [];
    pacedMs = 0;
    shadowFresh = true;
    moving = false;
    good = 0;
    upAfter = G.upAfter;
    sinceUp = Infinity;
  }

  /** Before a rAF's work: false = skip this rAF (paced at 30 and too soon). */
  function shouldDraw(t) {
    if (!on || pace === 1 || lastDrawT === null) return true;
    return t - lastDrawT >= 1000 / 30 - G.paceSlackMs;
  }

  function decide(p80) {
    decisions += 1;
    lastP80 = p80;
    sinceUp += 1;
    if (pace === 1) {
      if (p80 > G.budget60) {
        good = 0;
        if (sinceUp <= 2) upAfter = Math.min(G.upAfterMax, upAfter * 2);
        if (scale > G.floor + 1e-6) {
          // Pixels go as the square of the ratio, so the ratio that would bring
          // this p80 to budget is the square root of the miss — taken in a
          // bounded step, because a window is ten frames and not a promise.
          const f = Math.sqrt(G.budget60 / p80);
          scale = Math.max(G.floor, scale * Math.min(G.stepDownMax, Math.max(G.stepDownMin, f)));
        } else if (p80 <= G.hold30) {
          pace = 2;
          pacedMs = 0;
        }
      } else if (p80 <= G.headroom60 && scale < 1 && ++good >= upAfter) {
        scale = Math.min(1, scale * G.stepUp);
        good = 0;
        sinceUp = 0;
      }
    } else if (p80 > G.fail30) {
      pace = 1;
    } else if (pacedMs >= G.probeMs) {
      // The probe: one window at 60. A device that still cannot hold it is at
      // the floor and inside hold30, so the next decision paces it again.
      pace = 1;
      pacedMs = 0;
    }
  }

  /**
   * After a drawn frame. `moved` = the camera moved during that frame.
   * Decides the scale, pace and shadow cadence of the NEXT drawn frame.
   */
  function frameDrawn(t, moved) {
    const interval = lastDrawT === null ? null : t - lastDrawT;
    lastDrawT = t;
    drawn += 1;
    if (!on) {
      rest();
      tell();
      return;
    }
    if (!moved) {
      still += 1;
      if (still >= G.restFrames) rest();
      shadowFresh = true;
      tell();
      return;
    }
    still = 0;
    moving = true;
    if (interval !== null && interval <= G.gapMs) {
      samples.push(interval);
      if (pace === 2) pacedMs += interval;
    }
    if (samples.length >= G.window) {
      const p80 = quantile(samples, 0.8);
      samples = [];
      decide(p80);
    }
    shadowFresh = level !== 'light' || drawn % 2 === 0;
    tell();
  }

  return {
    shouldDraw,
    frameDrawn,
    /** Neutral now — for a capture, a forced harness frame, a setting change. */
    rest() { rest(); tell(); },
    setEnabled(v) { on = !!v; rest(); tell(); return on; },
    /** HARNESS ONLY: put the governor where a slow moving window would have —
     *  `scale` (clamped to [floor, 1]) and `pace` — so a runner whose frames are
     *  too slow to drive it there can still ask what a rest does after it. */
    force({ scale: s = scale, pace: p = pace } = {}) {
      if (!on) return snapshot();
      scale = Math.min(1, Math.max(G.floor, s));
      pace = p === 2 ? 2 : 1;
      moving = true;
      still = 0;
      tell();
      return snapshot();
    },
    setTier(t) { level = t; },
    get enabled() { return on; },
    get scale() { return scale; },
    get pace() { return pace; },
    /** Whether the frame about to be drawn re-renders the shadow map. */
    get shadowFresh() { return shadowFresh; },
    get state() { return snapshot(); },
  };
}

/** The Settings sentence for a governor state at a pixel ratio. */
export function describeGovernor(s, ratio) {
  if (s.mode === 'fixed') return 'Fixed: every frame is drawn at the sharpness chosen above.';
  if (!s.moving || (s.scale === 1 && s.pace === 1)) {
    return 'Adaptive: at the sharpness chosen above. While you move, a slow device draws fewer pixels or a steady 30 frames a second.';
  }
  const parts = [];
  if (s.scale < 1) parts.push(`${Math.round(s.scale * 100)} % of the chosen sharpness (pixel ratio ${ratio.toFixed(2)})`);
  parts.push(s.pace === 2 ? 'a steady 30 frames a second' : 'every frame');
  return `Adaptive, moving: ${parts.join(', ')}. Back to full sharpness when you stop.`;
}
