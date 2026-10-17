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
 *                massing — an ordered 4x4
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
 * public evidence controls. Unknown ranges fail open for visibility culling. */
export function opaqueConfidenceRange(range, view) {
  if (!range || range.length!==2 || !range.every(Number.isFinite)) return false;
  const [min,max]=range;
  if(min<0 || max>1 || min>max || (view.enabled && max>0.75))return false;
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
uniform float uReconAlpha;
// One component per level — x attested, y inferred, z reconstructed — 1.0 to
// hide. See setHidden() for why hiding is independent of the colour mode.
uniform vec3 uHideLevel;
// The grade colours, one uniform per level (GRADE_COLORS.*.scene), and how far each
// is mixed in — x attested, y inferred, z reconstructed, as uHideLevel.
uniform vec3 uTintAttested;
uniform vec3 uTintInferred;
uniform vec3 uTintReconstructed;
uniform vec3 uTintStrength;

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
  if (uConfMode > 0.0) {
    float inf = chicago_wRecon(vConfidence) * uConfMode;
    if (inf > 0.0) {
      float alpha = mix(1.0, uReconAlpha, inf);
      if (chicago_bayer4(gl_FragCoord.xy) >= alpha) discard;
    }
  }
`;

const FRAGMENT_TINT = /* glsl */`
  // Same guard as the discard: when the view is off, diffuseColor is not touched
  // by a single instruction. See VERTEX_ASSIGN for why that is load-bearing.
  if (uConfMode > 0.0) {
    float wAtt = chicago_wAttested(vConfidence) * uConfMode;
    float wInf = chicago_wInferred(vConfidence) * uConfMode;
    float wRec = chicago_wRecon(vConfidence) * uConfMode;
    diffuseColor.rgb = mix(diffuseColor.rgb, uTintAttested, wAtt * uTintStrength.x);
    diffuseColor.rgb = mix(diffuseColor.rgb, uTintInferred, wInf * uTintStrength.y);
    diffuseColor.rgb = mix(diffuseColor.rgb, uTintReconstructed, wRec * uTintStrength.z);
  }
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
  strength = {},
  reconstructedAlpha = 0.34,
} = {}) {
  const sceneHex = (level) => colors[level] ?? GRADE_COLORS[level].scene;
  const mixOf = (level) => strength[level] ?? GRADE_TINT_STRENGTH[level];
  const uniforms = {
    uConfMode: { value: 0 },
    uReconAlpha: { value: reconstructedAlpha },
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
    uTintStrength: { value: new THREE.Vector3(mixOf('attested'), mixOf('inferred'), mixOf('reconstructed')) },
  };

  const patched = new WeakSet();

  /**
   * Patch a material in place. Safe to call twice on the same material.
   * Works on MeshStandardMaterial / MeshPhysicalMaterial and on
   * MeshDepthMaterial (so a dithered wall casts a dithered shadow).
   * `packed` — `{ read, declare }`, see PACKED_VERTEX_DECL — reads the channel
   * from the structures batch's packed scalars rather than a float
   * `_confidence` (T-2574); every other layer reads the float. A channel may
   * hand `assign` — whole statements that set `vConfidence` — instead of a
   * `read` expression, and a `key` naming it in the program cache key: the
   * colour lane of frontage and the yard goods does (T-2689,
   * compact-streams.js COLOR_LANE_CONFIDENCE).
   */
  function patch(material, { packed = null } = {}) {
    if (!material || patched.has(material)) return material;
    patched.add(material);

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
        '#include <begin_vertex>' + (packed
          ? `\n  ${packed.assign ?? `vConfidence = ${packed.read};`}\n` : VERTEX_ASSIGN),
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
      return `chicago4d-confidence${packed ? `|packed:${packed.key ?? packed.read}` : ''}${priorKey ? `|over:${priorKey}` : ''}${outer}`;
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
    /** Everything visible again — what the reset affordance calls. */
    showAll() {
      for (const level of Object.keys(hidden)) this.setHidden(level, false);
      return this.hidden;
    },
  };
}
