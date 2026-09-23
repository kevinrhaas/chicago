/**
 * facades.js — why no two buildings in this town are the same colour.
 *
 * The owner's report (T-0002, legacy K4; this half is T-0048): the buildings "read as freshly
 * painted and identical". Both halves of that were literally true of the
 * render. Every wall in the town took its colour from its ARCHETYPE — 114 wall
 * slots carrying four base colours between them (R-W2a §1) — so two neighbours
 * of the same archetype were the same brown to the bit, and nothing anywhere
 * asked how long a building had been standing in the weather.
 *
 * What this module is, in the project's own vocabulary
 * ---------------------------------------------------
 * It is **reconstructed** — invented within bounds because the scene needs it
 * and nothing states it (AGENTS.md § RECONSTRUCTED IS A TIER). No source this
 * repository holds gives the colour of any wall in 1835 Chicago, and the
 * dataset says so itself: of 335 records, `paint` is `reconstructed` on 236,
 * `inferred` on 15, and **`attested` on exactly two**. So the honest move is
 * not to leave 333 buildings identical — it is to vary them within a stated
 * bound, record the invention in `docs/LIBERTIES.md`, and NEVER touch the two
 * records a source actually speaks for.
 *
 * The one hard rule: **a record whose paint is `attested` is not touched at
 * all** — not weathered, not jittered, not by a thousandth. That is the
 * Sauganash's documented white (`Wau-Bun`) and the one attested `unpainted`.
 * `toneFor` returns the identity tone for them and says so in `reason`, and the
 * smoke asserts their drawn colour is unchanged to the bit.
 *
 * The two inputs, and why they are the ones available
 * --------------------------------------------------
 * **1. Age, where the dataset has one.** `documented_range.from` is the earliest
 * date the record is claimed to have stood in this form. Against the scene's
 * target date it gives an age in years: 1816 for the fort's buildings, 1833 for
 * the Green Tree, 1835 for most of the anonymous infill. Older wood silvers —
 * `docs/research/04-structures-south.md` reads the fort in 1835 as "serviceable,
 * weathered, whitewashed/unpainted log-and-brick" `[INF]`, which is the closest
 * thing to a statement about surface condition this repository holds.
 *
 * **The limit, stated rather than hidden: for the 262 records dated 1835-01-01
 * the date is a SCENE-PROGRAMME date, not a construction date.** Those records
 * are the inferred infill; the programme places them in the 1835 town and says
 * nothing about when they were built. So their age reads as ~0 and they get
 * essentially no silvering, which is not a claim that they are new — it is the
 * absence of a claim. Inventing ages for them would be a second reconstruction
 * stacked on the first, and it is not needed: the jitter below is what makes
 * them differ from each other.
 *
 * **2. Identity.** A deterministic hash of `id|phase` gives every structure its
 * own small offset in value and in warmth. Deterministic because a scene that
 * repainted itself on reload would make every frame gate in this suite
 * non-reproducible, and keyed on the record's own identity because that is the
 * only per-building quantity in the dataset that is not evidence.
 *
 * What it does NOT do
 * -------------------
 * - It does not read material names. On 38 of the 334 shipped assets
 *   `gltf-transform`'s palette pass folds the names away entirely (ROADMAP
 *   K36(a)), so a name-keyed rule would silently skip exactly the buildings
 *   with the most materials. The tone is per STRUCTURE and multiplies whatever
 *   that structure's surfaces are, textured or not.
 * - It does not add a draw call. The tone is folded into the per-vertex colour
 *   the batch already carries (R-W5a), so the untextured town stays one batch.
 * - It does not change board WIDTH or the lap rhythm. That is geometry, it
 *   needs the nightly bake, and it is the other half of T-0002 — ticket T-0049.
 */

/**
 * The bounds of the invention. Every number here is a limit on how far a
 * surface may be moved from the colour its archetype baked, and none of them is
 * derived from a source, because no source states one.
 *
 * `silverMax` and `soilMax` are set so that the oldest building in the town
 * (the fort, 19 years) reads as visibly grey and dirty beside a new one without
 * either of them reaching a colour the archetype could not have baked: 0.35 of
 * the way to its own luminance is still recognisably the same brown, and 0.10
 * of darkening is under the spread the archetypes already use between their own
 * wall finishes.
 *
 * `jitterValue` and `jitterWarm` are the "no two alike" half, and their ceiling
 * is the one bound this file can take from something already committed: **the
 * spread the archetypes themselves bake.** An unpainted wall is
 * `0.52, 0.44, 0.34` and an outbuilding's board is `0.335, 0.310, 0.268`
 * (R-W2a §1) — about 30 % of value between two surfaces this project already
 * calls the same material. ±16 % of value sits inside that, so no building is
 * tinted to a shade the generators could not have given it outright, and it is
 * a difference a visitor reads as two houses rather than two paints.
 *
 * They were ±10 % and ±4.5 % when this shipped, and the frames said that was
 * too little: photographed at `lake_market` and `from_above` with the tone on
 * and off, the two pictures were hard to tell apart. The measurement was never
 * the problem — 331 tones, no two neighbours alike — but the acceptance clause
 * is written about what a visitor SEES, and a difference only an instrument can
 * find does not discharge it.
 */
