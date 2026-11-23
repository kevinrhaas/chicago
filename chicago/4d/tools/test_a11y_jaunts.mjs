#!/usr/bin/env node
// T-3671 — WCAG 2.1 AA for jaunts, their narration and the Field Check tour. Real markup, CSS
// and modules (jaunt-panel.js, narration.js with a stand-in media element, jaunt-menu.js,
// jaunt-cards.js, tour-overlay.js), no town: 390x780 phone and 1280x800 desktop.
//
//  1.2.1  a voiced opening, stop and ending show the words the voice says, lit while it reads;
//         an age tab is read in that telling's own recording, or in none (T-3735)
//  1.4.2  Pause / Resume narration on the controls and on the collapsed bar, while a voice speaks
//  2.2.1  the closing scene's own clock is held once the visitor touches or keys in the panel
//  4.1.3  one polite status line says started / arrived / closing / complete, once each
//  2.1.1, 2.1.2, 2.4.3, 4.1.2  named keys, a progressbar, Esc on road notes and the stand-in
//         card, the menu's list, its mode radios on the arrows, and the tour card taking focus,
//         ending on Esc (not on its Release step) and giving focus back
//
// Pictures: C4D_TEST_OUT=<dir> saves jaunts-other-age-<width>-after.png there.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { createClosingClock } from '../renderers/web/js/jaunt-pace.js';
const { chromium } = createRequire(import.meta.url)('playwright');

// ---- 2.2.1 in node: the closing clock waits while the visitor holds the scene.
{
  let t = 0, held = true, done = 0;
  const clock = createClosingClock({ now: () => t, voice: { playing: () => false, ended: () => false }, hold: () => held, finish: () => done++ });
  clock.update({ phase: 'closing', session: 1, leg: 3, outcome: { text: 'Short ending.' } });
  t = 60; assert.equal(clock.tick(), false, 'a held closing scene does not end on its clock'); assert.equal(done, 0);
  held = false; assert.equal(clock.tick(), true, 'let go, it ends'); assert.equal(done, 1);
  console.log('PASS 2.2.1 closing clock: held while the visitor is at the scene');
}

