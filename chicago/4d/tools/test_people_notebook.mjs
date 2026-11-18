/** The legacy 1835 card saves only its selected person, with the real citation join;
 * failed browser storage is stated on the card and never reported as a save. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { createRequire } from 'node:module';
import { notebookPersonEntry } from '../renderers/web/js/people.js';
const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve(new URL('..', import.meta.url).pathname);
const dataRoot = process.env.C4D_TEST_ROOT || root;
const read = relative => JSON.parse(fs.readFileSync(path.join(dataRoot, relative)));
const row = read('data/sidecars/1835/people.json').people.find(person => person.id === 'hogan_john_s_c');
const household = read(`data/residents/${row.file}`);
const citations = read('data/sidecars/1835/residents_sources.json').citations;
const person = household.persons.find(person => person.id === row.id);
const entry = notebookPersonEntry(row, household, new Map(Object.entries(citations)), '1835');
assert.equal(entry.person, row.id); assert.equal(entry.title, person.name); assert.equal(entry.year, '1835');
assert.deepEqual(entry.sources.map(source => source.id), person.sources);
assert(entry.sources.every(source => source.title && source.title !== source.id));
assert.equal(notebookPersonEntry({ ...row, id: 'not-in-this-household' }, household, citations, '1835'), null);
assert.equal(notebookPersonEntry(row, null, citations, '1835'), null);
const server = http.createServer((req, res) => {
  const pathname = new URL(req.url, 'http://local').pathname;
  if (pathname === '/') { res.setHeader('Content-Type', 'text/html'); res.end('<!doctype html><html><body><section class="panel-body"><div id="people-directory"></div></section></body></html>'); return; }
  const prefix = pathname.startsWith('/data/') ? dataRoot : path.join(root, 'renderers/web');
  const file = path.resolve(prefix, `.${pathname}`);
  if (!file.startsWith(`${prefix}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => { res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : 'application/json' }); res.end(err ? '' : bytes); });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium', args: ['--no-sandbox'] });
try {
  const context = await browser.newContext();
  const page = await context.newPage(); const errors = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/`);
  for (const refuse of [false, true]) {
    const result = await page.evaluate(async ({ row, refuse }) => {
      const { mountPeople } = await import('/js/people.js');
      const { createFieldNotebook } = await import('/js/field-notebook.js');
      let raw = null;
      const notebook = createFieldNotebook({ storage: { getItem: () => raw,
        setItem: (_, value) => { if (refuse) throw new Error('Storage blocked'); raw = value; } } });
      const selections = [];
      const directory = await mountPeople({ mount: document.getElementById('people-directory'),
        people: { people: [row], counts: { people: 1, households: 1 }, vocabulary: {} }, registry: new Map(),
        sceneId: '1835', dataBase: new URL('/data/', location.href), notebook,
        onPersonSelected: (id, name) => selections.push({ id, name }) });
      await directory.open(row.id);
      const button = document.querySelector('.people-notebook-save');
      const disabled = button.disabled;
      button.click();
      const status = document.querySelector('.people-notebook-status').textContent;
      button.click();
      return { disabled, status, afterSecond: document.querySelector('.people-notebook-status').textContent,
        entries: notebook.read().entries, selections };
    }, { row, refuse });
    assert.equal(result.disabled, false);
    assert.deepEqual(result.selections, [{ id: row.id, name: row.name }]);
    if (refuse) {
      assert.match(result.status, /could not save/); assert.equal(result.entries.length, 0);
    } else {
      assert.match(result.status, /Saved/); assert.match(result.afterSecond, /already/);
      assert.equal(result.entries.length, 1); assert.equal(result.entries[0].person, row.id);
      assert.deepEqual(result.entries[0].sources.map(source => source.id), person.sources);
    }
  }

  // Use a second real page on the same origin: storage events, unlike same-tab
  // writes, are what refresh a notebook while its reader has unsaved edits.
  const other = await page.context().newPage();
  other.on('pageerror', error => errors.push(error.message));
  await other.goto(`http://127.0.0.1:${server.address().port}/`);
  try {
    await page.evaluate(async () => {
      const { mountFieldNotebook } = await import('/js/field-notebook-view.js');
      const { createFieldNotebook, NOTEBOOK_KEY } = await import('/js/field-notebook.js');
      localStorage.removeItem(NOTEBOOK_KEY);
      window.notebookReadsBlocked = false;
      const notebook = createFieldNotebook({ storage: {
        getItem(key) { if (window.notebookReadsBlocked) throw new DOMException('Storage blocked', 'SecurityError'); return localStorage.getItem(key); },
        setItem: (key, value) => localStorage.setItem(key, value),
      } });
      const host = document.createElement('section'); host.id = 'notebook-draft-fixture'; document.body.append(host);
      window.notebookDraftFixture = mountFieldNotebook(host, { notebook });
      host.querySelector('details').open = true;
      window.notebookStorageEvents = 0;
      window.notebookCountStorage = e => { if (e.key === NOTEBOOK_KEY) window.notebookStorageEvents++; };
      window.addEventListener('storage', window.notebookCountStorage);
    });
    let revision = 0;
    const writeOther = async (entries, raw = null) => {
      const before = await page.evaluate(() => window.notebookStorageEvents);
      const value = raw ?? JSON.stringify({ version: 1, revision: ++revision, entries });
      await other.evaluate(value => localStorage.setItem('chicago4d.notebook.v1', value), value);
      await page.waitForFunction(before => window.notebookStorageEvents > before, before);
    };
    const entryFor = (id, text) => ({ id, kind: 'note', title: id, text, year: '1835', sources: [] });
    const noteFor = id => page.locator(`[data-notebook-id="${id}"] textarea`);
    const stable = entryFor('stable-draft', 'Original stored text');
    const removed = entryFor('removed-draft', 'Original removable text');
    await writeOther([stable, removed]);
    await noteFor(stable.id).fill('Keep my unsaved draft');
    await noteFor(removed.id).fill('This draft will belong to a deleted entry');

    await writeOther([{ ...stable, text: 'External edit while I type' }, removed]);
    assert.equal(await noteFor(stable.id).inputValue(), 'Keep my unsaved draft', 'valid external refresh preserves a live unsaved draft');

    await page.evaluate(() => { window.notebookReadsBlocked = true; });
    await writeOther([stable, removed]);
    assert.match(await page.locator('#notebook-draft-fixture [role="status"]').textContent(), /could not save/);
    assert.equal(await page.locator('#notebook-draft-fixture .field-notebook-entry').count(), 0);
    await page.evaluate(() => { window.notebookReadsBlocked = false; });
    await writeOther([stable, removed]);
    assert.equal(await noteFor(stable.id).inputValue(), 'Keep my unsaved draft', 'temporary blocked storage does not prove a draft was deleted');

    for (const malformed of ['{', JSON.stringify({ version: 2, entries: [] })]) {
      await writeOther([], malformed);
      assert.equal(await page.locator('#notebook-draft-fixture .field-notebook-entry').count(), 0);
      assert.match(await page.locator('#notebook-draft-fixture [role="status"]').textContent(), /could not (save|be read)/);
      await writeOther([stable, removed]);
      assert.equal(await noteFor(stable.id).inputValue(), 'Keep my unsaved draft', 'unreadable storage preserves the last live draft');
    }

    await writeOther([stable]);
    assert.equal(await noteFor(removed.id).count(), 0, 'successful external deletion removes its editor');
    await writeOther([stable, { ...removed, text: 'Freshly restored persisted text' }]);
    assert.equal(await noteFor(removed.id).inputValue(), 'Freshly restored persisted text', 'restoring a deleted ID must not revive its stale draft');
    assert.equal(await noteFor(stable.id).inputValue(), 'Keep my unsaved draft', 'pruning removed IDs leaves live drafts intact');

    // Two batches pass 100 distinct draft IDs while each persisted notebook stays
    // below the entry cap. Neither deleted batch may survive in the draft cache.
    for (let batch = 0; batch < 2; batch++) {
      const churn = Array.from({ length: 60 }, (_, i) => entryFor(`churn-${batch}-${i}`, 'Stored before deletion'));
      await writeOther([stable, ...churn]);
      await page.evaluate(ids => {
        for (const id of ids) {
          const note = document.querySelector(`[data-notebook-id="${id}"] textarea`);
          note.value = `Unsaved ${id}`; note.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, churn.map(e => e.id));
      await writeOther([stable]);
      await writeOther([stable, ...churn.map(e => ({ ...e, text: `Fresh ${e.id}` }))]);
      const restored = await page.locator('#notebook-draft-fixture .field-notebook-entry').evaluateAll(articles =>
        Object.fromEntries(articles.map(article => [article.dataset.notebookId, article.querySelector('textarea').value])));
      for (const e of churn) assert.equal(restored[e.id], `Fresh ${e.id}`, 'cross-tab churn must not retain a removed entry draft');
      assert.equal(restored[stable.id], 'Keep my unsaved draft');
    }
  } finally {
    await page.evaluate(() => {
      window.notebookDraftFixture?.destroy();
      window.removeEventListener('storage', window.notebookCountStorage);
      document.getElementById('notebook-draft-fixture')?.remove();
    });
    await other.close();
  }
  assert.deepEqual(errors, []);
  console.log('PEOPLE NOTEBOOK PASS — real 1835 record/citations, identity/save/deduplication, denied storage, cross-tab live-draft preservation and deleted-ID pruning over 120 IDs, no page errors');
} finally { await browser.close(); server.close(); }