export const FACADE = {
  /** Years of exposure at which weathering is complete. */
  ageFullYears: 12,
  /** How far a fully weathered surface moves toward its own luminance. */
  silverMax: 0.35,
  /** How far a fully weathered surface darkens (rain, smoke, mud). */
  soilMax: 0.10,
  /** Per-building value jitter, plus or minus. */
  jitterValue: 0.16,
  /** Per-building warm/cool tilt, plus or minus, applied to red against blue. */
  jitterWarm: 0.07,
  /** Lime is renewed; a whitewashed wall silvers at this fraction of the rate. */
  whitewashRate: 0.5,
  /**
   * THE REPULSION (T-0047), and every number in it is a bound on the SAME
   * invention the jitter above already declares — not a new one. A candidate
   * tone is drawn from the identical interval `jitterValue` fences, so nothing
   * here can put a wall outside L126's stated bounds; what the pass chooses is
   * WHICH of the deals a building takes, not how far it may go.
   *
   * `repelReach` is 60 m because that is what "neighbouring" already means in
   * this project — the figure `tools/measure_facade_variety.mjs` measures pairs
   * at and `tools/smoke_renderer.mjs` asserts the no-two-alike invariant at,
   * and the nearest structure within a 126 m platted block face.
   *
   * `repelTarget` is 0.14 of applied value for two buildings standing on the
   * same spot, falling linearly to nothing at the reach. It is a FLOOR the pass
   * tries to clear and stops caring about the moment it does — deliberately,
   * because the acceptance is a RATIO (a tenth percentile at least half the
   * median) and a cost that also pulled a well-separated pair back toward the
   * target would collapse the town: measured, a two-sided cost took the median
   * pair from 10.3 % to 4.9 % and the ratio DOWN to 0.31. A floor asks the tail
   * to reach where the middle already stands; it never asks the middle to come
   * back down.
   *
   * `repelCandidates` is 32, and the ladder was measured rather than guessed —
   * over the 329 nearest-neighbour pairs, the tenth percentile goes 6.6 % at 8
   * candidates, 7.2 % at 16, 7.7 % at 32, 7.8 % at 48 and 7.9 % at 64, which is
   * where it stops paying. The whole pass is 339 x 32 x 2 hashes of a short
   * string — about 22k, under a millisecond, once at load.
   */
  repelReach: 60,
  repelTarget: 0.14,
  repelCandidates: 32,
  /**
   * Two sweeps. The first deals in id order against the neighbours dealt SO
   * FAR, which is what makes the answer independent of anything but the ids;
   * the second re-offers every building the same candidates against the
   * finished town, so the buildings dealt early — which saw an empty
   * neighbourhood — get the same information as the ones dealt late. It is
   * worth exactly one repeat: one sweep reads 0.537 on the acceptance ratio,
   * two reads 0.580, and three and four read 0.580 unchanged.
   */
  repelSweeps: 2,
  /** Masonry does not silver at all, and its jitter is halved. */
  masonry: ['brick', 'stone', 'earth'],
  masonryJitter: 0.5,
};

