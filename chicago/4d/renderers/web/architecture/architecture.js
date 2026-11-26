/**
 * architecture.js — the Architecture site (T-3750).
 *
 * The owner, 2026-11-26: "Expose the architecture site and building kit to expert users,
 * separate link/site." This page shows the sixteen building kits of the Prairie Avenue
 * programme (data/components/prairie_1904/k*.json) and every building whose record names
 * one of their parts, each with its model in an orbit viewer. Everything it shows comes
 * from data.json, which tools/architecture_site.py derives at publish from the committed
 * records; this file words nothing about a building or a kit on its own.
 *
 * Routes (the hash, so one static page serves them all):
 *   #kits             the sixteen kits          #kit/K06[/<part id>]   one kit, one part
 *   #houses           every kit-built building  #house/<structure id>  one building
 *   #about            what this is and how to read it
 *
 * The models: a kit's specimen is its generator's own sample (specimens/, copied unchanged);
 * a building's model is the file the town draws (../../data/gltf/), loaded the way the town
 * loads it — meshopt, the shared KTX2 loader, the shared texture sheets with their retries,
 * and on the dev preview its publication aliases (the pointer is read from walk/index.html).
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { initKTX2, registerKTX2 } from '../js/ktx2.js';
import { fetchPublishedAssetBytes, registerPublishedTextureBuffers } from '../js/published-assets.js';

const HERE = new URL('./', import.meta.url);
const APP = new URL('../../', HERE);                  // /4d/ or /4d/dev/
const DATA = new URL('data/', APP);
const SITE = new URL(APP.pathname.endsWith('/4d/dev/') ? '../../' : '../', APP);
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const GRADE_WORD = { attested: 'Attested', inferred: 'Inferred', reconstructed: 'Reconstructed' };
const chip = (g) => `<span class="chip ${GRADE_WORD[g] ? g : 'none'}">${esc(GRADE_WORD[g] ?? 'ungraded')}</span>`;
const mib = (b) => `${(b / 1048576).toFixed(b < 1048576 ? 2 : 1)} MB`;
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

let DATA_JSON = null;
let byKit = new Map();
let byHouse = new Map();

// ---- the shared viewer ---------------------------------------------------------------
const viewer = (() => {
  let renderer = null, scene, camera, grid, root = null, host = null, raf = 0;
  const target = new THREE.Vector3();
  const orbit = { theta: Math.PI * 0.22, phi: Math.PI * 0.36, radius: 10 };
  const pointers = new Map();
  let pinch = null, serial = 0, gridStep = 1;
  let glbLoader = null;

  function ensure() {
    if (renderer) return;
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-label', 'Model viewer: drag to turn, scroll or pinch to zoom, right-drag or two fingers to pan');
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    initKTX2(renderer);
    scene = new THREE.Scene();
    scene.background = new THREE.Color('#c9cec7');
    scene.add(new THREE.HemisphereLight(0xf4f4ee, 0x5b6356, 2.2));
    const sun = new THREE.DirectionalLight(0xffffff, 2.3);
    sun.position.set(30, 60, 40);
    scene.add(sun);
    const fill = new THREE.DirectionalLight(0xdfe8ff, 0.7);
    fill.position.set(-40, 20, -30);
    scene.add(fill);
    camera = new THREE.PerspectiveCamera(35, 1, 0.05, 2000);
    glbLoader = registerPublishedTextureBuffers(registerKTX2(new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)));
    canvas.addEventListener('pointerdown', down);
    canvas.addEventListener('pointermove', move);
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
    canvas.addEventListener('wheel', (e) => { e.preventDefault(); zoom(Math.exp(e.deltaY * 0.0012)); }, { passive: false });
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    canvas.addEventListener('dblclick', () => frame());
    new ResizeObserver(() => draw()).observe(canvas);
  }

  function down(e) {
    e.target.setPointerCapture?.(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey });
    pinch = null;
  }
  function move(e) {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    p.x = e.clientX; p.y = e.clientY;
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      if (pinch) { zoom(pinch.d / Math.max(d, 1)); pan(mx - pinch.mx, my - pinch.my); }
      pinch = { d, mx, my };
      return;
    }
    if (p.pan) pan(dx, dy);
    else { orbit.theta -= dx * 0.008; orbit.phi = Math.min(Math.PI * 0.49, Math.max(0.05, orbit.phi - dy * 0.008)); draw(); }
  }
  function up(e) { pointers.delete(e.pointerId); pinch = null; }
  function zoom(f) { orbit.radius = Math.min(1500, Math.max(0.2, orbit.radius * f)); draw(); }
  function pan(dx, dy) {
    const h = renderer.domElement.clientHeight || 1;
    const k = (2 * orbit.radius * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) / h;
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const upv = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    target.addScaledVector(right, -dx * k).addScaledVector(upv, dy * k);
    draw();
  }

  function draw() {
    if (!renderer || raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      const c = renderer.domElement, w = c.clientWidth, h = c.clientHeight;
      if (!w || !h) return;
      if (c.width !== Math.round(w * renderer.getPixelRatio()) || c.height !== Math.round(h * renderer.getPixelRatio())) {
        renderer.setSize(w, h, false);
      }
      camera.aspect = w / h;
      camera.position.set(
        target.x + orbit.radius * Math.sin(orbit.phi) * Math.sin(orbit.theta),
        target.y + orbit.radius * Math.cos(orbit.phi),
        target.z + orbit.radius * Math.sin(orbit.phi) * Math.cos(orbit.theta));
      camera.near = Math.max(0.02, orbit.radius / 500);
      camera.far = orbit.radius * 50 + 200;
      camera.updateProjectionMatrix();
      camera.lookAt(target);
      renderer.render(scene, camera);
    });
  }

  /** The box of what is visible under `obj`, from its meshes only. */
  function visibleBox(obj) {
    const box = new THREE.Box3();
    obj.updateMatrixWorld(true);
    obj.traverseVisible((o) => { if (o.isMesh) box.expandByObject(o); });
    return box;
  }

  function frame() {
    if (!root) return;
    const box = visibleBox(root);
    if (box.isEmpty()) return;
    const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
    target.copy(centre);
    const fit = Math.max(size.x, size.y, size.z) * 0.5 / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    orbit.radius = Math.max(0.6, fit * 1.35);
    orbit.theta = Math.PI * 0.22; orbit.phi = Math.PI * 0.36;
    if (grid) scene.remove(grid);
    // Squares of 1 m under a part or a house; 5 or 10 m under a long specimen row, so the
    // grid stays a scale and never a solid sheet. The HUD names the square.
    const span = Math.max(size.x, size.z) * 1.3;
    gridStep = span > 160 ? 10 : span > 50 ? 5 : 1;
    const cells = Math.max(4, Math.ceil(span / gridStep));
    grid = new THREE.GridHelper(cells * gridStep, cells, 0x51606f, 0x8c968f);
    grid.position.set(centre.x, box.min.y - 0.002, centre.z);
    scene.add(grid);
    hud(box);
    draw();
  }

  function hud(box) {
    const size = box.getSize(new THREE.Vector3());
    let tris = 0;
    root.traverseVisible((o) => {
      if (!o.isMesh || !o.geometry) return;
      const g = o.geometry, n = g.index ? g.index.count : g.attributes.position?.count ?? 0;
      tris += Math.round(n / 3) * (o.isInstancedMesh ? o.count : 1);
    });
    const el = host?.querySelector('.hud');
    if (el) el.innerHTML = `<span>${size.x.toFixed(2)} × ${size.z.toFixed(2)} m, ${size.y.toFixed(2)} m high</span><span>${tris.toLocaleString()} triangles · grid ${gridStep} m</span>`;
  }

  async function show(container, url, { published = false } = {}) {
    ensure();
    const mine = ++serial;
    host = container;
    container.querySelector('.stage').replaceChildren(renderer.domElement);
    const msg = container.querySelector('.msg');
    msg.hidden = false;
    msg.textContent = 'Loading the model…';
    if (root) { scene.remove(root); dispose(root); root = null; }
    if (grid) { scene.remove(grid); grid = null; }
    draw();
    try {
      if (published) await aliasPointer();
      const bytes = await fetchPublishedAssetBytes(url);
      if (mine !== serial) return null;
      const gltf = await new Promise((ok, no) => glbLoader.parse(bytes, new URL('.', url).href, ok, no));
      if (mine !== serial) { dispose(gltf.scene); return null; }
      root = gltf.scene;
      scene.add(root);
      msg.hidden = true;
      frame();
      return { root, bytes: bytes.byteLength };
    } catch (err) {
      if (mine === serial) msg.textContent = `The model did not load: ${err.message}`;
      return null;
    }
  }

  /** Show only the named root nodes, and frame them. GLTFLoader strips the dots from a node's
   *  name (PropertyBinding.sanitizeNodeName), so the record's names are compared the same way. */
  function isolate(names) {
    if (!root) return;
    const want = new Set(names.map((n) => THREE.PropertyBinding.sanitizeNodeName(n)));
    for (const child of root.children) child.visible = want.has(child.name);
    frame();
  }

  function dispose(obj) {
    obj.traverse((o) => {
      o.geometry?.dispose?.();
      for (const m of [].concat(o.material ?? [])) {
        for (const v of Object.values(m)) if (v?.isTexture) v.dispose();
        m.dispose?.();
      }
    });
  }

  function release() { serial++; host = null; if (root) { scene.remove(root); dispose(root); root = null; } }
  return { show, isolate, frame, release };
})();

