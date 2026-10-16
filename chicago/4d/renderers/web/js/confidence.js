/**
 * confidence.js — THE confidence view.
 *
 * `docs/PROVENANCE.md`: "For a museum, a classroom, or a civic audience this is
 * the single most valuable thing the project offers." It is a deliverable, not a
 * debug overlay, and it is implemented exactly once — as a single
 * `onBeforeCompile` patch on the shared building material — so that it cannot be
 * forgotten per-building.
 *
 * The channel is `_CONFIDENCE`, a custom glTF SCALAR float attribute
 * (docs/GLB-CONTRACT.md): 0.0 documented, 0.5 derived, 1.0 inferred.
 * GLTFLoader lowercases unknown attributes, so it arrives as
 * `geometry.attributes._confidence`. three will not wire it up for us and must
 * not: it is data, not colour, and nothing may tint by accident. We declare the
 * attribute in the patch and carry it to the fragment stage ourselves.
 *
 * How each level renders when the view is on:
 *
 *   attested       lerped toward gold
 *   inferred       lerped toward silver
 *   reconstructed  lerped toward bronze, and screen-door dithered translucent
 *
 * — that is the default LOOK of each grade (GRADE_LOOK). Since T-2646 every grade
 * has its own look, set by `setGrade()`: a colour, a mode and an opacity.
 *
 *   tint    recoloured toward the grade's colour; opacity is how far.
 *   dither  recoloured, and screen-door dithered at opacity — today's
 *           Reconstructed massing, for any grade.
 *   ghost   recoloured and drawn see-through at opacity: really blended, in a
 *           second pass drawn LAST with depthWrite off (renderGhost below).
 *
 * The dither is an ordered 4x4
 *                Bayer threshold against gl_FragCoord with a `discard`, IN THE
 *                OPAQUE PASS. No blending, no depth sorting, no per-object
 *                render order. That is what lets it work inside one BatchedMesh,
 *                where every building shares a draw call and sorting is not
 *                available even in principle.
 */

import * as THREE from 'three';

/**
 * THE GRADE COLOURS (T-2671) — the one definition every place a grade shows reads.
 * Owner, 2026-10-16: "gold silver bronze and bronze is obviously browner than gold.
 * Gold being attested of course."
 *
 *   scene  the Confidence view's tint on the world, which is always daylight, so it
 *          has one value in either theme. A 0x hex, read once into a THREE.Color.
 *   dark / light  the interface's two themes. `fill` is a dot, a swatch, a bar or a
 *          border and holds 3:1 on every machine's panel; `ink` is grade TEXT and
 *          holds 4.5:1 there and on a chip's 12% wash of its fill.
 *
 * css/walk.css carries the interface pairs as `--grade-<level>` / `--grade-<level>-ink`
 * (:root dark, [data-theme="light"] light), because a stylesheet cannot import a
 * module; tools/check_grade_colors.mjs refuses the two drifting apart, re-measures
 * every contrast against all four machines' panels in both themes, and holds the
 * three distinct under simulated deuteranopia, protanopia and tritanopia. Bronze is
 * kept apart from gold in hue AND a clear step down in lightness: it is the lightness
 * step that still separates them once a colour-vision deficiency has taken the hue.
 */
export const GRADE_COLORS = Object.freeze({
  attested: Object.freeze({
    scene: 0xd4af37,
    dark: Object.freeze({ fill: '#d4ae38', ink: '#e2c25a' }),
    light: Object.freeze({ fill: '#a07c10', ink: '#775a08' }),
  }),
  inferred: Object.freeze({
    scene: 0xb8c0c8,
    dark: Object.freeze({ fill: '#c9d0d8', ink: '#d3d9e0' }),
    light: Object.freeze({ fill: '#737d88', ink: '#4e5761' }),
  }),
  reconstructed: Object.freeze({
    scene: 0x8c5a2b,
    dark: Object.freeze({ fill: '#a86a3a', ink: '#d29262' }),
    light: Object.freeze({ fill: '#8a5228', ink: '#633819' }),
  }),
});

/**
 * How far BY GRADE pulls each level's surface toward its colour (0 untouched, 1 the
 * flat colour). Attested is pulled least, so the house a source describes still reads
 * as its own stone and brick under the gold; reconstructed most, under its dither.
 */
export const GRADE_TINT_STRENGTH = Object.freeze({ attested: 0.62, inferred: 0.72, reconstructed: 0.8 });

/** The three looks a grade can take, and the number each is in the shader. */
export const GRADE_MODES = Object.freeze({ tint: 0, ghost: 1, dither: 2 });

/**
 * Each grade's look until something sets another (T-2646) — exactly the Confidence
 * view that shipped before per-grade looks existed: Attested and Inferred tinted,
 * Reconstructed tinted and dithered to 34% (its massing). `opacity` is the tint's
 * strength for `tint`, the fraction kept for `dither`, and the alpha for `ghost`.
 */