/** Rec. 709 luminance, in the renderer's linear working space. */
function luminance(r, g, b) {
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * FNV-1a over the record's identity. Any stable hash would do; this one is four
 * lines and has no dependencies, which matters in a renderer that vendors
 * everything it uses.
 */
function hash32(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i += 1) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Two independent uniforms in [0,1) from one hash, by splitting its halves. */
function uniforms(seed) {
  const h = hash32(seed);
  return [(h >>> 16) / 65536, (h & 0xffff) / 65536];
}

/**
 * The k-th candidate value jitter for a structure, all of them drawn from the
 * one interval `FACADE.jitterValue` fences.
 *
 * `k = 0` is the plain deal this module has always made — the hash of
 * `id|phase` — so a building with no neighbour inside the reach keeps exactly
 * the tone it had before T-0047, and the repulsion can only ever move a
 * building that has something to be told apart from.
 */
function candidateValue(sidecar, spread, k) {
  const identity = `${sidecar?.id ?? ''}|${sidecar?.phase ?? ''}`;
  const [u1] = uniforms(k === 0 ? identity : `${identity}|repel${k}`);
  return 1 + FACADE.jitterValue * spread * (u1 * 2 - 1);
}

/** How far apart two buildings this far apart are asked to stand, in applied value. */
function wanted(d) {
  return FACADE.repelTarget * Math.max(0, 1 - d / FACADE.repelReach);
}

/** Whole years between an ISO date and the scene's target date, floored at 0. */
function ageYears(fromISO, targetISO) {
  const from = Date.parse(`${String(fromISO ?? '').slice(0, 10)}T00:00:00Z`);
  const to = Date.parse(`${String(targetISO ?? '').slice(0, 10)}T00:00:00Z`);
  if (!Number.isFinite(from) || !Number.isFinite(to)) return 0;
  return Math.max(0, (to - from) / (365.2425 * 24 * 3600 * 1000));
}

/**
 * The tone for one structure: how its archetype's colours are to be moved.
 *
 * @param {object} sidecar  the record's compiled sidecar
 * @returns {{
 *   silver: number, soil: number, value: number, warm: number,
 *   age: number, paint: string|null, confidence: string|null,
 *   eligible: boolean, reason: string,
 * }}
 */
export function toneFor(sidecar) {
  const identity = { silver: 0, soil: 0, value: 1, warm: 0 };
  const paintAttr = sidecar?.attributes?.paint ?? null;
  const paint = paintAttr?.value ?? null;
  const confidence = paintAttr?.confidence ?? null;
  const age = ageYears(sidecar?.documented_range?.from, sidecar?.target_date);

  // The whole of the honesty rule, in one branch: a source spoke for this
  // surface, so nothing here may move it.
  if (confidence === 'attested') {
    return {
      ...identity, age, paint, confidence, eligible: false,
      reason: `paint is attested (${paint}) — a documented finish is never modulated`,
    };
  }

  const masonry = FACADE.masonry.includes(paint);
  const rate = masonry ? 0 : (paint === 'whitewash' ? FACADE.whitewashRate : 1);
  const weather = Math.min(1, age / FACADE.ageFullYears) * rate;

  const [, u2] = uniforms(`${sidecar?.id ?? ''}|${sidecar?.phase ?? ''}`);
  const spread = masonry ? FACADE.masonryJitter : 1;

  return {
    silver: FACADE.silverMax * weather,
    soil: FACADE.soilMax * weather,
    value: candidateValue(sidecar, spread, 0),
    warm: FACADE.jitterWarm * spread * (u2 * 2 - 1),
    age,
    paint,
    confidence,
    spread,
    /** Which candidate this tone came from — 0 until `dealTones` says otherwise. */
    deal: 0,
    eligible: true,
    reason: masonry
      ? `masonry (${paint}) — jitter only, no silvering`
      : `${paint ?? 'no stated paint'} at ${age.toFixed(1)} y`,
  };
}

/** The identity tone, for callers with no record at all. */
export const NEUTRAL_TONE = {
  silver: 0, soil: 0, value: 1, warm: 0, age: 0, paint: null, confidence: null,
  spread: 0, deal: 0, eligible: false, reason: 'no record',
};

/**
 * Apply a tone to one linear RGB triple and return the FACTORS, not the colour.
 *
 * Factors rather than colours because the renderer has to be able to wind the
 * whole thing back at runtime — `buildings.setWeathering(0)` is what lets a
 * gate photograph the same scene with and without this module and prove the
 * difference reaches the render (R-BUG6(a): a compile-time flag is not a
 * runtime handle). A per-channel factor is exact for that, because a source
 * mesh carries ONE material colour across all its vertices, so one triple
 * describes the whole range.
 *
 * Silvering is a mix toward the surface's own luminance, which is what
 * weathered wood does — it loses chroma and keeps roughly its value — and it is
 * expressed as a factor by dividing, which is why a zero channel falls back to
 * 1: a channel that is already zero cannot be moved toward anything.
 */
export function toneFactors(r, g, b, tone) {
  const lum = luminance(r, g, b);
  const mixed = [
    r + (lum - r) * tone.silver,
    g + (lum - g) * tone.silver,
    b + (lum - b) * tone.silver,
  ];
  const dim = (1 - tone.soil) * tone.value;
  const tilt = [1 + tone.warm, 1, 1 - tone.warm];
  const src = [r, g, b];
  return mixed.map((m, i) => (src[i] > 1e-6 ? (m / src[i]) * dim * tilt[i] : dim * tilt[i]));
}

/**
 * THE REPULSION PASS — why a town-wide deal needs to know where the buildings
 * stand (T-0047).
 *
 * `toneFor` is blind by construction: it hashes a record's identity and hands
 * back a tone, which is deterministic, cheap, and knows nothing about what is
 * standing next door. A blind deal has a tail, and T-0048 measured it on the
 * published mirror — over 321 nearest-neighbour pairs inside 60 m the median
 * pair differed by **10.4 %** in applied value and the tenth percentile by
 * **2.4 %**, which is at or under what a visitor can see between two walls in
 * the same light. No pair was identical — that invariant has been gated since
 * T-0002 — but about a tenth of them read as one paint.
 *
 * **The fix is not a bigger jitter.** The interval is already argued from the
 * spread the archetypes themselves bake (L126), so widening it would put walls
 * at shades the generators could not have given them outright. This is K49's
 * stratification finding one layer over: an even deal is not an even LOOK, and
 * the answer is to deal against the STRUCTURE of the thing being dealt into.
 * So every building is offered `repelCandidates` deals out of the same
 * interval and takes the one that stands furthest clear of the neighbours
 * already dealt. The bound does not move; the choice inside it does.
 *
 * **What it costs the rest of the module: nothing.** Candidate 0 is the plain
 * `id|phase` hash, so a building with nothing inside `repelReach` keeps the
 * exact tone it had before this pass existed, and an `attested` paint never
 * enters the pass at all — it is not eligible, and the smoke still asserts its
 * drawn colour bit-exact.
 *
 * **Determinism, which every frame gate in this suite rests on.** The pass
 * sorts by id, sweeps twice, and breaks ties toward the lowest candidate — no
 * clock, no random, no dependence on the order records happened to load in.
 * Two loads of one scene give one town.
 *
 * @param {Iterable<object>} sidecars every structure's compiled sidecar
 * @returns {Map<string, object>} structure id -> its tone
 */
export function dealTones(sidecars) {
  const out = new Map();
  const rows = [];
  for (const sc of sidecars ?? []) {
    if (!sc?.id) continue;
    const tone = toneFor(sc);
    out.set(sc.id, tone);
    const e = sc?.placement?.local_e;
    const n = sc?.placement?.local_n;
    // Unplaced or documented-paint records are carried through untouched: a
    // building with no coordinate has no neighbourhood to be told apart in.
    if (!tone.eligible || !Number.isFinite(e) || !Number.isFinite(n)) continue;
    rows.push({ id: sc.id, sc, tone, e, n, applied: tone.value * (1 - tone.soil), deal: 0 });
  }
  rows.sort((a, b) => (a.id < b.id ? -1 : (a.id > b.id ? 1 : 0)));

  // The neighbourhoods, once. 335 structures is 56k distances — cheaper than
  // the grid index that would avoid them, and it runs at load, not per frame.
  const near = rows.map(() => []);
  for (let i = 0; i < rows.length; i += 1) {
    for (let j = i + 1; j < rows.length; j += 1) {
      const d = Math.hypot(rows[i].e - rows[j].e, rows[i].n - rows[j].n);
      if (d > FACADE.repelReach) continue;
      near[i].push({ at: j, d });
      near[j].push({ at: i, d });
    }
  }
  for (const list of near) list.sort((a, b) => a.d - b.d);

  for (let sweep = 0; sweep < FACADE.repelSweeps; sweep += 1) {
    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i];
      // Sweep 0 sees only what has been dealt; sweep 1 sees the finished town.
      const seen = sweep === 0 ? near[i].filter((o) => o.at < i) : near[i];
      if (!seen.length) continue;
      let bestDeal = 0;
      let bestCost = Infinity;
      for (let k = 0; k < FACADE.repelCandidates; k += 1) {
        const applied = candidateValue(row.sc, row.tone.spread, k) * (1 - row.tone.soil);
        let cost = 0;
        for (const o of seen) {
          // A shortfall and nothing else: once a neighbour is far enough away
          // in value, moving further buys nothing and would cost the median.
          const short = wanted(o.d) - Math.abs(applied - rows[o.at].applied);
          if (short > 0) cost += short * short;
        }
        if (cost < bestCost - 1e-12) { bestCost = cost; bestDeal = k; }
      }
      row.deal = bestDeal;
      row.tone = { ...row.tone, value: candidateValue(row.sc, row.tone.spread, bestDeal) };
      row.applied = row.tone.value * (1 - row.tone.soil);
    }
  }

  for (let i = 0; i < rows.length; i += 1) {
    const row = rows[i];
    out.set(row.id, row.deal === 0 ? row.tone : {
      ...row.tone,
      deal: row.deal,
      reason: `${row.tone.reason} — deal ${row.deal} of ${FACADE.repelCandidates}, `
        + `held clear of ${near[i].length} neighbour(s) within ${FACADE.repelReach} m`,
    });
  }
  return out;
}
