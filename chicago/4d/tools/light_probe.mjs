/**
 * light_probe.mjs — what the lighting rig actually delivers, in numbers.
 *
 *   node tools/light_probe.mjs                 the source tree
 *   node tools/light_probe.mjs --published     the published mirror
 *   node tools/light_probe.mjs --json          machine-readable, for a gate
 *
 * WHY THIS EXISTS. RENDERING §4 W1 asks for a white-card harness, and it asks
 * for it because the last attempt at environment lighting was tuned by looking
 * at frames. A frame cannot tell you whether a wall is pale because the light is
 * blue or because the wall is: tone mapping, the sRGB encode and the sky are all
 * in the way. So this measures the rig itself, upstream of every one of them.
 *
 * HOW. It borrows the live page's renderer, scene and lights — `api.renderer`,
 * `api.scene3d` — and renders one lit pixel per probe into a LINEAR render
 * target with tone mapping OFF. What comes back is therefore the rendered
 * radiance in the working colour space, not a screenshot value, and the two
 * quantities W1 argues about fall straight out of it:
 *
 *   irradiance   a white Lambertian card (base colour 1,1,1, roughness 1) facing
 *                a given axis returns E/PI for that axis. Six axes give the
 *                shape of the fill — how much light reaches a north wall, an
 *                eave's underside, a leaf facing away from the sun.
 *   albedo       the same card in a documented base colour returns that colour's
 *                own hue, multiplied by the irradiance. Dividing the two says
 *                whether the rig PRESERVES the material or overrides it, which
 *                is the whole of the albedo-integrity acceptance: a documented
 *                white wall reads white, and a brown log wall keeps the R/B
 *                ratio its base colour specifies.
 *
 * The probes are rendered in their OWN scene, carrying references to the live
 * scene's lights and its `environment`. Nothing is added to the scene a visitor
 * sees, and the page's renderer state is restored before the probe returns —
 * asserted by re-reading it, because a probe that leaves tone mapping off would
 * silently corrupt every capture taken after it.
 *
 * THE SUN IS EXCLUDED BY DEFAULT and that is the point. W1 is about the FILL:
 * what lights the surfaces the sun does not reach. The direct term is measured
 * separately (`--sun`) so the two cannot be confused in one number, which is how
 * "total illuminance doubled" happened the last time this was tuned.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const flag = (n) => argv.includes(n);
const PUBLISHED = flag('--published');
const AS_JSON = flag('--json');
const WITH_SUN = flag('--sun');
const PORT = Number(process.env.PROBE_PORT || 4193);
const YEAR = process.env.CRITIC_YEAR || '1835';

const ROOT = PUBLISHED ? path.resolve(APP, '../../site/chicago/4d') : APP;
const ENTRY = PUBLISHED ? '/walk/' : '/renderers/web/index.html';

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
  '.geojson': 'application/json',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' }).end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));

/**
 * THE MATERIALS the albedo test is run against — the project's OWN committed
 * palette, not test colours, so that a pass is a statement about the town.
 *
 *   white_card    a perfect diffuser. Not a material: the instrument. Its
 *                 reading IS the irradiance, and its rendered hue is the hue
 *                 the rig imposes on a surface with no hue of its own.
 *   sauganash_white  `generators/placeholder.py` PALETTE #f2efe6, the documented
 *                 white of Wau-Bun's "pretentious white two-story building".
 *                 This is the wall the project's own sentence is about.
 *   log_wing      PALETTE #6b5334, the log finish. `world.js` records the failed
 *                 environment collapsing a brown log wall's R/B ratio; this is
 *                 the committed brown that test is run on.
 *   fresh_timber  `generators/inferred_placeholder.py` WALL_COLOURS, the finish
 *                 most of the anonymous town carries, so the test covers what is
 *                 actually on screen rather than only the landmarks.
 *
 * On the number 1.75. `world.js` quotes "R/B ≈ 1.75" as what a brown log wall's
 * base colour asks for, against 1.08 at the failure. Neither the colour it was
 * measured on nor the space it was measured in is recoverable from the repo —
 * the committed log brown is R/B 2.06 encoded and 4.87 linear — so this harness
 * does not chase 1.75. It states each card's own base ratio and measures the
 * rendered one against THAT, which is the invariant the sentence was reaching
 * for and is checkable without knowing what was in the working directory in
 * August 2026.
 */
const CARDS = [
  { id: 'white_card', hex: 0xffffff },
  { id: 'sauganash_white', hex: 0xf2efe6 },
  { id: 'log_wing', hex: 0x6b5334 },
  { id: 'fresh_timber', hex: 0xc3a478 },
];

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${PORT}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 180000 });

