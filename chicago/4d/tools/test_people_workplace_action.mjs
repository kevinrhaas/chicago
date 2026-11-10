// The 1835 card's workplace remains usable when Find/Follow precede it.
// Exercise the native action builders and native click handler in browser DOM;
// no town rendering or claim about the complete release smoke is made here.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const peopleSource = fs.readFileSync(new URL('../renderers/web/js/people.js', import.meta.url), 'utf8');
const smokeSource = fs.readFileSync(new URL('./smoke_renderer.mjs', import.meta.url), 'utf8');
const row = JSON.parse(fs.readFileSync(new URL('../data/sidecars/1835/people.json', import.meta.url), 'utf8'))
  .people.find(p => p.id === 'hogan_john_s_c');
assert.equal(row.works_at, 'hogan_store');
const begin = peopleSource.indexOf('  function goButton(');
const end = peopleSource.indexOf('\n  /**\n   * The re-admission', begin);
const clickBegin = peopleSource.indexOf("  cardEl.addEventListener('click', (ev) => {");
const clickEnd = peopleSource.indexOf('\n  });\n\n  paint();', clickBegin);
assert(begin >= 0 && end > begin && clickBegin >= 0 && clickEnd > clickBegin);
const builders = peopleSource.slice(begin, end);
const handler = peopleSource.slice(clickBegin, clickEnd + '\n  });'.length);
// Use the smoke's actual selectors, so reverting either one reproduces the bug.
const selector = smokeSource.match(/const go = card\?\.querySelector\('([^']+)'\)/)?.[1];
const clickSelector = smokeSource.match(/await clickChrome\('(\#people-card \.people-go[^']*)'\)/)?.[1];
assert(selector && clickSelector);
let pw;
try { pw = await import('playwright'); }
catch { pw = await import(path.join(process.env.NODE_PATH, 'playwright/index.mjs')); }
const browser = await pw.chromium.launch({ headless: true,
  executablePath: process.env.PW_EXECUTABLE ?? '/usr/bin/chromium', args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  for (const present of [false, true]) {
    await page.setContent('<main id="people-card"></main>');
    await page.evaluate(({ builders, handler, row, present }) => {
      const cardEl = document.getElementById('people-card');
      const inTown = () => present, onFollow = () => { throw Error('Workplace click must not follow'); };
      const buildingTitle = id => id === 'hogan_store' ? "Hogan's store" : null;
      const escapeHtml = value => String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
      cardEl.innerHTML = new Function('inTown', 'onFollow', 'buildingTitle', 'escapeHtml', 'r',
        builders + '\nreturn actionsHtml(r);')(inTown, onFollow, buildingTitle, escapeHtml, row);
      const state = { open: row.id }, byId = new Map([[row.id, row]]);
      const onGoTo = target => { window.__workplaceTarget = target; };
      window.__workplaceTarget = null;
      new Function('cardEl', 'state', 'byId', 'onGoTo', 'onFollow', 'onBusiness', 'close', handler)(
        cardEl, state, byId, onGoTo, onFollow, () => {}, () => {});
    }, { builders, handler, row, present });
    const actual = await page.locator(selector).evaluate(el => ({
      disabled: el.disabled, structure: el.dataset.structure, text: el.textContent.trim(),
    }));
    assert.equal(actual.disabled, false);
    assert.equal(actual.structure, 'hogan_store');
    assert.match(actual.text, /Go to where they worked/);
    // The old ambiguous selector is a real negative control in both cases:
    // away it is disabled; present it is Find, never the workplace action.
    assert.equal(await page.locator('.people-go').first().getAttribute('data-structure'), null);
    assert.equal(await page.locator('.people-find').isDisabled(), !present);
    await page.locator(clickSelector).click();
    assert.deepEqual(await page.evaluate(() => window.__workplaceTarget), {
      kind: 'person', id: row.id, label: row.name, lives_at: null, works_at: 'hogan_store',
    });
  }
  console.log('PEOPLE WORKPLACE ACTION PASS: real 1835 Hogan record, native action HTML and click handler, smoke selectors choose enabled workplace with Find/Follow present or disabled; old selector rejected');
} finally { await browser.close(); }
