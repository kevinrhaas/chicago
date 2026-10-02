'use strict';
// The Images section: every photograph, drawing, map plate and filing in data/images.json,
// as a grid, a list or a site plan of the street, each cross-linked to its buildings.
// app.js owns the library; it calls PrairieImages.attach(library) once that has loaded and
// asks PrairieImages.decorate() for each building card's image strip.
window.PrairieImages = (() => {
  const $ = id => document.getElementById(id);
  const node = (tag, text, cls) => { const el = document.createElement(tag); if (text !== undefined && text !== null) el.textContent = String(text); if (cls) el.className = cls; return el; };
  const array = v => Array.isArray(v) ? v : [];
  const SVG = 'http://www.w3.org/2000/svg';
  const svg = (tag, attrs = {}) => { const el = document.createElementNS(SVG, tag); for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v); return el; };
  // A package path, unless the 4D mirror serves its directory from the site root (viewer/root-served.js, T-1828).
  const packagePath = path => { const r = self.ROOT_SERVED; return r && r.dirs.some(d => path.startsWith(d)) ? r.base + path : '../' + path; };
  // The package's own copy of a file (the retired first store, still published as a fallback).
  function packageURL(path) {
    if (!path || typeof path !== 'string' || /^[a-z]+:/i.test(path) || path.startsWith('/') || path.split('/').includes('..')) return null;
    try { return new URL(packagePath(path), location.href).href; } catch { return null; }
  }
  // Where a local file is read from: the image store (kevinrhaas/chicago-images, owner 2026-10-02)
  // for the logical research/images/files/ paths, the package for everything else.
  function localURL(path) {
    const st = imgs?.image_store;
    if (st && typeof path === 'string' && path.startsWith(st.prefix) && !path.split('/').includes('..')) {
      try { return new URL(path.slice(st.prefix.length), st.base_url).href; } catch { /* fall through */ }
    }
    return packageURL(path);
  }
  // Every place an image can come from, in order: the store, the package copy, the holder.
  function candidates(r, which, size) {
    const path = r.local && (which === 'thumb' ? (r.local.thumb || r.local.display) : (r.local.display || (!r.image_url && r.local.thumb)));
    return [...new Set([path && localURL(path), path && packageURL(path), fallbackURL(r, size)].filter(Boolean))];
  }
  // Point an <img> at the first candidate and step to the next on error; onFail when all fail.
  function loadChain(img, urls, onFail) {
    let i = 0; img.src = urls[0];
    img.addEventListener('error', () => { i += 1; if (i < urls.length) { if (i === urls.length - 1) img.referrerPolicy = 'no-referrer'; img.src = urls[i]; } else onFail?.(); });
  }
  function remoteURL(value) { try { const u = new URL(value); return /^https?:$/.test(u.protocol) ? u.href : null; } catch { return null; } }
  function extLink(text, url) { const href = remoteURL(url); if (!href) return null; const a = node('a', text); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
  const noteKey = (el, key, label) => { el.dataset.note = String(key).slice(0, 300); el.dataset.noteLabel = String(label || key).slice(0, 300); return el; };

  let lib = null, imgs = null, plan = null, byId = new Map(), buildingsById = new Map(), ready = false;
  let view = 'grid', current = [], openIndex = -1, selectedParcel = null;
  const PERIOD_LABEL = { 'in-period': 'In period · to 1911', 'near-period': 'Near period · 1912–1930', later: 'Later · 1931 on' };
  const RIGHTS_LABEL = { 'public domain': 'Public domain', 'no known restrictions': 'No known restrictions', 'copyright — link only': 'In copyright · link only', 'unknown — link only': 'Rights unknown · link only' };
  // Street order: the library's building order, then the street and district views.
  const buildingName = id => { const b = buildingsById.get(id); return b ? (b.address || '').replace(/\s*S\.\s*Prairie Avenue/, ' Prairie') + ' · ' + (b.name || id) : id; };
  const shortAddr = id => { const b = buildingsById.get(id); return b ? (b.address || id).replace(/\s*S\.\s*Prairie Avenue/, ' Prairie').replace(/ Avenue| Street/, '') : id; };
  // A lot (a traced 1911 parcel) by its printed number: 'prairie_1730' → '1730 Prairie'.
  const lotsById = () => new Map(array(plan?.parcels).map(p => [p.id, p]));
  const lotLabel = id => { const p = lotsById().get(id); const n = (p?.addresses?.[0] || '').replace(/\s.*$/, ''); return n ? n + ' Prairie' : 'Unnumbered lot'; };
  const lotName = id => { const p = lotsById().get(id); const names = array(p?.building_ids).map(b => buildingsById.get(b)?.name).filter(Boolean); return lotLabel(id) + (names.length ? ' · ' + names.join('; ') : ' · no building record yet'); };
  const thumbOf = r => r.local && (localURL(r.local.thumb) || localURL(r.local.display));
  // A thumb-only local copy (fetch_image.py --thumb-only) is not a full view: the holder's image is.
  const fullOf = r => r.local && (localURL(r.local.display) || (!r.image_url && localURL(r.local.thumb)));
  // Link-only items are SHOWN from their holder, never copied here (owner, 2026-10-01): the
  // record's own image_url, asked for at a small size where the host has a size parameter.
  function remoteURL2(value, size) {
    const href = remoteURL(value); if (!href) return null;
    let u = href;
    if (/googleusercontent\.com|bp\.blogspot\.com/.test(u)) u = u.replace(/\/s\d+(-[a-z0-9-]+)?\//, '/s' + size + '/').replace(/=s\d+(-[a-z0-9-]+)?$/, '=s' + size);
    else if (/\/iiif\//.test(u) && /\/full\/[^/]+\/0\/default\.(jpg|png)/.test(u)) u = u.replace(/\/full\/[^/]+\/0\//, '/full/!' + size + ',' + size + '/0/');
    else if (/tile\.loc\.gov\/storage-services\/service\//.test(u)) { if (/\.tiff?$/i.test(u)) return null; if (size <= 640) u = u.replace(/[uv]\.jpg$/i, 'r.jpg'); }
    else if (!/\.(jpe?g|png|gif|webp)(\?|#|$)/i.test(u)) return null;
    return u;
  }
  const fallbackURL = (r, size) => remoteURL2(r.image_url || r.local?.fetched_from, size);
  const remoteThumbOf = r => !r.local && r.image_url ? remoteURL2(r.image_url, 480) : null;
  const remoteFullOf = r => !r.local?.display && r.image_url ? remoteURL2(r.image_url, 1600) : null;
  function remoteImg(src, r) { const img = node('img'); img.src = src; img.alt = r.title || ''; img.loading = 'lazy'; img.decoding = 'async'; img.referrerPolicy = 'no-referrer'; return img; }
  const dateText = r => r.date || (r.date_earliest && r.date_latest && r.date_earliest !== r.date_latest ? r.date_earliest + '–' + r.date_latest : r.date_earliest || r.date_latest) || 'Undated';
  const sortYear = r => r.date_earliest || r.date_latest || 9999;

  async function load() {
    const [a, b] = await Promise.all(['../data/images.json', '../data/site-plan.json'].map(u => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' HTTP ' + r.status); return r.json(); })));
    imgs = a; plan = b; byId = new Map(array(imgs.images).map(r => [r.id, r]));
  }
  const loaded = load().catch(err => { const s = $('imageStatus'); if (s) s.textContent = 'The image index could not be loaded: ' + err.message; });

  function forBuilding(id) { return array(imgs?.by_building?.[id]).map(i => byId.get(i)).filter(Boolean); }
  // The card's lead picture: an in-period front view held here, else anything held here.
  function leadImage(id) {
    const list = forBuilding(id).filter(r => thumbOf(r) || remoteThumbOf(r));
    const score = r => (r.period === 'in-period' ? 0 : r.period === 'near-period' ? 2 : 4) + (/front|elevation|oblique/i.test(r.view || '') && !/plan|section/i.test(r.view || '') ? 0 : 1) + (/plan|section|map/i.test(r.view || '') ? 2 : 0) + (thumbOf(r) ? 0 : 0.5);
    return list.sort((x, y) => score(x) - score(y))[0] || null;
  }

  function filters() {
    return { term: $('imageSearch').value.trim().toLowerCase(), building: $('imageBuilding').value, kind: $('imageKind').value, period: $('imagePeriod').value, rights: $('imageRights').value, sort: $('imageSort').value };
  }
  function matches(r, f) {
    if (f.building.startsWith('lot:')) { if (!array(r.parcel_ids).includes(f.building.slice(4))) return false; }
    else if (f.building === '_street' ? !r.streetscape : f.building !== 'all' && !r.building_ids.includes(f.building)) return false;
    if (f.kind === '_drawn' ? !/drawing|plan|map|plate|atlas|bird/.test(r.kind) : f.kind !== 'all' && r.kind !== f.kind) return false;
    if (f.period === 'by-year') { const y = Number($('year').value); if (!(sortYear(r) <= y)) return false; }
    else if (f.period !== 'all' && r.period !== f.period) return false;
    if (f.rights === 'here' && !r.local) return false;
    if (f.rights === 'link' && r.local) return false;
    if (f.term) {
      const hay = [r.id, r.title, r.kind, r.view, r.facing, r.camera_position, r.date, r.creator, r.repository, r.collection, r.call_number, r.notes, ...array(r.addresses), ...r.building_ids.map(buildingName)].join(' ').toLowerCase();
      if (!f.term.split(/\s+/).every(t => hay.includes(t))) return false;
    }
    return true;
  }
  function filtered() {
    const f = filters();
    const order = new Map(array(lib.buildings).map((b, i) => [b.id, i]));
    const rank = r => Math.min(...r.building_ids.map(b => order.get(b) ?? 999), 999);
    return array(imgs.images).filter(r => matches(r, f)).sort(f.sort === 'date' ? (a, b) => sortYear(a) - sortYear(b) || rank(a) - rank(b) : f.sort === 'kind' ? (a, b) => a.kind.localeCompare(b.kind) || rank(a) - rank(b) : (a, b) => rank(a) - rank(b) || sortYear(a) - sortYear(b));
  }

  function thumbBox(r, cls = 'img-thumb') {
    const box = node('div', null, cls), src = thumbOf(r);
    if (src) {
      const img = node('img'); img.alt = r.title || ''; img.loading = 'lazy'; img.decoding = 'async';
      // The /4d/ dev-preview mirror ships without the local derivatives: fall back to the holder.
      loadChain(img, candidates(r, 'thumb', 480), () => img.replaceWith(node('span', r.kind, 'img-ph')));
      box.append(img);
    }
    else {
      const placeholder = () => { box.classList.add('link-only'); box.replaceChildren(node('span', r.kind, 'img-ph'), node('span', 'View at ' + (r.repository || 'holder') + ' ↗', 'img-ph-sub')); };
      const remote = remoteThumbOf(r);
      if (remote) { const img = remoteImg(remote, r); img.addEventListener('error', placeholder); box.classList.add('remote'); box.title = 'Shown from ' + (r.repository || 'its holder') + ' — not copied here'; box.append(img, node('span', '↗', 'remote-mark')); }
      else placeholder();
    }
    return box;
  }
  function badges(r) {
    const b = node('div', null, 'img-badges');
    b.append(node('span', PERIOD_LABEL[r.period] || r.period, 'badge period-' + r.period));
    if (!r.local) b.append(node('span', 'Link only', 'badge link-badge')); else if (!r.local.display) b.append(node('span', 'Thumbnail here', 'badge link-badge'));
    return b;
  }
  function chipsFor(r, onPick) {
    const wrap = node('div', null, 'img-chips');
    r.building_ids.slice(0, 6).forEach(id => { const c = node('button', shortAddr(id), 'chip'); c.type = 'button'; c.title = buildingName(id); c.addEventListener('click', e => { e.stopPropagation(); onPick(id); }); wrap.append(c); });
    if (r.building_ids.length > 6) wrap.append(node('span', '+' + (r.building_ids.length - 6), 'meta'));
    if (!r.building_ids.length) array(r.parcel_ids).slice(0, 4).forEach(pid => { const c = node('button', lotLabel(pid), 'chip'); c.type = 'button'; c.title = lotName(pid); c.addEventListener('click', e => { e.stopPropagation(); pickLot(pid); }); wrap.append(c); });
    if (r.streetscape && !r.building_ids.length && !array(r.parcel_ids).length) wrap.append(node('span', 'Streetscape', 'chip chip-static'));
    return wrap;
  }

  function renderGrid(list) {
    const grid = node('div', null, 'img-grid');
    list.forEach((r, i) => {
      const card = node('article', null, 'img-card'); noteKey(card, 'image:' + r.id, r.title);
      const open = node('button', null, 'img-open'); open.type = 'button'; open.setAttribute('aria-label', 'Open ' + (r.title || r.id));
      open.append(thumbBox(r)); open.addEventListener('click', () => openDetail(i));
      const body = node('div', null, 'img-body');
      body.append(node('h3', r.title || r.id), node('p', [dateText(r), r.kind, r.view].filter(Boolean).join(' · '), 'meta'), badges(r), chipsFor(r, pickBuilding));
      card.append(open, body); grid.append(card);
    });
    return grid;
  }
  function renderList(list) {
    const wrap = node('div', null, 'img-table-wrap'), table = node('table', null, 'img-table');
    const head = node('tr'); ['', 'Title', 'Date', 'Kind · view', 'Buildings', 'Holder', 'Copy'].forEach(h => head.append(node('th', h)));
    const thead = node('thead'); thead.append(head); table.append(thead);
    const body = node('tbody');
    list.forEach((r, i) => {
      const tr = node('tr'); noteKey(tr, 'image:' + r.id, r.title);
      const t0 = node('td'); const btn = node('button', null, 'img-open small'); btn.type = 'button'; btn.setAttribute('aria-label', 'Open ' + (r.title || r.id)); btn.append(thumbBox(r, 'img-thumb small')); btn.addEventListener('click', () => openDetail(i)); t0.append(btn);
      const t1 = node('td'); const tl = node('button', r.title || r.id, 'text-button title-link'); tl.type = 'button'; tl.addEventListener('click', () => openDetail(i)); t1.append(tl);
      const t4 = node('td'); t4.append(chipsFor(r, pickBuilding));
      tr.append(t0, t1, node('td', dateText(r)), node('td', [r.kind, r.view].filter(Boolean).join(' · ')), t4, node('td', r.repository || '—'), node('td', r.local?.display ? 'Held here' : r.local ? 'Thumbnail here' : 'Link only'));
      body.append(tr);
    });
    table.append(body); wrap.append(table); return wrap;
  }

  // ---- the site plan -------------------------------------------------------------------
  // Local metres (x east, y north). Wide screens lay the street on its side, north to the
  // left, so the six blocks read as one strip; narrow screens keep north up.
  function project(points, wide, box) {
    return points.map(([x, y]) => wide ? [(box.maxY - y), (box.maxX - x)] : [(x - box.minX), (box.maxY - y)]);
  }
  function bounds() {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const p of [...plan.blocks.map(b => b.outline), ...plan.carriageways.map(c => c.polygon)]) for (const [x, y] of p) { minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); }
    const pad = 14; return { minX: minX - pad, maxX: maxX + pad, minY: minY - pad, maxY: maxY + pad };
  }
  const pts = p => p.map(q => q.map(n => n.toFixed(1)).join(',')).join(' ');
  const centroid = p => { const n = p.length; return [p.reduce((s, q) => s + q[0], 0) / n, p.reduce((s, q) => s + q[1], 0) / n]; };
  function siteMap(list, opts = {}) {
    const wrap = node('div', null, 'site-map' + (opts.mini ? ' mini' : ''));
    const box = bounds(), wide = opts.mini ? true : (wrap.isConnected ? wrap.clientWidth : $('imageViews').clientWidth || innerWidth) >= 700;
    const W = wide ? box.maxY - box.minY : box.maxX - box.minX, H = wide ? box.maxX - box.minX : box.maxY - box.minY;
    const s = svg('svg', { viewBox: `0 0 ${W.toFixed(0)} ${H.toFixed(0)}`, role: 'img', 'aria-label': 'Site plan of Prairie Avenue, 16th to 22nd Street, after the Sanborn 1911 sheets' });
    const counts = new Map(); list.forEach(r => array(r.parcel_ids).forEach(pid => counts.set(pid, (counts.get(pid) || 0) + 1)));
    const max = Math.max(1, ...counts.values());
    plan.blocks.forEach(b => s.append(svg('polygon', { points: pts(project(b.outline, wide, box)), class: 'sp-block' })));
    plan.alleys.forEach(a => s.append(svg('polygon', { points: pts(project(a.polygon, wide, box)), class: 'sp-alley' })));
    plan.carriageways.forEach(c => s.append(svg('polygon', { points: pts(project(c.polygon, wide, box)), class: 'sp-road' + (c.street === 'prairie' ? ' prairie' : '') })));
    const focus = new Set(opts.focus || []);
    plan.parcels.forEach(p => {
      const ids = p.building_ids, n = counts.get(p.id) || 0;
      const poly = svg('polygon', { points: pts(project(p.polygon, wide, box)), class: 'sp-parcel' + (ids.length ? ' has-building' : '') + (n ? ' has-images' : '') + (ids.some(b => focus.has(b)) || focus.has(p.id) ? ' focus' : '') + (selectedParcel === p.id ? ' selected' : '') });
      // Log-scaled: Glessner alone has ~150 records and would wash every other lot out.
      if (n) poly.style.setProperty('--heat', (0.22 + 0.78 * Math.log1p(n) / Math.log1p(max)).toFixed(2));
      const label = (p.addresses[0] || '').replace(/\s.*$/, '');
      const title = svg('title'); title.textContent = (label ? label + ' Prairie' : 'Unnumbered lot') + (ids.length ? ' — ' + ids.map(b => buildingsById.get(b)?.name || b).join('; ') : '') + (n ? ' · ' + n + ' image' + (n === 1 ? '' : 's') : '');
      poly.append(title);
      if (!opts.mini && (ids.length || array(imgs.by_parcel?.[p.id]).length)) {
        poly.setAttribute('tabindex', '0'); poly.setAttribute('role', 'button');
        const act = () => pickLot(p.id);
        poly.addEventListener('click', act); poly.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); act(); } });
      }
      s.append(poly);
      if (!opts.mini && label) {
        const [cx, cy] = centroid(project(p.polygon, wide, box));
        const t = svg('text', { x: cx.toFixed(1), y: cy.toFixed(1), class: 'sp-num' + (n ? ' on' : ''), transform: wide ? `rotate(-90 ${cx.toFixed(1)} ${cy.toFixed(1)})` : '' }); t.textContent = label; s.append(t);
      }
    });
    if (!opts.mini) {
      // Street names, at the middle of each street's longest carriageway run.
      const seen = new Set();
      plan.carriageways.forEach(c => {
        if (seen.has(c.street)) return; seen.add(c.street);
        const pr = project(c.polygon, wide, box), [cx, cy] = centroid(pr);
        const xs = pr.map(q => q[0]), ys = pr.map(q => q[1]), horiz = (Math.max(...xs) - Math.min(...xs)) > (Math.max(...ys) - Math.min(...ys));
        const t = svg('text', { x: cx.toFixed(1), y: cy.toFixed(1), class: 'sp-street', transform: horiz ? '' : `rotate(-90 ${cx.toFixed(1)} ${cy.toFixed(1)})` });
        t.textContent = plan.streets[c.street]?.label || c.street; s.append(t);
      });
      const n = svg('g', { class: 'sp-north', transform: `translate(${wide ? 22 : W - 22} 22)` });
      n.append(svg('path', { d: wide ? 'M-8 0 L8 -6 L8 6 Z' : 'M0 -10 L6 8 L-6 8 Z' }));
      const nt = svg('text', { x: wide ? 18 : 0, y: wide ? 3.5 : 22 }); nt.textContent = 'N'; n.append(nt);
      s.append(n);
    }
    wrap.append(s);
    return wrap;
  }
  function renderMap(list) {
    const wrap = node('div', null, 'map-view');
    const legend = node('p', 'Shaded lots have images in the current filter — darker means more (log scale). Pick a lot to see its pictures. Lots are the Sanborn 1911 parcels, matched to buildings by house number; a lot is a locator, not a 1904 footprint.', 'meta');
    wrap.append(legend, siteMap(list));
    const placed = new Set(Object.keys(plan.placed || {}));
    const off = array(lib.buildings).filter(b => !placed.has(b.id));
    const offList = node('div', null, 'off-plan');
    offList.append(node('p', 'Off this plan (adjacent streets):', 'help-head'));
    off.forEach(b => { const n = list.filter(r => r.building_ids.includes(b.id)).length; const c = node('button', (b.address || b.id) + ' · ' + (b.name || '') + (n ? ' · ' + n : ''), 'chip'); c.type = 'button'; c.addEventListener('click', () => pickBuilding(b.id, true)); offList.append(c); });
    const street = list.filter(r => r.streetscape).length;
    const sc = node('button', 'Street & district views · ' + street, 'chip'); sc.type = 'button'; sc.addEventListener('click', () => { $('imageBuilding').value = '_street'; render(); }); offList.append(sc);
    wrap.append(offList);
    const f = filters();
    if (f.building !== 'all') {
      const strip = node('div', null, 'map-strip');
      strip.append(node('h3', f.building === '_street' ? 'Street & district views' : f.building.startsWith('lot:') ? lotName(f.building.slice(4)) : buildingName(f.building)), renderGrid(list));
      if (!list.length) strip.append(node('p', 'No images match the other filters for this selection.', 'empty'));
      wrap.append(strip);
    }
    return wrap;
  }

  function summaryLine(list) {
    const f = filters(), total = array(imgs.images).length;
    const parts = [list.length + ' of ' + total + ' records'];
    const held = list.filter(r => r.local).length; parts.push(held + ' viewable here');
    $('imageCount').textContent = parts.join(' · ');
    const chips = $('imageActive'); chips.replaceChildren();
    const clear = (label, fn) => { const c = node('button', label + ' ✕', 'chip'); c.type = 'button'; c.addEventListener('click', () => { fn(); render(); }); chips.append(c); };
    if (f.building !== 'all') clear(f.building === '_street' ? 'Street views' : f.building.startsWith('lot:') ? 'Lot ' + lotLabel(f.building.slice(4)) : shortAddr(f.building), () => { $('imageBuilding').value = 'all'; selectedParcel = null; });
    if (f.kind !== 'all') clear($('imageKind').selectedOptions[0].textContent, () => { $('imageKind').value = 'all'; });
    if (f.period !== 'all') clear($('imagePeriod').selectedOptions[0].textContent, () => { $('imagePeriod').value = 'all'; });
    if (f.rights !== 'all') clear($('imageRights').selectedOptions[0].textContent, () => { $('imageRights').value = 'all'; });
    if (f.term) clear('“' + f.term + '”', () => { $('imageSearch').value = ''; });
  }
  function render() {
    if (!ready) return;
    current = filtered(); summaryLine(current);
    document.querySelectorAll('[data-image-view]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.imageView === view)));
    const host = $('imageViews'); host.replaceChildren();
    if (view === 'map') host.append(renderMap(current));
    else if (!current.length) host.append(node('p', array(imgs.images).length ? 'No images match these filters.' : 'The image collection is being gathered; none are indexed yet.', 'empty'));
    else host.append(view === 'list' ? renderList(current) : renderGrid(current));
    writeState();
  }

  // ---- detail --------------------------------------------------------------------------
  function openDetail(i) {
    openIndex = i; const r = current[i]; if (!r) return;
    const d = $('imageDialog'), body = $('imageDialogBody'); body.replaceChildren();
    const fig = node('figure', null, 'img-figure'), full = fullOf(r);
    const remote = !full && remoteFullOf(r);
    if (full) { const a = node('a'); a.href = full; a.target = '_blank'; a.rel = 'noopener'; const img = node('img'); img.alt = r.title || ''; const urls = candidates(r, 'full', 1600); loadChain(img, urls); img.addEventListener('load', () => { a.href = img.currentSrc || img.src; }); a.append(img); fig.append(a); }
    else if (remote) {
      const a = node('a'); a.href = remoteURL(r.image_url) || remote; a.target = '_blank'; a.rel = 'noopener noreferrer'; const img = remoteImg(remote, r); img.loading = 'eager';
      img.addEventListener('error', () => a.replaceWith(thumbBox(Object.assign({}, r, { image_url: null }), 'img-thumb big')));
      a.append(img); fig.append(a, node('p', 'Shown from ' + (r.repository || 'its holder') + ' — not copied here. ' + (RIGHTS_LABEL[r.rights] || r.rights) + '.', 'meta remote-note'));
    }
    else { const ph = thumbBox(r, 'img-thumb big'); fig.append(ph); }
    const cap = node('figcaption'); cap.append(node('p', [r.kind, dateText(r), r.creator].filter(Boolean).join(' · '), 'kicker'), node('h2', r.title || r.id)); fig.append(cap);
    const info = node('div', null, 'img-info');
    const dl = node('dl');
    for (const [k, v] of [['View', [r.view, r.facing && 'facing ' + r.facing].filter(Boolean).join(', ')], ['Camera', r.camera_position], ['Date', dateText(r) + (r.period ? ' — ' + (PERIOD_LABEL[r.period] || r.period) : '')], ['Made by', r.creator], ['Holder', [r.repository, r.collection].filter(Boolean).join(' · ')], ['Call no.', r.call_number], ['Rights', (RIGHTS_LABEL[r.rights] || r.rights) + (r.rights_basis ? ' — ' + r.rights_basis : '')], ['Checked', r.verified === 'viewed' ? 'Image or full record seen' : 'Catalogue listing only'], ['Record', r.id]]) if (v) dl.append(node('dt', k), node('dd', v));
    info.append(dl);
    if (r.notes) info.append(node('p', r.notes));
    if (array(r.measurements).length) {
      info.append(node('h3', 'Measurements stated'));
      const ul = node('ul'); r.measurements.forEach(m => ul.append(node('li', [m.what, m.value, m.locator && '(' + m.locator + ')'].filter(Boolean).join(' — ')))); info.append(ul);
    }
    const links = node('div', null, 'links');
    [['Catalogue record ↗', r.catalog_url], ['Original image ↗', r.image_url]].forEach(([t, u]) => { const a = extLink(t, u); if (a) links.append(a); });
    if (full) { const a = node('a', 'Copy held here ↗'); a.href = full; a.target = '_blank'; links.append(a); }
    const share = node('button', 'Copy link to this image', 'text-button'); share.type = 'button';
    share.addEventListener('click', () => { const u = new URL(location.href); u.hash = 'image=' + encodeURIComponent(r.id); navigator.clipboard?.writeText(u.href).then(() => { share.textContent = 'Link copied'; }, () => { share.textContent = u.href; }); });
    links.append(share); info.append(links);
    if (r.building_ids.length) {
      info.append(node('h3', 'Shows'));
      const ul = node('ul', null, 'img-shows');
      r.building_ids.forEach(id => {
        const li = node('li'), n = forBuilding(id).length;
        const a = node('button', buildingName(id), 'text-button'); a.type = 'button'; a.addEventListener('click', () => { d.close(); window.dispatchEvent(new CustomEvent('prairie:open-building', { detail: id })); });
        const all = node('button', 'All ' + n + ' image' + (n === 1 ? '' : 's'), 'chip'); all.type = 'button'; all.addEventListener('click', () => { d.close(); pickBuilding(id, true); });
        li.append(a, ' ', all); ul.append(li);
      });
      info.append(ul);
      const related = [...new Set(r.building_ids.flatMap(id => forBuilding(id)))].filter(x => x.id !== r.id).slice(0, 12);
      if (related.length) {
        info.append(node('h3', 'More of the same buildings'));
        const strip = node('div', null, 'img-related');
        related.forEach(x => { const b = node('button', null, 'img-open small'); b.type = 'button'; b.title = x.title; b.append(thumbBox(x, 'img-thumb small')); b.addEventListener('click', () => { let j = current.findIndex(c => c.id === x.id); if (j < 0) { current = [x, ...current]; j = 0; } openDetail(j); }); strip.append(b); });
        info.append(strip);
      }
    }
    if (array(r.parcel_ids).length) {
      if (!r.building_ids.length) {
        info.append(node('h3', 'Lot'));
        const wrap = node('div', null, 'img-chips');
        r.parcel_ids.forEach(pid => { const c = node('button', lotName(pid) + ' · ' + array(imgs.by_parcel?.[pid]).length, 'chip'); c.type = 'button'; c.addEventListener('click', () => { d.close(); pickLot(pid, true); }); wrap.append(c); });
        info.append(wrap);
      }
      info.append(node('h3', 'Where on the street'), siteMap([], { mini: true, focus: [...r.building_ids, ...r.parcel_ids] }));
    }
    body.append(fig, info);
    $('imagePrev').disabled = i <= 0; $('imageNext').disabled = i >= current.length - 1;
    $('imagePos').textContent = (i + 1) + ' of ' + current.length;
    if (!d.open) d.showModal();
    writeState(r.id);
  }
  function pickLot(pid, scroll) {
    $('imageBuilding').value = 'lot:' + pid; selectedParcel = pid; render();
    if (scroll) $('images').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function pickBuilding(id, scroll) {
    $('imageBuilding').value = id; selectedParcel = plan.placed?.[id]?.parcels?.[0] || null; render();
    if (scroll) $('images').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ---- state in the URL: #images?view=map&b=pa-1729-5, #image=<id> ----------------------
  let restoring = false;
  function writeState(imageId) {
    if (restoring) return;
    const f = filters(), q = new URLSearchParams();
    if (view !== 'grid') q.set('view', view);
    if (f.building !== 'all') q.set('b', f.building);
    if (f.kind !== 'all') q.set('kind', f.kind);
    if (f.period !== 'all') q.set('period', f.period);
    if (f.rights !== 'all') q.set('rights', f.rights);
    if (f.term) q.set('q', f.term);
    const hash = imageId ? 'image=' + encodeURIComponent(imageId) : (q.toString() ? 'images?' + q : null);
    if (hash) history.replaceState(null, '', '#' + hash);
    else if (/^#(image=|images\?)/.test(location.hash)) history.replaceState(null, '', '#images');
  }
  function readState() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (h.startsWith('image=')) { const id = h.slice(6); return { image: id }; }
    if (h.startsWith('images?')) return { q: new URLSearchParams(h.slice(7)) };
    return null;
  }
  function applyState(st) {
    if (!st) return false;
    restoring = true;
    if (st.q) {
      view = ['grid', 'list', 'map'].includes(st.q.get('view')) ? st.q.get('view') : 'grid';
      const set = (id, v) => { if (v && [...$(id).options].some(o => o.value === v)) $(id).value = v; };
      set('imageBuilding', st.q.get('b')); set('imageKind', st.q.get('kind')); set('imagePeriod', st.q.get('period')); set('imageRights', st.q.get('rights'));
      $('imageSearch').value = st.q.get('q') || '';
    }
    render(); restoring = false;
    if (st.image && byId.has(st.image)) {
      let j = current.findIndex(r => r.id === st.image);
      if (j < 0) { ['imageBuilding', 'imageKind', 'imagePeriod', 'imageRights'].forEach(id => { $(id).value = 'all'; }); $('imageSearch').value = ''; render(); j = current.findIndex(r => r.id === st.image); }
      if (j >= 0) openDetail(j);
    }
    $('images').scrollIntoView({ behavior: 'instant', block: 'start' });
    return true;
  }

  function options(sel, values, label = v => v) { values.forEach(v => { const o = node('option', label(v)); o.value = v; sel.append(o); }); }
  async function attach(library) {
    lib = library; buildingsById = new Map(array(lib.buildings).map(b => [b.id, b]));
    await loaded; if (!imgs || !plan) return;
    const withImages = array(lib.buildings).filter(b => forBuilding(b.id).length);
    const bsel = $('imageBuilding');
    const gStreet = node('option', 'Street & district views'); gStreet.value = '_street'; bsel.append(gStreet);
    const gB = node('optgroup'); gB.label = 'Buildings'; options(gB, withImages.map(b => b.id), id => buildingName(id) + ' (' + forBuilding(id).length + ')'); bsel.append(gB);
    // Every traced lot with a record, along the street — including lots the library has no
    // building record for yet, whose pictures were placed by address.
    const gL = node('optgroup'); gL.label = 'Lots along the street (1911 numbers)';
    options(gL, array(plan.parcels).filter(p => array(imgs.by_parcel?.[p.id]).length).map(p => 'lot:' + p.id), v => lotName(v.slice(4)) + ' (' + imgs.by_parcel[v.slice(4)].length + ')'); bsel.append(gL);
    const kinds = [...new Set(array(imgs.images).map(r => r.kind))].sort();
    const drawn = node('option', 'All drawings, plans & maps'); drawn.value = '_drawn'; $('imageKind').append(drawn);
    options($('imageKind'), kinds, k => k[0].toUpperCase() + k.slice(1));
    ['imageSearch'].forEach(id => $(id).addEventListener('input', () => { selectedParcel = null; render(); }));
    ['imageBuilding', 'imageKind', 'imagePeriod', 'imageRights', 'imageSort'].forEach(id => $(id).addEventListener('change', () => { if (id === 'imageBuilding') { const v = $(id).value; selectedParcel = v.startsWith('lot:') ? v.slice(4) : plan.placed?.[v]?.parcels?.[0] || null; } render(); }));
    document.querySelectorAll('[data-image-view]').forEach(b => b.addEventListener('click', () => { view = b.dataset.imageView; render(); }));
    $('year').addEventListener('input', () => { if ($('imagePeriod').value === 'by-year') render(); });
    const d = $('imageDialog');
    $('imagePrev').addEventListener('click', () => openDetail(openIndex - 1));
    $('imageNext').addEventListener('click', () => openDetail(openIndex + 1));
    $('imageClose').addEventListener('click', () => d.close());
    d.addEventListener('close', () => writeState());
    d.addEventListener('click', e => { if (e.target === d) d.close(); });
    d.addEventListener('keydown', e => { if (e.key === 'ArrowLeft' && openIndex > 0) openDetail(openIndex - 1); if (e.key === 'ArrowRight' && openIndex < current.length - 1) openDetail(openIndex + 1); });
    let lastWide = null; addEventListener('resize', () => { const w = $('imageViews').clientWidth >= 700; if (view === 'map' && w !== lastWide) { lastWide = w; render(); } });
    ready = true;
    const c = imgs.counts || {};
    $('imageStatus').textContent = (c.images || 0) + ' records across ' + (c.buildings_with_images || 0) + ' of ' + (c.buildings || 0) + ' buildings · ' + (c.in_period || 0) + ' made by 1911 · ' + (c.local || 0) + ' held here';
    if (!applyState(readState())) render();
    addEventListener('hashchange', () => { const st = readState(); if (st) applyState(st); });
    window.dispatchEvent(new CustomEvent('prairie:images-ready'));
  }

  // A building card's strip: a few thumbnails and the way into the full set.
  function decorate(container, id, summaryEl) {
    if (!ready) return;
    const list = forBuilding(id); if (!list.length) return;
    const lead = leadImage(id);
    if (lead && summaryEl) { const t = node('img', null, 'card-lead'); t.src = thumbOf(lead) || remoteThumbOf(lead); t.referrerPolicy = 'no-referrer'; t.alt = ''; t.loading = 'lazy'; t.addEventListener('error', () => t.remove()); summaryEl.prepend(t); }
    if (summaryEl) summaryEl.append(node('span', list.length + ' image' + (list.length === 1 ? '' : 's'), 'badge img-count'));
    const strip = node('div', null, 'card-strip');
    list.slice(0, 8).forEach(r => { const b = node('button', null, 'img-open small'); b.type = 'button'; b.title = r.title; b.append(thumbBox(r, 'img-thumb small')); b.addEventListener('click', () => { pickBuilding(id); const j = current.findIndex(c => c.id === r.id); openDetail(j); }); strip.append(b); });
    const actions = node('div', null, 'links');
    const all = node('button', 'See all ' + list.length + ' in Images', 'chip'); all.type = 'button'; all.addEventListener('click', () => { view = view === 'map' ? 'grid' : view; pickBuilding(id, true); });
    actions.append(all);
    if (plan.placed?.[id]) { const m = node('button', 'Show on the site plan', 'chip'); m.type = 'button'; m.addEventListener('click', () => { view = 'map'; pickBuilding(id, true); }); actions.append(m); }
    container.append(node('h3', 'Images'), strip, actions);
  }
  return { attach, decorate, forBuilding, all: () => array(imgs?.images) };
})();