/** On the dev preview the town's GLBs may be served from production's identical copy; the
 *  app's page carries the pointer to that catalogue. Copy it here once, so published-assets.js
 *  resolves this page's fetches exactly as it resolves the town's. Production has none. */
let aliasRead = null;
function aliasPointer() {
  aliasRead ??= fetch(new URL('walk/index.html', APP)).then((r) => (r.ok ? r.text() : '')).then((html) => {
    const tag = html.match(/<meta\b[^>]*name=["']c4d-asset-aliases["'][^>]*>/i)?.[0];
    if (!tag || document.querySelector('meta[name="c4d-asset-aliases"]')) return;
    const attr = (n) => tag.match(new RegExp(`${n}=["']([^"']+)["']`, 'i'))?.[1];
    const meta = document.createElement('meta');
    meta.name = 'c4d-asset-aliases';
    meta.content = new URL(attr('content'), new URL('walk/', APP)).pathname;
    meta.setAttribute('data-sha256', attr('data-sha256') ?? '');
    document.head.append(meta);
  }).catch(() => {});
  return aliasRead;
}

// ---- views ---------------------------------------------------------------------------
const view = () => $('#view');
function setCurrent(route) {
  for (const a of document.querySelectorAll('.menu a')) {
    if (a.dataset.route === route) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  }
}

function kitsView() {
  setCurrent('kits');
  const d = DATA_JSON;
  const parts = d.kits.reduce((n, k) => n + k.collections.reduce((m, c) => m + c.items.length, 0), 0);
  view().innerHTML = `
    <span class="label amber">The architectural library</span>
    <h1>Sixteen kits, <em>one street of 1904.</em></h1>
    <p class="lede">The Prairie Avenue houses are built from a library of components. A house record names its parts
      and their sizes; the kits supply the stone, brick, windows, roofs and cornices. Each kit below shows its rule,
      every part with its measured values and how sure each is, the generator's own specimen in 3D, and every
      building whose record uses it.</p>
    <div class="stats">
      <a class="stat" href="#kits"><b>${d.kits.length}</b><span>Kits</span></a>
      <span class="stat"><b>${parts}</b><span>Parts and recipes</span></span>
      <a class="stat" href="#houses"><b>${d.houses.length}</b><span>Buildings using them</span></a>
      <span class="stat"><b>${d.kits.filter((k) => k.specimen).length}</b><span>Specimens in 3D</span></span>
    </div>
    <div class="grid">${d.kits.map((k) => `
      <a class="card" href="#kit/${k.code}">
        ${k.study ? `<span class="thumb" style="background-image:url('${esc(k.study)}')" role="img" aria-label="${esc(k.name)} study"></span>` : `<span class="thumb none">${k.code}</span>`}
        <span class="body">
          <span class="code">${k.code}</span>
          <h3>${esc(k.name)}</h3>
          <p>${esc(k.line)}</p>
          <span class="meta"><span>${plural(k.collections.reduce((m, c) => m + c.items.length, 0), 'part')}</span>
            <span>${plural(k.houses.length, 'building')}</span>${k.specimen ? '<span>3D specimen</span>' : ''}</span>
        </span>
      </a>`).join('')}
    </div>`;
}

function paramList(params) {
  if (!params.length) return '';
  return `<ul class="params">${params.map(([k, v]) => `<li><b>${esc(k)}</b> ${esc(Array.isArray(v) ? `[${v.join(', ')}]` : v)}</li>`).join('')}</ul>`;
}

function housesLinks(ids, limit = 12) {
  const named = ids.map((id) => byHouse.get(id)).filter(Boolean);
  const link = (h) => `<a href="#house/${esc(h.id)}" title="${esc(shortName(h))}">${esc(listName(h))}</a>`;
  if (named.length <= limit) return named.map(link).join(', ');
  return `${named.slice(0, limit).map(link).join(', ')} <details class="more"><summary>and ${named.length - limit} more</summary>${named.slice(limit).map(link).join(', ')}</details>`;
}
const shortName = (h) => h.name.replace(/\s*\((?:K\d\d|T-\d+)[^)]*\)\s*$/, '');
/** In a list of many, the address alone where the name leads with one ("1945 Prairie Avenue — …"). */
const listName = (h) => shortName(h).split(' — ')[0];

function nodeFor(kit, id) {
  return kit.specimen_nodes.find((n) => n === id || n === `${id}.full`) ?? null;
}

function kitView(code, part) {
  setCurrent('kits');
  const k = byKit.get(code);
  if (!k) return notFound(`There is no kit ${code}.`);
  view().innerHTML = `
    <p class="crumbs"><a href="#kits">Kits</a> / ${k.code}</p>
    <div class="detail-head">
      <span class="label amber">${k.code}${k.ticket ? ` · ${esc(k.ticket)}` : ''}</span>
      <h1>${esc(k.name)}</h1>
      <p class="lede">${esc(k.title)}</p>
      <ul class="links">
        <li><a href="${esc(k.file)}" rel="noopener">Kit record</a></li>
        ${k.generator ? `<li><a href="${esc(k.generator)}" rel="noopener">Generator</a></li>` : ''}
        ${k.readme ? `<li><a href="${esc(k.readme)}" rel="noopener">Study notes</a></li>` : ''}
        ${k.specimen ? `<li><a href="${esc(k.specimen)}" download>Specimen GLB · ${mib(k.specimen_bytes)}</a></li>` : ''}
      </ul>
    </div>
    <div class="split">
      <div>
        ${k.specimen ? `
          <div class="viewer" id="kit-viewer"><div class="stage"></div><div class="msg"></div><div class="hud"></div></div>
          <div class="viewer-tools">
            <label class="mono" for="part-pick">Show</label>
            <select id="part-pick"><option value="">Every part</option>${k.specimen_nodes.map((n) => `<option value="${esc(n)}">${esc(n.replace(/\.full$/, ''))}${/\.light$/.test(n) ? ' (light tier)' : ''}</option>`).join('')}</select>
            <button class="btn" type="button" id="reframe">Reframe</button>
          </div>` : k.study ? `<figure><img class="study" src="${esc(k.study)}" alt="${esc(k.name)} study" loading="lazy"></figure>` : ''}
      </div>
      <div class="panel">
        <h3>The kit's rule</h3>
        <p class="rule">${esc(k.rule)}</p>
      </div>
    </div>
    ${k.specimen && k.study ? `<h2>The study</h2><figure><img class="study" src="${esc(k.study)}" alt="${esc(k.name)} study, from the kit's own study notes" loading="lazy"><figcaption>From the kit's study notes, rendered by the same three.js the town uses.</figcaption></figure>` : ''}
    ${k.collections.map((c) => `
      <h2>${esc(title(c.key))} <span class="count">${c.items.length}</span></h2>
      <div class="parts">${c.items.map((it) => {
        const users = k.part_houses[it.id] ?? [];
        const node = nodeFor(k, it.id);
        return `<article class="part" id="part-${esc(it.id)}">
          <div class="part-head"><code>${esc(it.id)}</code>${it.confidence ? chip(it.confidence) : ''}
            ${node ? `<button class="btn" type="button" data-show="${esc(node)}">Show in 3D</button>` : ''}</div>
          ${it.note ? `<p>${esc(it.note)}</p>` : ''}
          ${paramList(it.params)}
          ${users.length ? `<p class="users">Used by ${plural(users.length, 'building')}: ${housesLinks(users, 8)}</p>` : ''}
        </article>`;
      }).join('')}</div>`).join('')}
    <h2>Buildings built on ${k.code} <span class="count">${k.houses.length}</span></h2>
    <p class="users">${k.houses.length ? housesLinks(k.houses, 40) : 'No building record names this kit yet.'}</p>`;
  if (k.specimen) {
    const box = $('#kit-viewer');
    const pick = $('#part-pick');
    const everyPart = k.specimen_nodes.filter((x) => !/\.light$/.test(x));
    const showNode = (n) => { pick.value = n ?? ''; viewer.isolate(n ? [n] : everyPart); };
    viewer.show(box, new URL(k.specimen, HERE)).then((r) => {
      if (!r) return;
      // A specimen lays every variant out in one row, tens of metres long, so the page opens
      // on one part (the one asked for, else the first) and `Every part` shows the row.
      const n = (part && nodeFor(k, part)) || everyPart[0];
      showNode(n ?? null);
    });
    pick.addEventListener('change', () => showNode(pick.value || null));
    $('#reframe').addEventListener('click', () => viewer.frame());
    for (const b of view().querySelectorAll('[data-show]')) {
      b.addEventListener('click', () => { showNode(b.dataset.show); box.scrollIntoView({ behavior: 'smooth', block: 'center' }); });
    }
  }
  if (part) document.getElementById(`part-${part}`)?.scrollIntoView({ block: 'center' });
}

const title = (key) => ({ variants: 'Variants', fabrics: 'Fabrics', recipes: 'Recipes', layers: 'Layers', datums: 'Datums',
  samples: 'Samples', trim: 'Trim', parts: 'Parts', families: 'Families' })[key] ?? key.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());

function housesView() {
  setCurrent('houses');
  const d = DATA_JSON;
  const years = [...new Set(d.houses.map((h) => h.year))];
  view().innerHTML = `
    <span class="label sky">The buildings</span>
    <h1>Every building <em>built on a kit.</em></h1>
    <p class="lede">Each building whose record names a kit's part, read from the records themselves. Open one to turn its
      model, the same file the town draws, and see which kits and which parts it is built from.</p>
    <div class="filters">
      <input type="search" id="q" placeholder="Search by address, name or id" aria-label="Search buildings">
      <select id="yr" aria-label="Year"><option value="">Every year</option>${years.map((y) => `<option>${y}</option>`).join('')}</select>
      <select id="kt" aria-label="Kit"><option value="">Every kit</option>${d.kits.map((k) => `<option value="${k.code}">${k.code} ${esc(k.name)}</option>`).join('')}</select>
      <span class="count" id="n"></span>
    </div>
    <table class="table"><thead><tr><th>Building</th><th>Year</th><th>Grade</th><th>Kits</th></tr></thead><tbody id="rows"></tbody></table>`;
  const q = $('#q'), yr = $('#yr'), kt = $('#kt');
  const saved = new URLSearchParams(location.hash.split('?')[1] ?? '');
  q.value = saved.get('q') ?? ''; yr.value = saved.get('year') ?? ''; kt.value = saved.get('kit') ?? '';
  const fill = () => {
    const needle = q.value.trim().toLowerCase();
    const rows = d.houses.filter((h) => (!yr.value || h.year === yr.value) && (!kt.value || h.kits.includes(kt.value))
      && (!needle || `${h.name} ${h.id} ${h.aka.join(' ')}`.toLowerCase().includes(needle)));
    $('#rows').innerHTML = rows.map((h) => `<tr>
      <td><a href="#house/${esc(h.id)}">${esc(shortName(h))}</a></td>
      <td class="yr">${h.year}</td><td>${chip(h.grade)}</td>
      <td><span class="kitcodes">${h.kits.map((c) => `<a href="#kit/${c}" title="${esc(byKit.get(c)?.name)}">${c}</a>`).join('')}</span></td></tr>`).join('');
    $('#n').textContent = `${rows.length} of ${d.houses.length}`;
    const p = new URLSearchParams();
    if (q.value.trim()) p.set('q', q.value.trim());
    if (yr.value) p.set('year', yr.value);
    if (kt.value) p.set('kit', kt.value);
    history.replaceState(null, '', `#houses${p.toString() ? `?${p}` : ''}`);
  };
  for (const el of [q, yr, kt]) el.addEventListener('input', fill);
  fill();
}

