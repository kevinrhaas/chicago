'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = String(text);
    if (cls) node.className = cls;
    return node;
  };
  const label = value => value.replaceAll('-', ' ').replace(/^./, c => c.toUpperCase());
  const link = (text, href, external = false) => {
    const node = el('a', text);
    const url = new URL(href, location.href);
    if (!['https:', 'http:'].includes(url.protocol)) return el('span', text);
    node.href = href;
    if (external) { node.target = '_blank'; node.rel = 'noopener noreferrer'; }
    return node;
  };
  function paragraph(parent, title, text, cls) {
    const p = el('p', undefined, cls);
    p.append(el('strong', title + ' '), document.createTextNode(text));
    parent.append(p);
  }
  function list(parent, title, values) {
    parent.append(el('h4', title));
    const ul = el('ul');
    for (const value of values) ul.append(el('li', value));
    parent.append(ul);
  }
  let data, pages, books, records, packets, scene = '';
  const filters = [['notebook-search', 'q'], ['notebook-topic', 'topic'], ['notebook-basis', 'basis'], ['notebook-book', 'book']];
  function clear() {
    for (const [id] of filters) $(id).value = '';
    scene = '';
  }
  function sync() {
    const url = new URL(location.href);
    for (const [id, key] of filters) {
      if ($(id).value) url.searchParams.set(key, $(id).value);
      else url.searchParams.delete(key);
    }
    if (scene) url.searchParams.set('scene', scene);
    else url.searchParams.delete('scene');
    history.replaceState(null, '', url);
  }
  function recordLinks(parent, ids) {
    const ul = el('ul');
    for (const id of ids) {
      const li = el('li');
      li.append(link(records[id].title, '#record-' + id));
      ul.append(li);
    }
    parent.append(ul);
  }
  function recordCard(record) {
    const card = el('details', undefined, 'research-card record-card');
    card.id = 'record-' + record.id;
    const summary = el('summary'), title = el('span', undefined, 'card-title');
    title.append(el('span', record.topic, 'topic-label'), el('span', record.title, 'claim-title'), el('span', record.historical_location, 'record-place'));
    summary.append(title, el('span', label(record.evidence_type), 'badge basis-' + record.evidence_type));
    card.append(summary);
    const body = el('div', undefined, 'card-body');
    body.append(el('p', record.finding, 'statement'));
    paragraph(body, 'Date scope:', record.date_scope, 'date-scope');
    body.append(el('h4', 'Transcription / locating text'), el('p', record.excerpt, 'transcription'));
    if (record.quantities.length) {
      const ul = el('ul', undefined, 'quantity-list');
      for (const q of record.quantities) {
        const li = el('li');
        li.append(el('strong', q.value.toLocaleString() + ' ' + q.unit), document.createTextNode(' · ' + q.name), el('small', q.qualifier));
        ul.append(li);
      }
      body.append(ul);
    }
    const use = el('div', undefined, 'implications');
    paragraph(use, 'Proposed rendering use:', record.render_use);
    paragraph(use, 'Limits:', record.limitations);
    body.append(use, el('h4', 'Source and locator'));
    for (const sid of record.source_ids) {
      const page = pages[sid], book = books[page.book_id], source = el('div', undefined, 'record-source');
      source.append(link(book.title + ' · p. ' + page.printed_page, page.url, true));
      source.append(el('p', record.locator + ' · ' + page.verification + ' · scan n' + page.scan_index));
      source.append(link('Open original scan ↗', page.local_image || page.image_url, true), document.createTextNode(' · '), link('Source context', '#source-' + sid));
      body.append(source);
    }
    body.append(link('Link to this observation', '#' + card.id));
    card.append(body);
    return card;
  }
  function render(update = true) {
    const query = $('notebook-search').value.trim().toLocaleLowerCase();
    const topic = $('notebook-topic').value, basis = $('notebook-basis').value, book = $('notebook-book').value;
    const selected = scene ? new Set(packets[scene].record_ids) : null;
    const matches = data.records.filter(r => (!topic || r.topic === topic) && (!basis || r.evidence_type === basis) && (!book || r.source_ids.some(id => pages[id].book_id === book)) && (!selected || selected.has(r.id)) && (!query || JSON.stringify(r).toLocaleLowerCase().includes(query)));
    const opened = new Set([...$('observation-list').querySelectorAll('details[open]')].map(n => n.id));
    $('observation-list').replaceChildren(...matches.map(r => { const node = recordCard(r); node.open = opened.has(node.id); return node; }));
    $('notebook-count').textContent = matches.length + ' of ' + data.records.length + ' observations' + (scene ? ' · Scene study: ' + packets[scene].title : '');
    $('notebook-empty').hidden = matches.length > 0;
    $('notebook-expand').disabled = !matches.length;
    $('notebook-collapse').disabled = !matches.length;
    if (update) sync();
  }
  function renderScenes() {
    $('scene-list').replaceChildren(...data.scene_packets.map(packet => {
      const card = el('details', undefined, 'scene-card'); card.id = 'scene-' + packet.id;
      const summary = el('summary'), title = el('span', undefined, 'card-title');
      title.append(el('span', packet.record_ids.length + ' linked observations · Proposed scene', 'topic-label'), el('span', packet.title, 'claim-title'), el('span', packet.historical_location, 'scene-place'));
      summary.append(title); card.append(summary);
      const body = el('div', undefined, 'card-body'); body.append(el('p', packet.purpose));
      const explore = link('Explore this scene’s observations →', '?scene=' + packet.id + '#observations');
      explore.className = 'scene-evidence';
      explore.addEventListener('click', event => {
        event.preventDefault(); clear(); scene = packet.id; render(); location.hash = 'observations'; $('notebook-search').focus({preventScroll:true});
      });
      body.append(explore);
      list(body, 'Proposed actions', packet.proposed_actions);
      list(body, 'Still unresolved', packet.unresolved);
      list(body, 'Keep out of this reconstruction', packet.exclude);
      body.append(el('h4', 'Read the underlying evidence')); recordLinks(body, packet.record_ids);
      body.append(link('Link to this scene study', '#' + card.id)); card.append(body); return card;
    }));
  }
  function renderSources() {
    $('source-list').replaceChildren(...data.books.map(book => {
      const article = el('article', undefined, 'source-book');
      article.append(el('h3', book.title));
      paragraph(article, 'Reporting period:', book.date_scope);
      paragraph(article, 'Reading limits:', book.bias);
      paragraph(article, 'Rights:', book.rights);
      article.append(link('Open the complete digitized volume ↗', book.url, true));
      for (const page of data.pages.filter(p => p.book_id === book.id)) {
        const details = el('details', undefined, 'source-page'); details.id = 'source-' + page.id;
        details.append(el('summary', 'p. ' + page.printed_page + ' · ' + page.title));
        const body = el('div', undefined, 'card-body');
        body.append(el('p', page.verification + ' · inspected ' + page.inspected_on + ' · archive scan n' + page.scan_index, 'scan-meta'));
        body.append(link('Archive page ↗', page.url, true), document.createTextNode(' · '), link('Open original scan ↗', page.local_image || page.image_url, true));
        if (page.local_image) {
          const preview = link('', page.local_image, true); preview.className = 'scan-preview';
          const img = el('img'); img.src = page.local_image; img.loading = 'lazy'; img.decoding = 'async'; img.alt = 'Original page ' + page.printed_page + ' of ' + book.title + ': ' + page.title;
          img.width = 280; img.height = 240; preview.append(img); body.append(preview);
          body.append(el('p', 'Unmodified local scan · ' + (page.bytes / 1024 / 1024).toFixed(2) + ' MB · SHA-256: ' + page.sha256, 'scan-meta'));
        }
        const refs = data.records.filter(r => r.source_ids.includes(page.id)).map(r => r.id);
        body.append(el('h4', refs.length + ' linked observations')); recordLinks(body, refs);
        details.append(body); article.append(details);
      }
      return article;
    }));
  }
  function renderRevisions() {
    $('revision-list').replaceChildren(...data.corrections.map(change => {
      const article = el('article', undefined, 'revision-card'); article.append(el('h3', change.title));
      paragraph(article, 'Earlier:', change.before); paragraph(article, 'Now:', change.after); recordLinks(article, change.record_ids); return article;
    }));
  }
  function revealHash() {
    let id; try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (id.startsWith('record-') && records[id.slice(7)] && !$(id)) { clear(); render(); }
    const node = $(id);
    if (node) { if (node.tagName === 'DETAILS') node.open = true; node.scrollIntoView({block:'start'}); }
  }
  function initialize(value) {
    if (!value.records?.length || !value.pages?.length || !value.books?.length || !value.scene_packets?.length) throw new Error('Unexpected notebook format.');
    data = value;
    const index = values => Object.fromEntries(values.map(x => [x.id, x]));
    pages = index(data.pages); books = index(data.books); records = index(data.records); packets = index(data.scene_packets);
    const option = (id, value, text = value) => { const node = el('option', text); node.value = value; $(id).append(node); };
    const topics = [...new Set(data.records.map(r => r.topic))].sort();
    for (const topic of topics) option('notebook-topic', topic);
    for (const basis of [...new Set(data.records.map(r => r.evidence_type))].sort()) option('notebook-basis', basis, label(basis));
    for (const book of data.books) option('notebook-book', book.id, book.title);
    for (const [number, name] of [[data.records.length, 'field observations'], [data.pages.length, 'source pages'], [topics.length, 'research topics'], [data.scene_packets.length, 'scene studies']]) {
      const p = el('p'); p.append(el('strong', number), document.createTextNode(name)); $('notebook-stats').append(p);
    }
    $('scenes-heading').textContent = data.scene_packets.length + ' places to investigate';
    $('notebook-method').textContent = data.method; $('notebook-updated').textContent = 'Updated ' + data.updated;
    const params = new URLSearchParams(location.search);
    for (const [id, key] of filters) {
      const value = params.get(key) || '';
      if (id === 'notebook-search' || [...$(id).options].some(o => o.value === value)) $(id).value = value;
    }
    if (packets[params.get('scene')]) scene = params.get('scene');
    $('notebook-filters').addEventListener('submit', e => e.preventDefault());
    for (const [id] of filters) $(id).addEventListener(id === 'notebook-search' ? 'input' : 'change', () => {
      if (location.hash.startsWith('#record-')) history.replaceState(null, '', location.pathname + location.search);
      render();
    });
    $('notebook-clear').addEventListener('click', () => { clear(); render(); $('notebook-search').focus(); });
    for (const [id, open] of [['notebook-expand', true], ['notebook-collapse', false]]) $(id).addEventListener('click', () => $('observation-list').querySelectorAll('details').forEach(n => { n.open = open; }));
    window.addEventListener('hashchange', revealHash);
    window.addEventListener('beforeprint', () => document.querySelectorAll('main details').forEach(n => { n.dataset.wasOpen = String(n.open); n.open = true; }));
    window.addEventListener('afterprint', () => document.querySelectorAll('main details').forEach(n => { n.open = n.dataset.wasOpen === 'true'; delete n.dataset.wasOpen; }));
    render(false); renderScenes(); renderSources(); renderRevisions();
    $('notebook-status').hidden = true;
    for (const id of ['scenes', 'observations', 'sources', 'revisions']) $(id).hidden = false;
    revealHash();
  }
  fetch('field-notebook-1871.json', {cache:'no-cache'}).then(response => {
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  }).then(initialize).catch(error => {
    const status = $('notebook-status');
    status.replaceChildren(el('p', 'The interactive notebook could not load. ' + error.message));
    status.append(link('Read the complete static edition', 'notebook-reading.html'), document.createTextNode(' · '), link('Open notebook JSON', 'field-notebook-1871.json'));
    const retry = el('button', 'Try again'); retry.type = 'button'; retry.addEventListener('click', () => location.reload()); status.append(document.createTextNode(' '), retry);
  });
})();
