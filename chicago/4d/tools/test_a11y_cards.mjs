// T-3671: the cards a visitor opens, by keyboard and screen reader (WCAG 2.1 AA). Real card
// markup, CSS and modules in Playwright at 390x780 and 1280x800; no town is loaded.
//   the building card (popup.js): a dialog named by its title (4.1.2); focus on the title as it
//     opens and back to its opener, or to the scene canvas, as it closes (2.4.3); Esc closes;
//     its tab strip is one Tab stop with Left/Right/Home/End (4.1.2, 2.1.1); a redraw keeps the
//     focused tab; each "why" says what it opens (aria-expanded, aria-controls)
//   Inspect's tab strip (apps/inspect-view.js): the same arrow keys
//   the story and question cards: named, focused on open, focus back on close, Esc closes;
//     an answered question says so in words (1.1.1)
//   a locked term's meaning (term-tips.js): Esc dismisses the meaning and leaves the card (1.4.13)
//   the field notebook: every field labelled, each entry's note and keys tied to its title (3.3.2)
//   the person card: named by the person's name; every card image has alt text (1.1.1)
// C4D_SHOTS=dir saves the pictures; C4D_SHOTS_ONLY=1 takes them without asserting (a "before").
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const index = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const meta = index.match(/<meta name="viewport"[^>]+>/)[0];
const imports = index.match(/<script type="importmap">[\s\S]*?<\/script>/)?.[0] ?? '';
const popupTag = index.match(/<aside id="popup"[^>]*><\/aside>/)[0];
const shots = process.env.C4D_SHOTS ?? '';
const only = !!process.env.C4D_SHOTS_ONLY;
const tag = process.env.C4D_SHOTS_TAG ?? 'after';
if (shots) fs.mkdirSync(shots, { recursive: true });
const check = only ? () => {} : (v, m) => assert.ok(v, m);
const same = only ? () => {} : (a, b, m) => assert.deepEqual(a, b, m);

