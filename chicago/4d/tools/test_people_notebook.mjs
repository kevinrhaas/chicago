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
  const page = await browser.newPage(); const errors = []; page.on('pageerror', error => errors.push(error.message));
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
  assert.deepEqual(errors, []);
  console.log('PEOPLE NOTEBOOK PASS — real 1835 record and citations, identity callback, save, deduplication, visible denied-storage error, no page errors');
} finally { await browser.close(); server.close(); }