function houseView(id) {
  setCurrent('houses');
  const h = byHouse.get(id);
  if (!h) return notFound(`There is no kit-built building ${id}.`);
  const modelUrl = new URL(h.asset, DATA);
  view().innerHTML = `
    <p class="crumbs"><a href="#houses">Buildings</a> / ${esc(h.id)}</p>
    <div class="detail-head">
      <span class="label sky">${esc(h.year)} · ${esc(h.archetype)}</span>
      <h1>${esc(shortName(h))}</h1>
      ${h.aka.length ? `<p class="lede">${esc(h.aka.join(' · '))}</p>` : ''}
      <ul class="links">
        <li><a href="${esc(h.record)}" rel="noopener">Building record</a></li>
        <li><a href="${esc(new URL(`sidecars/${h.year}/${h.id}.json`, DATA))}">Compiled sidecar</a></li>
        <li><a href="${esc(modelUrl)}" download>Model GLB</a></li>
        <li><a href="${esc(new URL(`${h.year}/`, APP))}">Walk ${esc(h.year)}</a></li>
      </ul>
    </div>
    <div class="split">
      <div>
        <div class="viewer" id="house-viewer"><div class="stage"></div><div class="msg"></div><div class="hud"></div></div>
        <div class="viewer-tools"><button class="btn" type="button" id="reframe">Reframe</button><span class="mono dim" id="bytes"></span></div>
      </div>
      <div class="panel">
        <h3>How sure the model is</h3>
        <p>${chip(h.grade)}</p>
        ${h.grade_why ? `<p>${esc(h.grade_why)}</p>` : ''}
        <h3 style="margin-top:14px">Built from</h3>
        <div class="kits-used">${h.kits.map((c) => {
          const k = byKit.get(c);
          const parts = h.parts[c] ?? [];
          return `<div class="row"><a href="#kit/${c}">${c} ${esc(k?.name)}</a>
            <ul class="params">${parts.map((p) => `<li><a href="#kit/${c}/${esc(p)}">${esc(p)}</a></li>`).join('') || '<li class="dim">the kit as a whole</li>'}</ul></div>`;
        }).join('')}</div>
      </div>
    </div>`;
  viewer.show($('#house-viewer'), modelUrl, { published: true }).then((r) => {
    if (r) $('#bytes').textContent = `${mib(r.bytes)} as published`;
  });
  $('#reframe').addEventListener('click', () => viewer.frame());
}