async function probe(withSun) {
  return page.evaluate(async ({ cards, withSun, threeUrl }) => {
  const THREE = await import(threeUrl);
  const api = window.__chicago4d;
  const { renderer, scene3d } = api;

  // The rig, borrowed rather than rebuilt: whatever world.js put in the scene is
  // what gets measured. Rebuilding it here would measure this file's idea of the
  // rig, which is exactly the mistake the harness exists to prevent.
  const lights = [];
  scene3d.traverse((o) => {
    if (o.isLight && (withSun || !o.isDirectionalLight)) lights.push(o);
  });

  const probeScene = new THREE.Scene();
  probeScene.environment = scene3d.environment;
  probeScene.environmentIntensity = scene3d.environmentIntensity;
  for (const l of lights) {
    const clone = l.clone();
    // A directional light's direction is its position relative to its target,
    // and clone() does not bring the target across.
    if (clone.isDirectionalLight) {
      clone.position.copy(l.getWorldPosition(new THREE.Vector3()));
      clone.target.position.copy(l.target.getWorldPosition(new THREE.Vector3()));
      probeScene.add(clone.target);
    }
    clone.castShadow = false;
    probeScene.add(clone);
  }

  // One pixel per probe, rendered flat-on. An orthographic camera looking down
  // -z at a unit plane rotated to face each axis: the plane's normal is what is
  // being measured, so the camera must not be part of the answer, and for a
  // Lambertian it is not.
  const AXES = [
    ['up', [0, 1, 0]], ['down', [0, -1, 0]],
    ['north', [0, 0, -1]], ['south', [0, 0, 1]],
    ['east', [1, 0, 0]], ['west', [-1, 0, 0]],
  ];
  const target = new THREE.WebGLRenderTarget(1, 1, {
    type: THREE.FloatType,
    colorSpace: THREE.LinearSRGBColorSpace,
  });
  const cam = new THREE.OrthographicCamera(-0.5, 0.5, 0.5, -0.5, 0.1, 10);
  const plane = new THREE.PlaneGeometry(2, 2);
  const buf = new Float32Array(4);

  const priorTarget = renderer.getRenderTarget();
  const priorToneMapping = renderer.toneMapping;
  const priorExposure = renderer.toneMappingExposure;
  const priorColorSpace = renderer.outputColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;

  const out = {};
  for (const card of cards) {
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(card.hex), roughness: 1.0, metalness: 0.0,
    });
    const mesh = new THREE.Mesh(plane, mat);
    probeScene.add(mesh);
    out[card.id] = { base: [mat.color.r, mat.color.g, mat.color.b], axes: {} };
    for (const [name, n] of AXES) {
      // Point the card's +z (the plane's normal) along the axis, and stand the
      // camera off along the same axis looking back at it.
      mesh.lookAt(n[0], n[1], n[2]);
      cam.position.set(n[0] * 2, n[1] * 2, n[2] * 2);
      cam.lookAt(0, 0, 0);
      cam.updateMatrixWorld();
      renderer.setRenderTarget(target);
      renderer.clear();
      renderer.render(probeScene, cam);
      renderer.readRenderTargetPixels(target, 0, 0, 1, 1, buf);
      out[card.id].axes[name] = [buf[0], buf[1], buf[2]];
    }
    probeScene.remove(mesh);
    mat.dispose();
  }

  renderer.setRenderTarget(priorTarget);
  renderer.toneMapping = priorToneMapping;
  renderer.toneMappingExposure = priorExposure;
  renderer.outputColorSpace = priorColorSpace;
  target.dispose();
  plane.dispose();

  return {
    probes: out,
    lights: lights.map((l) => ({
      type: l.type, name: l.name, intensity: l.intensity,
      color: [l.color.r, l.color.g, l.color.b],
      groundColor: l.groundColor ? [l.groundColor.r, l.groundColor.g, l.groundColor.b] : null,
    })),
    environment: !!scene3d.environment,
    environmentIntensity: scene3d.environmentIntensity,
    // Proof the page was handed back the way it was found. A probe that leaves
    // tone mapping off poisons every capture taken after it.
    restored: renderer.toneMapping === priorToneMapping
      && renderer.outputColorSpace === priorColorSpace
      && renderer.getRenderTarget() === priorTarget,
  };
  }, {
    cards: CARDS,
    withSun,
    threeUrl: '/renderers/web/vendor/three-0.185.1/three.module.js',
  });
}

// BOTH rigs, in one page visit. The fill alone is what W1 rebalances; the fill
// plus the sun is what a wall in the frame actually receives, and the albedo
// acceptance is a statement about that wall. Reporting one without the other is
// how "total illuminance doubled" passed a review once already.
const fill = await probe(false);
const full = await probe(true);
const exposure = await page.evaluate(() => window.__chicago4d.renderer.toneMappingExposure);

