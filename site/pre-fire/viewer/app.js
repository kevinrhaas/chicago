let model;
const $ = (id) => document.getElementById(id);
const cleanYear = (value) => { const m = String(value || '').match(/\d{4}/); return m ? Number(m[0]) : null; };

function activeInYear(row, year) {
  const built = cleanYear(row.year_completed) ?? cleanYear(row.year_started);
  const gone = cleanYear(row.year_demolished);
  return built !== null && built <= year && (gone === null || gone >= year);
}

function closestMap(year) {
  return [...model.maps].sort((a,b) => {
    const da = Math.abs(Number(a.reference_year)-year), db = Math.abs(Number(b.reference_year)-year);
    return da-db || Number(b.reference_year)-Number(a.reference_year);
  })[0];
}

function currentEvent(events, year) {
  const eligible = events.filter(e => (cleanYear(e.effective_start) ?? -Infinity) <= year && (cleanYear(e.effective_end) ?? Infinity) >= year);
  return eligible.sort((a,b) => (cleanYear(b.effective_start) ?? 0)-(cleanYear(a.effective_start) ?? 0))[0];
}

function knownStart(row) {
  return cleanYear(row.year_completed) ?? cleanYear(row.year_started);
}

function alternateNames(row) {
  return (model.namesByBuilding[row.building_id] || [])
    .filter(name => name.name_type !== 'canonical' && name.name !== row.canonical_name)
    .map(name => name.name);
}

function searchableText(row) {
  return [
    row.canonical_name,
    ...alternateNames(row),
    ...mediaForBuilding(row).flatMap(media => [media.title, media.creator, media.repository]),
    row.address_historical,
    row.building_type,
    row.year_started,
    row.year_completed,
    row.year_demolished,
  ].join(' ').toLowerCase();
}

function mediaForBuilding(row) {
  return model.mediaByBuilding[row.building_id] || [];
}

