/** T-3054: the sun's shadow biases are fractions of a shadow texel on every detail tier.
 * node tools/check_shadow_bias.mjs [--self-test]
 * Source contract plus arithmetic. The `light` tier draws the sun's shadow at 23.4 cm a
 * texel and kept the -0.0004 depth bias and 0.045 m normal bias tuned on the 11.7 cm texel
 * of `full`, so on the owner's iPhone a pale sunlit wall shadowed itself in blocks (the
 * 1835 freight shed by the Dearborn draw). world.js now derives both from the texel
 * wherever the map is sized; this reads both places, replays each tier's rig, and requires
 * `full` and `balanced` to keep exactly -0.0004 and 0.045 m and every tier to hold the
 * same fraction of its texel.
 * `--self-test` feeds it the pre-T-3054 source and requires the check to refuse it.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../renderers/web/js');
const worldSrc = await readFile(path.join(web, 'world.js'), 'utf8');
const mainSrc = await readFile(path.join(web, 'main.js'), 'utf8');

function check(world, main) {
  const reach = Number(world.match(/export const SHADOW_REACH_M = (\d+(?:\.\d+)?);/)?.[1]);
  assert.ok(reach > 0, 'world.js states SHADOW_REACH_M');
  const fullTexel = world.match(/const FULL_TEXEL_M = ([^;]+);/)?.[1];
  const depthExpr = world.match(/export const SHADOW_BIAS_TEXELS = ([^;]+);/)?.[1];
  const normalExpr = world.match(/export const SHADOW_NORMAL_BIAS_TEXELS = ([^;]+);/)?.[1];
  assert.ok(fullTexel && depthExpr && normalExpr,
    'world.js states both biases per texel (SHADOW_BIAS_TEXELS, SHADOW_NORMAL_BIAS_TEXELS)');
  const evalIn = (expr) => Function('SHADOW_REACH_M', `const FULL_TEXEL_M = ${fullTexel}; return (${expr});`)(reach);
  const depthRatio = evalIn(depthExpr);
  const ratio = evalIn(normalExpr);
  assert.ok(ratio > 0 && depthRatio < 0, `the biases per texel are signed as three wants (got ${depthRatio}, ${ratio})`);
  const maps = world.match(/const baseMap = lowSpec \? (\d+) : (\d+);/);
  assert.ok(maps, 'world.js sizes the base shadow map by lowSpec');
  const [lowMap, fullMap] = [Number(maps[1]), Number(maps[2])];
  // No bias is written as a length anywhere; both go through the texel, at boot and in
  // setShadowRig.
  const lengths = [...world.matchAll(/light\.shadow\.(normalBias|bias) = ([^;]+);/g)].map((m) => m[0]);
  assert.deepEqual(lengths, [], `no shadow bias is written as a length: ${lengths.join(' | ')}`);
  const derived = [...world.matchAll(/Object\.assign\(light\.shadow, shadowBiasFor\(([^;]+)\)\);/g)];
  assert.ok(derived.length >= 2, `the biases are derived at boot and by setShadowRig (found ${derived.length})`);
  const rigBody = world.slice(world.indexOf('setShadowRig(metres)'));
  assert.match(rigBody.slice(0, rigBody.indexOf('return {')),
    /Object\.assign\(light\.shadow, shadowBiasFor\(shadowRig\.texelM\)\)/,
    'setShadowRig re-derives the biases from the texel it just set');
  // Replay each tier's rig exactly as setShadowRig sizes it.
  const tiers = {};
  for (const m of main.matchAll(/\n\s*(full|balanced|light):\s*\{[^}]*?shadowReachM:\s*(\d+)/g)) {
    tiers[m[1]] = Number(m[2]);
  }
  assert.deepEqual(Object.keys(tiers).sort(), ['balanced', 'full', 'light'], 'main.js states each tier\'s shadow reach');
  const rows = [];
  for (const [device, baseMap] of [['desktop', fullMap], ['lowSpec', lowMap]]) {
    for (const [tier, r] of Object.entries(tiers)) {
      const map = Math.max(512, Math.round(baseMap * (r / reach)));
      const texel = (2 * r) / map;
      rows.push({ device, tier, texel, bias: ratio * texel, depth: depthRatio * texel });
    }
  }
  for (const row of rows.filter((x) => x.device === 'desktop' && x.tier !== 'light')) {
    assert.ok(Math.abs(row.bias - 0.045) < 1e-9,
      `${row.tier} on a desktop keeps the 0.045 m normal bias (got ${row.bias.toFixed(4)})`);
    assert.ok(Math.abs(row.depth + 0.0004) < 1e-12,
      `${row.tier} on a desktop keeps the -0.0004 depth bias (got ${row.depth})`);
  }
  for (const row of rows) {
    assert.ok(row.bias / row.texel > 0.38,
      `${row.device} ${row.tier}: normal bias ${row.bias.toFixed(4)} m is ${(row.bias / row.texel).toFixed(3)} of its ${(row.texel * 100).toFixed(1)} cm texel`);
    assert.ok(Math.abs(row.depth / row.texel - depthRatio) < 1e-12,
      `${row.device} ${row.tier}: depth bias ${row.depth} holds the same fraction of its texel`);
  }
  return rows;
}

if (process.argv.includes('--self-test')) {
  // The pre-T-3054 rig: fixed lengths at boot, and a setShadowRig that left them alone.
  const before = worldSrc
    .replace(/Object\.assign\(light\.shadow, shadowBiasFor\(\(2 \* half\) \/ baseMap\)\);/,
      'light.shadow.bias = -0.0004;\n  light.shadow.normalBias = 0.045;')
    .replace(/\n\s*Object\.assign\(light\.shadow, shadowBiasFor\(shadowRig\.texelM\)\);/, '');
  assert.notEqual(before, worldSrc, 'the self-test could rewrite the source it breaks');
  let refused = false;
  try { check(before, mainSrc); } catch (e) { refused = true; console.log(`   self-test | refused as it should: ${e.message.split("\n")[0]}`); }
  assert.ok(refused, 'the check refuses the fixed-length rig');
  console.log('PASS shadow bias self-test: the pre-T-3054 rig is refused');
} else {
  const rows = check(worldSrc, mainSrc);
  const lp = rows.find((x) => x.device === 'lowSpec' && x.tier === 'light');
  console.log(`PASS shadow bias: ${rows.map((x) => `${x.device}/${x.tier} ${(x.texel * 100).toFixed(1)} cm -> ${x.depth.toFixed(4)}, ${(x.bias * 100).toFixed(1)} cm`).join(', ')}`
    + ` (phone light ${(lp.bias * 100).toFixed(1)} cm)`);
}
