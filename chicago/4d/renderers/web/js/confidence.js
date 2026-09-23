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
 *   documented   unchanged
 *   inferred     lerped toward amber
 *   inferred     screen-door dithered translucent massing — an ordered 4x4
 *                Bayer threshold against gl_FragCoord with a `discard`, IN THE
 *                OPAQUE PASS. No blending, no depth sorting, no per-object
 *                render order. That is what lets it work inside one BatchedMesh,
 *                where every building shares a draw call and sorting is not
 *                available even in principle.
 */

import * as THREE from 'three';

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

const FRAGMENT_DECL = /* glsl */`
varying float vConfidence;
uniform float uConfMode;
uniform float uReconAlpha;
// One component per level — x attested, y inferred, z reconstructed — 1.0 to
// hide. See setHidden() for why hiding is independent of the colour mode.
uniform vec3 uHideLevel;
uniform vec3 uInferredTint;
uniform vec3 uReconTint;

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
  // could only ask it while the whole town was amber and dithered, and the
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
    float wDer = chicago_wInferred(vConfidence) * uConfMode;
    float wInf = chicago_wRecon(vConfidence) * uConfMode;
    diffuseColor.rgb = mix(diffuseColor.rgb, uInferredTint, wDer * 0.72);
    diffuseColor.rgb = mix(diffuseColor.rgb, uReconTint, wInf * 0.80);
  }
`;

/**
 * One uniforms object shared by every patched material, so flipping the view is
 * a single assignment no matter how many materials exist.
 */
export function createConfidenceView({
  derived = 0xe2a63f,
  inferred = 0x93a6bb,
  inferredAlpha = 0.34,
} = {}) {
  const uniforms = {
    uConfMode: { value: 0 },
    uReconAlpha: { value: inferredAlpha },
    uHideLevel: { value: new THREE.Vector3(0, 0, 0) },
    // ONE conversion, not two — and here it matters more than anywhere else in
    // the renderer, because these two colours are the confidence view itself.
    //
    // `new THREE.Color(hex)` already reads the hex as sRGB and stores it in the
    // renderer's linear working space (ColorManagement.enabled is true by
    // default since three r152). The `.convertSRGBToLinear()` that used to
    // follow applied the transfer function a second time, and the error is not
    // a uniform darkening: squaring the transfer scales the three channels by
    // DIFFERENT factors, so 0x93a6bb reached the shader at 0.237 / 0.315 /
    // 0.425 of its intended radiance — a quarter as bright in red, nearly half
    // in blue. The tint was both far too dark and visibly skewed toward blue.
    //
    // What makes that a provenance bug rather than a cosmetic one: `reconstructed`
    // is the SAME hex as `--inf` in css/walk.css, which paints the legend
    // swatch (`.sw-rec`) and the three-part gradient in the confidence key. The
    // tint on the wall is supposed to be the colour of the chip the visitor is
    // reading it against. Double-converted, it could not be, so the one view
    // that exists to say which parts we made up disagreed with its own legend.
    uInferredTint: { value: new THREE.Color(derived) },
    uReconTint: { value: new THREE.Color(inferred) },
  };

  const patched = new Set();

  /**
   * Patch a material in place. Safe to call twice on the same material.
   * Works on MeshStandardMaterial / MeshPhysicalMaterial and on
   * MeshDepthMaterial (so a dithered wall casts a dithered shadow).
   */
  function patch(material) {
    if (!material || patched.has(material)) return material;
    patched.add(material);

    const prior = material.onBeforeCompile;
    material.onBeforeCompile = (shader, renderer) => {
      if (typeof prior === 'function') prior(shader, renderer);
      Object.assign(shader.uniforms, uniforms);

      shader.vertexShader = VERTEX_DECL + shader.vertexShader.replace(
        '#include <begin_vertex>',
        '#include <begin_vertex>' + VERTEX_ASSIGN,
      );

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
     * in ordinary daylight than through an amber filter.
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
