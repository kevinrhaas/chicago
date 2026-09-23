#!/usr/bin/env node
/**
 * T-0016 (ROADMAP R-M1d) — REPORT ANY ROAD BAND THAT MOVES AGAINST ITS OWN BANK.
 *
 *   node tools/road_band_movement.mjs --self-test
 *
 * THE FAULT THIS EXISTS FOR. The road-legibility gate in `smoke_renderer.mjs`
 * asserts ONCE PER STATION:
 *
 *     check(`the roads reach the screen ${station.what}`,
 *           bands.length >= station.minBands && bad.length === 0, report)
 *
 * but the measurement underneath is PER BAND — five distance bands, each with
 * its own median ΔL*, its own share of perceptible probes, its own Weber
 * contrast and its own ground L*. A band may therefore collapse by 55 points
 * (71 % → 16 % perceptible) and, as long as it stays the right side of
 * ROAD_MIN_PERCEPTIBLE, the station still passes and the suite still prints
 * "229/2 before, 229/2 after". Nothing in the run says a thing.
 *
 * That is not a missing bar. The bars are a deliberate provisional baseline the
 * owner ruled on (T-0033 / R-M1b: "keep this baseline until I complain about it
 * more later"), and R-W1 is the standing proof that tightening them punishes
 * legitimate work — it preserved the road/ground ratio to within 0.4 %, got the
 * whole scene 14–17 % darker, and lost a bar it had not actually regressed.
 *
 * So this is a REPORT and not a gate. It banks what each gated band reads and
 * says out loud when a band moves away from that — IN EITHER DIRECTION, because
 * a band that doubles is as much a thing someone should have noticed as a band
 * that halves, and because a report that only ever complains gets read as noise.
 *
 * Nothing here can fail a run. `compare()` returns rows; the caller prints them.
 * The three thresholds in smoke_renderer.mjs are not read by this file and are
 * not touched by it.
 */

/**
 * How far a band must move before it is worth a line. Every band wanders a
 * little between runs — the wind moves, the sun angle is frozen but the
 * rasteriser is not exact — and a report that fires on that is a report nobody
 * reads. These are set an order of magnitude above run-to-run jitter and an
 * order of magnitude below the collapse in the ticket (55 points).
 */
export const MATERIAL = {
  // Percentage POINTS of perceptible probes, as a fraction. The ticket's
  // collapse is 0.55; a band that moves a tenth of its range is worth saying.
  perceptible: 0.10,
  // CIE L*. ROAD_MIN_DELTA_L is 1.8, so a third of a unit is a real shift in a
  // quantity whose whole gated range is a couple of units wide.
  medianDeltaL: 0.3,
  // Weber is a ratio, so it moves proportionally — 25 % of the banked value,
  // floored so a band banked near zero cannot report on rounding noise.
  weberRel: 0.25,
  weberFloor: 0.005,
  // Median ground L*. This is the "is there light to see by" reading; it moves
  // with exposure, which is exactly what R-W1 did legitimately, so it is
  // reported generously rather than tightly.
  groundL: 2.0,
};

const key = (viewport, station, lo, hi) => `${viewport}/${station}/${lo}-${hi}`;

/**
 * Flatten a run's stations into banked-shaped rows. Only GATED bands are
 * banked: an ungated band projects too few probes to say anything, and banking
 * one would report movement in a number that is noise by definition.
 */
export function collect (viewport, stations, opts = {}) {
  const failing = opts.failing || (() => false);
  const out = {};
  for (const st of stations) {
    for (const b of st.bands || []) {
      if (!b.gated) continue;
      const row = {
        medianDeltaL: round(b.medianDeltaL, 2),
        opaqueDeltaL: round(b.opaqueDeltaL, 2),
        perceptible: round(b.perceptible, 4),
        weber: round(b.weber, 5),
        groundL: round(b.groundL, 1),
        nBare: b.nBare,
      };
      // A BANK IS A RECORD, NOT A CERTIFICATE. A band may be below its bar when
      // it is banked — T-0114 has had two of them red since 2026-08-20 — and
      // refusing to bank those would mean the one band everyone is worried
      // about is the one band nobody can watch for FURTHER collapse. So it is
      // banked and marked, and the mark is what stops a reader mistaking the
      // baseline for a pass.
      if (failing(b)) row.failingGateWhenBanked = true;
      out[key(viewport, st.id, b.lo, b.hi)] = row;
    }
  }
  return out;
}

const round = (v, dp) => (typeof v === 'number' && Number.isFinite(v)
  ? Number(v.toFixed(dp)) : null);

/**
 * compare(banked, current) → rows, worst first.
 *
 * Each row is one band that moved materially, or appeared, or stopped being
 * gated. `dir` is 'fell' | 'rose' | 'appeared' | 'ungated' so a caller can
 * colour or filter without re-deriving the sign.
 */