export const GRADE_LOOK = Object.freeze({
  attested: Object.freeze({ mode: 'tint', opacity: GRADE_TINT_STRENGTH.attested }),
  inferred: Object.freeze({ mode: 'tint', opacity: GRADE_TINT_STRENGTH.inferred }),
  reconstructed: Object.freeze({ mode: 'dither', opacity: 0.34 }),
});

/** How far a dithered or ghosted grade is recoloured — opacity is spent on the
 * dither or the alpha there, so the colour is held at the old Reconstructed mix. */
export const GRADE_LOOK_TINT = GRADE_TINT_STRENGTH.reconstructed;

/** The camera layer the ghost pass draws on (renderGhost). */
export const GHOST_LAYER = 31;

const GRADE_NAMES = ['attested', 'inferred', 'reconstructed'];
const GRADE_NAMES_BY_MODE = Object.fromEntries(Object.entries(GRADE_MODES).map(([k, v]) => [v, k]));

export const LEVELS = {
  attested: 0.0,
  inferred: 0.5,
  reconstructed: 1.0,
};

/** Level name for a raw channel value — the inverse of LEVELS, band-wise. */
export function levelOf(value) {
  if (value >= 0.75) return 'reconstructed';
  if (value >= 0.25) return 'inferred';
  return 'attested';
}

/** Whether every interpolated value in a triangle remains opaque under the
 * public evidence controls. Unknown ranges fail open for visibility culling.
 * With the view on, a grade drawn as dither or ghost is not opaque wherever the
 * shader gives it weight (attested below 0.25, inferred between 0.25 and 0.75,
 * reconstructed above 0.75 — the bands' open edges, as the shader weighs them).
 * A view with no `modes` is read with the default looks: reconstructed dithered. */
export function opaqueConfidenceRange(range, view) {
  if (!range || range.length!==2 || !range.every(Number.isFinite)) return false;
  const [min,max]=range;
  if(min<0 || max>1 || min>max)return false;
  if(view.enabled){
    const mode=(level)=>view.modes?.[level] ?? GRADE_LOOK[level].mode;
    if(mode('attested')!=='tint' && min<0.25)return false;
    if(mode('inferred')!=='tint' && max>0.25 && min<0.75)return false;
    if(mode('reconstructed')!=='tint' && max>0.75)return false;
  }
  const levels=['attested','inferred','reconstructed'];
  const first=levels.indexOf(levelOf(min)),last=levels.indexOf(levelOf(max));
  return !levels.slice(first,last+1).some(level=>view.hidden?.[level]);
}

const VERTEX_DECL = /* glsl */`
attribute float _confidence;
varying float vConfidence;
`;

const VERTEX_ASSIGN = /* glsl */`
  // Sanitise the channel at its source.
  //
  // A geometry that reaches a batch without _CONFIDENCE leaves this attribute
  // unbound, and an unbound attribute is NOT reliably zero on real hardware — it
  // can arrive as NaN. That matters far more than it sounds, because NaN * 0.0
  // is still NaN, so even the switched-OFF path would poison diffuseColor
  // through the mix() below and render the building pure black while the sky
  // and ground looked perfect. Software rasterisers hand back a tidy zero and
  // hide it, so this only shows up on a real GPU.
  //
  // (c == c) is false only for NaN — the portable test, since isnan() is
  // unreliable across drivers.
  float chicagoC = _confidence;
  vConfidence = (chicagoC == chicagoC) ? clamp(chicagoC, 0.0, 1.0) : 0.0;
`;

/**
 * A PACKED channel: the structures batch packs confidence with roughness, grain
 * and the piece tone into one four-byte attribute (T-2574), and hands `patch`
 * the GLSL that reads it and the function that declares it
 * (compact-attributes.js SCALARS_GLSL) — passed in rather than imported, so
 * this module stays loadable on its own. A packed byte is never NaN and the
 * packing already clamped it, so there is nothing left to sanitise.
 */
const PACKED_VERTEX_DECL = /* glsl */`
varying float vConfidence;
`;

