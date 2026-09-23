/**
 * world.js — sky, sun, light, environment, tone mapping.
 *
 * The sun is not art-directed. `data/scenes/1835.json` records a lighting
 * moment ("10:00", 1 July 1835) and `data/datum.json` records where that is
 * (41.8867 N, 87.6380 W); the azimuth and elevation are computed from those two
 * facts and drive both the sky and the single directional light. If the scene
 * date moves, the shadows move.
 *
 * On the clock: standard time zones did not exist in 1835 — they arrive with the
 * railroads in 1883. A time written against an 1835 scene can only mean LOCAL
 * MEAN time at that longitude, so that is how it is read here. It matters: the
 * datum longitude is 5h 50m west of Greenwich, nearly ten minutes off the
 * Central Standard meridian, and reading 10:00 as CST would put the sun in the
 * wrong place by about two and a half degrees.
 *
 * The sky's ABSOLUTE brightness, on the other hand, is not physics and has to be
 * calibrated — see SKY_EXPOSURE below.
 */

import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';

const DEG = Math.PI / 180;

/**
 * The one free constant in the sky, and why it has a number rather than a
 * default.
 *
 * Preetham's model — which `Sky.js` implements — produces radiance in arbitrary
 * units: its `EE = 1000.0` "sun intensity" is a convention, not a measurement,
 * so the model fixes the sky's COLOUR but says nothing about where that colour
 * should sit on the exposure scale. three's own example papers over this by
 * running the whole scene at `toneMappingExposure = 0.5`, which is not available
 * here: the same exposure lights the buildings, and their albedo is evidence.
 *
 * So the sky gets its own exposure, and the number is measured rather than
 * dialled by eye. Against `dupage_tallgrass_2018-07-24.jpg` — a verified 24 July
 * photograph of Illinois tallgrass at this latitude, framed the way the standard
 * `prairie_west` shot is framed — the sky reads sRGB (101,153,209) about 15°
 * above the horizon, (125,165,205) at 8°, (137,166,200) at 4°. Running this
 * shader through the same ACES + sRGB chain the renderer uses, 0.045 lands the
 * 1835 sky within a few units of all three at the shot's own view azimuth. The
 * scene default of 1.0 rendered (245,252,255) — a white wash at every elevation,
 * which is what the baseline showed.
 *
 * It is applied to the sky ALONE. It is deliberately NOT a change to
 * `toneMappingExposure`, which would move the ground, the water and every
 * documented wall colour with it.
 *
 * What it does NOT fix, because a single scalar cannot: the SHAPE of the sky
 * with elevation. Exposure moves all three channels at every elevation together;
 * the error against the photograph was concentrated in red and green, and only
 * near the horizon. That is HORIZON_RESTORE below.
 */
const SKY_EXPOSURE = 0.045;

/**
 * The calibrated exposure the whole scene is graded at, and the one number the
 * brightness aid is allowed to move.
 *
 * K24. `toneMappingExposure` lights the ground, the water and every documented
 * wall colour together — which is exactly why SKY_EXPOSURE above refuses to use
 * it, and exactly why a visitor-facing brightness control has to be built as an
 * accommodation rather than as a second grade. 0.95 is the calibrated position:
 * every gate in `tools/smoke_renderer.mjs`, every frame `tools/critic_shots.mjs`
 * takes and every reading `tools/light_probe.mjs` reports is taken here, and the
 * aid below is off at boot so they stay taken here.
 *
 * The ceiling is ONE PHOTOGRAPHIC STOP — a doubling, 0.95 → 1.90 — and the stop
 * is the bound rather than a number chosen for how it looks. A stop is the unit
 * a camera's own exposure compensation is calibrated in, it is the largest
 * correction that still reads as the same photograph, and past it ACES rolls the
 * sunlit roofs and the sky together into a flat highlight: the scene stops
 * getting easier to see and starts losing the surfaces this project documents.
 * A visitor who cannot see the town at +1 stop has a problem the renderer should
 * not answer by inventing a brighter 1835.
 */
const BASE_EXPOSURE = 0.95;
const MAX_BRIGHTNESS_STOPS = 1;

