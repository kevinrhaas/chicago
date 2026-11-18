import { fieldNotebook, LIMITS, safeNotebookURL } from './field-notebook.js';
import { t } from './strings/index.js';
import './strings/notebook.js';
const tr = (key) => t(`notebook.${key}`);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const meta = e => [e.year, e.place, e.grade].filter(Boolean).join(' · ');
const node = (doc, tag, text, cls) => {
  const el = doc.createElement(tag);
  if (text != null) el.textContent = text;
  if (cls) el.className = cls;
  return el;
};
const button = (doc, text, fn) => {
  const el = node(doc, 'button', text, 'setting-button'); el.type = 'button'; el.addEventListener('click', fn); return el;
};

/** Complete portable document: all text escaped; photos embedded; no external scripts or styles. */
export function notebookHTML(entries) {
  const source = s => {
    const url = safeNotebookURL(s.url);
    return `<li>${url ? `<a href="${escape(url)}">${escape(s.title)}</a>` : escape(s.title)}</li>`;
  };
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${escape(tr('title'))}</title><style>body{max-width:48rem;margin:2rem auto;padding:0 1rem;color:#172127;font:16px/1.5 system-ui,sans-serif}article{border-top:1px solid #87959c;padding:1rem 0;break-inside:avoid}h1,h2,h3{line-height:1.2}h2{font-size:1.25rem}h3{font-size:1rem}.note{white-space:pre-wrap}img{max-width:100%;height:auto}a{overflow-wrap:anywhere;color:#16496c}@media print{body{margin:0;font-size:11pt}article{break-inside:auto}img{max-height:100mm}h2,h3{break-after:avoid}a{color:inherit}}</style><body><h1>4D Chicago · ${escape(tr('title'))}</h1><p>${escape(tr('export.note'))}</p>${entries.map(e => `<article><h2>${escape(e.title || tr('note'))}</h2><p>${escape(meta(e))}</p>${e.photo && /^data:image\/(jpeg|png);base64,[A-Za-z0-9+/=]+$/.test(e.photo) ? `<img src="${e.photo}" alt="${escape(e.title)}">` : ''}${e.excerpt ? `<h3>${escape(tr('evidence'))}</h3><p class="note">${escape(e.excerpt)}</p>` : ''}<h3>${escape(tr('note'))}</h3><p class="note">${escape(e.text)}</p><h3>${escape(tr('sources'))}</h3>${e.sources?.length ? `<ul>${e.sources.map(source).join('')}</ul>` : `<p>${escape(tr('export.none'))}</p>`}${safeNotebookURL(e.link) ? `<p><a href="${escape(safeNotebookURL(e.link))}">${escape(tr('moment'))}</a></p>` : ''}</article>`).join('')}</body></html>`;
}
export function downloadNotebook(entries, doc = globalThis.document) {
  const url = URL.createObjectURL(new Blob([notebookHTML(entries)], { type: 'text/html;charset=utf-8' }));
  const a = doc.createElement('a'); a.href = url; a.download = '4d-chicago-field-notebook.html';
  doc.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
/** Printing uses a small document frame, never a second running town. */
export function printNotebook(entries, doc = globalThis.document) {
  doc.querySelectorAll('.field-notebook-print-frame').forEach(frame => frame.remove());
  const frame = doc.createElement('iframe');
  frame.title = tr('title'); frame.className = 'field-notebook-print-frame';
  frame.setAttribute('aria-hidden', 'true');
  const remove = () => frame.remove();
  frame.addEventListener('load', () => {
    const win = frame.contentWindow;
    win.addEventListener('afterprint', remove, { once: true });
    const images = [...win.document.images];
    Promise.all(images.map(img => img.complete ? Promise.resolve() : new Promise(resolve => {
      img.onload = resolve; img.onerror = resolve;
    }))).then(() => { try { win.focus(); win.print(); } catch { remove(); } });
  }, { once: true });
  frame.srcdoc = notebookHTML(entries);
  doc.body.append(frame);
  return frame;
}

export function mountFieldNotebook(container, { notebook = fieldNotebook, context = () => ({}) } = {}) {
  const doc = container.ownerDocument;
  const root = node(doc, 'details', null, 'nav-block field-notebook');
  root.id = 'field-notebook';
  root.append(node(doc, 'summary', tr('title'), 'nav-place'), node(doc, 'p', tr('intro'), 'nav-sub'),
    node(doc, 'p', tr('privacy'), 'nav-sub'), node(doc, 'p', tr('limits'), 'nav-sub'));
  const form = doc.createElement('form');
  const titleLabel = node(doc, 'label', tr('heading'));
  const title = doc.createElement('input'); title.type = 'text'; title.maxLength = 200;
  titleLabel.append(title);
  const textLabel = node(doc, 'label', tr('note'));
  const text = doc.createElement('textarea'); text.rows = 4; text.maxLength = LIMITS.noteChars;
  textLabel.append(text);
  const submit = node(doc, 'button', tr('add'), 'setting-button'); submit.type = 'submit';
  form.append(titleLabel, textLabel, submit);
  const status = node(doc, 'p', '', 'field-notebook-status'); status.setAttribute('role', 'status');
  const result = r => { status.textContent = tr(r.ok ? (r.duplicate ? 'duplicate' : 'saved') : `error.${r.reason}`); };
  form.addEventListener('submit', e => {
    e.preventDefault();
    const c = context() || {};
    const scene = typeof c.scene === 'object' ? c.scene?.id ?? c.scene?.target_date?.slice(0, 4) : c.scene;
    const r = notebook.add({ kind: 'note', title: title.value.trim(), text: text.value, year: c.year ?? scene, place: c.place ?? '' });
    result(r);
    if (r.ok) { title.value = ''; text.value = ''; title.focus(); }
  });
  const exportButtons = node(doc, 'div', null, 'field-notebook-actions');
  const runExport = fn => { const state = notebook.read(); if (state.error) result({ ok: false, reason: state.error }); else fn(state.entries, doc); };
  exportButtons.append(button(doc, tr('download'), () => runExport(downloadNotebook)), button(doc, tr('print'), () => runExport(printNotebook)));
  const entries = node(doc, 'div', null, 'field-notebook-entries');
  const drafts = new Map();
  function paint() {
    const state = notebook.read();
    entries.replaceChildren();
    if (state.error) { result({ ok: false, reason: state.error }); return; }
    if (!state.entries.length) entries.append(node(doc, 'p', tr('empty'), 'nav-sub'));
    for (const entry of [...state.entries].reverse()) {
      const article = node(doc, 'article', null, 'field-notebook-entry');
      article.dataset.notebookId = entry.id;
      const heading = node(doc, 'h3', entry.title || tr('note'));
      article.append(heading, node(doc, 'p', meta(entry), 'nav-sub'));
      if (entry.photo) { const img = doc.createElement('img'); img.src = entry.photo; img.alt = entry.title; img.loading = 'lazy'; article.append(img); }
      if (entry.excerpt) {
        const details = doc.createElement('details');
        details.append(node(doc, 'summary', tr('evidence')), node(doc, 'p', entry.excerpt, 'field-notebook-excerpt')); article.append(details);
      }
      const label = node(doc, 'label', tr('note'));
      const note = doc.createElement('textarea'); note.rows = 3; note.maxLength = LIMITS.noteChars; note.value = drafts.get(entry.id) ?? entry.text;
      note.addEventListener('input', () => drafts.set(entry.id, note.value));
      label.append(note); article.append(label);
      if (entry.sources.length) {
        const list = doc.createElement('ul');
        for (const s of entry.sources) {
          const li = doc.createElement('li');
          if (s.url) { const a = node(doc, 'a', s.title); a.href = s.url; a.target = '_blank'; a.rel = 'noopener noreferrer'; li.append(a); }
          else li.textContent = s.title;
          list.append(li);
        }
        article.append(node(doc, 'h4', tr('sources')), list);
      }
      if (entry.link) { const a = node(doc, 'a', tr('moment')); a.href = entry.link; article.append(a); }
      const actions = node(doc, 'div', null, 'field-notebook-actions');
      actions.append(button(doc, tr('edit'), () => {
        const r = notebook.update(entry.id, note.value); result(r);
        if (r.ok) { drafts.delete(entry.id); [...entries.children].find(item => item.dataset.notebookId === entry.id)?.querySelector('textarea')?.focus(); }
      }), button(doc, tr('remove'), () => {
        const r = notebook.remove(entry.id); result(r);
        if (r.ok) { drafts.delete(entry.id); status.textContent = tr('deleted'); title.focus(); }
      }));
      article.append(actions); entries.append(article);
    }
  }
  root.append(form, status, exportButtons, entries); container.append(root);
  const unsubscribe = notebook.subscribe(paint);
  const refresh = e => { if (!e || e.key === 'chicago4d.notebook.v1' || e.key === null) paint(); };
  doc.defaultView?.addEventListener('storage', refresh);
  paint();
  return { refresh: paint, destroy() { unsubscribe(); doc.defaultView?.removeEventListener('storage', refresh); root.remove(); } };
}