export function compare (banked, current, material = MATERIAL) {
  const rows = [];
  const seen = new Set();

  for (const [k, cur] of Object.entries(current)) {
    seen.add(k);
    const was = banked[k];
    if (!was) {
      rows.push({ band: k, dir: 'appeared', severity: 0.5,
        note: `newly gated — ΔL* ${fmt(cur.medianDeltaL)}, `
            + `${pct(cur.perceptible)} perceptible of ${cur.nBare} bare` });
      continue;
    }
    const moves = [];
    let severity = 0;

    const dP = num(cur.perceptible) - num(was.perceptible);
    if (Math.abs(dP) >= material.perceptible) {
      moves.push(`perceptible ${pct(was.perceptible)} → ${pct(cur.perceptible)}`
        + ` (${signed(dP * 100, 0)} points)`);
      severity = Math.max(severity, Math.abs(dP) / material.perceptible);
    }

    const dL = num(cur.medianDeltaL) - num(was.medianDeltaL);
    if (Math.abs(dL) >= material.medianDeltaL) {
      moves.push(`ΔL* ${fmt(was.medianDeltaL)} → ${fmt(cur.medianDeltaL)}`
        + ` (${signed(dL, 1)})`);
      severity = Math.max(severity, Math.abs(dL) / material.medianDeltaL);
    }

    const dW = num(cur.weber) - num(was.weber);
    const wBar = Math.max(Math.abs(num(was.weber)) * material.weberRel, material.weberFloor);
    if (Math.abs(dW) >= wBar) {
      moves.push(`weber ${fmt(was.weber, 4)} → ${fmt(cur.weber, 4)}`);
      severity = Math.max(severity, Math.abs(dW) / wBar);
    }

    const dG = num(cur.groundL) - num(was.groundL);
    if (Math.abs(dG) >= material.groundL) {
      // Named but never severe on its own: R-W1 moved this legitimately by
      // re-exposing the scene, and a report that shouts about exposure is the
      // same mistake the ΔL* bar made.
      moves.push(`ground L* ${fmt(was.groundL, 1)} → ${fmt(cur.groundL, 1)}`
        + ` (${signed(dG, 1)}, exposure)`);
      severity = Math.max(severity, 0.5);
    }

    if (!moves.length) continue;
    // Direction is taken from the legibility numbers, not from ground L*: a
    // scene that got darker while the road stayed as readable has not regressed.
    const lead = Math.abs(dP) >= material.perceptible ? dP : dL;
    rows.push({ band: k, dir: lead < 0 ? 'fell' : 'rose', severity, note: moves.join(', ') });
  }

  for (const k of Object.keys(banked)) {
    if (seen.has(k)) continue;
    rows.push({ band: k, dir: 'ungated', severity: 1,
      note: 'was gated when banked and is not gated now — either the probes '
          + 'stopped projecting or the station moved' });
  }

  return rows.sort((a, b) => b.severity - a.severity);
}

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const fmt = (v, dp = 1) => (typeof v === 'number' && Number.isFinite(v) ? v.toFixed(dp) : '—');
const pct = (v) => `${(num(v) * 100).toFixed(0)} %`;
const signed = (v, dp) => `${v >= 0 ? '+' : ''}${v.toFixed(dp)}`;

/** One line per row, for the run log. */
export function render (rows) {
  if (!rows.length) return ['road bands: every gated band within its banked figure'];
  return [`road bands: ${rows.length} moved against the bank —`]
    .concat(rows.map((r) => `  ${r.dir.padEnd(9)} ${r.band}  ${r.note}`));
}