/**
 * Putting the colour back into Preetham's horizon.
 *
 * THE DEFECT. Follow the model down to the horizon and watch the wavelength
 * dependence leave it. `Sky.js` builds in-scatter as
 *
 *     Lin = ( sunE * (betaR*rPhase + betaM*mPhase) / (betaR + betaM) * (1 - Fex) ) ^ 1.5
 *
 * and `Fex`, the extinction, is by far the strongest wavelength-dependent factor
 * in it. Along a horizon ray the model's own optical-length term runs to ~26×
 * the zenith path at 1° up and ~37× at the horizontal, so `Fex` has gone to
 * zero in all three channels and `1 - Fex` is 1, 1, 1. What is left is the
 * ratio of the two phase functions, and those are almost achromatic:
 * evaluated for this scene at 1° up, the red:green:blue in-scatter comes out
 * 0.816 : 0.919 : 1.000. The model therefore renders a WHITE horizon and hands
 * the whitening job to a neutral, so the band above the skyline arrived as
 * sRGB (181,191,195) at saturation 0.072.
 *
 * The photograph disagrees, and not by a little. `bar/dupage_tallgrass_
 * 2018-07-24.jpg` reads (136,163,192) at saturation 0.288 immediately above its
 * own sky/land step — B-R +55 against our +14. Note WHERE the error is: our
 * blue is essentially right (195 against 191). The whole of it is red +45 and
 * green +28. The horizon was not short of blue, it was carrying red and green
 * that a real horizon does not carry.
 *
 * THE CORRECTION. So this restores the channel dependence the saturated `1-Fex`
 * threw away, and does it the only way that leaves everything else alone: red
 * and green are attenuated toward the horizon, blue is not touched at all, and
 * the attenuation dies out with height fast enough that the upper sky renders as
 * the model built it — 0.3 % of the green at 30°, 0.03 % at 40°, nothing that
 * survives rounding to 8 bits anywhere above that.
 *
 *     scale(channel) = 1 - A * exp( -( sin(elevation) / E ) ^ P )
 *
 * A, E and P are FITTED — to the photograph, not by eye. The bar's sky was
 * sampled at ten elevations from 16° down to 0.5°, and A and E were solved by
 * running each candidate back through this scene's own shader, exposure, ACES
 * curve and sRGB encode and least-squaring against those samples
 * (`gaa_fit4.mjs` in the working directory). Residuals: 1.6 units RMS in red,
 * 1.0 in green, worst case 4, and the last degree — the elevation the
 * verification actually reads — lands within one unit on both.
 *
 * Red and green have to be solved TOGETHER, which is easy to get wrong: ACES is
 * not a per-channel curve. Its input matrix row for red is
 * (0.597, 0.355, 0.048), so taking green out takes red with it, and fitting the
 * two channels separately produced a pair that each looked right alone and
 * overshot red by 10 units together. The exponent is shared and lands at 1.6; a
 * plain exponential (P = 1) fits the middle of the band and then overshoots the
 * last degree, which is exactly where the check is.
 *
 * WHAT IT IS NOT. It is not exposure and it is not a tone curve: the patch
 * multiplies `texColor` inside the SKY shader. It is not "add blue": blue is
 * untouched, and every unit of the change is red and green coming off.
 *
 * WHAT IT NOW ALSO IS, since W1. This used to say the patch reached nothing but
 * the backdrop, because the PMREM built from this sky was disposed unused. It is
 * installed now, so the fit below no longer decides only what the horizon LOOKS
 * like — it decides what colour the light coming from that horizon IS, and it
 * reaches every wall in the town. The fit was made against a photograph and is
 * the better authority for both jobs, but a future change to it is a change to
 * the lighting and must be measured with `tools/light_probe.mjs`, not only with
 * a capture of the sky.
 *
 * ITS ONE HONEST COST, so nobody has to rediscover it. The fit is azimuth-blind,
 * because the model's horizon goes achromatic in every direction and the defect
 * is therefore the same in every direction — but the model's horizon BRIGHTNESS
 * is not the same in every direction. `prairie_west` looks south, within 19° of
 * the sun's azimuth and into the forward-scattering lobe, and the bar photograph
 * is framed the same way. The anti-sun views (`river_bank`, looking north) start
 * darker, so subtracting the same fraction of red and green leaves them bluer
 * and DARKER than the photograph: measured at 1° above the north horizon,
 * (104,132,166) — hue improved (B-R +62 against the bar's +55, where before it
 * was +17) but luminance down to 128 against the bar's 160, because red and
 * green are most of what luminance is. So the render brackets the photograph
 * rather than sitting on it, and it now brackets from the blue side instead of
 * the grey side.
 *
 * A floor keyed on the horizon's own chromaticity was tried and thrown away: it
 * scales with the blue channel, and the anti-sun blue is low too, so it moved
 * B-R by three units and earned nothing. Fixing this properly means an azimuth
 * term, and an azimuth term needs a second VERIFIED July photograph shot away
 * from the sun to fit against. `bar/REFERENCES.md` does not have one, and
 * guessing the anti-sun sky from the solar one is exactly the kind of invention
 * this project does not do.
 */
const HORIZON_RESTORE = {
  /** red: how much comes off at the horizon, and the scale in sin(elevation) */
  redAmount: 0.495, redScale: 0.130,
  /** green: two thirds as much to remove, and it reaches a little higher */
  greenAmount: 0.330, greenScale: 0.190,
  /** shared falloff exponent */
  power: 1.6,
};

/**
 * The colour the air itself is, and therefore the colour distance goes to.
 *
 * This is the MEASURED horizon sky of `bar/dupage_tallgrass_2018-07-24.jpg`:
 * sRGB (136,163,192), taken from the twelve pixels immediately above the
 * sky/land step, which is a reading that does not depend on knowing the
 * photograph's field of view.
 *
 * It replaces a hand-picked grey-green (0x98a69d), and the reason is worth
 * keeping. That value was reasoned from "a hazed plain keeps some of its own
 * green", and it does — but it was set so far toward the sward that a
 * fully-hazed surface rendered at sRGB (143,157,130): GREENER than the sky it
 * was supposed to converge on, and REDDER than it was blue (B-R -13). Real
 * aerial perspective pushes distance toward the sky, i.e. BLUE — the bar's own
 * most distant land reads (118,146,145), B-R +27. With a haze that goes the
 * other way, no amount of distance can make ground and air meet: the horizon
 * stayed a step rather than a convergence (63 luminance across four pixels,
 * where the note below this one had designed for 15).
 *
 * The green does not disappear, it just stops being IN the air: the ground
 * keeps its own colour and the haze mixes it toward the sky, which is the
 * order the physics happens in. A fully-hazed surface now renders sRGB
 * (152,175,195) — B-R +43, and 12 luminance off this scene's own horizon sky.
 *
 * Shared with the water's grazing-angle term in terrain.js, and with the
 * horizon-timber band in trees.js, so the river, the far ground and the far
 * timber all agree about what distance looks like. Changing it here without
 * changing it there splits the scene's idea of distance in three.
 */
export const HORIZON_HAZE = 0x88a3c0;