const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const index = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const meta = index.match(/<meta name="viewport"[^>]+>/)[0];
const imports = index.match(/<script type="importmap">[\s\S]*?<\/script>/)[0];
const tourMarkup = index.match(/<div id="tour" class="tour" hidden>[\s\S]*?\n<\/div>\n/)[0];
const out = process.env.C4D_TEST_OUT;
if (out) fs.mkdirSync(out, { recursive: true });

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><html lang="en" data-skin="control-room"><head><meta charset="utf-8">${meta}${imports}
      <link rel="stylesheet" href="/css/walk.css"><link rel="stylesheet" href="/css/tour.css"></head>
      <body><button id="outside" style="position:fixed;top:0;right:0">Outside control</button>
      <section id="popup" hidden></section>${tourMarkup}<div id="menu-host" style="position:fixed;inset:auto 0 0 auto;width:360px;max-height:50vh;overflow:auto"></div></body></html>`);
    return;
  }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript' : file.endsWith('.css') ? 'text/css' : 'application/octet-stream' });
    res.end(err ? '' : bytes);
  });
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox'] });
let failed = false;
try {
  for (const width of [390, 1280]) {
    const phone = width === 390;
    const context = await browser.newContext({ viewport: { width, height: phone ? 780 : 800 }, isMobile: phone, hasTouch: phone, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(origin);
    // ---- the rig: a two-stop jaunt, every part voiced, a stand-in media element and bus.
    await page.evaluate(async () => {
      const { createJauntPanel } = await import('/js/jaunt-panel.js');
      const { reduce, emptyState } = await import('/js/jaunts.js');
      const N = await import('/js/narration.js');
      const { jauntMeter } = await import('/js/jaunt-pace.js');
      const claim = (id) => ({ id, confidence: 'attested', text: `Claim ${id}.`, sources: [] });
      const jaunt = { id: 'a11y-walk', content_version: 1, title: 'A Morning Walk', scene: '1835', premise: 'Two corners.',
        default_mode: 'walk', allowed_modes: ['walk'], places: { s1: 'The Sauganash', s2: 'Hogan’s store', s3: 'The withheld door' },
        opening: { text: 'JAUNT: A MORNING WALK. A town of a few streets.\n\nTwo corners are enough to begin.' },
        stops: [
          { id: 'one', destination: { kind: 'structure', id: 's1' }, text: 'Begin outside the Sauganash, a white house with blue shutters.', evidence: ['c1'], links: [], next: 'two' },
          { id: 'two', destination: { kind: 'structure', id: 's2' }, since: 'An hour later', text: 'This is the old mail corner by Hogan’s store.', evidence: ['c2'], links: [], next: '$end' },
        ],
        endings: [{ id: 'end', default: true, completion_eligible: true, text: 'You have two corners to start from.' }],
        evidence: [claim('c1'), claim('c2')], keepsake: { title: 'A note', text: 'Two corners.' }, grade_band: '6-8' };
      // T-3735: its telling for ages 8-10, voiced too (its first stop's words differ).
      const younger = { ...jaunt, id: 'a11y-walk-grades-3-5', version_of: 'a11y-walk', grade_band: '3-5',
        stops: [{ ...jaunt.stops[0], text: 'Start at the hotel. It is white with blue shutters.' }, jaunt.stops[1]] };
      // ... and for ages 14-15, not voiced.
      const older = { ...jaunt, id: 'a11y-walk-grades-9-10', version_of: 'a11y-walk', grade_band: '9-10',
        stops: [{ ...jaunt.stops[0], text: 'Begin by the tavern, a white building with blue shutters.' }, jaunt.stops[1]] };
      const R = await import('/js/reading-level.js');
      R.addTable(R.tellingTable(jaunt, [younger, older]));
      const clips = {};
      for (const j of [jaunt, younger, older]) for (const s of N.narrationScripts(j)) {
        const sha = await N.textKey(s.text);
        clips[N.clipKey(sha, s.speaker)] ??= { text_sha256: sha, file: `narration/${j.id}-${s.part}-${s.id}.mp3`, bytes: 160000, output_format: 'mp3_44100_64' };
      }
      class FakeAudio extends EventTarget {
        constructor() { super(); this.paused = true; this.currentTime = 0; this.duration = 20; this.readyState = 4; this.src = ''; window.__media = this; }
        play() { this.paused = false; this.dispatchEvent(new Event('playing')); return Promise.resolve(); }
        pause() { this.paused = true; }
        removeAttribute() { this.src = ''; }
        load() {}
      }
      const ctx = { createMediaElementSource: () => ({ connect() {}, disconnect() {} }) };
      const narration = N.createNarration({ media: () => new FakeAudio(), speech: () => ({ ctx, bus: {}, audible: true }), voiced: (j) => j.id !== older.id,
        fetcher: async (url) => (String(url).endsWith('catalog.json') ? { ok: false } : { ok: true, json: async () => ({ version: 1, clips }) }) });
      const calls = [];
      let state;
      const panelRef = {};
      const act = (name) => (...args) => { calls.push(name); if (name === 'dismissContext') { state = { ...state, contextDismissed: true }; panelRef.panel.render(state); } };
      const actions = Object.fromEntries(['next', 'prev', 'end', 'menu', 'choose', 'revise', 'retry', 'detail', 'returnFromDetail', 'setMode', 'straight', 'resumeRide', 'dismissContext', 'replay', 'kindle', 'skip', 'finish', 'closeOverlay'].map(n => [n, act(n)]));
      const panel = panelRef.panel = createJauntPanel({ destinations: { byId: () => null }, actions, narration, tellings: () => [younger, older] });
      await narration.prepare(jaunt);
      window.__rig = { panel, narration, reduce, emptyState, jaunt, calls, jauntMeter,
        get state() { return state; }, set state(v) { state = v; panel.render(v); } };
    });
    const rig = (fn, arg) => page.evaluate(fn, arg);
    const status = () => rig(() => document.querySelector('[data-jaunt-status]')?.textContent ?? null);

    // ---- opening: the welcome is the transcript, lit as it is read; Pause holds the voice.
    await rig(() => { const r = window.__rig; r.state = r.reduce(r.emptyState(), { type: 'START', jaunt: r.jaunt, session: 1, mode: 'walk' }); });
    await page.waitForFunction(() => window.__rig.narration.state.playing === 'a11y-walk:opening:opening');
    let seen = await rig(() => {
      const p = document.getElementById('jaunt-panel'), keys = p.querySelector('[data-action="voice"]'), bar = p.querySelector('[data-action="bar-voice"]');
      const listen = p.querySelector('[data-action="listen"]');
      return { status: document.querySelector('[data-jaunt-status]')?.getAttribute('role'), live: document.querySelector('[data-jaunt-status]')?.getAttribute('aria-live'),
        outside: !p.contains(document.querySelector('[data-jaunt-status]')),
        voice: keys && !keys.hidden ? keys.getAttribute('aria-label') : null, barVoice: bar?.getAttribute('aria-label'),
        lit: [...p.querySelectorAll('.jaunt-welcome-story [data-voiced]')].map(el => el.classList.contains('jaunt-voicing')),
        fold: p.querySelector('[data-transcript="opening:opening"]')?.hidden, described: document.getElementById(listen?.getAttribute('aria-describedby'))?.textContent,
        names: ['prev', 'menu', 'end'].map(a => p.querySelector(`[data-action="${a}"]`).getAttribute('aria-label')) };
    });
    assert.equal(seen.status, 'status'); assert.equal(seen.live, 'polite'); assert(seen.outside, 'the status line stands outside the hidden-between-outings panel');
    assert.equal(await status(), 'Jaunt started: A Morning Walk. Flying to the start, The Sauganash.');
    assert.equal(seen.voice, 'Pause narration', '1.4.2: a Pause key while the opening is read');
    assert.equal(seen.barVoice, 'Pause narration', '1.4.2: and on the collapsed bar');
    assert.deepEqual(seen.lit, [true, true, true], '1.2.1: the title and both paragraphs are lit as the voice reads them');
    assert.equal(seen.fold, true, 'the card shows the voiced words, so no separate transcript is shown');
    assert.match(seen.described, /the words on this card/);
    assert.deepEqual(seen.names, ['Previous stop', 'Jaunts menu', 'End jaunt']);
    await page.locator('[data-action="voice"]').focus();
    await page.keyboard.press('Enter');
    seen = await rig(() => ({ paused: window.__rig.narration.paused, media: window.__media.paused, label: document.activeElement.getAttribute('aria-label'), action: document.activeElement.dataset.action }));
    assert.deepEqual(seen, { paused: true, media: true, label: 'Resume narration', action: 'voice' }, '1.4.2: Enter pauses, focus stays on the key');
    await page.keyboard.press('Enter');
    assert.deepEqual(await rig(() => ({ paused: window.__rig.narration.paused, media: window.__media.paused })), { paused: false, media: false }, 'and resumes');
    console.log(`PASS ${width} opening: transcript on the card, lit; Pause/Resume by keyboard; started said`);

    // ---- arrival at stop 1: said once; the stop's words are its transcript; another age's words put its voice away.
    await rig(() => { const r = window.__rig; r.narration.stop(); r.state = r.reduce(r.state, { type: 'ARRIVE', session: 1, leg: r.state.leg }); });
    await page.waitForFunction(() => window.__rig.narration.state.playing === 'a11y-walk:stop:one');
    assert.equal(await status(), 'Arrived at The Sauganash. Stop 1 of 2.');
    await rig(() => window.__rig.panel.meter(window.__rig.jauntMeter({ count: 2, index: 0, value: 0.5 })));
    seen = await rig(() => {
      const m = document.querySelector('#jaunt-panel .jaunt-controls .jaunt-meter');
      return { role: m.getAttribute('role'), text: m.getAttribute('aria-valuetext'), now: m.getAttribute('aria-valuenow') };
    });
    assert.deepEqual(seen, { role: 'progressbar', text: 'Stop 1 of 2, 25 percent of the jaunt', now: '25' });
    // A reading-age tab swaps the card's words in place (reading-level.js sayAt) and names the age
    // on the panel's body. T-3735 (the owner, 2026-11-23): the words of a telling with its own
    // recording are read in that recording, at once; words no voiced telling says have no voice.
    const tab = (age) => page.locator(`#jaunt-panel .reading-tab[data-reading-age="${age}"]`).click();
    assert.deepEqual(await rig(() => [...document.querySelectorAll('#jaunt-panel .reading-tab')].map(t => t.dataset.readingAge)), ['8-10', '11-13', '14-15'], 'the stop has a tab for each telling');
    await tab('8-10');
    await page.waitForFunction(() => /a11y-walk-grades-3-5-stop-one\.mp3$/.test(window.__media.src) && !window.__media.paused);
    seen = await rig(() => ({ playing: window.__rig.narration.state.playing, fold: document.querySelector('[data-transcript="stop:one"]')?.hidden,
      listen: (l => l?.dataset.action === 'listen' && !l.hidden)(document.querySelector('[data-transcript="stop:one"]')?.previousElementSibling), words: document.querySelector('#jaunt-panel [data-voiced="stop"]')?.textContent }));
    assert.deepEqual(seen, { playing: 'a11y-walk:stop:one', fold: true, listen: true, words: 'Start at the hotel. It is white with blue shutters.' },
      'an age with its own recording: that recording plays at once, its card its transcript');
    if (out) await page.screenshot({ path: path.join(out, `jaunts-other-age-${width}-after.png`) });
    await tab('14-15');
    await page.waitForFunction(() => window.__rig.narration.state.playing === null && !document.querySelector('[data-transcript="stop:one"]'));
    assert.equal(await rig(() => document.querySelectorAll('#jaunt-panel [data-action="listen"]').length), 1, 'an age with no recording: no voice, no Listen at the stop (only the opening\'s), no Transcript');
    await tab('11-13');
    await page.waitForFunction(() => /a11y-walk-stop-one\.mp3$/.test(window.__media.src) && !window.__media.paused);
    assert(await rig(() => document.querySelector('[data-transcript="stop:one"]').hidden), 'its own age: its own recording again, the card its transcript');
    console.log(`PASS ${width} stop: arrival said, progressbar named, an age tab plays that telling's own recording, or none`);

    // ---- the way on: road notes close on Esc; arrival moves focus to the stop's heading.
    await rig(() => { const r = window.__rig; r.narration.stop(); let s = r.reduce(r.state, { type: 'NEXT' });
      s = { ...s, context: { lines: [{ generated: true, text: 'Past the river.' }], passed: [] } }; r.state = s; });
    assert.equal(await status(), 'On the way to Hogan’s store, final stop, 2 of 2.');
    await page.locator('#jaunt-panel .jaunt-leg-notes .jaunt-notes-close').focus();
    assert.equal(await rig(() => document.activeElement.getAttribute('aria-label')), 'Dismiss road notes');
    await page.keyboard.press('Escape');
    seen = await rig(() => ({ dismissed: window.__rig.calls.includes('dismissContext'), notes: !!document.querySelector('#jaunt-panel .jaunt-leg-notes'),
      focus: document.activeElement?.closest('#jaunt-panel') ? document.activeElement.dataset.action || document.activeElement.className : null }));
    assert(seen.dismissed && !seen.notes, 'Esc dismisses the road notes'); assert(seen.focus, `focus stays on the outing (${seen.focus})`);
    await rig(() => { const r = window.__rig; r.state = r.reduce(r.state, { type: 'ARRIVE', session: 1, leg: r.state.leg }); });
    seen = await rig(() => ({ focus: document.activeElement.tagName + ':' + document.activeElement.textContent, voiced: document.querySelector('#jaunt-panel [data-voiced="stop"]')?.textContent }));
    assert.equal(seen.focus, 'H2:Hogan’s store', '2.4.3: arriving puts focus on the stop');
    assert.equal(seen.voiced, 'An hour later. This is the old mail corner by Hogan’s store.', 'its since is shown as it is read');
    assert.equal(await status(), 'Arrived at Hogan’s store. Final stop, 2 of 2.');
    // Collapsed, the bar keeps Pause.
    await page.waitForFunction(() => window.__rig.narration.state.playing === 'a11y-walk:stop:two');
    await rig(() => window.__rig.panel.collapse(true));
    seen = await rig(() => { const b = document.querySelector('[data-action="bar-voice"]'), r = b.getBoundingClientRect(); return { label: b.getAttribute('aria-label'), w: r.width, h: r.height }; });
    assert.equal(seen.label, 'Pause narration'); assert(seen.w >= 44 && seen.h >= 44, `the bar's Pause is a 44 px target ${JSON.stringify(seen)}`);
    await rig(() => window.__rig.panel.collapse(false));
    console.log(`PASS ${width} the way on: Esc closes road notes, arrival focuses the stop, the bar keeps Pause`);

    // ---- closing: the ending is its transcript; touching the panel holds the scene's clock.
    await rig(() => { const r = window.__rig; r.narration.stop(); r.state = r.reduce(r.state, { type: 'NEXT', closing: true }); });
    assert.equal(await rig(() => window.__rig.state.phase), 'closing');
    await page.waitForFunction(() => window.__rig.narration.state.playing === 'a11y-walk:ending:end');
    assert.equal(await status(), 'Closing: A Morning Walk.');
    seen = await rig(() => ({ holding: window.__rig.panel.holding, lit: [...document.querySelectorAll('#jaunt-panel [data-voiced="ending"]')].map(p => p.classList.contains('jaunt-voicing')),
      text: document.querySelector('#jaunt-panel [data-voiced="ending"]')?.textContent }));
    assert.deepEqual(seen, { holding: false, lit: [true], text: 'You have two corners to start from.' });
    assert.equal(await rig(() => document.activeElement.tagName + ':' + document.activeElement.textContent), 'H2:A Morning Walk', 'the closing scene takes focus, and keeps it as its voice starts');
    await page.locator('#jaunt-panel .jaunt-body').dispatchEvent('pointerdown');
    assert.equal(await rig(() => window.__rig.panel.holding), true, '2.2.1: a visitor at the scene holds it');
    await rig(() => { const r = window.__rig; r.narration.stop(); r.state = r.reduce(r.state, { type: 'FINISH' }); });
    assert.equal(await status(), 'Outing complete: A Morning Walk.');
    console.log(`PASS ${width} closing: ending lit as read, the clock held, completion said`);

    // ---- words withheld on the card are not read aloud (jaunt-context.js claimPresentation).
    await rig(() => { const r = window.__rig; r.narration.stop();
      const bad = { ...r.jaunt, id: 'a11y-withheld', stops: [{ ...r.jaunt.stops[0], evidence: ['q'] }], evidence: [{ id: 'q', confidence: 'reconstructed', text: 'A said thing.', speaker: 'Someone', sources: [] }] };
      let s = r.reduce(r.emptyState(), { type: 'START', jaunt: bad, session: 2, mode: 'walk' }); s = r.reduce(s, { type: 'ARRIVE', session: 2, leg: s.leg }); r.state = s; });
    await rig(() => window.__rig.narration.prepare(window.__rig.state.jaunt));
    await page.waitForTimeout(100);
    seen = await rig(() => ({ listen: !!document.querySelector('#jaunt-panel .jaunt-body > [data-action="listen"]'),
      at: [window.__rig.narration.state.at, window.__rig.narration.state.playing].includes('a11y-withheld:stop:one') ? 'voiced' : null,
      text: document.querySelector('#jaunt-panel .jaunt-body > p[data-withheld]')?.textContent }));
    assert.deepEqual(seen, { listen: false, at: null, text: 'Unverified attribution withheld.' });
    console.log(`PASS ${width} withheld words: no Listen, nothing voiced`);

    // ---- the stand-in card returns on Esc.
    seen = await rig(async () => {
      const { createJauntCards } = await import('/js/jaunt-cards.js');
      let returned = 0;
      const cards = createJauntCards({ registry: new Map(), popup: { show: () => false, close() {} }, hud: { setPanel() {} }, api: {}, sources: async () => null, onReturn: () => { returned++; } });
      await cards.open({ kind: 'structure', id: 'nowhere' }, { signal: new AbortController().signal });
      const card = document.getElementById('jaunt-context-card'), focused = document.activeElement === card.querySelector('button');
      document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
      const r = { shown: !card.hidden, focused, returned };
      cards.destroy(); return r;
    });
    assert.deepEqual(seen, { shown: true, focused: true, returned: 1 }, 'Esc on the stand-in card returns to the outing');

    // ---- the menu: a list of cards, Start says which jaunt, the modes are one Tab stop on the arrows.
    seen = await rig(async () => {
      const { createJauntMenu } = await import('/js/jaunt-menu.js');
      const root = document.getElementById('menu-host');
      const menu = createJauntMenu({ root, estimate: () => ({ seconds: 600 }), onStart: async () => {}, onPreview: () => {},
        choice: { get: () => [], subscribe() {}, has: () => false, top: () => '18+', toggle() {}, clear() {} } });
      menu.show([{ id: 'one', title: 'A Morning Walk', premise: 'Two corners.', category: 'Orientation', menu_group: 'Places', stop_count: 2,
        availability: 'available', default_mode: 'walk', allowed_modes: ['walk', 'horse', 'fly'] }]);
      const list = root.querySelector('.jaunt-list'), card = list.querySelector('.jaunt-card'), start = card.querySelector('[data-action="start"]');
      card.querySelector('[data-action="more"]').click();
      const picks = [...card.querySelectorAll('.jaunt-mode-pick')];
      const tabbable = picks.filter(b => b.tabIndex === 0).map(b => b.dataset.mode);
      picks[0].focus(); picks[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true }));
      return { list: list.getAttribute('role'), item: card.getAttribute('role'), start: start.getAttribute('aria-label'),
        described: document.getElementById(start.getAttribute('aria-describedby'))?.textContent, tabbable,
        after: { focus: document.activeElement.dataset.mode, checked: picks.find(b => b.getAttribute('aria-checked') === 'true')?.dataset.mode, tabbable: picks.filter(b => b.tabIndex === 0).map(b => b.dataset.mode) } };
    });
    assert.deepEqual(seen, { list: 'list', item: 'listitem', start: 'Start Jaunt', described: 'A Morning Walk', tabbable: ['walk'],
      after: { focus: 'horse', checked: 'horse', tabbable: ['horse'] } });
    console.log(`PASS ${width} menu: list of cards, Start described by its jaunt, mode radios on the arrows`);

    // ---- the tour: the card takes focus, is a region the walking keys pass through, ends on Esc and gives focus back.
    seen = await rig(async () => {
      const { createTourOverlay } = await import('/js/tour-overlay.js');
      const { ownsKeyboard } = await import('/js/controls/keyboard.js');
      let skipped = 0;
      const overlay = createTourOverlay({ onSkip: () => { skipped++; overlay.paint(null); } });
      const outside = document.getElementById('outside'); outside.focus();
      const view = (step, extra = {}) => ({ step, n: step + 1, of: 10, task: 'Look around', bubble: 'Look around.', target: null, action: null, waiting: true, ...extra });
      overlay.paint(view(1));
      const card = document.querySelector('#tour .tour-card');
      const r = { focused: document.activeElement === card, role: card.getAttribute('role'), name: card.getAttribute('aria-label'), walks: !ownsKeyboard(card) };
      overlay.paint(view(4, { task: 'Release it', escape: 'page' }));
      card.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
      r.releaseKept = skipped === 0;
      overlay.paint(view(5, { task: 'Interact' }));
      document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
      r.skipped = skipped; r.back = document.activeElement === outside; r.hidden = document.getElementById('tour').hidden;
      return r;
    });
    assert.deepEqual(seen, { focused: true, role: 'region', name: 'Field check', walks: true, releaseKept: true, skipped: 1, back: true, hidden: true });
    console.log(`PASS ${width} tour: focus in, walking keys pass, Esc ends (not on Release), focus returns`);

    // ---- the phone stays one column wide.
    const scroll = await rig(() => ({ body: document.body.scrollWidth, width: innerWidth }));
    assert(scroll.body <= scroll.width + 1, JSON.stringify(scroll));
    assert.deepEqual(errors, []);
    await context.close();
  }
  console.log('A11Y JAUNTS PASS — transcripts, Pause, status line, held closing, keys and Esc, menu list and radios, tour focus');
} catch (err) {
  failed = true; console.error(err);
} finally {
  await browser.close(); server.close();
}
process.exit(failed ? 1 : 0);
