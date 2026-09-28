/* Chicago Building Atlas — notes on cards, maps and pages.
 *
 * One script for every Atlas documentation page (not 4D). A page opts in with
 *   <link rel="stylesheet" href="/notes/notes.css">
 *   <script src="/notes/notes.js" data-page="prairie-1904" defer></script>
 * and marks what can carry notes with attributes, so a viewer that renders by
 * innerHTML needs no calls:
 *   data-note="building:b-12"        the stable key the notes are filed under
 *   data-note-label="Glessner House" what the panel calls it
 *   data-note-place="inline"         pencil sits in the flow (headings, table
 *                                    cells) instead of the host's top-right corner
 * A <details> host gets its pencil inside its <summary>, so it shows while closed.
 * `[data-notes-slot]` receives the page's Notes button; without one it floats.
 *
 * ACCESS (enforced by the database — chicago/atlas-notes/setup.sql):
 * everyone reads the notes that are not archived; a person holding a personal
 * edit link (…?notes=<token>) adds, archives and restores them, and sees the
 * archived ones plus the IP / browser / device stamped on each. The token is
 * moved off the address bar into this browser's storage on arrival, so a copied
 * URL never carries it. `?notes=signout` forgets it.
 *
 * Until DB below is filled in, this script does nothing at all.
 */