// ---------------------------------------------------------------------------
// SELF-TEST — each assertion must fire when the thing it is about is put back.
//
// The acceptance for T-0016 is "replay R-W1's merge and the tool names
// south_water 250-600 m unprompted". R-W1 is history and cannot be re-merged,
// but the figures it produced are recorded in smoke_renderer.mjs's own header:
// South Water Street at 250-600 m scored 0.3 L* with 14 % of probes perceptible,
// and the whole scene got 14-17 % darker while the road/ground RATIO held to
// within 0.4 %. That is the replay: bank a healthy town, hand it R-W1's frame,
// and see whether this file names the right band without being asked.
// ---------------------------------------------------------------------------
if (process.argv[2] === '--self-test') {
  let failed = 0;
  const t = (label, cond, detail = '') => {
    console.log(`  ${cond ? 'ok    ' : 'FAIL  '}${label}${detail ? ` — ${detail}` : ''}`);
    if (!cond) failed = 1;
  };

  // A healthy bank: three stations, the numbers a passing run reads.
  const bank = {
    'desktop/south_water/250-600': { medianDeltaL: 2.5, opaqueDeltaL: 3.2, perceptible: 0.71, weber: 0.0620, groundL: 49.8, nBare: 42 },
    'desktop/south_water/100-250': { medianDeltaL: 3.4, opaqueDeltaL: 4.5, perceptible: 0.70, weber: 0.0810, groundL: 50.1, nBare: 38 },
    'desktop/from_above/100-250':  { medianDeltaL: 2.9, opaqueDeltaL: 3.8, perceptible: 0.68, weber: 0.0700, groundL: 48.9, nBare: 55 },
  };

  // R-W1's frame: south_water 250-600 collapses to the recorded 0.3 L* / 14 %,
  // and EVERY band darkens 14-17 % while its Weber contrast is preserved.
  const rw1 = {
    'desktop/south_water/250-600': { medianDeltaL: 0.3, opaqueDeltaL: 3.2, perceptible: 0.14, weber: 0.0618, groundL: 42.1, nBare: 42 },
    'desktop/south_water/100-250': { medianDeltaL: 3.4, opaqueDeltaL: 4.5, perceptible: 0.70, weber: 0.0808, groundL: 42.4, nBare: 38 },
    'desktop/from_above/100-250':  { medianDeltaL: 2.9, opaqueDeltaL: 3.8, perceptible: 0.68, weber: 0.0698, groundL: 41.5, nBare: 55 },
  };

  const rows = compare(bank, rw1);
  const top = rows[0];
  t('R-W1 replay: a band is named at all', rows.length > 0, `${rows.length} row(s)`);
  t('R-W1 replay: the WORST band named is south_water 250-600 m, unprompted',
    top && top.band === 'desktop/south_water/250-600', top ? top.band : 'none');
  t('R-W1 replay: it is named as a FALL', top && top.dir === 'fell', top && top.dir);
  t('R-W1 replay: the 55-point collapse is in the line',
    top && /perceptible 71 % → 14 %/.test(top.note), top && top.note);
  t('R-W1 replay: the exposure drop is reported but does not outrank the collapse',
    rows.some((r) => /exposure/.test(r.note)) && top.severity > 1,
    `severity ${top && top.severity.toFixed(1)}`);
  t('R-W1 replay: the two bands that only darkened are NOT called falls',
    rows.filter((r) => r.dir === 'fell').length === 1,
    `${rows.filter((r) => r.dir === 'fell').length} fall(s)`);

  // The ticket's own number, in the direction nobody watches for.
  const rose = compare(
    { 'desktop/south_water/250-600': { medianDeltaL: 0.6, opaqueDeltaL: 3.2, perceptible: 0.16, weber: 0.0200, groundL: 49.8, nBare: 42 } },
    { 'desktop/south_water/250-600': { medianDeltaL: 2.5, opaqueDeltaL: 3.2, perceptible: 0.71, weber: 0.0620, groundL: 49.8, nBare: 42 } });
  t('a band that RECOVERS is reported too, and as a rise',
    rose.length === 1 && rose[0].dir === 'rose', rose[0] && rose[0].dir);

  // Quiet when nothing moved — the property that makes the report readable.
  t('an unchanged run reports nothing', compare(bank, bank).length === 0);
  t('jitter under the materiality bar reports nothing',
    compare(bank, { ...bank,
      'desktop/south_water/250-600': { ...bank['desktop/south_water/250-600'],
        medianDeltaL: 2.6, perceptible: 0.735 } }).length === 0);

  // Appearing and disappearing bands are movements as well.
  t('a newly gated band is named', compare({}, { 'desktop/x/2-40': bank['desktop/from_above/100-250'] })
    .some((r) => r.dir === 'appeared'));
  t('a band that stopped being gated is named',
    compare(bank, {}).filter((r) => r.dir === 'ungated').length === 3);

  // `collect` must bank the gated bands and refuse the rest.
  const collected = collect('desktop', [{ id: 'south_water', bands: [
    { lo: 250, hi: 600, gated: true, medianDeltaL: 2.4567, opaqueDeltaL: 3.2, perceptible: 0.712345, weber: 0.061999, groundL: 49.84, nBare: 42 },
    { lo: 600, hi: 4000, gated: false, medianDeltaL: 9, opaqueDeltaL: 9, perceptible: 9, weber: 9, groundL: 9, nBare: 1 },
  ] }]);
  t('collect banks the gated band', collected['desktop/south_water/250-600']?.medianDeltaL === 2.46);
  t('collect refuses the ungated band', !collected['desktop/south_water/600-4000']);

  console.log(failed ? '\nSELF-TEST FAIL' : '\nSELF-TEST PASS');
  process.exit(failed);
}