function aboutView() {
  setCurrent('about');
  view().innerHTML = `
    <span class="label">About</span>
    <h1>How to read <em>this site.</em></h1>
    <div class="panel" style="margin-top:18px">
      <p>4D Chicago is records first. A building is a JSON record of measured values, each with a confidence and the
        sources behind it; Python generators build its model in a pinned Blender from the component kits shown here.
        Change a kit and every building that uses it is rebuilt and checked against its photographs again.</p>
      <p><b>Confidence.</b> ${chip('attested')} a source states it. ${chip('inferred')} it follows from sources by a
        stated reading. ${chip('reconstructed')} no source settles it; it is built to a recorded rule, and the
        project's liberties ledger says so.</p>
      <p><b>Specimens</b> are each kit generator's own sample of every variant, the file its study was made from.
        <b>Building models</b> are the files the town draws, at web detail. The grid under every model is in metres.</p>
      <p><b>Which buildings use a kit</b> is read from the records: a building is listed under a kit when its record names
        one of that kit's parts or is built on its archetype.</p>
      <p>Drag to turn a model, scroll or pinch to zoom, right-drag or use two fingers to pan, double-click to reframe.</p>
      <p><a href="${esc(new URL('technicians/', SITE))}">For technicians</a> explains the whole pipeline.
        The records, generators and checks are in <a href="https://github.com/kevinrhaas/chicago">the repository</a>;
        <a href="https://github.com/kevinrhaas/chicago/blob/main/chicago/4d/docs/LIBERTIES.md">the liberties</a> list every reconstruction.</p>
    </div>`;
}