/**
 * THE GROUND'S HALF OF THE ENVIRONMENT — a reflectance, not a colour.
 *
 * An environment map of an analytic sky has a defect nothing in the sky model
 * can fix: the model is defined over the whole sphere, so it paints the ground
 * half too, and it paints it BLUE. Install that as `scene.environment` and every
 * downward-facing surface in the town — an eave's underside, the shaded side of
 * a log wall, the interior of a crown — is lit by sky from below as well as
 * above. That is not aerial physics, it is a hole in the model, and it is the
 * whole of why the last attempt "swamped albedo": the environment it installed
 * had no ground in it, so it replaced the warm bounce with more sky and every
 * surface converged on the sky's hue regardless of what it was made of.
 *
 * So the environment is built with a ground in it. Its radiance is DERIVED, and
 * from numbers already committed rather than picked:
 *
 *     L_ground = reflectance * E_horizontal / PI
 *
 * `reflectance` is the dun `0x7a6b4e` the hemisphere light already carried as
 * its ground colour. Read as a reflectance — which is what its numbers already
 * are, linear (0.195, 0.144, 0.074), a 15 % reflector — it is a plausible
 * prairie-and-mud albedo and needs no new constant. What was missing was the
 * other factor: the old rig applied that colour at a hand-picked intensity, so
 * the bounce bore no relation to how much light was actually falling on the
 * ground it was supposed to be bouncing off.
 *
 * `E_horizontal` is the light this scene actually delivers to a horizontal
 * surface: the sun's own term, computed here from its colour, intensity and
 * elevation, plus SKY_FILL_UP below.
 */
const GROUND_REFLECTANCE = 0x7a6b4e;

/**
 * The fill the environment actually delivers, MEASURED — and the discrepancy
 * that came out of measuring it, which is the finding of this phase.
 *
 * `SKY_FILL_UP` is the irradiance on an upward-facing white Lambertian card from
 * this environment at intensity 1, sun excluded, reported by a committed
 * instrument:
 *
 *     node tools/light_probe.mjs
 *
 * `CALIBRATED_FILL_UP` is the same reading taken from the rig this phase
 * replaces — a `HemisphereLight(0xa8c4e0, 0x7a6b4e, 2.4)` plus a second at 0.20.
 *
 *     measured 2026-08-14      R       G       B     luminance
 *     the old hemisphere    1.0440  1.4565  1.9535     1.4047
 *     this sky, at 1        0.3663  0.7916  1.5492     0.7558
 *
 * THE OLD FILL WAS NOT THE SKY. It delivered 1.86x the luminance of the sky it
 * stood for and nearly three times the red, at a scene exposure calibrated so
 * that same sky renders within a few units of a verified photograph. So the town
 * was lit by a fill that contradicted its own backdrop, and every later
 * calibration — the sward's density, the wall colours, the crown contrast — was
 * measured under it.
 *
 * WHICH LEAVES A CHOICE, and it was made by measuring both halves of it rather
 * than by argument. RENDERING §4 W1 says to rebalance "so total illuminance
 * stays calibrated rather than doubled", which here means scaling the sky back
 * UP by 1.858 to restore the luminance the old fill delivered. That was built
 * and measured, and it fails the acceptance it was built to satisfy:
 *
 *     log wall R/B retained, against a white card in the same light
 *       the old hemisphere fill                85 %
 *       this environment at its own magnitude  76 %
 *       this environment scaled to 1.858       62 %
 *
 * Scaling a sky that is genuinely blue — the calibrated zenith is B/R 4.2 —
 * until it carries a hand-picked fill's luminance puts nearly three times the
 * blue on every surface, and the browns converge toward it. That is the 2026-08
 * failure this file already records, arrived at from the other direction.
 *
 * So the environment is installed at ITS OWN MAGNITUDE — `environmentIntensity`
 * stays 1 and there is no invented scalar anywhere in the fill. The scene's
 * total illuminance falls 16 % as a result, which is the honest consequence of
 * lighting the town with the sky it is calibrated against, and every number it
 * moves is measured in `docs/STATUS.md` rather than left to be discovered.
 *
 * NEITHER FIGURE IS FREE TO DRIFT. `tools/smoke_renderer.mjs` re-measures the
 * fill through the same probe and fails if the rig has moved more than 5 % from
 * what is written here, because a stale figure would mis-derive both the ground
 * bounce and the intensity, and a bounce wrong in the direction of "too dark" is
 * exactly the failure this phase exists to retire.
 */
const SKY_FILL_UP = [0.3663, 0.7916, 1.5492];
const CALIBRATED_FILL_UP = [1.0440, 1.4565, 1.9535];
/** The environment is installed as measured. Named, rather than left implicit,
 *  because "1" here is a decision and not a default. */
const ENV_INTENSITY = 1.0;
const FILL_UP = SKY_FILL_UP.map((v) => v * ENV_INTENSITY);

/**
 * Exponential-squared haze, tuned so it is nothing at conversational range,
 * a readable recession across the middle distance, and total at the edge of what
 * is modelled: ~1.7 % at 100 m, 13 % at 300 m, 46 % at 700 m, 98 % at 1500 m.
 *
 * That last figure is the point, and it is a HONESTY constraint rather than a
 * look: docs/LIBERTIES.md L17 records that the ground beyond the 640 m
 * heightfield is a radial skirt carried out to 1400 m — geometry for the horizon
 * only, nothing modelled, sampled or claimed — on the standing condition that
 * "the scene's fog is total by 1500 m". Fog here hides ground we have not built.
 * It must never be turned down far enough to display it, and it is not doing any
 * work the other way either: no distant landform is drawn INTO the haze.
 */
const HAZE_DENSITY = 0.00125;

/**
 * ROADMAP R-W3b(a) — HOW FAR FROM THE VISITOR THE SUN'S SHADOW REACHES, in
 * metres, as the half-width of the orthographic box that follows them.
 *
 * Exported because it is a claim a gate can read: `tools/smoke_renderer.mjs`
 * asserts that the shipped rig carries this reach at the texel size the block
 * beside `light.shadow` documents, and `tools/measure_shadow_reach.mjs` prints
 * what each candidate value would cost. The full reasoning, the measured
 * coverage it buys and the draw-call ceiling that decides the number are in that
 * block — read it before changing this.
 */