(() => {
  'use strict';
  // The notes project (Supabase). The publishable key is designed to ship in a
  // public page: every table is closed to it, and the four notes_* functions
  // are the only way in. See chicago/atlas-notes/README.md.
  const DB = window.ATLAS_NOTES_DB || { // a test (chicago/atlas-notes/smoke.mjs) may inject its own
    url: '',
    key: '',
  };
  const SITE = 'chicago.polecat.live';
  const K = { token: 'atlas.notes.token', device: 'atlas.notes.device' };

  const script = document.currentScript;
  const PAGE = (script && script.dataset.page) || location.pathname.split('/').filter(Boolean)[0] || 'home';
  if (!DB.url || !DB.key) return;

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch { /* private mode */ } },
  };

  // ---- the edit link --------------------------------------------------------
  (() => {
    let url; try { url = new URL(location.href); } catch { return; }
    if (!url.searchParams.has('notes')) return;
    const value = url.searchParams.get('notes').trim();
    if (/^(signout|off|logout)$/i.test(value)) store.set(K.token, null);
    else if (value) store.set(K.token, value);
    url.searchParams.delete('notes');
    try { history.replaceState(history.state, '', url.pathname + url.search + url.hash); } catch { /* file:// */ }
  })();
  let device = store.get(K.device);
  if (!device) {
    device = (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now()).replace(/-/g, '').slice(0, 12);
    store.set(K.device, device);
  }

  const state = { token: store.get(K.token), editor: null, rows: [], loaded: false, error: null, notice: null };

  // ---- database -------------------------------------------------------------
  async function rpc(fn, args) {
    let res;
    try {
      res = await fetch(DB.url.replace(/\/+$/, '') + '/rest/v1/rpc/' + fn, {
        method: 'POST', headers: { apikey: DB.key, 'Content-Type': 'application/json' }, body: JSON.stringify(args),
      });
    } catch (e) { throw new Error('The notes database could not be reached. Check the connection and try again.'); }
    const text = await res.text();
    if (!res.ok) {
      if (/edit link not recognised/.test(text)) { const e = new Error('This edit link is not recognised.'); e.code = 'auth'; throw e; }
      if (res.status === 404) throw new Error('The notes database is not set up yet (run chicago/atlas-notes/setup.sql).');
      throw new Error('The notes database answered HTTP ' + res.status + '.');
    }
    return text ? JSON.parse(text) : null;
  }
  async function load() {
    state.error = null;
    try {
      if (state.token) {
        try { state.editor = await rpc('notes_whoami', { p_token: state.token }); }
        catch (e) {
          if (e.code !== 'auth') throw e;
          state.token = null; state.editor = null; store.set(K.token, null);
          state.notice = 'That edit link is not recognised, so this page is read-only. Ask for a new link.';
        }
      }
      state.rows = await rpc('notes_list', { p_site: SITE, p_page: PAGE, p_token: state.editor ? state.token : null }) || [];
      state.loaded = true;
    } catch (e) { state.error = e.message; }
    paint();
  }

  // ---- small DOM helpers ----------------------------------------------------
  const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = String(text); return n; };
  const PENCIL = '<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true" focusable="false"><path d="M13.6 3.2a1.9 1.9 0 0 1 2.7 0l.5.5a1.9 1.9 0 0 1 0 2.7L7.4 15.8 3.5 16.5l.7-3.9z M12.2 4.6l3.2 3.2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/></svg>';
  const when = iso => { try { return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }); } catch { return iso; } };
  function uaShort(ua) {
    if (!ua) return '';
    const browser = /Edg\//.test(ua) ? 'Edge' : /OPR\//.test(ua) ? 'Opera' : /Firefox\//.test(ua) ? 'Firefox' : /(CriOS|Chrome)\//.test(ua) ? 'Chrome' : /Safari\//.test(ua) ? 'Safari' : 'Browser';
    const os = /iPhone/.test(ua) ? 'iPhone' : /iPad/.test(ua) ? 'iPad' : /Android/.test(ua) ? 'Android' : /Mac OS X/.test(ua) ? 'macOS' : /Windows/.test(ua) ? 'Windows' : /Linux/.test(ua) ? 'Linux' : '';
    return os ? browser + ' on ' + os : browser;
  }
  const active = target => state.rows.filter(r => r.target === target && !r.archived_at);
  const cssEscape = s => (window.CSS && CSS.escape ? CSS.escape(s) : String(s).replace(/["\\]/g, '\\$&'));

  // ---- pencils ----------------------------------------------------------------
  function hostOf(node) { return node.tagName === 'DETAILS' ? node.querySelector(':scope > summary') || node : node; }
  function decorate(node) {
    const host = hostOf(node);
    let pencil = host.querySelector(':scope > .an-pencil');
    if (!pencil) {
      pencil = el('button', 'an-pencil'); pencil.type = 'button';
      pencil.innerHTML = PENCIL; pencil.append(el('span', 'an-n'));
      host.append(pencil);
    }
    paintPencil(pencil, node);
  }
  function paintPencil(pencil, node) {
    const target = node.dataset.note, label = node.dataset.noteLabel || target;
    const n = active(target).length;
    pencil.classList.toggle('an-has', n > 0);
    pencil.classList.toggle('an-inline', node.dataset.notePlace === 'inline');
    const badge = pencil.querySelector('.an-n'), shown = n ? String(n) : '';
    if (badge.textContent !== shown) badge.textContent = shown; // unconditional writes would re-trigger the observer
    pencil.setAttribute('aria-label', (n ? n + (n === 1 ? ' note' : ' notes') : 'Notes') + ' — ' + label);
    pencil.title = n ? n + (n === 1 ? ' note' : ' notes') : state.editor ? 'Add a note' : 'Notes';
  }
  function decorateAll(root = document) {
    if (root.matches && root.matches('[data-note]')) decorate(root);
    if (root.querySelectorAll) root.querySelectorAll('[data-note]').forEach(decorate);
  }
  const ownerOf = pencil => { let n = pencil.parentElement; if (n && n.tagName === 'SUMMARY') n = n.parentElement; return n && n.closest('[data-note]'); };

  // ---- the page's Notes button ----------------------------------------------
  let toggle;
  function mountToggle() {
    toggle = el('button', 'an-toggle'); toggle.type = 'button';
    toggle.innerHTML = PENCIL; toggle.append(el('span', 'an-toggle-label', 'Notes'), el('span', 'an-n'));
    const slot = document.querySelector('[data-notes-slot]');
    if (slot) slot.append(toggle); else { toggle.classList.add('an-fab'); document.body.append(toggle); }
    toggle.addEventListener('click', e => { e.stopPropagation(); if (panel && panelTarget === 'page' && !panel.hidden) close(); else open('page', 'This page', toggle); });
  }

  function paint() {
    const root = document.documentElement;
    root.classList.toggle('an-editor', !!state.editor);
    root.classList.add('an-ready');
    decorateAll();
    const count = state.rows.filter(r => !r.archived_at).length;
    if (toggle) {
      const badge = toggle.querySelector('.an-n'), shown = count ? String(count) : '';
      if (badge.textContent !== shown) badge.textContent = shown;
      toggle.hidden = !state.editor && !count && !state.notice;
      toggle.setAttribute('aria-label', 'Notes on this page' + (count ? ' (' + count + ')' : '') + (state.editor ? ' — editing as ' + state.editor.name : ''));
    }
    if (panel && !panel.hidden) renderPanel();
  }

  // ---- the panel -------------------------------------------------------------
  let panel, backdrop, panelTarget = null, panelLabel = '', anchor = null, showArchived = false, busy = false, status = '', draft = '';
  function ensurePanel() {
    if (panel) return;
    backdrop = el('div', 'an-backdrop'); backdrop.hidden = true;
    panel = el('div', 'an-panel'); panel.hidden = true;
    panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-labelledby', 'an-title');
    document.body.append(backdrop, panel);
    backdrop.addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) { e.preventDefault(); close(); } });
    document.addEventListener('pointerdown', e => {
      if (panel.hidden || panel.contains(e.target) || e.target.closest('.an-pencil, .an-toggle')) return;
      close(false);
    });
    addEventListener('resize', () => { if (!panel.hidden) place(); });
  }
  function open(target, label, from) {
    ensurePanel();
    if (panelTarget !== target) { showArchived = false; draft = ''; status = ''; }
    panelTarget = target; panelLabel = label; anchor = from;
    document.querySelectorAll('[aria-expanded="true"].an-pencil, [aria-expanded="true"].an-toggle').forEach(b => b.setAttribute('aria-expanded', 'false'));
    if (from) from.setAttribute('aria-expanded', 'true');
    panel.hidden = false; backdrop.hidden = false;
    renderPanel();
    const focus = panel.querySelector('textarea') || panel.querySelector('.an-close');
    if (focus) focus.focus({ preventScroll: true });
  }
  function close(refocus = true) {
    if (!panel || panel.hidden) return;
    panel.hidden = true; backdrop.hidden = true;
    if (anchor) { anchor.setAttribute('aria-expanded', 'false'); if (refocus && anchor.isConnected) anchor.focus({ preventScroll: true }); }
    panelTarget = null;
  }
  const phone = () => matchMedia('(max-width: 700px)').matches;
  function place() {
    panel.classList.toggle('an-sheet', phone());
    backdrop.classList.toggle('an-dim', phone());
    if (phone() || !anchor || !anchor.isConnected) {
      panel.style.left = panel.style.top = '';
      if (!phone()) { panel.style.left = Math.max(16, (innerWidth - panel.offsetWidth) / 2) + 'px'; panel.style.top = scrollY + 80 + 'px'; }
      return;
    }
    panel.style.maxHeight = '';
    const r = anchor.getBoundingClientRect(), w = panel.offsetWidth, h = panel.offsetHeight;
    const below = innerHeight - r.bottom - 20, above = r.top - 20;
    const left = Math.min(Math.max(12, r.right - w), innerWidth - w - 12);
    // Below if it fits, else above if that fits, else the roomier side, shortened to fit.
    const up = h > below && (h <= above || above > below);
    if (h > (up ? above : below)) panel.style.maxHeight = Math.max(360, up ? above : below) + 'px';
    const top = up ? r.top - 8 - Math.min(h, Math.max(360, above)) : r.bottom + 8;
    panel.style.left = left + scrollX + 'px';
    panel.style.top = top + scrollY + 'px';
  }

  function noteItem(r) {
    const li = el('li', 'an-note' + (r.archived_at ? ' an-archived' : ''));
    const head = el('div', 'an-note-head');
    head.append(el('strong', null, r.author || 'Editor'), el('time', null, when(r.created_at)));
    head.querySelector('time').dateTime = r.created_at;
    li.append(head, el('p', 'an-body', r.body));
    if (state.editor) {
      const meta = [r.ip && 'IP ' + r.ip, uaShort(r.ua), r.device && 'device ' + String(r.device).slice(0, 6)].filter(Boolean).join(' · ');
      if (meta) li.append(el('p', 'an-meta', meta));
      if (r.archived_at) li.append(el('p', 'an-meta', 'Archived ' + when(r.archived_at) + (r.archived_by ? ' by ' + r.archived_by : '')));
      const act = el('button', 'an-link', r.archived_at ? 'Restore' : 'Archive'); act.type = 'button';
      act.addEventListener('click', () => archive(r, !r.archived_at));
      li.append(act);
    }
    return li;
  }
  function renderPanel() {
    const isPage = panelTarget === 'page';
    panel.replaceChildren();
    const head = el('div', 'an-head');
    const titles = el('div');
    titles.append(el('p', 'an-kicker', isPage ? 'Notes' : 'Notes on'), el('h2', 'an-title', isPage ? 'This page' : panelLabel));
    titles.lastChild.id = 'an-title';
    const x = el('button', 'an-close', '×'); x.type = 'button'; x.setAttribute('aria-label', 'Close notes'); x.addEventListener('click', () => close());
    head.append(titles, x); panel.append(head);

    // The list scrolls; the compose box below it stays in view however tight the space.
    const scroller = el('div', 'an-scroll'), compose = el('div', 'an-compose'); panel.append(scroller, compose);
    if (state.notice) scroller.append(el('p', 'an-status an-warn', state.notice));
    if (state.error) {
      scroller.append(el('p', 'an-status an-warn', state.error));
      const retry = el('button', 'an-link', 'Try again'); retry.type = 'button'; retry.addEventListener('click', load); scroller.append(retry);
    } else if (!state.loaded) scroller.append(el('p', 'an-meta', 'Loading notes…'));

    if (!isPage) {
      const node = document.querySelector('[data-note="' + cssEscape(panelTarget) + '"]');
      if (node && anchor && anchor.classList.contains('an-toggle')) {
        const go = el('button', 'an-link', 'Show it on the page ↓'); go.type = 'button';
        go.addEventListener('click', () => { if (node.tagName === 'DETAILS') node.open = true; close(false); node.scrollIntoView({ behavior: 'smooth', block: 'center' }); const p = hostOf(node).querySelector(':scope > .an-pencil'); if (p) p.focus({ preventScroll: true }); });
        scroller.append(go);
      }
    }

    const mine = state.rows.filter(r => r.target === panelTarget);
    const live = mine.filter(r => !r.archived_at), gone = mine.filter(r => r.archived_at);
    if (state.loaded) {
      const list = el('ol', 'an-list');
      live.forEach(r => list.append(noteItem(r)));
      if (live.length) scroller.append(list);
      else scroller.append(el('p', 'an-empty', isPage ? 'No notes about the page as a whole yet.' : 'No notes yet.'));
      if (state.editor && gone.length) {
        const t = el('button', 'an-link', (showArchived ? 'Hide' : 'Show') + ' archived (' + gone.length + ')'); t.type = 'button';
        t.addEventListener('click', () => { showArchived = !showArchived; renderPanel(); });
        scroller.append(t);
        if (showArchived) { const ol = el('ol', 'an-list'); gone.forEach(r => ol.append(noteItem(r))); scroller.append(ol); }
      }
    }

    if (state.editor && state.loaded) {
      const form = el('form', 'an-form');
      const ta = el('textarea'); ta.rows = 3; ta.maxLength = 4000; ta.placeholder = isPage ? 'A note about this page…' : 'Add a note…'; ta.value = draft;
      ta.setAttribute('aria-label', 'New note');
      ta.addEventListener('input', () => { draft = ta.value; });
      ta.addEventListener('keydown', e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); form.requestSubmit(); } });
      const row = el('div', 'an-form-row');
      row.append(el('span', 'an-meta', 'As ' + state.editor.name));
      const save = el('button', 'an-save', busy ? 'Saving…' : 'Save note'); save.type = 'submit'; save.disabled = busy;
      row.append(save);
      form.append(ta, row);
      form.addEventListener('submit', e => { e.preventDefault(); add(ta.value); });
      compose.append(form);
    }
    if (status) compose.append(el('p', 'an-status', status));

    if (isPage && state.loaded) {
      const others = new Map();
      state.rows.filter(r => r.target !== 'page' && !r.archived_at).forEach(r => {
        const g = others.get(r.target) || { label: r.target_label || r.target, rows: [] }; g.rows.push(r); others.set(r.target, g);
      });
      if (others.size) {
        scroller.append(el('h3', 'an-sub', 'Notes elsewhere on this page'));
        const ul = el('ul', 'an-index');
        for (const [target, g] of others) {
          const b = el('button', 'an-index-item'); b.type = 'button';
          b.append(el('span', 'an-index-label', g.label), el('span', 'an-n', g.rows.length), el('span', 'an-index-snip', g.rows[0].body));
          b.addEventListener('click', () => open(target, g.label, toggle));
          const li = el('li'); li.append(b); ul.append(li);
        }
        scroller.append(ul);
      }
    }

    if (!compose.childNodes.length) compose.remove();
    const foot = el('div', 'an-foot');
    if (state.editor) {
      foot.append(el('span', null, 'Editing as ' + state.editor.name));
      const out = el('button', 'an-link', 'Sign out on this device'); out.type = 'button';
      out.addEventListener('click', () => { store.set(K.token, null); state.token = null; state.editor = null; state.notice = null; load(); });
      foot.append(out);
    } else foot.append(el('span', null, 'Read-only. Notes are written by the Atlas editors.'));
    panel.append(foot);
    if (!panel.hidden) place(); // it may have grown (a new note, the archived list)
  }

  async function add(text) {
    const body = text.trim();
    if (!body || busy) return;
    const node = document.querySelector('[data-note="' + cssEscape(panelTarget) + '"]');
    const label = panelTarget === 'page' ? document.title : (node && node.dataset.noteLabel) || panelLabel;
    busy = true; status = ''; renderPanel();
    try {
      const rows = await rpc('notes_add', { p_token: state.token, p_site: SITE, p_page: PAGE, p_target: panelTarget, p_label: label, p_body: body, p_path: location.pathname, p_device: device });
      state.rows.unshift(...(rows || []));
      draft = ''; status = 'Saved.';
    } catch (e) { status = e.message; }
    busy = false; paint();
    const ta = panel && panel.querySelector('textarea'); if (ta && !draft) ta.focus({ preventScroll: true });
  }
  async function archive(row, flag) {
    status = '';
    try {
      const [updated] = await rpc('notes_archive', { p_token: state.token, p_id: row.id, p_archive: flag }) || [];
      if (updated) Object.assign(row, updated);
      status = flag ? 'Archived — hidden from the page, kept in the database.' : 'Restored.';
    } catch (e) { status = e.message; }
    paint();
  }

  // ---- wiring ----------------------------------------------------------------
  document.addEventListener('click', e => {
    const pencil = e.target.closest && e.target.closest('.an-pencil');
    if (!pencil) return;
    e.preventDefault(); e.stopPropagation(); // a pencil inside <summary> must not toggle the card
    const node = ownerOf(pencil);
    if (!node) return;
    if (panel && !panel.hidden && panelTarget === node.dataset.note && anchor === pencil) close();
    else open(node.dataset.note, node.dataset.noteLabel || node.dataset.note, pencil);
  }, true);

  function start() {
    mountToggle();
    decorateAll();
    new MutationObserver(records => {
      for (const m of records) {
        if (m.type === 'attributes') { if (m.target.matches('[data-note]')) decorate(m.target); continue; }
        m.addedNodes.forEach(n => { if (n.nodeType === 1 && !n.classList.contains('an-pencil')) decorateAll(n); });
        // A host whose text was rewritten (el.textContent = …) lost its pencil; put it back.
        const host = m.target.nodeType === 1 && !m.target.closest('.an-pencil') && m.target.closest('[data-note]');
        if (host && !hostOf(host).querySelector(':scope > .an-pencil')) decorate(host);
      }
    }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-note', 'data-note-label'] });
    paint();
    load();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