function notFound(text) {
  view().innerHTML = `<h1>Not here</h1><p class="lede">${esc(text)} <a href="#kits">Back to the kits</a>.</p>`;
}

function route() {
  viewer.release();
  const [path] = location.hash.replace(/^#/, '').split('?');
  const [head, a, ...rest] = path.split('/');
  const b = rest.length ? decodeURIComponent(rest.join('/')) : null;
  if (head === 'kit' && a) kitView(a.toUpperCase(), b ?? null);
  else if (head === 'house' && a) houseView(decodeURIComponent(a));
  else if (head === 'houses') housesView();
  else if (head === 'about') aboutView();
  else kitsView();
  if (!(head === 'kit' && b)) window.scrollTo(0, 0);
}

async function boot() {
  const status = $('#status');
  try {
    const r = await fetch(new URL('data.json', HERE));
    if (!r.ok) throw new Error(`data.json: HTTP ${r.status}`);
    DATA_JSON = await r.json();
  } catch (err) {
    status.textContent = `The kits did not load (${err.message}).`;
    status.classList.add('err');
    return;
  }
  status.textContent = '';
  byKit = new Map(DATA_JSON.kits.map((k) => [k.code, k]));
  byHouse = new Map(DATA_JSON.houses.map((h) => [h.id, h]));
  for (const a of document.querySelectorAll('.foot a[href^="../"]')) a.href = new URL(a.getAttribute('href').replace(/^(\.\.\/)+/, ''), a.getAttribute('href').startsWith('../../../') ? SITE : APP).href;
  $('#built').textContent = DATA_JSON.commit ? `Built from ${DATA_JSON.commit}` : '';
  window.addEventListener('hashchange', route);
  route();
  window.__architecture = { data: DATA_JSON, viewer };
}
boot();
