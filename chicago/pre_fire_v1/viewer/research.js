'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let cards = [];
  const readable = value => Array.isArray(value) ? value.join(' · ') : value == null ? '' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const titleCase = value => readable(value).replace(/[_-]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = readable(text);
    if (className) node.className = className;
    return node;
  };
  function safeUrl(value) {
    if (typeof value !== 'string' || !value.trim()) return null;
    try {
      const url = new URL(value, window.location.href);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : null;
    } catch (_) { return null; }
  }
  function link(title, url) {
    const href = safeUrl(url);
    if (!href) return element('span', title);
    const node = element('a', title);
    node.href = href;
    node.target = '_blank';
    node.rel = 'noopener noreferrer';
    return node;
  }
  function paragraph(parent, label, value, className) {
    if (!value || (Array.isArray(value) && !value.length)) return;
    const p = element('p', undefined, className);
    p.append(element('strong', label + ' '), document.createTextNode(readable(value)));
    parent.append(p);
  }
  function sourceList(sources, className = 'sources') {
    const list = element('ol', undefined, className);
    (sources || []).forEach(source => {
      const li = element('li');
      li.append(link(source.title || source.url || 'Source', source.url));
      const meta = [source.source_date, source.source_kind && titleCase(source.source_kind), source.access && ('Access: ' + titleCase(source.access))].filter(Boolean);
      if (meta.length) li.append(element('p', meta.join(' · '), 'source-meta'));
      paragraph(li, 'Locator:', source.locator);
      const reference = source.reference_image;
      if (reference && safeUrl(reference.local_image)) {
        const figure = element('figure', undefined, 'source-image');
        const preview = link('', reference.local_image);
        const img = element('img');
        img.src = safeUrl(reference.local_image); img.alt = reference.alt;
        img.width = reference.width; img.height = reference.height;
        img.loading = 'lazy'; img.decoding = 'async';
        preview.append(img);
        const caption = element('figcaption', reference.caption);
        paragraph(caption, 'Credit:', reference.credit);
        paragraph(caption, 'Rights:', reference.rights);
        figure.append(preview, caption, link('Open full reference image', reference.local_image));
        li.append(figure);
      }
      list.append(li);
    });
    return list;
  }
  function makeCard(card) {
    const details = element('details', undefined, 'research-card');
    details.id = 'claim-' + card.id;
    const summary = element('summary');
    const header = element('span', undefined, 'card-title');
    header.append(element('span', titleCase(card.category), 'topic-label'), element('span', card.title, 'claim-title'));
    const status = ['documented', 'inferred', 'open'].includes(card.evidence_status) ? card.evidence_status : 'open';
    const statusText = status === 'open' ? 'Open question' : titleCase(status);
    summary.append(header, element('span', statusText, 'badge ' + status));
    details.append(summary);
    const body = element('div', undefined, 'card-body');
    body.append(element('p', card.statement, 'statement'));
    paragraph(body, 'Applies to:', card.applies_to, 'date-scope');
    const implications = element('div', undefined, 'implications');
    paragraph(implications, 'For the reconstruction:', card.render_implication);
    paragraph(implications, 'Limits & liberties:', card.limits);
    paragraph(implications, 'Next evidence to collect:', card.next_step);
    body.append(implications);
    if (card.sources?.length) {
      body.append(element('h3', 'Sources & locators'), sourceList(card.sources));
    } else {
      body.append(element('p', 'No source is attached to this record. Treat it as an open research item.', 'source-meta'));
    }
    if (card.notebook_ids?.length) {
      body.append(element('h3', 'Primary-source field observations'));
      const observations = element('ul', undefined, 'notebook-links');
      for (const id of card.notebook_ids) {
        const item = element('li');
        const anchor = element('a', titleCase(id));
        anchor.href = 'notebook.html#record-' + encodeURIComponent(id);
        item.append(anchor); observations.append(item);
      }
      body.append(observations);
    }
    const permalink = element('a', 'Link to this finding', 'permalink');
    permalink.href = '#' + details.id;
    body.append(permalink);
    details.append(body);
    return details;
  }
  function syncQuery() {
    const url = new URL(window.location.href);
    for (const [key, value] of [['q', $('research-search').value], ['topic', $('category').value], ['evidence', $('evidence').value]]) {
      if (value) url.searchParams.set(key, value);
      else url.searchParams.delete(key);
    }
    history.replaceState(null, '', url);
  }
  function renderCards(updateUrl = true) {
    const query = $('research-search').value.trim().toLocaleLowerCase();
    const category = $('category').value;
    const status = $('evidence').value;
    const matched = cards.filter(card => (!category || card.category === category) && (!status || card.evidence_status === status) && (!query || JSON.stringify(card).toLocaleLowerCase().includes(query)));
    const previouslyOpen = new Set([...$('research-cards').querySelectorAll('details[open]')].map(node => node.id));
    const nodes = matched.map(card => {
      const node = makeCard(card);
      node.open = previouslyOpen.has(node.id);
      return node;
    });
    $('research-cards').replaceChildren(...nodes);
    $('results-count').textContent = matched.length + ' of ' + cards.length + ' findings';
    $('empty-state').hidden = !!matched.length;
    $('expand-all').disabled = !matched.length;
    $('collapse-all').disabled = !matched.length;
    if (updateUrl) syncQuery();
  }
  function renderAudit(entries) {
    $('year-audit').replaceChildren(...entries.map(entry => {
      const article = element('article', undefined, 'audit-card');
      const head = element('div', undefined, 'audit-heading');
      head.append(element('h3', entry.year), element('span', entry.status, 'audit-status'));
      article.append(head);
      if (entry.date) article.append(element('p', entry.date, 'source-meta'));
      article.append(element('p', entry.summary));
      const lessons = element('ul');
      (entry.lessons || []).forEach(lesson => lessons.append(element('li', lesson)));
      if (lessons.childElementCount) article.append(lessons);
      if (entry.references?.length) article.append(element('h4', 'Repository evidence'), sourceList(entry.references, 'audit-references'));
      return article;
    }));
  }
  function renderReadiness(entries) {
    $('readiness').replaceChildren(...entries.map(entry => {
      const li = element('li', undefined, 'readiness-card');
      if (entry.priority) li.append(element('p', entry.priority, 'topic-label'));
      li.append(element('h3', entry.title));
      paragraph(li, 'Deliverable:', entry.deliverable);
      paragraph(li, 'Ready when:', entry.acceptance);
      return li;
    }));
  }
  function revealHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id.startsWith('claim-')) return;
    let node = document.getElementById(id);
    if (!node && cards.some(card => 'claim-' + card.id === id)) {
      $('research-search').value = '';
      $('category').value = '';
      $('evidence').value = '';
      renderCards();
      node = document.getElementById(id);
    }
    if (node) { node.open = true; node.scrollIntoView({block: 'start'}); }
  }
  function initialize(data) {
    if (!Array.isArray(data.cards) || !Array.isArray(data.year_audit) || !Array.isArray(data.readiness)) throw new Error('The research file has an unexpected format.');
    cards = data.cards;
    const categories = [...new Set(cards.map(card => card.category))].filter(Boolean).sort();
    for (const category of categories) {
      const option = element('option', titleCase(category));
      option.value = category;
      $('category').append(option);
    }
    if (data.scope) $('scope').textContent = readable(data.scope);
    if (data.updated) $('updated').textContent = 'Research updated ' + readable(data.updated);
    $('audit-snapshot').textContent = readable(data.audit_snapshot);
    $('inventory').textContent = cards.length + ' findings · ' + categories.length + ' topics';
    const params = new URLSearchParams(location.search);
    $('research-search').value = params.get('q') || '';
    for (const [id, key] of [['category', 'topic'], ['evidence', 'evidence']]) {
      const value = params.get(key) || '';
      if ([...$(id).options].some(option => option.value === value)) $(id).value = value;
    }
    $('filters').addEventListener('submit', event => event.preventDefault());
    $('research-search').addEventListener('input', () => renderCards());
    $('category').addEventListener('change', () => renderCards());
    $('evidence').addEventListener('change', () => renderCards());
    $('clear-filters').addEventListener('click', () => {
      $('research-search').value = '';
      $('category').value = '';
      $('evidence').value = '';
      renderCards();
      $('research-search').focus();
    });
    $('expand-all').addEventListener('click', () => $('research-cards').querySelectorAll('details').forEach(node => { node.open = true; }));
    $('collapse-all').addEventListener('click', () => $('research-cards').querySelectorAll('details').forEach(node => { node.open = false; }));
    window.addEventListener('hashchange', revealHash);
    window.addEventListener('beforeprint', () => {
      $('research-cards').querySelectorAll('details').forEach(node => { node.dataset.printOpen = String(node.open); node.open = true; });
    });
    window.addEventListener('afterprint', () => {
      $('research-cards').querySelectorAll('details').forEach(node => { node.open = node.dataset.printOpen === 'true'; delete node.dataset.printOpen; });
    });
    renderCards(false);
    renderAudit(data.year_audit);
    renderReadiness(data.readiness);
    $('load-status').hidden = true;
    for (const id of ['research', 'other-years', 'next']) $(id).hidden = false;
    revealHash();
  }
  fetch('research-1871.json', {cache: 'no-cache'}).then(response => {
    if (!response.ok) throw new Error('The research file could not be retrieved (HTTP ' + response.status + ').');
    return response.json();
  }).then(initialize).catch(error => {
    const status = $('load-status');
    status.replaceChildren(element('p', 'Could not load the research dossier. ' + error.message));
    status.append(link('Open the research JSON directly', 'research-1871.json'));
    const retry = element('button', 'Try again');
    retry.type = 'button';
    retry.addEventListener('click', () => location.reload());
    status.append(retry);
    status.classList.add('load-error');
  });
})();