const FRAGMENT_DECL = /* glsl */`
varying float vConfidence;
uniform float uConfMode;
// One component per level — x attested, y inferred, z reconstructed — 1.0 to
// hide. See setHidden() for why hiding is independent of the colour mode.
uniform vec3 uHideLevel;
// The grade colours, one uniform per level (GRADE_COLORS.*.scene), and how far each
// is mixed in — x attested, y inferred, z reconstructed, as uHideLevel.
uniform vec3 uTintAttested;
uniform vec3 uTintInferred;
uniform vec3 uTintReconstructed;
// T-2646: each grade's look — x attested, y inferred, z reconstructed. Mode is
// GRADE_MODES (0 tint, 1 ghost, 2 dither); opacity is the tint's strength, the
// dither's kept fraction or the ghost's alpha, by mode.
uniform vec3 uGradeMode;
uniform vec3 uGradeOpacity;

// Ordered 4x4 Bayer matrix. Screen-door translucency: a stable per-pixel
// threshold means no sorting, no blending, and no order dependence between the
// buildings sharing a batch.
float chicago_bayer4(vec2 fragXY) {
  int x = int(mod(fragXY.x, 4.0));
  int y = int(mod(fragXY.y, 4.0));
  int i = x + y * 4;
  float m[16];
  m[0]  =  0.0; m[1]  =  8.0; m[2]  =  2.0; m[3]  = 10.0;
  m[4]  = 12.0; m[5]  =  4.0; m[6]  = 14.0; m[7]  =  6.0;
  m[8]  =  3.0; m[9]  = 11.0; m[10] =  1.0; m[11] =  9.0;
  m[12] = 15.0; m[13] =  7.0; m[14] = 13.0; m[15] =  5.0;
  float v = 0.0;
  for (int k = 0; k < 16; k++) { if (k == i) v = m[k]; }
  return (v + 0.5) / 16.0;
}

// Crisp bands, because the contract's values are exactly 0.0 / 0.5 / 1.0 — but
// they degrade sanely if a generator ever emits something in between.
float chicago_wAttested(float c) { return 1.0 - clamp(c * 4.0, 0.0, 1.0); }
float chicago_wInferred(float c)  { return 1.0 - min(abs(c - 0.5) * 4.0, 1.0); }
float chicago_wRecon(float c) { return clamp((c - 0.75) * 4.0, 0.0, 1.0); }
vec3 chicago_grade(float c) { return vec3(chicago_wAttested(c), chicago_wInferred(c), chicago_wRecon(c)); }
// 1.0 in each component whose grade is in mode m.
vec3 chicago_inMode(float m) { return vec3(1.0) - step(vec3(0.5), abs(uGradeMode - vec3(m))); }
`;

const FRAGMENT_DISCARD = /* glsl */`
  // HIDING A LEVEL, and it is deliberately not conditional on uConfMode.
  //
  // Colouring by evidence and removing what is not evidenced are two different
  // questions, and the second is the more searching one: it answers "show me
  // only the Chicago somebody actually wrote down", which is this dataset's
  // strongest claim about itself. Tying it to the colour mode would mean you
  // could only ask it while the whole town was tinted and dithered, and the
  // answer is far more legible in ordinary daylight.
  //
  // Banded from the same thresholds as levelOf() so the shader and the labels
  // cannot disagree about which level a fragment is in.
  // GUARD FIRST, exactly as the mode check below does, and for the reason
  // written there: off must mean UNTOUCHED. The first version of this ran the
  // step()/discard arithmetic on every fragment of every patched material
  // whenever the page was open, with the uniform at (0,0,0) — and the river
  // disappeared. The whole town rendered one flat olive: the water surface was
  // gone and you were looking at the riverbed. Nothing was being hidden and the
  // uniform proved it; the cost was in having the branch there at all.
  //
  // So the hide path is entered only when something is actually hidden, and a
  // visitor who never opens the panel gets the shader that existed before it.
  if (uHideLevel.x + uHideLevel.y + uHideLevel.z > 0.0) {
    float lvlI = step(0.25, vConfidence);
    float lvlR = step(0.75, vConfidence);
    float hide = uHideLevel.x * (1.0 - lvlI)
               + uHideLevel.y * lvlI * (1.0 - lvlR)
               + uHideLevel.z * lvlR;
    if (hide > 0.0) discard;
  }

  // Off must mean untouched. Guard on the mode BEFORE reading the channel, so a
  // bad value cannot reach the arithmetic at all when the view is switched off.
#ifdef CHICAGO_GHOST_PASS
  // The ghost pass draws ONLY the ghosted grades, and nothing while the view is
  // off; a shader with no alpha to set (no <opaque_fragment>) draws nothing here.
  #ifndef CHICAGO_GHOST_ALPHA
  discard;
  #endif
  if (uConfMode <= 0.0) discard;
  if (dot(chicago_grade(vConfidence), chicago_inMode(1.0)) < 0.5) discard;
#else
  if (uConfMode > 0.0) {
    vec3 chicagoW = chicago_grade(vConfidence) * uConfMode;
    // A ghosted grade is not in the opaque pass at all — it is drawn, blended,
    // in the ghost pass after everything else — and casts no shadow.
    if (dot(chicagoW, chicago_inMode(1.0)) >= 0.5) discard;
    // A dithered grade keeps its opacity of its fragments: the Reconstructed
    // massing path, for whichever grade asks for it.
    vec3 chicagoDither = chicagoW * chicago_inMode(2.0);
    float dith = chicagoDither.x + chicagoDither.y + chicagoDither.z;
    if (dith > 0.0) {
      float keep = mix(1.0, dot(chicagoDither, uGradeOpacity) / dith, dith);
      if (chicago_bayer4(gl_FragCoord.xy) >= keep) discard;
    }
  }
#endif
`;