export const SHADOW_REACH_M = 240;

/**
 * Solar azimuth and elevation, NOAA's algorithm.
 *
 * @param {object} o
 * @param {number} o.lat            degrees north
 * @param {number} o.lon            degrees east (negative west)
 * @param {string} o.date           'YYYY-MM-DD'
 * @param {string} o.localMeanTime  'HH:MM', local mean solar time at `lon`
 * @returns {{azimuthDeg:number, elevationDeg:number, declinationDeg:number,
 *            equationOfTimeMin:number, utcHours:number}}
 */
export function solarPosition({ lat, lon, date, localMeanTime = '12:00' }) {
  const [y, mo, d] = date.split('-').map(Number);
  const [hh, mm] = localMeanTime.split(':').map(Number);
  const localHours = hh + (mm || 0) / 60;

  // Local mean time -> UTC. Longitude west is negative, so this adds.
  const utcHours = localHours - lon / 15;

  // Julian day (Fliegel & Van Flandern), then centuries from J2000.0.
  const a = Math.floor((14 - mo) / 12);
  const yy = y + 4800 - a;
  const mm2 = mo + 12 * a - 3;
  const jdn = d + Math.floor((153 * mm2 + 2) / 5) + 365 * yy + Math.floor(yy / 4)
    - Math.floor(yy / 100) + Math.floor(yy / 400) - 32045;
  const jd = jdn - 0.5 + utcHours / 24;
  const T = (jd - 2451545.0) / 36525;

  const L0 = mod360(280.46646 + T * (36000.76983 + 0.0003032 * T));
  const M = 357.52911 + T * (35999.05029 - 0.0001537 * T);
  const e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T);
  const C = Math.sin(M * DEG) * (1.914602 - T * (0.004817 + 0.000014 * T))
    + Math.sin(2 * M * DEG) * (0.019993 - 0.000101 * T)
    + Math.sin(3 * M * DEG) * 0.000289;
  const trueLong = L0 + C;
  const omega = 125.04 - 1934.136 * T;
  const lambda = trueLong - 0.00569 - 0.00478 * Math.sin(omega * DEG);
  const eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60;
  const eps = eps0 + 0.00256 * Math.cos(omega * DEG);

  const decl = Math.asin(Math.sin(eps * DEG) * Math.sin(lambda * DEG)) / DEG;

  const varY = Math.tan(eps / 2 * DEG) ** 2;
  const eqTime = 4 / DEG * (
    varY * Math.sin(2 * L0 * DEG)
    - 2 * e * Math.sin(M * DEG)
    + 4 * e * varY * Math.sin(M * DEG) * Math.cos(2 * L0 * DEG)
    - 0.5 * varY * varY * Math.sin(4 * L0 * DEG)
    - 1.25 * e * e * Math.sin(2 * M * DEG)
  );

  const trueSolarMin = mod(utcHours * 60 + eqTime + 4 * lon, 1440);
  const hourAngle = trueSolarMin / 4 - 180;

  const latR = lat * DEG, declR = decl * DEG, haR = hourAngle * DEG;
  const cosZenith = Math.min(1, Math.max(-1,
    Math.sin(latR) * Math.sin(declR) + Math.cos(latR) * Math.cos(declR) * Math.cos(haR)));
  const zenith = Math.acos(cosZenith);
  const elevation = 90 - zenith / DEG;

  let azimuth;
  const denom = Math.cos(latR) * Math.sin(zenith);
  if (Math.abs(denom) < 1e-9) {
    azimuth = hourAngle > 0 ? 180 : 0;
  } else {
    const cosAz = Math.min(1, Math.max(-1,
      (Math.sin(latR) * cosZenith - Math.sin(declR)) / denom));
    const a = Math.acos(cosAz) / DEG;
    // NOAA's branch, and it is easy to get backwards: before local solar noon
    // the sun is EAST of south, after it is west. Getting this wrong put the
    // 10 a.m. July sun in the north-east and the shadows on the wrong side.
    azimuth = hourAngle > 0 ? mod360(a + 180) : mod360(540 - a);
  }

  return {
    azimuthDeg: mod360(azimuth),
    elevationDeg: elevation,
    declinationDeg: decl,
    equationOfTimeMin: eqTime,
    utcHours,
  };
}

/** Compass bearing + elevation -> a unit direction in three's world frame. */
export function sunDirection(azimuthDeg, elevationDeg, target = new THREE.Vector3()) {
  const az = azimuthDeg * DEG;
  const el = elevationDeg * DEG;
  const horiz = Math.cos(el);
  return target.set(
    Math.sin(az) * horiz,     // +x east
    Math.sin(el),             // +y up
    -Math.cos(az) * horiz,    // -z north
  ).normalize();
}

function mod(a, n) { return ((a % n) + n) % n; }
function mod360(a) { return mod(a, 360); }

/**
 * Build the sky, the sun and the environment for a scene.
 *
 * @param {object} o
 * @param {THREE.WebGLRenderer} o.renderer
 * @param {THREE.Scene} o.scene
 * @param {object} o.sceneJson   data/scenes/<year>.json
 * @param {object} o.datum       data/datum.json
 * @param {boolean} o.lowSpec    smaller shadow map, cheaper env
 * @param {string[]} [o.problems] collector, same list the scene loader writes to
 */