function mediaMarkup(row) {
  const media = mediaForBuilding(row);
  if (!media.length) return '<span class="no-media">—</span>';
  return `<div class="building-media-gallery">${media.map(item => {
    const representation = (item.representation_type || 'historical image').replaceAll('_',' ');
    const caution = item.accuracy_note ? `<span class="image-caution">${escapeHtml(item.accuracy_note)}</span>` : '';
    return `<figure class="building-media"><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer"><img src="../${escapeHtml(item.local_path)}" alt="${escapeHtml(item.title)}" loading="lazy"></a><figcaption><a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a><span>${escapeHtml(item.depicted_year || 'date unknown')} · ${escapeHtml(representation)}</span>${caution}</figcaption></figure>`;
  }).join('')}</div>`;
}

function knownSpan(row) {
  const start = row.year_completed || row.year_started || '—';
  const end = row.year_demolished || 'unknown';
  return `${start}–${end}`;
}

function render() {
  const year = Number($('year').value);
  $('yearOutput').value = year;
  $('yearOutput').textContent = year;
  $('yearNumber').value = year;
  const nearest = closestMap(year);
  const variants = model.maps.filter(m => m.reference_year === nearest.reference_year);
  const variant = $('mapVariant');
  const prior = variant.value;
  variant.innerHTML = variants.map(m => `<option value="${escapeHtml(m.map_id)}">${escapeHtml(m.title)}</option>`).join('');
  variant.value = variants.some(m => m.map_id === prior) ? prior : variants[0].map_id;
  const map = variants.find(m => m.map_id === variant.value) || nearest;
  $('mapTitle').textContent = map.title; $('mapYear').textContent = `shows ${map.reference_year}`;
  $('mapImage').src = `../${map.local_image_path.replace('maps/','maps/')}`;
  $('mapImage').alt = `${map.title}, reference year ${map.reference_year}`;
  $('mapLink').href = map.source_url;
  $('mapMeta').textContent = `${map.map_type.replaceAll('_',' ')} · created ${map.map_date} · ${map.credit_line} · ${map.rights_statement.replaceAll('_',' ')}`;
  $('mapNote').textContent = map.notes;

  const extent = currentEvent(model.cityExtentEvents, year);
  $('extentName').textContent = extent?.name || 'No dated city extent';
  $('extentNote').textContent = extent ? `${extent.legal_or_source_description}. Geometry: ${extent.geometry_status.replaceAll('_',' ')}.` : 'Chicago was not yet incorporated; consult the period map and landscape event.';
  const land = currentEvent(model.landformEvents, year);
  $('landName').textContent = land?.feature || 'No dated landscape event';
  $('landNote').textContent = land?.description || 'No specific event is currently cataloged for this year.';

  const rawQuery = $('search').value.trim();
  const query = rawQuery.toLowerCase();
  const activeRows = model.buildings.filter(r => activeInYear(r, year));
  $('activeCount').textContent = activeRows.length.toLocaleString();
  let rows = activeRows;
  if (query) {
    rows = model.buildings.filter(r => searchableText(r).includes(query));
    $('recordsHeading').textContent = 'All-year search results';
    $('recordsStatus').textContent = `${rows.length.toLocaleString()} records match “${rawQuery}” across the full index. Choose a timeline year to view a building in context.`;
  } else {
    $('recordsHeading').textContent = 'Known active records';
    $('recordsStatus').textContent = `${rows.length.toLocaleString()} records are active in ${year}. Search covers the complete 1674–1871 index, not only this year.`;
  }
  rows.sort((a,b) => a.canonical_name.localeCompare(b.canonical_name));
  $('imageCount').textContent = new Set(rows.flatMap(row => mediaForBuilding(row).map(media => media.media_id))).size.toLocaleString();
  $('buildingRows').innerHTML = rows.length ? rows.map(r => {
    const aliases = alternateNames(r);
    const jumpYear = knownStart(r);
    const aliasMarkup = aliases.length ? `<span class="aliases">Also known as ${escapeHtml(aliases.join(' · '))}</span>` : '';
    const jumpMarkup = jumpYear === null ? '—' : `<button class="jump-year" data-jump-year="${jumpYear}">View ${jumpYear}</button>`;
    return `<tr><td><strong>${escapeHtml(r.canonical_name)}</strong>${r.needs_review==='true'?' <small>⚑ review</small>':''}${aliasMarkup}</td><td>${mediaMarkup(r)}</td><td>${escapeHtml(knownSpan(r))}</td><td>${escapeHtml((r.building_type||'—').replaceAll('_',' '))}</td><td>${escapeHtml(r.address_historical||'—')}</td><td>${escapeHtml(r.fire_fate_1871||'—')}</td><td>${escapeHtml(r.confidence)}</td><td>${jumpMarkup}</td></tr>`;
  }).join('') : '<tr><td colspan="8" class="empty-state">No matching records. Try another name, alias, address, type, or year.</td></tr>';
}

function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

fetch('data.json?v=5').then(r => r.json()).then(data => {
  model = data;
  model.namesByBuilding = (model.names || []).reduce((index, name) => {
    (index[name.building_id] ||= []).push(name);
    return index;
  }, {});
  const mediaById = Object.fromEntries((model.media || []).map(media => [media.media_id,media]));
  model.mediaByBuilding = (model.mediaBuildings || []).reduce((index, link) => {
    const media = mediaById[link.media_id];
    if (media) (index[link.building_id] ||= []).push({...media,subject_relationship:link.relationship,subject_confidence:link.confidence});
    return index;
  }, {});
  $('year').addEventListener('input',render);
  $('yearNumber').addEventListener('input',() => {
    const rawYear = $('yearNumber').value;
    const year = Number(rawYear);
    if (/^\d{4}$/.test(rawYear) && year >= 1674 && year <= 1871) { $('year').value = year; render(); }
  });
  $('yearNumber').addEventListener('change',() => {
    if (!$('yearNumber').value) { $('yearNumber').value = $('year').value; return; }
    const year = Math.min(1871, Math.max(1674, Number($('yearNumber').value)));
    if (Number.isFinite(year)) { $('year').value = year; render(); }
  });
  $('search').addEventListener('input',render);
  $('mapVariant').addEventListener('change',render);
  document.querySelectorAll('[data-year]').forEach(b => b.addEventListener('click',() => { $('year').value=b.dataset.year; render(); }));
  $('buildingRows').addEventListener('click', event => {
    const button = event.target.closest('[data-jump-year]');
    if (!button) return;
    $('year').value = button.dataset.jumpYear;
    $('search').value = '';
    render();
    $('recordsHeading').scrollIntoView({behavior:'smooth',block:'start'});
  });
  render();
}).catch(error => { document.body.insertAdjacentHTML('beforeend',`<p>Could not load viewer data: ${escapeHtml(error.message)}</p>`); });