const FRAGMENT_TINT = /* glsl */`
  // Same guard as the discard: when the view is off, diffuseColor is not touched
  // by a single instruction. See VERTEX_ASSIGN for why that is load-bearing.
  if (uConfMode > 0.0) {
    vec3 chicagoW = chicago_grade(vConfidence) * uConfMode;
    // Tint spends opacity on the colour; dither and ghost spend it on the
    // dither or the alpha, and hold the colour at GRADE_LOOK_TINT.
    vec3 chicagoTint = chicago_inMode(0.0);
    vec3 chicagoMix = chicagoW * (chicagoTint * uGradeOpacity
      + (vec3(1.0) - chicagoTint) * ${GRADE_LOOK_TINT.toFixed(2)});
    diffuseColor.rgb = mix(diffuseColor.rgb, uTintAttested, chicagoMix.x);
    diffuseColor.rgb = mix(diffuseColor.rgb, uTintInferred, chicagoMix.y);
    diffuseColor.rgb = mix(diffuseColor.rgb, uTintReconstructed, chicagoMix.z);
  }
`;

// T-2646: the ghost's alpha, set where three writes the fragment out. Only the
// ghost pass's twin materials compile it in (CHICAGO_GHOST_PASS).
const FRAGMENT_GHOST_ALPHA = /* glsl */`
#ifdef CHICAGO_GHOST_PASS
  gl_FragColor.a *= dot(chicago_grade(vConfidence), chicago_inMode(1.0) * uGradeOpacity);
#endif
`;

/**
 * The key three would compile a material's hooks under, as it stands now: a key
 * the material was given wins; otherwise the source text of its hook, which is
 * three's own default; and nothing at all for the unhooked default material.
 */
export function programKeyOf(material) {
  if (Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey')) {
    return String(material.customProgramCacheKey());
  }
  const hook = material.onBeforeCompile;
  if (typeof hook !== 'function' || hook === THREE.Material.prototype.onBeforeCompile) return '';
  return hook.toString();
}

/**
 * One uniforms object shared by every patched material, so flipping the view is
 * a single assignment no matter how many materials exist.
 */
