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
  function temporal(building, year) {
    const status1904 = plain(building.status_1904).toLowerCase();
    if (year === 1904 && (building.excluded_1904 === true || /^(absent|excluded|not (present|built|standing)|demolished|replaced|destroyed|burned|burnt)(?:$|[\s_—:;-])/.test(status1904))) return { kind: 'outside', label: 'Excluded from 1904 · recorded status' };
    const built = yearNumber(building.built_year), demolished = yearNumber(building.demolished_year);
    if (built !== null && built > year) return { kind: 'outside', label: 'Not yet built by recorded date' };
    if (demolished !== null && demolished <= year) return { kind: 'outside', label: demolished === year ? 'Demolition year — exact date needed' : 'Demolished by recorded date' };
    if (built !== null && demolished !== null) return { kind: 'bounded', label: 'Within recorded date bounds' };
    return { kind: 'uncertain', label: 'Compatible year · incomplete date bounds' };
  }
  function renderBuildings() {
    const year = Number($('year').value), term = $('buildingSearch').value.trim().toLowerCase(), filter = $('yearFilter').value;
    $('yearOutput').value = year;
    document.querySelectorAll('[data-year]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.year) === year)));
    const buildings = array(data.buildings).filter(b => {
      const state = temporal(b, year).kind;
      return (filter === 'all' || (filter === 'compatible' ? state !== 'outside' : state === filter)) && (!term || [b.name,b.address,b.architect,b.notes,b.id].map(plain).join(' ').toLowerCase().includes(term));
    });
    $('buildingCount').textContent = buildings.length + ' of ' + array(data.buildings).length + ' records · ' + year;
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
      content.append(citations(b.source_ids)); detail.append(summary,content); list.append(detail);
    }
    if (!buildings.length) list.append(node('p', 'No matching buildings. Try another search or show all researched buildings.', 'empty'));
  }
  function renderMap() {
    const map = array(data.maps).find(m => String(m.id) === $('mapSelect').value);
    $('mapLinks').replaceChildren(); $('mapImage').hidden = true; $('mapImage').removeAttribute('src'); $('mapError').hidden = true;
    if (!map) { $('mapTitle').textContent = 'No map record available'; return; }
    $('mapTitle').textContent = map.title || map.id; $('mapDate').textContent = 'Source date: ' + (map.date || 'unresolved'); $('mapNote').textContent = map.notes || '';
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
      const card = node('article', null, 'source-card'); card.id = 'source-' + encodeURIComponent(s.id);
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
      card.append(summary,content); list.append(card);
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
      card.append(summary,content); list.append(card);
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
      array(data.glessner?.sections).forEach(section => { const card = node('article',null,'glessner-section'); card.append(node('h3',section.title),node('p',plain(section.text)),citations(section.source_ids)); $('glessnerSections').append(card); });
      $('year').addEventListener('input',renderBuildings); $('buildingSearch').addEventListener('input',renderBuildings); $('yearFilter').addEventListener('change',renderBuildings);
      document.querySelectorAll('[data-year]').forEach(button => button.addEventListener('click', () => { $('year').value = button.dataset.year; renderBuildings(); }));
      $('sourceSearch').addEventListener('input',renderSources); $('sourceKind').addEventListener('change',renderSources); $('mapSelect').addEventListener('change',renderMap);
      $('mapImage').addEventListener('error', () => { $('mapImage').hidden = true; $('mapError').hidden = false; });
      $('downloadBuildings').disabled = false; $('downloadSources').disabled = false;
      $('downloadBuildings').addEventListener('click',() => downloadCSV('prairie-avenue-buildings.csv',array(data.buildings),['id','name','address','architect','built_year','demolished_year','status_1904','notes','source_ids','events']));
      $('downloadSources').addEventListener('click',() => downloadCSV('prairie-avenue-sources.csv',array(data.sources),['id','title','url','kind','date','notes','local_path','rights_status']));
      renderBuildings(); renderMap(); renderSources(); initEvidenceLayers(); $('loadStatus').textContent = array(data.buildings).length + ' building records · ' + array(data.sources).length + ' sources · ' + array(data.maps).length + ' map references';
    } catch (error) { $('loadStatus').textContent = 'The collection could not be loaded. Reload this page or open the Research JSON link below. ' + error.message; }
  }
  init();
})();