const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#237279"/></svg>';
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><html lang="en" data-theme="dark"><head>${meta}${imports}
      <link rel="stylesheet" href="/css/walk.css"><link rel="stylesheet" href="/css/drawer.css">
      <link rel="stylesheet" href="/css/navigator.css"><link rel="stylesheet" href="/css/inspect.css">
      <link rel="stylesheet" href="/css/card.css"><link rel="stylesheet" href="/css/field-notebook.css"><link rel="stylesheet" href="/css/skins.css">
      <style>body{margin:0;background:#1d3a40} #view{position:fixed;inset:0;width:100%;height:100%;background:#28626b}
      #openers{position:fixed;left:8px;top:8px;display:flex;gap:6px;flex-wrap:wrap;z-index:1;max-width:60%}
      #insp,#nb{display:none} body.show-insp #insp, body.show-nb #nb{display:block;position:fixed;inset:0;overflow:auto;background:var(--panel-solid,#13262b);color:var(--ink,#fff);padding:12px;z-index:5}</style>
      </head><body><canvas id="view"></canvas>
      <div id="openers"><button id="open-card" type="button">Open the fixture house</button>
      <button id="open-tale" type="button">Tell me a story</button><button id="open-ask" type="button">Ask a question</button></div>
      <div id="insp"></div><div id="nb"></div>
      ${popupTag}</body></html>`); return;
  }
  if (url.pathname.endsWith('.svg')) { res.writeHead(200, { 'Content-Type': 'image/svg+xml' }); res.end(svg); return; }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript'
      : file.endsWith('.json') ? 'application/json' : file.endsWith('.html') ? 'text/html' : 'text/css' });
    res.end(err ? '' : bytes);
  });
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
const active = (page) => page.evaluate(() => {
  const a = document.activeElement;
  return { tag: a?.tagName, id: a?.id ?? '', tab: a?.dataset?.popTab ?? a?.dataset?.inspTab ?? '', text: (a?.textContent ?? '').trim().slice(0, 60),
    inPopup: !!a?.closest?.('#popup'), inTale: !!a?.closest?.('.tale-card') };
});
const t0 = Date.now();
let checks = 0;
try {
  for (const width of [390, 1280]) {
    const phone = width === 390;
    const context = await browser.newContext({ viewport: { width, height: phone ? 780 : 800 },
      isMobile: phone, hasTouch: phone, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(origin);
    await page.evaluate(async () => {
      const { createPopup } = await import('/js/popup.js');
      const record = { id: 'fixture_house', sidecar: {
        id: 'fixture_house', name: 'Fixture house', phase: 'as_built',
        summary: 'A one-room frame house on the fixture street.',
        placement: { symbolic_location: 'Fixture street', position_confidence: 'inferred', position_sources: ['src_a'], position_note: 'Placed from the fixture plat.' },
        attributes: {
          storeys: { value: 1, confidence: 'attested', sources: ['src_a'], note: 'The fixture plat shows one storey.' },
          roof_form: { value: 'gable', confidence: 'inferred', sources: ['src_a'], note: 'A gable is the common form on this street.' },
          finish: { value: 'clapboard', confidence: 'reconstructed', sources: [], note: '' },
        },
        citations: [{ source_id: 'src_a', citation: 'A fixture plat of the town, 1835.' }],
        research_note: 'The fixture record says what it rests on.',
      } };
      window.fxRecord = record;
      const root = document.getElementById('popup');
      const popup = window.fxPopup = createPopup(root, {});
      // main.js's own Escape: a card open is closed (T-0108).
      window.addEventListener('keydown', (e) => { if (e.code === 'Escape' && popup.openId) popup.close(); });
      document.getElementById('open-card').addEventListener('click', () => popup.show(record));
    });

    // ---- the building card -------------------------------------------------------------- //
    await page.focus('#open-card');
    await page.keyboard.press('Enter');
    const dialog = await page.evaluate(() => {
      const root = document.getElementById('popup');
      const by = root.getAttribute('aria-labelledby');
      return { role: root.getAttribute('role'), by, name: by ? document.getElementById(by)?.textContent?.trim() : null,
        live: root.getAttribute('aria-live') };
    });
    same(dialog.role, 'dialog', 'the card is a dialog'); checks++;
    same(dialog.name, 'Fixture house', 'the dialog is named by its title'); checks++;
    same(dialog.live, null, 'the card is not a live region read whole on every redraw'); checks++;
    let a = await active(page);
    same([a.tag, a.id], ['H2', 'pop-title'], 'opening the card puts focus on its title'); checks++;
    const stops = await page.evaluate(() => [...document.querySelectorAll('#popup .pop-tab')].filter((t) => t.tabIndex === 0).map((t) => t.dataset.popTab));
    same(stops, ['evidence'], 'the tab strip is one Tab stop, on the selected tab'); checks++;
    // Tab along the card to the strip.
    for (let i = 0; i < 40 && (await active(page)).tab === ''; i++) await page.keyboard.press('Tab');
    a = await active(page);
    same(a.tab, 'evidence', 'Tab reaches the strip on its selected tab'); checks++;
    await page.keyboard.press('ArrowRight');
    a = await active(page);
    const sel = await page.evaluate(() => {
      const t = document.activeElement, pane = document.getElementById(t.getAttribute('aria-controls'));
      return { selected: t.getAttribute('aria-selected'), shown: !!pane && !pane.hidden,
        labelled: pane?.getAttribute('aria-labelledby') === t.id && !!t.id,
        others: [...document.querySelectorAll('#popup .pop-pane')].filter((p) => !p.hidden).length };
    });
    same(a.tab, 'images', 'Right arrow moves to the next tab'); checks++;
    same(sel, { selected: 'true', shown: true, labelled: true, others: 1 }, 'the tab moved to is selected and its panel, labelled by it, is the one shown'); checks++;
    if (shots) {
      await page.evaluate(() => { document.getElementById('popup').scrollTop = document.querySelector('#popup .pop-tabs').offsetTop - 80; });
      await page.screenshot({ path: path.join(shots, `cards-building-tabs-${width}-${tag}.png`) });
    }
    await page.keyboard.press('End');
    same((await active(page)).tab, 'record', 'End goes to the last tab'); checks++;
    await page.keyboard.press('ArrowRight');
    same((await active(page)).tab, 'evidence', 'Right arrow from the last wraps to the first'); checks++;
    await page.keyboard.press('ArrowLeft');
    same((await active(page)).tab, 'record', 'Left arrow from the first wraps to the last'); checks++;
    await page.keyboard.press('Home');
    same((await active(page)).tab, 'evidence', 'Home goes to the first tab'); checks++;
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
    await page.evaluate(() => fxPopup.setLiberties([]));   // the liberties land: the card redraws
    a = await active(page);
    same([a.tab, a.inPopup], ['liberties', true], 'a redraw keeps focus on the tab it was on'); checks++;
    await page.keyboard.press('Home');
    const why = await page.evaluate(() => {
      const b = document.querySelector('#popup .pop-pane:not([hidden]) [data-toggle-note]');
      const before = { expanded: b?.getAttribute('aria-expanded'), controls: !!document.getElementById(b?.getAttribute('aria-controls') ?? '') };
      b?.click();
      const note = document.getElementById(b?.getAttribute('aria-controls') ?? '');
      return { before, after: b?.getAttribute('aria-expanded'), shown: !!note && !note.hidden };
    });
    same(why, { before: { expanded: 'false', controls: true }, after: 'true', shown: true }, 'a "why" says what it opens and whether it is open'); checks++;
    await page.keyboard.press('Escape');
    a = await active(page);
    check(await page.locator('#popup').isHidden(), 'Esc closes the card'); checks++;
    same(a.id, 'open-card', 'closing gives focus back to what opened the card'); checks++;
    // A card opened from the scene (nothing focused) gives focus to the scene canvas.
    await page.evaluate(() => { document.activeElement?.blur(); fxPopup.show(fxRecord); });
    same((await active(page)).id, 'pop-title', 'a card opened from the scene takes focus too'); checks++;
    await page.keyboard.press('Escape');
    same((await active(page)).id, 'view', 'a card opened from the scene gives focus back to the scene'); checks++;
    // A locked term's meaning: Esc dismisses it and leaves the card open (1.4.13).
    await page.evaluate(async () => {
      const { markTerms } = await import('/js/term-tips.js');
      fxPopup.show(fxRecord);
      const p = document.createElement('p'); p.id = 'term-host'; p.textContent = 'Every grade is shown in the Confidence view.';
      document.querySelector('#popup .pop-head').append(p);
      markTerms(p);
    });
    await page.locator('#term-host .locked-term').focus();
    await page.keyboard.press('Enter');
    check(await page.locator('#term-tip').isVisible(), 'the term\'s meaning opens from the keyboard'); checks++;
    await page.locator('#term-tip').hover();
    check(await page.locator('#term-tip').isVisible(), 'the meaning stays while it is hovered'); checks++;
    await page.keyboard.press('Escape');
    check(await page.locator('#term-tip').isHidden(), 'Esc dismisses the meaning'); checks++;
    check(await page.locator('#popup').isVisible(), 'the same Esc leaves the card open'); checks++;
    same((await active(page)).text, 'Confidence view', 'and focus is back on the term'); checks++;
    await page.keyboard.press('Escape');
    check(await page.locator('#popup').isHidden(), 'the next Esc closes the card'); checks++;
    // Every picture in a card says what it shows.
    const missingAlt = await page.evaluate(() => [...document.querySelectorAll('#popup img, .insp-person-card img')].filter((i) => !i.hasAttribute('alt')).length);
    same(missingAlt, 0, 'no card image without alt'); checks++;

    // ---- Inspect's tab strip -------------------------------------------------------------- //
    await page.evaluate(async () => {
      const view = await import('/js/apps/inspect-view.js');
      document.body.classList.add('show-insp');
      const host = document.getElementById('insp');
      await view.mount(host, { selected: 'fixture_house', scene: { id: '1835' },
        actions: { record: () => fxRecord, cardSections: (id) => fxPopup.sections(fxRecord),
          peopleDirectory: () => ({ people: [{ id: 'p9', name: 'Fixture Resident', lives_at: 'fixture_house', relationship: 'head',
            household: 'hh9', household_name: 'The Fixture household at 1 Fixture Street', grade: 'attested' }] }) } });
    });
    await page.locator('#insp .insp-tab[aria-selected="true"]').focus();
    same((await active(page)).tab, 'overview', 'Inspect opens on Overview'); checks++;
    await page.keyboard.press('ArrowRight');
    a = await active(page);
    same(a.tab, 'people', 'Right arrow moves along Inspect\'s tabs'); checks++;
    same(await page.evaluate(() => document.activeElement.getAttribute('aria-selected')), 'true', 'and selects the tab'); checks++;
    await page.keyboard.press('End');
    const last = await page.evaluate(() => {
      const t = document.activeElement;
      const r = t.getBoundingClientRect();
      return { key: t.dataset.inspTab, selected: t.getAttribute('aria-selected'), onScreen: r.right <= innerWidth + 1 && r.left >= -1,
        stops: [...document.querySelectorAll('#insp .insp-tab')].filter((b) => b.tabIndex === 0).length };
    });
    same([last.key, last.selected], ['sources', 'true'], 'End goes to the last tab shown (Research is hidden unless Expert research is on)'); checks++;
    check(last.onScreen, 'a tab moved to on a narrow strip is scrolled into view'); checks++;
    same(last.stops, 1, 'Inspect\'s strip is one Tab stop'); checks++;
    if (shots) await page.screenshot({ path: path.join(shots, `cards-inspect-tabs-${width}-${tag}.png`) });
    await page.keyboard.press('Home');
    same((await active(page)).tab, 'overview', 'Home goes back to Overview'); checks++;
    // A person in the house opens by keyboard (the People tab's rows are keys), and Back
    // returns to their row (2.1.1, 2.4.3): a way to a person's card without the 3-D scene.
    await page.keyboard.press('ArrowRight');
    await page.locator('#insp [data-person-card="p9"]').waitFor();
    await page.locator('#insp [data-person-card="p9"]').focus();
    await page.keyboard.press('Enter');
    await page.locator('#insp .insp-person-card').waitFor();
    a = await active(page);
    check(/Back/.test(a.text) || (await page.evaluate(() => document.activeElement.hasAttribute('data-person-back'))), `a person's card opens with focus on its Back key (${a.text})`); checks++;
    same(await page.evaluate(() => { const c = document.querySelector('#insp .insp-person-card'); return document.getElementById(c.getAttribute('aria-labelledby'))?.textContent; }),
      'Fixture Resident', 'the person card is named by the person'); checks++;
    await page.keyboard.press('Enter');
    same(await page.evaluate(() => document.activeElement.dataset.personCard), 'p9', 'Back returns focus to the person\'s row'); checks++;
    await page.evaluate(() => document.body.classList.remove('show-insp'));

    if (only) { await context.close(); continue; }   // the pictures are taken

    // ---- the story and question cards -------------------------------------------------- //
    await page.evaluate(async () => {
      const { createTaleCard } = await import('/js/tale-card.js');
      const { createAskCard } = await import('/js/ask-card.js');
      const tale = window.fxTale = createTaleCard({});
      const ask = window.fxAsk = createAskCard({});
      document.getElementById('open-tale').onclick = () => tale.show({ teller: 'Fixture Teller', personId: 'p1',
        tale: { id: 't1', title: 'The fixture flood', text: ['The river rose over the fixture street.'] } });
      document.getElementById('open-ask').onclick = () => ask.show({ teller: 'Fixture Teller', personId: 'p1', asks: [
        { id: 'a1', q: 'Where do you live?', a: ['On the fixture street.'], more: [{ q: 'Since when?', a: ['Since the spring.'] }] },
        { id: 'a2', q: 'What is your work?', a: ['I keep the fixture store.'] }] });
    });
    await page.focus('#open-tale');
    await page.keyboard.press('Enter');
    const taleName = await page.evaluate(() => {
      const c = document.querySelector('.tale-card:not(.ask-card)');
      return { role: c.getAttribute('role'), name: (c.getAttribute('aria-labelledby') ?? '').split(' ').map((id) => document.getElementById(id)?.textContent).join(' ') };
    });
    same(taleName, { role: 'dialog', name: 'Fixture Teller tells you a story The fixture flood' }, 'the story card is a dialog named by its teller and title'); checks++;
    a = await active(page);
    same([a.inTale, a.text], [true, 'The fixture flood'], 'opening the story puts focus on its title'); checks++;
    await page.keyboard.press('Escape');
    same((await active(page)).id, 'open-tale', 'Esc closes the story and gives focus back'); checks++;

    await page.focus('#open-ask');
    await page.keyboard.press('Enter');
    a = await active(page);
    same([a.inTale, a.text], [true, 'Where do you live?'], 'the questions open on the first question'); checks++;
    same(await page.evaluate(() => { const c = document.querySelector('.ask-card'); return document.getElementById(c.getAttribute('aria-labelledby'))?.textContent; }),
      'Ask Fixture Teller', 'the question card is named "Ask <name>"'); checks++;
    await page.keyboard.press('Enter');
    a = await active(page);
    same([a.inTale, a.text], [true, 'Where do you live?'], 'an answer puts focus on the question asked, at the head of the answer'); checks++;
    await page.evaluate(() => document.querySelector('.ask-card .ask-follow').focus());
    await page.keyboard.press('Enter');
    same((await active(page)).text, 'Since when?', 'a follow-up keeps focus in the card, on what was asked'); checks++;
    await page.evaluate(() => document.querySelector('.ask-card .ask-back').focus());
    await page.keyboard.press('Enter');
    a = await active(page);
    check(a.inTale && /^Where do you live\?/.test(a.text) && /\(asked\)/.test(a.text), `Other questions goes back to the question answered, which says it was asked (${a.text})`); checks++;
    await page.keyboard.press('Escape');
    same((await active(page)).id, 'open-ask', 'Esc closes the questions and gives focus back'); checks++;

    // ---- the person card ------------------------------------------------------------------ //
    const person = await page.evaluate(async () => {
      const { renderPersonCard } = await import('/js/person-card.js');
      const m = { id: 'p1', name: 'Fixture Person', back: 'People', grade: 'attested', place: 'Fixture street', facts: [], story: [],
        caveats: [], sheetNotes: [], sources: [], read: false,
        portrait: { image: '/x.svg', caption: 'a fixture daguerreotype', grade: 'attested' } };
      const card = renderPersonCard(document, m);
      document.getElementById('insp').append(card);
      const imgs = [...card.querySelectorAll('img')].map((i) => i.alt);
      return { name: document.getElementById(card.getAttribute('aria-labelledby'))?.textContent, imgs };
    });
    same(person.name, 'Fixture Person', 'the person card is named by the person'); checks++;
    check(person.imgs.length === 1 && person.imgs[0].includes('Fixture Person'), 'a portrait\'s alt names the person'); checks++;

    // ---- the field notebook ---------------------------------------------------------------- //
    const nb = await page.evaluate(async () => {
      localStorage.clear();
      const { mountFieldNotebook } = await import('/js/field-notebook-view.js');
      const { fieldNotebook } = await import('/js/field-notebook.js');
      const host = document.getElementById('nb');
      mountFieldNotebook(host);
      fieldNotebook.add({ kind: 'note', title: 'At the fixture store', text: 'Busy morning.', year: '1835' });
      host.querySelector('details').open = true;
      const unlabelled = [...host.querySelectorAll('input, textarea, select')].filter((f) => !f.closest('label') && !f.getAttribute('aria-label') && !f.labels?.length).length;
      const entry = host.querySelector('.field-notebook-entry');
      const desc = (n) => document.getElementById(n?.getAttribute('aria-describedby') ?? '')?.textContent;
      return { unlabelled, note: desc(entry?.querySelector('textarea')), keys: [...entry.querySelectorAll('.field-notebook-actions button')].map(desc) };
    });
    same(nb.unlabelled, 0, 'every notebook field has a label'); checks++;
    same(nb.note, 'At the fixture store', 'an entry\'s note field says which entry it is'); checks++;
    same(nb.keys, ['At the fixture store', 'At the fixture store'], 'an entry\'s keys say which entry they act on'); checks++;

    if (!only) assert.deepEqual(errors, [], `no page errors at ${width}`);
    await context.close();
  }
  if (!only) console.log(`test_a11y_cards: ${checks} checks passed at 390 and 1280 in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  else console.log(`test_a11y_cards: pictures only (${tag})`);
} finally {
  await browser.close();
  server.close();
}