export function createConfidenceView({
  colors = {},
  looks = {},
} = {}) {
  const sceneHex = (level) => colors[level] ?? GRADE_COLORS[level].scene;
  const look = Object.fromEntries(GRADE_NAMES.map((level) => [level, { ...GRADE_LOOK[level], ...(looks[level] || {}) }]));
  const uniforms = {
    uConfMode: { value: 0 },
    uHideLevel: { value: new THREE.Vector3(0, 0, 0) },
    // ONE conversion, not two — and here it matters more than anywhere else in
    // the renderer, because these two colours are the confidence view itself.
    //
    // `new THREE.Color(hex)` already reads the hex as sRGB and stores it in the
    // renderer's linear working space (ColorManagement.enabled is true by
    // default since three r152). The `.convertSRGBToLinear()` that used to
    // follow applied the transfer function a second time, and the error is not
    // a uniform darkening: squaring the transfer scales the three channels by
    // DIFFERENT factors, so the old 0x93a6bb reached the shader at 0.237 / 0.315 /
    // 0.425 of its intended radiance — a quarter as bright in red, nearly half
    // in blue. The tint was both far too dark and visibly skewed toward blue.
    //
    // What makes that a provenance bug rather than a cosmetic one: the tint on
    // the wall is supposed to be the colour of the legend swatch (`.sw-*`) and
    // the HUD chip's three-part dot the visitor is reading it against — both
    // painted from the same GRADE_COLORS, by way of walk.css's --grade-* tokens.
    // Double-converted, it could not be, so the one view that exists to say
    // which parts we made up disagreed with its own legend.
    uTintAttested: { value: new THREE.Color(sceneHex('attested')) },
    uTintInferred: { value: new THREE.Color(sceneHex('inferred')) },
    uTintReconstructed: { value: new THREE.Color(sceneHex('reconstructed')) },
    uGradeMode: { value: new THREE.Vector3(...GRADE_NAMES.map((l) => GRADE_MODES[look[l].mode] ?? 0)) },
    uGradeOpacity: { value: new THREE.Vector3(...GRADE_NAMES.map((l) => look[l].opacity)) },
  };

  const patched = new WeakSet();
  let patchCount = 0;

  /**
   * Patch a material in place. Safe to call twice on the same material.
   * Works on MeshStandardMaterial / MeshPhysicalMaterial and on
   * MeshDepthMaterial (so a dithered wall casts a dithered shadow).
   * `packed` — `{ read, declare }`, see PACKED_VERTEX_DECL — reads the channel
   * from the structures batch's packed scalars rather than a float
   * `_confidence` (T-2574); every other layer reads the float.
   */
  function patch(material, { packed = null } = {}) {
    if (!material || patched.has(material)) return material;
    patched.add(material);
    patchCount += 1;

    const prior = material.onBeforeCompile;
    // Read BEFORE the hook below is installed: three's default key is the
    // source text of whatever `onBeforeCompile` is current, so asked afterwards
    // it would only ever answer with ours.
    const priorKey = programKeyOf(material);
    const hook = (shader, renderer) => {
      if (typeof prior === 'function') prior(shader, renderer);
      Object.assign(shader.uniforms, uniforms);

      const v = (packed ? PACKED_VERTEX_DECL : VERTEX_DECL) + shader.vertexShader.replace(
        '#include <begin_vertex>',
        '#include <begin_vertex>' + (packed ? `\n  vConfidence = ${packed.read};\n` : VERTEX_ASSIGN),
      );
      shader.vertexShader = packed ? packed.declare(v) : v;

      let f = FRAGMENT_DECL + shader.fragmentShader;
      // Discard first: an inferred fragment that is dithered away should not
      // pay for lighting, and it must not write depth.
      f = f.replace(
        '#include <clipping_planes_fragment>',
        '#include <clipping_planes_fragment>' + FRAGMENT_DISCARD,
      );
      // Tint after diffuseColor is final (map + any vertex colour applied).
      if (f.includes('#include <color_fragment>')) {
        f = f.replace(
          '#include <color_fragment>',
          '#include <color_fragment>' + FRAGMENT_TINT,
        );
      }
      // The ghost's alpha goes where three writes the fragment (T-2646). A shader
      // without that anchor cannot be ghosted, and its ghost pass draws nothing.
      if (f.includes('#include <opaque_fragment>')) {
        f = '#define CHICAGO_GHOST_ALPHA\n' + f.replace(
          '#include <opaque_fragment>',
          '#include <opaque_fragment>' + FRAGMENT_GHOST_ALPHA,
        );
      }
      shader.fragmentShader = f;
    };
    material.onBeforeCompile = hook;
    // THE PROGRAM CACHE KEY NAMES THE CHAIN, NOT THE MATERIAL (T-0053).
    //
    // three caches a compiled program under a key ending in
    // `customProgramCacheKey()`, whose default is `onBeforeCompile.toString()`.
    // Left at that default, every material this function touches reports the
    // source text of `hook` above, whatever was chained beneath it — so a plain
    // patched MeshStandardMaterial was handed the program of a mapless building
    // material, whose second hook reads `_roughness` and facade-tone attributes
    // the plain one never bound, and drew in solid black (T-0050).
    //
    // A key unique to each material would cure that and cost a program per
    // building material: 334 of them, compiling identical GLSL. What decides the
    // GLSL is the set of hooks on the material, so that is what goes in the key —
    // ours, plus whatever was beneath it when we arrived, plus whatever was
    // wrapped around it since. Every plain patched material still shares one
    // program and every building material shares another; only materials whose
    // hooks write different shaders are kept apart. A key a layer assigns AFTER
    // patching (enclosures.js and its kin) replaces this one, as before.
    material.customProgramCacheKey = function customProgramCacheKey() {
      const outer = this.onBeforeCompile === hook ? '' : `|wrap:${this.onBeforeCompile}`;
      return `chicago4d-confidence${packed ? `|packed:${packed.read}` : ''}${priorKey ? `|over:${priorKey}` : ''}${outer}`;
    };
    material.needsUpdate = true;
    return material;
  }

  /**
   * Guarantee the attribute exists. A geometry without `_CONFIDENCE` is a
   * generator bug, not something to paper over — we fill it with `attested`
   * so the scene still renders, and shout, because silently rendering unmarked
   * geometry as if it were attested is the one failure mode this whole view
   * exists to prevent.
   */
  function ensureAttribute(geometry, label = 'geometry') {
    if (geometry.getAttribute('_confidence')) return null;
    const count = geometry.getAttribute('position').count;
    geometry.setAttribute('_confidence',
      new THREE.BufferAttribute(new Float32Array(count), 1));
    const msg = `${label}: no _CONFIDENCE attribute in the GLB — rendering it as `
      + `documented, which it may not be. See docs/GLB-CONTRACT.md.`;
    console.warn(`[4D Chicago] ${msg}`);
    return msg;
  }

  /** Count vertices per level — the honest picture of what is on screen. */
  function census(geometry) {
    const attr = geometry.getAttribute('_confidence');
    const out = { attested: 0, inferred: 0, reconstructed: 0 };
    if (!attr) return out;
    for (let i = 0; i < attr.count; i++) out[levelOf(attr.getX(i))]++;
    return out;
  }

  let enabled = false;
  const hidden = { attested: false, inferred: false, reconstructed: false };
  const AXIS = { attested: 'x', inferred: 'y', reconstructed: 'z' };
  const TINT_UNIFORM = { attested: 'uTintAttested', inferred: 'uTintInferred', reconstructed: 'uTintReconstructed' };

  // ---- the ghost pass (T-2646) ------------------------------------------------
  //
  // A ghost is really see-through, and real transparency cannot live in the opaque
  // pass the dither lives in: it needs blending, no depth write, and to be drawn
  // after everything it is seen through. So a ghosted grade is discarded from the
  // opaque pass (and from the shadow pass, which shares that discard), and drawn
  // again by `renderGhost` straight after the frame's own render — the same scene,
  // the same camera, the same shadow maps — restricted by a camera layer to the
  // objects that carry a patched material, each wearing that material's ghost
  // twin: transparent, depthWrite off, compiled with CHICAGO_GHOST_PASS so that it
  // keeps only the ghosted grades' fragments, at their opacity. Nothing of this
  // runs, and no twin exists, until a grade is set to ghost while the view is on.
  //
  // A twin is the material itself one prototype down (Object.create): it inherits
  // every map, colour, hook and uniform as they stand, so nothing is copied and
  // nothing can drift; only its blending, depth write, id and defines are its own.
  // three keys the program on the defines, so the twin gets its own program and the
  // material keeps its. Transmissive materials are not given one — a second
  // transmission pass is not a cost a ghost may add — so their ghosted fragments
  // are simply not drawn.
  const twins = new WeakMap();
  let nextTwinId = 1_000_000_000;
  function ghostTwin(material) {
    let twin = twins.get(material);
    if (twin) return twin;
    twin = Object.create(material);
    Object.defineProperty(twin, 'id', { value: nextTwinId++ });
    twin._listeners = undefined;
    twin.transparent = true;
    twin.depthWrite = false;
    Object.defineProperty(twin, 'defines', {
      configurable: true,
      get() { return { ...(material.defines || {}), CHICAGO_GHOST_PASS: '' }; },
    });
    material.addEventListener('dispose', () => { twins.delete(material); twin.dispose(); });
    twins.set(material, twin);
    return twin;
  }
  const ghostable = (m) => !!m && patched.has(m) && !(m.transmission > 0) && m.visible !== false;
  const isPatched = (m) => (Array.isArray(m) ? m.some((x) => patched.has(x)) : patched.has(m));

  // What each patched object holds, as confidence ranges: per instance for a
  // structures batch (buildings.js records them), per geometry otherwise, read off
  // the float `_confidence` channel and re-read when it changes. `null` is a range
  // nobody can state, and is drawn in both passes.
  const rangeCache = new WeakMap();
  function geometryRange(geometry) {
    const attr = geometry?.getAttribute?.('_confidence');
    if (!attr || attr.itemSize !== 1) return null;
    // A phone frees a layer's page arrays once uploaded (upload-release.js), and
    // keeps the channel's range on the geometry first.
    if (!attr.array || !attr.array.length) return geometry.userData?.confidenceRange ?? null;
    const hit = rangeCache.get(attr);
    if (hit && hit.version === attr.version) return hit.range;
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < attr.count; i += 1) {
      const v = attr.getX(i);
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    const range = attr.count && Number.isFinite(lo) && Number.isFinite(hi) ? [lo, hi] : null;
    rangeCache.set(attr, { version: attr.version, range });
    return range;
  }
  // Which grades a range gives weight to — the shader's bands, open at the edges.
  const bandsOf = (range) => (range === null ? [true, true, true]
    : [range[0] < 0.25, range[1] > 0.25 && range[0] < 0.75, range[1] > 0.75]);
  // 'none'  nothing ghosted: the opaque pass only;
  // 'all'   nothing but ghosted (or hidden) grades: the ghost pass only;
  // 'some'  both passes.
  function share(range, ghosted, gone) {
    const bands = bandsOf(range);
    let ghost = false, other = false;
    bands.forEach((on, i) => {
      if (!on) return;
      if (ghosted[i]) ghost = true;
      else if (!gone[i]) other = true;
    });
    if (!ghost) return 'none';
    return other ? 'some' : 'all';
  }

  let targets = [];
  let builtFor = null;
  let builtAtPatch = -1;
  let framesSinceBuild = 0;
  let planKey = '';
  // The current plan: objects (and batch instances) left out of each pass.
  let plan = { opaqueObjects: [], opaqueInstances: [], ghostTargets: [], ghostInstances: [] };
  const ghostStats = { targets: 0, passes: 0, lastCalls: 0, opaqueSkipped: 0, ghostSkipped: 0 };
  /** Every object with a patched material, and the lights, put on GHOST_LAYER. */
  function collectGhostTargets(scene) {
    for (const o of targets) o.layers.disable(GHOST_LAYER);
    targets = [];
    scene.traverse((o) => {
      if (o.isLight) { o.layers.enable(GHOST_LAYER); return; }
      if (!(o.isMesh || o.isPoints || o.isLine)) return;
      if (isPatched(o.material)) targets.push(o);
    });
    builtFor = scene;
    builtAtPatch = patchCount;
    framesSinceBuild = 0;
    planKey = '';
  }
  function buildPlan() {
    const ghosted = GRADE_NAMES.map((l) => !hidden[l] && lookOf(l).mode === 'ghost');
    const gone = GRADE_NAMES.map((l) => hidden[l]);
    const next = { opaqueObjects: [], opaqueInstances: [], ghostTargets: [], ghostInstances: [] };
    for (const o of targets) {
      const ranges = o.isBatchedMesh ? o.userData?.confidenceRanges : null;
      const canGhost = Array.isArray(o.material) ? o.material.some(ghostable) : ghostable(o.material);
      if (ranges) {
        const leaveOpaque = [], leaveGhost = [];
        let anyGhost = false;
        for (let i = 0; i < ranges.length; i += 1) {
          if (!ranges[i]) continue;
          const sh = share(ranges[i], ghosted, gone);
          if (sh === 'all') leaveOpaque.push(i);
          if (sh === 'none') leaveGhost.push(i);
          else anyGhost = true;
        }
        if (leaveOpaque.length) next.opaqueInstances.push([o, leaveOpaque]);
        if (anyGhost && canGhost) {
          next.ghostTargets.push(o);
          if (leaveGhost.length) next.ghostInstances.push([o, leaveGhost]);
        }
        continue;
      }
      const sh = share(geometryRange(o.geometry), ghosted, gone);
      // Left out by its `visible`, which would take its children with it — so a
      // mesh with children stays in the opaque pass and lets the shader discard.
      if (sh === 'all' && !o.children.length) next.opaqueObjects.push(o);
      if (sh !== 'none' && canGhost) next.ghostTargets.push(o);
    }
    for (const o of plan.ghostTargets) o.layers.disable(GHOST_LAYER);
    for (const o of next.ghostTargets) o.layers.enable(GHOST_LAYER);
    plan = next;
    ghostStats.targets = next.ghostTargets.length;
    ghostStats.opaqueSkipped = next.opaqueObjects.length
      + next.opaqueInstances.reduce((n, [, ids]) => n + ids.length, 0);
    ghostStats.ghostSkipped = next.ghostInstances.reduce((n, [, ids]) => n + ids.length, 0);
  }
  /** Hide objects / instances for one pass; returns the function that puts them back. */
  function leaveOut(objects, instances) {
    const shown = objects.filter((o) => o.visible);
    for (const o of shown) o.visible = false;
    const hiddenNow = [];
    for (const [batch, ids] of instances) {
      const was = [];
      for (const i of ids) {
        let visible;
        try { visible = batch.getVisibleAt(i); } catch { continue; }
        if (visible) { batch.setVisibleAt(i, false); was.push(i); }
      }
      if (was.length) hiddenNow.push([batch, was]);
    }
    return () => {
      for (const o of shown) o.visible = true;
      for (const [batch, ids] of hiddenNow) for (const i of ids) batch.setVisibleAt(i, true);
    };
  }
  const twinOf = (m) => (ghostable(m) ? ghostTwin(m) : m);

  function lookOf(level) {
    return {
      mode: GRADE_NAMES_BY_MODE[uniforms.uGradeMode.value[AXIS[level]]],
      opacity: uniforms.uGradeOpacity.value[AXIS[level]],
      color: `#${uniforms[TINT_UNIFORM[level]].value.getHexString()}`,
    };
  }

  return {
    uniforms,
    patch,
    ensureAttribute,
    census,
    get enabled() { return enabled; },
    /** @param {boolean} on */
    set(on) {
      enabled = !!on;
      uniforms.uConfMode.value = enabled ? 1 : 0;
      return enabled;
    },
    toggle() { return this.set(!enabled); },

    /**
     * Remove everything at one level from the view.
     *
     * The other half of the confidence control, and the half that answers the
     * harder question. Colouring says how sure we are; hiding says what is left
     * if you keep only what somebody wrote down. Turning off `reconstructed`
     * empties most of the town, which is the honest picture of how much of 1835
     * Chicago is recoverable and is not a comfortable thing for this project to
     * show — which is exactly why it should be one click away.
     *
     * It works with the colour mode off, on purpose: the answer reads far better
     * in ordinary daylight than through the grade tint.
     */
    setHidden(level, on) {
      if (!(level in hidden)) return null;
      hidden[level] = !!on;
      uniforms.uHideLevel.value[AXIS[level]] = hidden[level] ? 1 : 0;
      return hidden[level];
    },
    get hidden() { return { ...hidden }; },

    /**
     * One grade's look (T-2646): any of `color` (a 0x number or a CSS colour),
     * `mode` ('tint' | 'ghost' | 'dither') and `opacity` (0..1). What is not given
     * is left as it is. Returns the look now in force, or null for a name that is
     * not a grade; a mode that is not one, or an opacity that is not a number, is
     * refused (null) and changes nothing.
     */
    setGrade(level, { color, mode, opacity } = {}) {
      if (!(level in hidden)) return null;
      if (mode !== undefined && !(mode in GRADE_MODES)) return null;
      if (opacity !== undefined && !Number.isFinite(Number(opacity))) return null;
      if (color !== undefined) uniforms[TINT_UNIFORM[level]].value.set(color);
      if (mode !== undefined) uniforms.uGradeMode.value[AXIS[level]] = GRADE_MODES[mode];
      if (opacity !== undefined) {
        uniforms.uGradeOpacity.value[AXIS[level]] = Math.min(1, Math.max(0, Number(opacity)));
      }
      return lookOf(level);
    },
    /** The look in force for one grade: `{ mode, opacity, color }`. */
    grade(level) { return level in hidden ? lookOf(level) : null; },
    /** Every grade's mode — what opaqueConfidenceRange reads off a view. */
    get modes() {
      return Object.fromEntries(GRADE_NAMES.map((l) => [l, lookOf(l).mode]));
    },
    /** Every grade back to GRADE_COLORS and GRADE_LOOK. */
    resetGrades() {
      for (const level of GRADE_NAMES) {
        this.setGrade(level, { color: GRADE_COLORS[level].scene, ...GRADE_LOOK[level] });
      }
      return Object.fromEntries(GRADE_NAMES.map((l) => [l, lookOf(l)]));
    },
    /** Whether a ghost pass has anything to draw: the view on, and a ghosted grade not hidden. */
    get ghosting() {
      return enabled && GRADE_NAMES.some((l) => !hidden[l] && lookOf(l).mode === 'ghost');
    },
    /** What the ghost pass drew last: objects it can draw, passes run, draw calls of the last. */
    get ghostStats() { return { ...ghostStats }; },

    /**
     * Draw the frame: `renderer.render(scene, camera)`, and — only while a grade is
     * ghosted with the view on — the ghost pass after it.
     *
     * With a ghost, an object (or a structures-batch instance) that holds nothing
     * but ghosted or hidden grades is left out of the opaque pass, shadow
     * included, and one that holds no ghosted grade is left out of the ghost pass,
     * so a frame's triangles grow by the structures that carry a ghosted grade AND
     * another one, not by the town. The ghost pass draws into the same target
     * without clearing it, adds its draws to renderer.info (a frame's stats count
     * both passes), renders no shadow and no background, wears each patched
     * material's twin, and puts back every material, visibility, layer mask and
     * renderer setting it touched. The object list is rebuilt when a material has
     * been patched since and every 30 frames, so a mesh added with an
     * already-patched material is reached too; the plan, when a look or a hidden
     * grade changes.
     */
    render(renderer, scene, camera) {
      if (!this.ghosting) { renderer.render(scene, camera); return 0; }
      framesSinceBuild += 1;
      if (builtFor !== scene || builtAtPatch !== patchCount || framesSinceBuild >= 30) collectGhostTargets(scene);
      const key = JSON.stringify([this.modes, hidden]);
      if (key !== planKey) { buildPlan(); planKey = key; }
      const putBack = leaveOut(plan.opaqueObjects, plan.opaqueInstances);
      try { renderer.render(scene, camera); } finally { putBack(); }
      return this.renderGhost(renderer, scene, camera);
    },

    /** The ghost pass alone, against the current plan; `render` calls it. */
    renderGhost(renderer, scene, camera) {
      if (!this.ghosting || !plan.ghostTargets.length) return 0;
      const drawn = plan.ghostTargets;
      const saved = drawn.map((o) => o.material);
      for (const o of drawn) o.material = Array.isArray(o.material) ? o.material.map(twinOf) : twinOf(o.material);
      const putBack = leaveOut([], plan.ghostInstances);
      const mask = camera.layers.mask;
      const background = scene.background;
      const { autoClear } = renderer;
      const { autoUpdate, needsUpdate } = renderer.shadowMap;
      const { autoReset } = renderer.info;
      const before = renderer.info.render.calls;
      camera.layers.set(GHOST_LAYER);
      scene.background = null;
      renderer.autoClear = false;
      renderer.shadowMap.autoUpdate = false;
      renderer.shadowMap.needsUpdate = false;
      renderer.info.autoReset = false;
      try {
        renderer.render(scene, camera);
      } finally {
        drawn.forEach((o, i) => { o.material = saved[i]; });
        putBack();
        camera.layers.mask = mask;
        scene.background = background;
        renderer.autoClear = autoClear;
        renderer.shadowMap.autoUpdate = autoUpdate;
        renderer.shadowMap.needsUpdate = needsUpdate;
        renderer.info.autoReset = autoReset;
      }
      ghostStats.passes += 1;
      ghostStats.lastCalls = renderer.info.render.calls - before;
      return ghostStats.lastCalls;
    },
    /** Everything visible again — what the reset affordance calls. */
    showAll() {
      for (const level of Object.keys(hidden)) this.setHidden(level, false);
      return this.hidden;
    },
  };
}
