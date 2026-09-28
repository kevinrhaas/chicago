'use strict';
(() => {
  const $ = id => document.getElementById(id);
  // Atlas navigation leaves the 4D preview; resource paths remain package-relative.
  if (location.pathname.includes('/4d/dev/')) document.querySelectorAll('a[href="../../"], a[href="../../rebuilding-1870s/viewer/"]').forEach(a => a.setAttribute('href', '../../' + a.getAttribute('href')));
  const node = (tag, text, cls) => { const el = document.createElement(tag); if (text !== undefined && text !== null) el.textContent = String(text); if (cls) el.className = cls; return el; };
  const plain = value => value == null ? '' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const array = value => Array.isArray(value) ? value : [];
  const yearNumber = value => value !== null && value !== undefined && /^\d{4}$/.test(String(value)) ? Number(value) : null;
  function safeURL(value, local = false) {
    if (!value || typeof value !== 'string') return null;
    if (local && (/^[a-z]+:/i.test(value) || value.startsWith('/') || value.split('/').includes('..'))) return null;
    try { const url = new URL(local ? '../' + value : value, location.href); return /^https?:$/.test(url.protocol) ? url.href : null; } catch { return null; }
  }
  function link(text, value, local = false) { const url = safeURL(value, local); if (!url) return node('span', text); const a = node('a', text); a.href = url; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
  // Notes (/notes/notes.js) file against these keys; a key must not change when a
  // record's wording does, so each is the record's own id where it has one.
  const noteKey = (el, key, label) => { el.dataset.note = String(key).slice(0, 300); el.dataset.noteLabel = String(label || key).slice(0, 300); return el; };
  let data, sourcesById;
  function citations(ids) {
    const el = node('div', null, 'citations');
    for (const id of array(ids)) {
      const source = sourcesById.get(id);
      if (!source) { el.append(node('span', 'Unresolved source: ' + id)); continue; }
      const a = node('a', source.title || id); a.href = '#source-' + encodeURIComponent(id);
      a.addEventListener('click', () => { $('sourceSearch').value = ''; $('sourceKind').value = 'all'; renderSources(); });
      el.append(a);
    }
    if (!el.childNodes.length) el.append(node('span', 'No source linked to this record.'));
    return el;
  }
  // A record leaves the list only when its own recorded dates or 1904 status rule it out.
  // "Demolished before 1904" holds for every later year too; "absent from this site in
  // 1904" says nothing about other years, so it applies to 1904 alone.
  const GONE_BY_1904 = /^(demolished|replaced|destroyed|burned|burnt)(?:$|[\s_—:;-])/;
  const ABSENT_1904 = /^(absent|excluded|not (present|built|standing))(?:$|[\s_—:;-])/;
  function temporal(building, year) {
    const status1904 = plain(building.status_1904).toLowerCase();
    if (year >= 1904 && GONE_BY_1904.test(status1904)) return { kind: 'outside', reason: 'gone', label: 'Gone before 1904 · recorded status' };
    if (year === 1904 && (building.excluded_1904 === true || ABSENT_1904.test(status1904))) return { kind: 'outside', reason: 'gone', label: 'Excluded from 1904 · recorded status' };
    const built = yearNumber(building.built_year), demolished = yearNumber(building.demolished_year);
    if (built !== null && built > year) return { kind: 'outside', reason: 'unbuilt', label: 'Not yet built by recorded date' };
    if (demolished !== null && demolished <= year) return { kind: 'outside', reason: 'demolished', label: demolished === year ? 'Demolition year — exact date needed' : 'Demolished by recorded date' };
    if (built !== null && demolished !== null) return { kind: 'bounded', label: 'Within recorded date bounds' };
    return { kind: 'uncertain', label: 'Compatible year · incomplete date bounds' };
  }
  const REASONS = { unbuilt: 'not yet built', demolished: 'already demolished', gone: 'recorded as gone by 1904' };
  function explainCount(year, filter) {
    const all = array(data.buildings), total = all.length;
    const outside = all.map(b => ({ b, t: temporal(b, year) })).filter(r => r.t.kind === 'outside');
    const byReason = {}; outside.forEach(r => { byReason[r.t.reason] = (byReason[r.t.reason] || 0) + 1; });
    const parts = Object.keys(REASONS).filter(k => byReason[k]).map(k => byReason[k] + ' ' + REASONS[k]);
    const note = $('countNote'), show = $('showHidden');
    show.hidden = true;
    if (!outside.length) note.textContent = 'All ' + total + ' researched buildings fall within ' + year + '.';
    else if (filter === 'all') note.textContent = 'Showing all ' + total + ', including ' + outside.length + ' outside ' + year + ' (' + parts.join(', ') + ') — marked on each card.';
    else if (filter === 'compatible') { note.textContent = outside.length + ' not shown for ' + year + (parts.length === 1 ? ' — ' + (outside.length === 1 ? '' : outside.length === 2 ? 'both ' : 'all ') + REASONS[outside[0].t.reason] : ': ' + parts.join(', ')) + '.'; show.hidden = false; }
    else note.textContent = outside.length + ' fall outside ' + year + ' (' + parts.join(', ') + ').';
    const help = $('countHelp'); help.replaceChildren();
    const frontages = frontageRecords().length, leads = array(data.occupancy_candidates).length;
    const undated = all.filter(b => yearNumber(b.built_year) === null).length;
    const min = Number($('year').min), atMin = all.filter(b => temporal(b, min).kind !== 'outside').length;
    help.append(
      node('p', total + ' is the number of named buildings and building histories researched so far — not a count of every structure that stood on the street. The 1911 Sanborn sheets show ' + frontages + ' mapped frontages, and the directories give ' + leads + ' name-and-address leads; each is a separate evidence layer below.'),
      node('p', 'The year slider hides a record only when its recorded dates rule it out: built later, demolished by then, or recorded as gone by 1904. Nothing is hidden by guesswork.'),
      node('p', undated + ' records have no recorded construction year, so they stay in view in every year, marked “incomplete date bounds”. That is why ' + min + ' already shows ' + atMin + ' rather than a handful. Some losses are dated only loosely (“circa 1882”, “1880s”); those houses stay in view until 1904, when their recorded status rules them out.'));
    if (outside.length) {
      help.append(node('p', 'Outside ' + year + ':', 'help-head'));
      const ul = node('ul'); outside.forEach(r => ul.append(node('li', (r.b.name || r.b.id) + ' — ' + (r.b.address || 'address unresolved') + ' · ' + r.t.label))); help.append(ul);
    }
    help.append(node('p', 'Date bounds use recorded construction and demolition years, not a verified annual occupancy census. Open a record for its evidence and unresolved details.', 'meta'));
  }
  function renderBuildings() {
    const year = Number($('year').value), term = $('buildingSearch').value.trim().toLowerCase(), filter = $('yearFilter').value;
    $('yearOutput').value = year; $('yearHint').textContent = year === 1904 ? 'target' : year === 1911 ? 'map ref.' : '';
    document.querySelectorAll('[data-year]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.year) === year)));
    const buildings = array(data.buildings).filter(b => {
      const state = temporal(b, year).kind;
      return (filter === 'all' || (filter === 'compatible' ? state !== 'outside' : state === filter)) && (!term || [b.name,b.address,b.architect,b.notes,b.id].map(plain).join(' ').toLowerCase().includes(term));
    });
    $('buildingCount').textContent = buildings.length + ' of ' + array(data.buildings).length + ' records · ' + year;
    explainCount(year, filter);
    const list = $('buildingList'); list.replaceChildren();
    for (const b of buildings) {
      const detail = node('details', null, 'record'), summary = node('summary'), content = node('div', null, 'record-content');
      summary.append(node('h3', b.name || b.id), node('span', b.address || 'Address unresolved', 'address'), node('span', temporal(b, year).label, 'badge'));
      const facts = node('dl');
      for (const [label,value] of [['Built',b.construction || b.built_year],['Demolished',b.demolition || b.demolished_year],['Architect',b.architect],['1904 status',b.status_1904]]) facts.append(node('dt', label), node('dd', plain(value) || 'Not established'));
      content.append(facts);
      if (b.notes) content.append(node('p', plain(b.notes)));
      if (array(b.events).length) {
        content.append(node('h3', 'Recorded history')); const events = node('ul');
        b.events.forEach(e => { const item = node('li', typeof e === 'string' ? e : [e.year || e.date || e.date_text,e.type || e.title,e.text || e.description || e.notes].filter(Boolean).map(plain).join(' · ')); if (array(e.source_ids).length) item.append(citations(e.source_ids)); events.append(item); });
        content.append(events);
      }
      content.append(citations(b.source_ids)); detail.append(summary,content); noteKey(detail, 'building:' + b.id, b.name || b.id); list.append(detail);
    }
    if (!buildings.length) list.append(node('p', 'No matching buildings. Try another search or show all researched buildings.', 'empty'));
  }
  function renderMap() {
    const map = array(data.maps).find(m => String(m.id) === $('mapSelect').value);
    $('mapLinks').replaceChildren(); $('mapImage').hidden = true; $('mapImage').removeAttribute('src'); $('mapError').hidden = true;
    if (!map) { $('mapTitle').textContent = 'No map record available'; delete $('mapTitle').dataset.note; return; }
    $('mapTitle').textContent = map.title || map.id; noteKey($('mapTitle'), 'map:' + map.id, map.title || map.id); $('mapDate').textContent = 'Source date: ' + (map.date || 'unresolved'); $('mapNote').textContent = map.notes || '';
    const url = safeURL(map.local_path, true);
    if (url && /\.(jpe?g|png|webp|gif|avif)(\?.*)?$/i.test(map.local_path)) { $('mapImage').alt = map.title || 'Historical source sheet'; $('mapImage').src = url; $('mapImage').hidden = false; }
    else $('mapError').hidden = false;
    if (url) $('mapLinks').append(link('Open full-resolution file ↗', map.local_path, true));
    if (map.source_id) $('mapLinks').append(citations([map.source_id]));
  }
  function renderSources() {
    const term = $('sourceSearch').value.trim().toLowerCase(), kind = $('sourceKind').value;
    const sources = array(data.sources).filter(s => (kind === 'all' || s.kind === kind) && (!term || [s.id,s.title,s.notes,s.date,s.kind].map(plain).join(' ').toLowerCase().includes(term)));
    $('sourceCount').textContent = sources.length + ' of ' + array(data.sources).length + ' sources';
    const list = $('sourceList'); list.replaceChildren();
    for (const s of sources) {
      const card = node('article', null, 'source-card'); card.id = 'source-' + encodeURIComponent(s.id); noteKey(card, 'source:' + s.id, s.title || s.id);
      const preview = s.preview_path || s.local_path;
      if (preview && /\.(jpe?g|png|webp|gif|avif)$/i.test(preview) && safeURL(preview,true)) { const img = node('img'); img.src = safeURL(preview,true); img.alt = s.title || ''; img.loading = 'lazy'; img.addEventListener('error', () => { img.hidden = true; }); card.append(img); }
      card.append(node('p', s.id, 'source-id'), node('h3', s.title || 'Untitled source'), node('span', [s.kind || 'Reference',s.date].filter(Boolean).join(' · '), 'badge'));
      if (s.notes) card.append(node('p', plain(s.notes)));
      card.append(node('p', 'Retrieval: ' + (s.retrieval_status || 'Not recorded'), 'meta'));
      card.append(node('p', 'Rights: ' + (s.rights_status || 'Not established'), 'meta'));
      const links = node('div', null, 'links'); if (s.url) links.append(link('Source record ↗', s.url)); if (s.local_path) links.append(link('Stored file ↗', s.local_path, true)); card.append(links); list.append(card);
    }
    if (!sources.length) list.append(node('p', 'No sources match these filters.', 'empty'));
  }
  function frontageRecords() { return array(Array.isArray(data.map_inventory) ? data.map_inventory : data.map_inventory?.records); }
  function renderFrontage() {
    const term = $('frontageSearch').value.trim().toLowerCase(), sheet = $('frontageSheet').value;
    const records = frontageRecords().filter(r => (sheet === 'all' || String(r.sheet) === sheet) && (!term || plain(r).toLowerCase().includes(term)));
    $('frontageCount').textContent = records.length + ' of ' + frontageRecords().length + ' frontage observations';
    const list = $('frontageList'); list.replaceChildren();
    records.forEach(r => {
      const card = node('details',null,'record'), summary = node('summary'), content = node('div',null,'record-content');
      summary.append(node('h3',[r.address,r.street || 'Prairie Avenue'].filter(Boolean).join(' ')),node('span','Observed ' + (r.observation_year || '1911') + ' · sheet ' + (r.sheet || 'unresolved') + (r.side ? ' · ' + r.side + ' side' : ''),'address'));
      const facts = node('dl');
      for (const [label,value] of [['Raw notation',r.raw_story_basement_notation],['Material',r.map_material_interpretation],['Use label',r.map_use_label],['Address read',r.address_confidence],['Dimensions (ft)',r.dimensions_ft],['Digitized',r.footprint_digitized === true ? 'Yes' : 'No']]) facts.append(node('dt',label),node('dd',plain(value) || 'Not established'));
      content.append(facts); if (r.notes) content.append(node('p',r.notes));
      content.append(node('p','Source: ' + (r.source_file || 'See source sheet attribution'),'meta'));
      if (r.source_id) content.append(citations([r.source_id]));
      card.append(summary,content); noteKey(card, 'frontage:' + (r.id || [r.sheet,r.address,r.side].join('|')), [r.address,r.street || 'Prairie Avenue'].filter(Boolean).join(' ') + ' · 1911 frontage'); list.append(card);
    });
    if (!records.length) list.append(node('p','No frontage observations match these filters.','empty'));
  }
  function renderDirectory() {
    const all = array(data.occupancy_candidates), term = $('directorySearch').value.trim().toLowerCase(), year = $('directoryYear').value;
    const records = all.filter(r => (year === 'all' || String(r.year_label) === year) && (!term || plain(r).toLowerCase().includes(term)));
    $('directoryCount').textContent = records.length + ' of ' + all.length + ' directory leads';
    const list = $('directoryList'); list.replaceChildren();
    records.forEach(r => {
      const card = node('details',null,'record'), summary = node('summary'), content = node('div',null,'record-content');
      summary.append(node('h3',r.listed_people || 'Name not resolved'),node('span',[r.address,r.street || 'Prairie Avenue'].filter(Boolean).join(' '),'address'),node('span','Directory label: ' + (r.year_label || 'unresolved'),'badge'));
      content.append(node('p',r.verification || 'Verification not recorded'),node('p',r.limits || 'Candidate directory reading; does not establish ownership or complete occupancy.'),node('p','Locator: ' + (r.source_locator || 'Not recorded'),'meta'));
      if (r.source_id) content.append(citations([r.source_id]));
      card.append(summary,content); noteKey(card, 'directory:' + [r.year_label,r.address,r.listed_people].join('|'), (r.listed_people || 'Directory lead') + ' · ' + (r.year_label || '')); list.append(card);
    });
    if (!records.length) list.append(node('p','No directory leads match these filters.','empty'));
  }
  function initEvidenceLayers() {
    for (const sheet of [...new Set(frontageRecords().map(r => String(r.sheet)).filter(v => v !== 'undefined'))].sort()) { const option = node('option','Sheet ' + sheet); option.value = sheet; $('frontageSheet').append(option); }
    for (const year of [...new Set(array(data.occupancy_candidates).map(r => String(r.year_label)).filter(v => v !== 'undefined'))].sort()) { const option = node('option',year); option.value = year; $('directoryYear').append(option); }
    const inventory = data.map_inventory || {};
    $('frontageContext').textContent = inventory.source_attribution || 'Source dates belong to the map observation, not automatically to the 1904 reconstruction.';
    for (const text of [inventory.temporal_rule,inventory.story_notation_rule,...array(inventory.limitations)].filter(Boolean)) $('frontageNotes').append(node('p',plain(text)));
    array(inventory.exceptions_1904).forEach(r => { const item = node('article'); item.append(node('h3',String(r.address) + ' · 1904 lost-building exception'),node('p',r.footprint_observation),node('p',r.certainty),node('p','Source: ' + (r.source_file || 'Unresolved') + ' · identification: ' + (r.identification_source || 'Unresolved'),'meta')); $('frontageNotes').append(item); });
    $('frontageSearch').addEventListener('input',renderFrontage); $('frontageSheet').addEventListener('change',renderFrontage);
    $('directorySearch').addEventListener('input',renderDirectory); $('directoryYear').addEventListener('change',renderDirectory);
    renderFrontage(); renderDirectory();
  }
  function downloadCSV(name, records, fields) {
    const cell = value => '"' + plain(value).replace(/"/g,'""').replace(/^([=+@-])/,'\'$1') + '"';
    const csv = '\uFEFF' + [fields.map(cell).join(','),...records.map(row => fields.map(f => cell(row[f])).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})); const a = node('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  // The sticky bar: anchors land below it, and the link for the section in view is marked.
  function initTopbar() {
    const bar = $('topbar'), root = document.documentElement;
    const measure = () => root.style.setProperty('--bar-h', bar.offsetHeight + 'px');
    measure(); if ('ResizeObserver' in window) new ResizeObserver(measure).observe(bar); else addEventListener('resize', measure);
    const nav = bar.querySelector('.section-links'), links = [...nav.querySelectorAll('a[href^="#"]')];
    const sections = links.map(a => document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
    let current = null;
    const mark = () => {
      const edge = bar.offsetHeight + 24;
      let active = null; for (const section of sections) if (section.getBoundingClientRect().top <= edge) active = section;
      if (innerHeight + scrollY >= root.scrollHeight - 4) active = sections[sections.length - 1];
      if (active === current) return; current = active;
      links.forEach(a => { if (active && a.getAttribute('href') === '#' + active.id) { a.setAttribute('aria-current', 'location'); if (nav.scrollWidth > nav.clientWidth) nav.scrollTo({ left: a.offsetLeft - (nav.clientWidth - a.offsetWidth) / 2, behavior: 'smooth' }); } else a.removeAttribute('aria-current'); });
    };
    let queued = false; addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; mark(); }); } }, { passive: true });
    mark();
  }
  async function init() {
    $('downloadBuildings').disabled = true; $('downloadSources').disabled = true;
    try {
      const response = await fetch('../data/library.json'); if (!response.ok) throw new Error('HTTP ' + response.status); data = await response.json();
      sourcesById = new Map(array(data.sources).map(s => [s.id,s]));
      $('scope').textContent = plain(data.meta?.scope); $('coverageNote').textContent = plain(data.meta?.coverage_note);
      $('year').value = yearNumber(data.meta?.target_year) || 1904;
      for (const kind of [...new Set(array(data.sources).map(s => s.kind).filter(Boolean))].sort()) { const option = node('option',kind); option.value = kind; $('sourceKind').append(option); }
      for (const map of array(data.maps)) { const option = node('option',map.title || map.id); option.value = map.id; $('mapSelect').append(option); }
      $('glessnerSummary').textContent = plain(data.glessner?.summary);
      array(data.glessner?.sections).forEach(section => { const card = noteKey(node('article',null,'glessner-section'), 'glessner:' + section.title, 'Glessner House · ' + section.title); card.append(node('h3',section.title),node('p',plain(section.text)),citations(section.source_ids)); $('glessnerSections').append(card); });
      $('year').addEventListener('input',renderBuildings); $('buildingSearch').addEventListener('input',renderBuildings); $('yearFilter').addEventListener('change',renderBuildings);
      document.querySelectorAll('[data-year]').forEach(button => button.addEventListener('click', () => { $('year').value = button.dataset.year; renderBuildings(); }));
      $('showHidden').addEventListener('click', () => { $('yearFilter').value = 'all'; renderBuildings(); });
      $('sourceSearch').addEventListener('input',renderSources); $('sourceKind').addEventListener('change',renderSources); $('mapSelect').addEventListener('change',renderMap);
      $('mapImage').addEventListener('error', () => { $('mapImage').hidden = true; $('mapError').hidden = false; });
      $('downloadBuildings').disabled = false; $('downloadSources').disabled = false;
      $('downloadBuildings').addEventListener('click',() => downloadCSV('prairie-avenue-buildings.csv',array(data.buildings),['id','name','address','architect','built_year','demolished_year','status_1904','notes','source_ids','events']));
      $('downloadSources').addEventListener('click',() => downloadCSV('prairie-avenue-sources.csv',array(data.sources),['id','title','url','kind','date','notes','local_path','rights_status']));
      initEvidenceLayers(); renderBuildings(); renderMap(); renderSources(); $('loadStatus').textContent = array(data.buildings).length + ' building records · ' + array(data.sources).length + ' sources · ' + array(data.maps).length + ' maps & images';
      // A deep link (#maps, #source-…) was resolved before the content existed; land it now.
      const target = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) requestAnimationFrame(() => target.scrollIntoView({ behavior: 'instant', block: 'start' }));
    } catch (error) { $('loadStatus').textContent = 'The collection could not be loaded. Reload this page or open the Research JSON link below. ' + error.message; }
  }
  initTopbar();
  init();
})();
