#!/usr/bin/env node
// T-2664 (NAV-802): the Field Check offered once per device after the first landing (Home's
// "First time? Take the 60-second tour"), declining or finishing never re-prompts, and one-time
// hints after it for the first Jaunt, the first Jump and the first Reconstructed building.
// Drives js/tour-offer.js over fake storage, element and clock, and reads the page's wiring;
// the smoke (part 13) shows the offer on Home, takes it, and fires a hint in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTourOffer, createHints, takeJumped, offerText, hintText, OFFER_KEY, HINTS_KEY, JUMPED_KEY, HINT_IDS, HINT_MS }
  from '../renderers/web/js/tour-offer.js';
import { TOUR_KEY } from '../renderers/web/js/tour.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const store = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m }; };
const refusing = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
const el = () => ({ hidden: true, textContent: '', dataset: {} });
const clock = () => { const q = []; return { wait: (fn, ms) => { q.push({ fn, ms }); return q.length; }, cancel: (id) => { if (q[id - 1]) q[id - 1].fn = null; }, run: () => q.splice(0).forEach((t) => t.fn?.()), q }; };
const words = (s) => s.split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w)).length;

// ---- the words ------------------------------------------------------------------------
assert.equal(offerText(), 'First time? Take the 60-second tour', 'the offer in the design\'s words (M2)');
assert.deepEqual(HINT_IDS, ['jaunt', 'jump', 'reconstructed'], 'three hints: first Jaunt, first Jump, first Reconstructed building');
for (const id of HINT_IDS) {
  const s = hintText(id);
  assert.ok(s && words(s) <= 14, `${id}: a hint is 14 words or fewer, like a bubble (${words(s)}): "${s}"`);
  assert.doesNotMatch(s, /[a-z0-9]+_[a-z0-9]+|\//i, `${id}: no id, snake_case or path`);
}
assert.match(hintText('reconstructed'), /^Reconstructed\b/, 'the locked term, spelled exactly');
assert.match(hintText('jaunt'), /\bNext Stop\b/, 'names the Jaunt panel\'s own button');
assert.match(hintText('jump'), /\bJump\b/, 'names the Navigator app that goes back');
assert.equal(hintText('nope'), '', 'an unknown hint has no words, never its id');
assert.equal(TOUR_KEY, 'chicago4d.tour', 'the offer reads the Field Check\'s own record');

// ---- the offer: once per device ----------------------------------------------------------
{
  const s = store();
  const offer = createTourOffer({ storage: s });
  assert.equal(offer.due(), true, 'a new device is offered the tour');
  assert.equal(offer.spend('declined'), true, 'going in another way declines it');
  assert.equal(s.m.get(OFFER_KEY), 'declined', 'and is remembered on this device');
  assert.equal(offer.due(), false, 'not offered again on this page');
  assert.equal(offer.spend('taken'), false, 'an answer is final');
  assert.equal(createTourOffer({ storage: s }).due(), false, 'nor on the next visit: declining never re-prompts');
}
{
  const s = store();
  const offer = createTourOffer({ storage: s });
  offer.spend('taken');
  assert.equal(s.m.get(OFFER_KEY), 'taken');
  assert.equal(createTourOffer({ storage: s }).due(), false, 'taking it is the once too');
}
{
  const s = store();
  s.setItem(TOUR_KEY, JSON.stringify({ active: false, step: null, done: true }));
  assert.equal(createTourOffer({ storage: s }).due(), false, 'a device that finished the Field Check (from Guide) is not offered it');
  s.setItem(TOUR_KEY, JSON.stringify({ active: true, step: 3, done: false }));
  assert.equal(createTourOffer({ storage: s }).due(), false, 'nor one with a Field Check left running for a reload to resume');
  s.setItem(TOUR_KEY, JSON.stringify({ active: false, step: null, done: false }));
  assert.equal(createTourOffer({ storage: s }).due(), true, 'a skipped Field Check from Guide does not spend the offer');
  s.setItem(TOUR_KEY, '{not json');
  assert.equal(createTourOffer({ storage: s }).due(), true, 'a damaged record reads as none');
}
{
  const offer = createTourOffer({ storage: refusing });
  assert.equal(offer.due(), true, 'storage refused: still offered, no error');
  offer.spend('declined');
  assert.equal(offer.due(), false, '…once for the page');
  offer.forget();
  assert.equal(offer.due(), true, 'the harness can forget it');
  assert.equal(createTourOffer({ storage: null }).due(), true, 'no storage at all: nothing throws');
}

// ---- the hints: each once ------------------------------------------------------------
{
  const e = el(), s = store(), c = clock();
  let running = false;
  const hints = createHints({ el: e, storage: s, blocked: () => running, wait: c.wait, cancel: c.cancel });
  running = true;
  assert.equal(hints.show('jaunt'), false, 'no hint while the Field Check runs');
  assert.equal(hints.seen('jaunt'), false, '…and one held back is still owed');
  running = false;
  assert.equal(hints.show('jaunt'), true, 'the first Jaunt\'s hint shows');
  assert.equal(e.hidden, false);
  assert.equal(e.textContent, hintText('jaunt'));
  assert.equal(e.dataset.hint, 'jaunt');
  assert.equal(hints.current, 'jaunt');
  assert.deepEqual(JSON.parse(s.m.get(HINTS_KEY)), ['jaunt'], 'remembered on this device');
  assert.equal(c.q[0].ms, HINT_MS, 'it goes by itself after a few seconds');
  c.run();
  assert.equal(e.hidden, true);
  assert.equal(hints.show('jaunt'), false, 'never twice on a page');
  assert.equal(hints.show('reconstructed'), true, 'each hint is its own once');
  hints.hide();
  assert.equal(hints.showing, false, 'the visitor\'s next move puts it away');
  assert.deepEqual(JSON.parse(s.m.get(HINTS_KEY)).sort(), ['jaunt', 'reconstructed']);
  const again = createHints({ el: el(), storage: s, wait: c.wait, cancel: c.cancel });
  assert.equal(again.show('jaunt'), false, 'nor on the next visit');
  assert.equal(again.show('reconstructed'), false);
  assert.equal(again.show('jump'), true, 'the one not yet seen still shows');
  assert.equal(again.show('bogus'), false, 'an unknown hint never shows');
}
{
  const e = el(), c = clock();
  const hints = createHints({ el: e, storage: refusing, blocked: () => { throw new Error('x'); }, wait: c.wait, cancel: c.cancel });
  assert.equal(hints.show('jump'), true, 'storage refused (and a throwing guard): still shows, no error');
  assert.equal(hints.show('jump'), false, '…once for the page');
  hints.forget();
  assert.equal(hints.show('jump'), true, 'the harness can forget them');
  assert.equal(createHints({ el: null, storage: null, wait: c.wait, cancel: c.cancel }).show('jaunt'), true, 'no element, no storage: nothing throws');
}

// ---- a Jump, not the Observatory ---------------------------------------------------------
{
  const s = store();
  assert.equal(takeJumped(s), false, 'an arrival with no stamp (from the Observatory, or typed) is not a Jump');
  s.setItem(JUMPED_KEY, '1904');
  assert.equal(takeJumped(s), true, 'the Navigator\'s Jump stamp is read');
  assert.equal(s.m.has(JUMPED_KEY), false, 'and cleared as it is read');
  assert.equal(takeJumped(s), false, 'so a reload is not a second Jump');
  assert.equal(takeJumped(refusing), false, 'storage refused: no error');
}

// ---- the page --------------------------------------------------------------------------
const html = read('renderers/web/index.html');
assert(/<button id="tour-offer" class="welcome-link welcome-tour-offer" type="button" hidden data-str="tour\.offer">First time\? Take the 60-second tour<\/button>/.test(html),
  'Home carries the offer, hidden until it is due, in the table\'s first-paint words');
assert(html.indexOf('id="tour-offer"') > html.indexOf('id="home-roam"') && html.indexOf('id="tour-offer"') < html.indexOf('id="welcome-jaunts-region"'),
  'under Home\'s three choices');
assert(/<p class="nav-hint" id="nav-hint" role="status" aria-live="polite" hidden><\/p>/.test(html), 'the hint line, announced');
const jumpView = read('renderers/web/js/apps/jump-view.js');
assert(jumpView.includes(`const JUMPED_KEY = '${JUMPED_KEY}'`), 'the Navigator\'s Jump writes the stamp the far year reads');
assert(/go\(d\.href\);/.test(jumpView) && /setItem\(JUMPED_KEY/.test(jumpView), 'as the page goes, not when the ring starts');
assert(!read('renderers/web/portal/portal.js').includes(JUMPED_KEY), 'the Observatory writes none: its arrival is not a Jump');
const welcome = read('renderers/web/js/welcome.js');
assert(/tourOffer\.hidden = !due;/.test(welcome), 'Home shows the offer only when it is due');
assert(/if \(tourOffer && !tourOffer\.hidden\) \{ tourOffer\.hidden = true; try \{ offer\?\.spend\?\.\('declined'\)/.test(welcome),
  'going into the town any other way while it shows declines it');
assert(/offer\?\.spend\?\.\('taken'\)[\s\S]{0,80}onTour\(\);/.test(welcome), 'taking it is remembered, then the tour runs');
const main = read('renderers/web/js/main.js');
assert(/blocked: \(\) => !!api\.tour\?\.running/.test(main), 'a hint waits while the Field Check runs');
assert(/if \(firstEntry && jumpedIn\) hints\.show\('jump'\);/.test(main), 'the far year of a Jump says how to go back, on the way in');
assert(/state\.phase === 'atStop'\) hints\.show\('jaunt'\)/.test(main), 'the first Jaunt\'s first stop');
assert(/if \(isReconstructed\(record\?\.sidecar\)\) api\.hints\?\.show\('reconstructed'\);/.test(main), 'a Reconstructed building\'s card');
// T-3022: the tag's Inspect opens the building as a click does, through openBuilding.
assert(/function openBuilding\(id(?:, \{ person = null \} = \{\})?\) \{[\s\S]{0,400}if \(isReconstructed\(record\.sidecar\)\) hints\.show\('reconstructed'\)/.test(main)
  && /onInspect: \(t\) => \{[\s\S]{0,300}openBuilding\(t\.id\)/.test(main), 'and Inspect from the tag');
assert(/if \(ok\) api\.tour\?\.start\(\);/.test(main) && /!resume && !destination && !tourEntering\) roamTip\.show/.test(main),
  'taking the offer goes in as Free roam goes, without Free roam\'s tip, and starts step 01');
const css = read('renderers/web/css/walk.css');
assert(/\.welcome-tour-offer\[hidden\], \.gate\[data-region\] \.welcome-tour-offer \{ display: none; \}/.test(css), 'the offer leaves with Home\'s sub-views');
assert(/\.nav-hint \{[^}]*pointer-events: none;/.test(css), 'a hint never sits between the visitor and a control');
assert(/prefers-reduced-motion: reduce\) \{ \.nav-hint \{ animation: none; \}/.test(css), 'still with reduced motion');

console.log('test_tour_offer: the Field Check is offered once per device, declining never re-prompts, and each of three hints shows once');