await browser.close();
server.close();

/**
 * Reported radiance -> irradiance. For a Lambertian, outgoing radiance is
 * albedo * E / PI, so E = PI * radiance / albedo. Reported per channel.
 */
function irradiance(radiance, base) {
  return radiance.map((v, i) => (base[i] > 1e-6 ? (Math.PI * v) / base[i] : 0));
}

/**
 * The renderer's own display chain, reproduced so a number here is comparable to
 * a number read off a capture: exposure, then the ACES filmic curve three ships,
 * then the sRGB encode. Not an approximation of them — the same expressions.
 */
function aces(x) {
  const a = 2.51, b = 0.03, c = 2.43, d = 0.59, e = 0.14;
  return Math.max(0, Math.min(1, (x * (a * x + b)) / (x * (c * x + d) + e)));
}
function encode(v) {
  return v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055;
}
function display(linear, exp) {
  return linear.map((v) => Math.round(255 * encode(aces(v * exp))));
}
const fmt = (v) => v.map((x) => x.toFixed(4)).join(' ');
const AXES = ['up', 'down', 'north', 'south', 'east', 'west'];

/** R/B in the space the acceptance sentence is written in — what you would read
 *  off a screenshot of the wall. */
function displayRB(rgb, exp) {
  const d = display(rgb, exp);
  return d[2] > 0 ? d[0] / d[2] : null;
}

function summarise(run) {
  const white = run.probes.white_card;
  const out = { irradiance: {}, cards: {} };
  for (const axis of AXES) out.irradiance[axis] = irradiance(white.axes[axis], white.base);
  for (const card of CARDS) {
    const p = run.probes[card.id];
    const baseRB = displayRB(p.base, 1);
    out.cards[card.id] = { baseRB, axes: {} };
    for (const axis of AXES) {
      out.cards[card.id].axes[axis] = {
        display: display(p.axes[axis], exposure),
        rb: displayRB(p.axes[axis], exposure),
      };
    }
  }
  return out;
}

const report = {
  environment: full.environment,
  environmentIntensity: full.environmentIntensity,
  exposure,
  restored: fill.restored && full.restored,
  lights: { fill: fill.lights, full: full.lights },
  fill: summarise(fill),
  full: summarise(full),
  errors,
};

if (AS_JSON) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log(`environment ${report.environment ? 'INSTALLED' : 'absent'}`
    + ` (intensity ${report.environmentIntensity})   exposure ${exposure}`);
  for (const l of full.lights) {
    console.log(`  light  ${(l.name || l.type).padEnd(12)} ${l.type.padEnd(18)}`
      + ` intensity ${l.intensity}`);
  }

  console.log('\nFILL ONLY — irradiance on a white Lambertian card (linear, working space)');
  for (const axis of AXES) {
    const e = report.fill.irradiance[axis];
    const lum = 0.2126 * e[0] + 0.7152 * e[1] + 0.0722 * e[2];
    console.log(`  ${axis.padEnd(6)} ${fmt(e)}    luminance ${lum.toFixed(4)}`);
  }
  console.log('\nFULL RIG (fill + sun) — irradiance');
  for (const axis of AXES) {
    const e = report.full.irradiance[axis];
    const lum = 0.2126 * e[0] + 0.7152 * e[1] + 0.0722 * e[2];
    console.log(`  ${axis.padEnd(6)} ${fmt(e)}    luminance ${lum.toFixed(4)}`);
  }

  console.log('\nALBEDO INTEGRITY — rendered sRGB and R/B, full rig');
  console.log('  card              base R/B   axis    rendered sRGB      R/B    off base');
  for (const card of CARDS) {
    const c = report.full.cards[card.id];
    for (const axis of ['up', 'north', 'south']) {
      const a = c.axes[axis];
      const off = c.baseRB && a.rb !== null ? `${((a.rb / c.baseRB - 1) * 100).toFixed(1)} %` : '—';
      console.log(`  ${card.id.padEnd(17)} ${(c.baseRB ?? 0).toFixed(3).padStart(6)}`
        + `   ${axis.padEnd(6)}  ${String(a.display.join(',')).padEnd(15)}`
        + ` ${(a.rb ?? 0).toFixed(3).padStart(6)}   ${off}`);
    }
  }

  if (!report.restored) console.log('\nWARNING: renderer state was not restored');
  if (errors.length) console.log(`\npage errors: ${errors.length}\n  ${errors.join('\n  ')}`);
}

process.exit(errors.length || !report.restored ? 1 : 0);