export function createWorld({
  renderer, scene, sceneJson, datum, lowSpec = false, problems = [],
}) {
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = BASE_EXPOSURE;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = lowSpec ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;

  const sun = solarPosition({
    lat: datum.origin_lat,
    lon: datum.origin_lon,
    date: sceneJson.target_date,
    localMeanTime: sceneJson.lighting?.local_time ?? '12:00',
  });
  const dir = sunDirection(sun.azimuthDeg, sun.elevationDeg);

  // Prairie haze and woodsmoke, per the scene's own lighting note. Turbidity 6
  // is hazier than a clear modern day and cheaper than any volumetric. It is the
  // aerosol term: it whitens the horizon and leaves the zenith alone, which is
  // the right shape — at 24° up it moves the sky by three or four units out of
  // 255, and at 3° up by fourteen.
  const sky = new Sky();
  sky.name = 'sky';
  sky.scale.setScalar(45000);
  sky.material.uniforms.turbidity.value = 6.0;
  sky.material.uniforms.rayleigh.value = 2.2;
  sky.material.uniforms.mieCoefficient.value = 0.006;
  sky.material.uniforms.mieDirectionalG.value = 0.82;
  sky.material.uniforms.sunPosition.value.copy(dir).multiplyScalar(45000 * 0.9);

  // No clouds. The vendored Sky ships an fbm cloud layer on by default
  // (coverage 0.4) whose `time` uniform nothing in this renderer drives, so what
  // it actually produces is one frozen noise field — an invented cloudscape over
  // a specific hour of a specific day, held still. There is no weather record
  // for 1 July 1835; drawing no clouds claims less than drawing those, so the
  // layer is switched off rather than animated.
  sky.material.uniforms.cloudCoverage.value = 0.0;
  sky.material.uniforms.cloudDensity.value = 0.0;

  // The sky's own exposure (see SKY_EXPOSURE). Patched into the vendored shader
  // rather than forked: vendor/ is read-only and pinned by sha256 in
  // vendor/MANIFEST, so this marker cannot move underneath us without a
  // deliberate three bump — and if a bump ever does move it, say so out loud
  // instead of silently rendering the white sky again.
  sky.material.uniforms.skyExposure = { value: SKY_EXPOSURE };
  sky.material.uniforms.horizonAmount = {
    value: new THREE.Vector2(HORIZON_RESTORE.redAmount, HORIZON_RESTORE.greenAmount),
  };
  sky.material.uniforms.horizonScale = {
    value: new THREE.Vector2(HORIZON_RESTORE.redScale, HORIZON_RESTORE.greenScale),
  };
  sky.material.uniforms.horizonPower = { value: HORIZON_RESTORE.power };

  const skyFrag = sky.material.fragmentShader;
  const declared = skyFrag.replace('uniform float time;', /* glsl */`uniform float time;
		uniform float skyExposure;
		uniform vec2 horizonAmount;
		uniform vec2 horizonScale;
		uniform float horizonPower;`);
  // `direction` is the vendored shader's own view ray, already normalised, so
  // direction.y IS sin(elevation) and no trig is needed. Clamped at 0 because
  // the box is drawn below the horizon too and a negative elevation would run
  // the exponential the wrong way; the sliver of sky under the horizontal is
  // a tenth of a degree at eye height and the ground covers it.
  const patched = declared.replace('gl_FragColor = vec4( texColor, 1.0 );', /* glsl */`
			// Restore the wavelength dependence Preetham's saturated (1 - Fex)
			// term loses at the horizon. See HORIZON_RESTORE. Red and green only:
			// the blue channel already matches the reference photograph.
			vec2 chiFade = exp( -pow( max( direction.y, 0.0 ) / horizonScale, vec2( horizonPower ) ) );
			texColor.rg *= max( vec2( 0.0 ), vec2( 1.0 ) - horizonAmount * chiFade );

			gl_FragColor = vec4( texColor * skyExposure, 1.0 );`);
  sky.material.fragmentShader = patched;
  // Both markers are load-bearing and they fail differently: without the first
  // the sky renders at the model's arbitrary scale (a white wash at every
  // elevation), without the second it renders Preetham's white horizon under a
  // correctly exposed zenith. Check them separately so the message names the
  // one that actually broke rather than guessing.
  const lost = [];
  if (declared === skyFrag) lost.push('the exposure uniform (the sky will read as a white wash)');
  if (patched === declared) lost.push('the horizon restore (the skyline will read grey, not blue)');
  if (lost.length) {
    const said = `world: the vendored Sky shader no longer carries ${lost.join(' or ')}`;
    problems.push(said);
    // Also to the console, because the caller is not obliged to pass a collector
    // and a silent fallback to the white sky is exactly the failure this guards.
    console.warn(`[4D Chicago] ${said}`);
  }
  sky.material.needsUpdate = true;
  scene.add(sky);

  // The sky IS the environment. One PMREM pass at boot; nothing animates it.
  //
  // The sun disc MUST be switched off for that pass. Its radiance runs to five
  // or six figures in linear space, which overflows the half-float cube target
  // PMREM blurs through; the overflow becomes Inf, the blur turns Inf into NaN,
  // and a NaN environment map makes every lit surface in the scene render pure
  // black while the sky itself — an unlit shader — keeps looking fine. That is
  // a genuinely baffling failure to debug from the symptom, so it is written
  // down here rather than rediscovered. The disc goes straight back on for the
  // real render, where tone mapping handles it.
  const light = new THREE.DirectionalLight(0xfff2dc, 3.0);
  light.name = 'sun';
  light.castShadow = true;
  light.position.copy(dir).multiplyScalar(320);
  light.target.position.set(0, 0, 0);
  scene.add(light);
  scene.add(light.target);

  // One shadow camera that follows the walker, and its reach is what decides how
  // much of the town can cast a shadow at all — ROADMAP R-W3b(a).
  //
  // IT USED TO BE +/-60 m, on the reasoning that this covers what you can resolve
  // on foot. Measured on the published mirror at eight anchors, that box holds
  // **5 to 8 of the town's 331 structures and 0 to 41 of its 730 stems**: from
  // South Water Street 8 buildings and 12 trees cast a shadow and the other 323
  // and 718 meet the ground with nothing under them. The mid-field town and the
  // whole river timber were floating, and no amount of light fixes that, because
  // the geometry was being clipped out of the depth map before it was drawn.
  //
  // 120 m doubled the reach and the map doubled with it, so THE TEXEL SIZE WAS
  // UNCHANGED — 11.7 cm on desktop, 23.4 cm on a phone, exactly what the old rig
  // resolved. Nothing a visitor stands next to got softer to buy it.
  //
  // R-W3b(a) STOPPED AT 120 m FOR ONE REASON, and it was not resolution: **the
  // reach is draw-call-bound, not fill-bound.** Every batch that enters the box
  // is another draw call in the shadow pass, and the budget is 80. Measured then
  // at the worst station (`green_tree`): 70 calls at 60 m, 74 at 120, 78 at 150
  // and **exactly 80 at 180** — the ceiling, with the town still two thirds
  // outside the box. It named the two routes past it: fewer batches (R-W5a2) or
  // true cascades (R-W3b(b)).
  //
  // **240 m, 2026-08-17 — R-W5a2 took the first route and the ceiling moved.**
  // Carrying roughness per vertex collapsed the town's 16 building batches to
  // ONE, which is one call saved in the colour pass and one saved in the shadow
  // pass for every batch that was entering the box. Re-measured on the published
  // mirror, same instrument, same anchors: `green_tree` reads **48 calls at
  // ±120 m and 50 at ±240**, `south_water` 40 and 41, `forks` 47 and 47 — against
  // the 74 the same station read before the merge. The reach doubled again and
  // the frame is 30 calls under budget instead of 6.
  //
  // WHY 240 AND NOT MORE, and it is a resolution answer this time rather than a
  // budget one. The map has to double with the box or the texel grows, and 4096²
  // is the largest map worth asking a browser for: 2·240/4096 is **11.7 cm**, the
  // same texel this rig has resolved since R-W3b(a), and 2·240/2048 is **23.4 cm**
  // on a phone, likewise unchanged. ±360 m would need 6144² to hold that, or it
  // buys its reach by blurring the eave shadow a visitor is standing under —
  // which is the trade R-W3b(a) refused and this parcel is not reopening. Past
  // here the honest route is still R-W3b(b), true cascades, which spends texels
  // where they are looked at instead of spreading them evenly over 480 m.
  const half = SHADOW_REACH_M;
  const cam = light.shadow.camera;
  cam.left = -half; cam.right = half; cam.top = half; cam.bottom = -half;
  cam.near = 1; cam.far = 900;
  cam.updateProjectionMatrix();
  // 4096 over a 480 m frustum is 11.7 cm per texel — the same figure the 2048
  // over 240 m carried, and the 1024 over 120 m before that. The phone's map
  // doubles too, for the same reason and the same result. `bias` and
  // `normalBias` below are in world units and are calibrated to the TEXEL, not
  // to the reach, which is why holding the texel size is what lets them stand.
  const baseMap = lowSpec ? 2048 : 4096;
  light.shadow.mapSize.setScalar(baseMap);
  light.shadow.bias = -0.0004;
  light.shadow.normalBias = 0.045;

  // THE FILL. One PMREM at boot, and it IS the fill — there is no hemisphere
  // light any more. See GROUND_REFLECTANCE for why the environment is built with
  // a ground in it, and why a sky-only environment is what swamped albedo the
  // last time this was tried.
  //
  // THE SUN DISC MUST BE SWITCHED OFF for the pass. Its radiance runs to five or
  // six figures in linear space, which overflows the half-float cube target
  // PMREM blurs through; the overflow becomes Inf, the blur turns Inf into NaN,
  // and a NaN environment map makes every lit surface in the scene render pure
  // black while the sky itself — an unlit shader — keeps looking fine. That is a
  // genuinely baffling failure to debug from the symptom, so it is written down
  // here rather than rediscovered. The disc goes straight back on for the real
  // render, where the direct sun is the directional light above and tone mapping
  // handles the disc.
  const sunHorizontal = new THREE.Color(light.color).multiplyScalar(
    light.intensity * Math.max(0, Math.sin(sun.elevationDeg * DEG)));
  const reflectance = new THREE.Color(GROUND_REFLECTANCE);
  // L = reflectance * E_h / PI, with E_h the sun's horizontal term plus the
  // measured sky fill. Written straight into the working colour space: this is a
  // radiance, not a colour anyone authored, and pushing it through the sRGB
  // transfer would darken it by a factor of three for no reason.
  const groundRadiance = new THREE.Color().setRGB(
    reflectance.r * (sunHorizontal.r + FILL_UP[0]) / Math.PI,
    reflectance.g * (sunHorizontal.g + FILL_UP[1]) / Math.PI,
    reflectance.b * (sunHorizontal.b + FILL_UP[2]) / Math.PI,
    THREE.LinearSRGBColorSpace,
  );

  const pmrem = new THREE.PMREMGenerator(renderer);
  const envScene = new THREE.Scene();
  const skyParent = sky.parent;
  sky.material.uniforms.showSunDisc.value = false;
  // The lower hemisphere, seen from inside. `renderOrder` is load-bearing: the
  // Sky shader forces its own depth to the far plane and writes no depth, so the
  // dome has to be drawn FIRST for the depth test to keep the sky off the ground
  // half. Drawn second, it would be a sphere painted over a sky that had already
  // won every pixel.
  const groundGeo = new THREE.SphereGeometry(
    1, 24, 8, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2);
  const groundMat = new THREE.MeshBasicMaterial({
    color: groundRadiance, side: THREE.BackSide, fog: false, toneMapped: false,
  });
  const groundDome = new THREE.Mesh(groundGeo, groundMat);
  groundDome.renderOrder = -1;
  envScene.add(groundDome);
  envScene.add(sky);
  const envRT = pmrem.fromScene(envScene);
  skyParent.add(sky);
  sky.material.uniforms.showSunDisc.value = true;
  pmrem.dispose();

  scene.environment = envRT.texture;
  scene.environmentIntensity = ENV_INTENSITY;

  /**
   * THE FILL, STATED — because one important surface cannot read it.
   *
   * `scene.environment` reaches `MeshStandardMaterial` and nothing else: three
   * applies a scene environment only to the physical materials, so the terrain,
   * the streets, the buildings and the near timber receive this fill and the
   * sward does not — `flora.js` draws with `MeshLambertMaterial` and its own
   * shader, and it used to find the hemisphere light by traversing the scene.
   *
   * Removing the hemisphere light would therefore have darkened the prairie by
   * the whole of its fill while every other surface was merely getting the same
   * light from a better-shaped source. So the fill is published here as a value
   * rather than left to be sniffed out of the light list, and flora.js reads it.
   * It is the fill as installed, so the sward and the town are lit by one sky.
   * It is the sky's own fill, so the sward moves with the town rather than
   * staying lit by a fill the town no longer has. That is a real change to the
   * prairie and a stated one, measured in docs/STATUS.md with this phase's
   * frames — not a silent re-tune of a layer calibrated by another phase.
   */
  scene.userData.chiSkyFill = FILL_UP.slice();

  // Aerial perspective. Exponential-squared rather than the linear ramp it
  // replaces, because linear fog starts at nothing and then turns on: with
  // near 340 / far 1500 the whole walkable town sat at exactly zero haze and the
  // ground at 400 m was the same colour as the ground at 3 m, which is what the
  // baseline showed. Exp2 has no near plane — it is small everywhere and never
  // zero, so distance reads continuously.
  //
  // The colour is HORIZON_HAZE — the photograph's own horizon sky. Distance
  // goes toward the AIR, and the air over a July plain is blue; the prairie's
  // green survives in the mix because the fog only reaches 95 % at the far edge
  // of what is drawn, not because the fog itself is green. See the constant for
  // what the green-tinted haze it replaces did to the horizon.
  scene.fog = new THREE.FogExp2(HORIZON_HAZE, HAZE_DENSITY);

  const offset = new THREE.Vector3();
  const shadowRig = {
    reachM: half,
    mapSize: light.shadow.mapSize.x,
    texelM: (2 * half) / light.shadow.mapSize.x,
    /** R-BUG6. Whether `follow` quantises the box onto its own texel grid. */
    snapped: true,
  };

  /**
   * R-BUG6 — THE SHADOW BOX MOVES IN WHOLE TEXELS, NOT WITH THE WALKER.
   *
   * The box follows the visitor, so before this it was re-centred on their exact
   * position every frame. A shadow map is a raster: its samples are a lattice
   * fixed to the box, so sliding the box by a fraction of a texel re-quantises
   * every shadow edge in the scene at once. Nothing in the world moved and every
   * boundary is redrawn slightly differently — which is what a visitor sees as
   * crawl along an eave line. Measured with the camera held perfectly still and
   * the box slid half a texel (`measure_river_edge.mjs --box-drift`): 2,023
   * changed pixels at `from_above` and 5,650 at `descend_main_stem`, both **0**
   * with the rounding below. The 2 mm nudge that opened R-BUG6 sees only 1.7 % of
   * this, because 2 mm is 1.7 % of a texel — see that parcel's finding 3 before
   * measuring a shadow box by moving a camera.
   *
   * The fix is the standard one and it is arithmetic rather than a tuning: round
   * the centre onto a world-anchored lattice of the box's OWN texel size, in the
   * light's own plane. Two consequences worth stating:
   *
   *   - the offset is at most half a texel — 5.9 cm on desktop, 11.7 cm on a
   *     phone — so no shadow moves anywhere a visitor could measure it, and
   *     nothing about the reach, the map size or the texel size changes;
   *   - the rounding is in LIGHT space, on the two axes of the map, so the box
   *     never moves along the sun's direction. Depth is untouched, which is what
   *     keeps `bias` and `normalBias` calibrated to the texel the way the block
   *     above says they are.
   *
   * The lattice has to be anchored to the world rather than to the walker, or
   * the rounding would simply follow them and quantise nothing.
   */
  const snapRight = new THREE.Vector3();
  const snapUp = new THREE.Vector3();
  {
    // The basis three itself will use: the shadow camera is placed at the light
    // and aimed at the target, so its right and up axes are fixed as long as the
    // sun is (the sun here is one date and one time — see the module header).
    const basis = new THREE.Matrix4().lookAt(
      dir.clone().multiplyScalar(320), new THREE.Vector3(), cam.up,
    );
    snapRight.setFromMatrixColumn(basis, 0);
    snapUp.setFromMatrixColumn(basis, 1);
  }
  const snapCentre = new THREE.Vector3();
  function centreFor(position) {
    snapCentre.set(position.x, 0, position.z);
    if (!shadowRig.snapped) return snapCentre;
    const texel = shadowRig.texelM;
    const e = snapCentre.dot(snapRight);
    const u = snapCentre.dot(snapUp);
    return snapCentre
      .addScaledVector(snapRight, Math.round(e / texel) * texel - e)
      .addScaledVector(snapUp, Math.round(u / texel) * texel - u);
  }
  let brightness = 0;
  return {
    sky, light, sun, direction: dir.clone(),
    /** The environment map this rig installed, and the fill it delivers. */
    environment: envRT.texture, skyFill: FILL_UP.slice(), envIntensity: ENV_INTENSITY,
    /**
     * R-W3b(a). The shadow rig as a claim rather than as three internals: how
     * far from the visitor a shadow can be cast, and how coarsely it is
     * resolved. A gate reading `light.shadow.camera.right` reads the same
     * number, but reading it here is reading what this module MEANT.
     */
    shadowRig,
    /**
     * Harness only — set the reach and report what took effect.
     *
     * It exists because of R-A1's finding: an assertion that the rig carries a
     * documented reach passes identically whether the reach reaches the screen
     * or reaches nothing. The gate winds the reach back to the pre-R-W3b(a)
     * ±60 m, photographs the same held frame and requires it to CHANGE — which
     * is a thing you cannot ask without being able to move the number.
     */
    setShadowReach(metres) {
      const r = Math.max(1, Number(metres) || 0);
      cam.left = -r; cam.right = r; cam.top = r; cam.bottom = -r;
      cam.updateProjectionMatrix();
      light.shadow.needsUpdate = true;
      shadowRig.reachM = r;
      shadowRig.texelM = (2 * r) / light.shadow.mapSize.x;
      return r;
    },
    /**
     * THE SCENE-DETAIL RIG — T-0115. The reach AND the map together, so the
     * TEXEL is what stays fixed.
     *
     * `setShadowReach` above moves the box and leaves the map alone, which is
     * exactly what the gate's liveness check wants: wind the reach back, watch
     * the frame change, wind it forward. It is the wrong instrument for a
     * detail level, because a level that halves the box and keeps a 4096² map
     * pays the same fill and the same memory for a smaller shadow — it buys
     * nothing except a shorter reach. Halving the map with the box is what
     * makes the step affordable, and it holds the one number the block by
     * `light.shadow` says must hold: 2·120/2048 is 11.7 cm on desktop and
     * 2·120/1024 is 23.4 cm on a phone, both the texel this rig has resolved
     * since R-W3b(a). Nothing a visitor stands next to gets softer; what the
     * step costs is reach, and it costs it where the visitor asked for a
     * cheaper frame.
     *
     * @param {number} metres half-width of the box, in metres
     * @returns {{reachM:number, mapSize:number, texelM:number}} what took effect
     */
    setShadowRig(metres) {
      const r = Math.max(1, Number(metres) || 0);
      const map = Math.max(512, Math.round(baseMap * (r / SHADOW_REACH_M)));
      cam.left = -r; cam.right = r; cam.top = r; cam.bottom = -r;
      cam.updateProjectionMatrix();
      if (map !== light.shadow.mapSize.x) {
        // A shadow map is sized at allocation, so the old render target has to
        // go before three will build one at the new size. Disposing without
        // clearing the handle leaves three re-using a destroyed texture.
        light.shadow.mapSize.setScalar(map);
        light.shadow.map?.dispose();
        light.shadow.map = null;
      }
      light.shadow.needsUpdate = true;
      shadowRig.reachM = r;
      shadowRig.mapSize = map;
      shadowRig.texelM = (2 * r) / map;
      return { reachM: r, mapSize: map, texelM: shadowRig.texelM };
    },
    /**
     * K24. The visitor's brightness aid, in stops above the calibrated grade.
     *
     * It multiplies the tone-mapping exposure and touches nothing else: no
     * light's intensity, no material, no sky uniform, no fog. So it cannot
     * become a second reconstruction — there is no setting of it under which a
     * wall is a different colour in the data than it was — and dropping it back
     * to 0 returns the calibrated frame exactly, which is the third assertion
     * the smoke takes of it.
     *
     * @param {number} stops 0 = calibrated, clamped to [0, MAX_BRIGHTNESS_STOPS]
     */
    setBrightness(stops) {
      const s = Math.min(MAX_BRIGHTNESS_STOPS, Math.max(0, Number(stops) || 0));
      brightness = s;
      renderer.toneMappingExposure = BASE_EXPOSURE * (2 ** s);
      return s;
    },
    /** The aid's current position, so a gate can assert it rather than assume it. */
    get brightness() { return brightness; },
    /** The calibrated position, named so the HUD does not restate the number. */
    baseExposure: BASE_EXPOSURE,
    maxBrightnessStops: MAX_BRIGHTNESS_STOPS,
    /** Keep the shadow frustum on the walker, quantised onto its own texel grid
     *  (R-BUG6 — see `centreFor`). Cheap; call every frame. */
    follow(position) {
      light.target.position.copy(centreFor(position));
      light.target.updateMatrixWorld();
      offset.copy(dir).multiplyScalar(320);
      light.position.copy(light.target.position).add(offset);
      light.updateMatrixWorld();
    },
    /**
     * Harness only — R-BUG6's own liveness handle, and it exists for the reason
     * R-A1 wrote down: "the box did not move" passes identically on a rig that
     * quantises and on a rig whose `follow` is never called, so the gate takes
     * the same millimetre with this off and requires the box to MOVE. It is also
     * how `--box-drift` photographs the before state on the shipped build.
     */
    setShadowSnap(on) {
      shadowRig.snapped = !!on;
      light.shadow.needsUpdate = true;
      return shadowRig.snapped;
    },
    describe() {
      return `sun ${sun.elevationDeg.toFixed(1)}° up, bearing ${sun.azimuthDeg.toFixed(1)}°`
        + ` (${sceneJson.lighting?.local_time ?? '?'} local mean time, ${sceneJson.target_date})`;
    },
    dispose() {
      envRT.dispose();
      groundGeo.dispose();
      groundMat.dispose();
      sky.geometry.dispose();
      sky.material.dispose();
    },
  };
}
