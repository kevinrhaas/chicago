#!/usr/bin/env node
// T-2663 (NAV-801): Tour mode, the Field Check. Drives the real engine (js/tour.js) over a
// fake page: each of the seven steps completes only on its own action, taken during it;
// progress survives a reload (QA-16: resume at 4, skip at 6, replay); bubbles are 14 words
// or fewer. The smoke (part 13) runs it in a page by touch and by mouse.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTour, STEPS, TOUR_KEY, YAW_DEG, WALK_M } from '../renderers/web/js/tour.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const store = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), m }; };

// The page, as the probe reads it.
const page = { yawDeg: 0, e: 0, n: 0, opens: 0, deeper: 0, confidence: false, confChanges: 0, scene: '1904', front: 'Glessner House' };
const views = [];
let finished = 0;
const storage = store();
const make = () => createTour({ probe: () => ({ ...page }), render: (v) => views.push(v), onFinish: () => finished++, storage });

// ---- the seven steps, in section 11's order and words ------------------------------------
assert.equal(STEPS.length, 7);
const words = (s) => s.split(/\s+/).filter(Boolean).length;
for (const scene of ['1904', '1835', '1812']) {
  for (const s of STEPS) {
    const b = s.bubble({ scene, front: scene === '1904' ? null : 'Fort Dearborn Commandant\'s Quarters' });
    assert(words(b) <= 14, `${scene}: "${b}" is ${words(b)} words`);
    assert(!/[a-z0-9]+_[a-z0-9]+/i.test(b), b);
  }
}
assert.equal(STEPS[3].bubble({ scene: '1904' }), 'Tap the Glessner House. Every building has a file.', 'step 04 in 1904');
assert.equal(STEPS[3].bubble({ scene: '1835', front: 'Sauganash Hotel' }), 'Tap the Sauganash Hotel. Every building has a file.', 'in 1835, the building in front of you');
assert.equal(STEPS[5].bubble({}), 'How sure are we? Turn on the Confidence view.', 'the locked term, exactly');

// ---- each step waits for its own action -----------------------------------------------------
let tour = make();
tour.start();
assert.equal(tour.step, 0);
assert.equal(views.at(-1).bubble, 'This is your Navigator. Everything you need lives here.');
assert.equal(views.at(-1).action, 'next');
assert.equal(views.at(-1).target, '#navigator', 'step 01 rings the Navigator');
tour.tick(); assert.equal(tour.step, 0, 'step 01 waits for Next');
tour.press(); assert.equal(tour.step, 1, 'Next moves on');
assert.equal(tour.press(), false, 'a waiting step has no Next');

// 02: a turn of 60 degrees, in small pieces and either way.
for (const yaw of [15, 30, 20, 5]) { page.yawDeg = yaw; tour.tick(); }
assert.equal(tour.step, 1, `a ${15 + 15 + 10 + 15}° wander is not yet ${YAW_DEG}°`);
page.yawDeg = 350; tour.tick();
assert.equal(tour.step, 2, 'the turn adds up across the north line');

// 03: five metres.
page.e = 3; page.n = 3; tour.tick(); assert.equal(tour.step, 2, `${Math.hypot(3, 3).toFixed(1)} m is short of ${WALK_M}`);
page.e = 4; page.n = 4; tour.tick(); assert.equal(tour.step, 3, 'walked five metres');

// 04: Inspect or a card opening on a structure, during the step.
page.yawDeg = 120; page.e = 40; tour.tick(); assert.equal(tour.step, 3, 'turning and walking do not inspect');
page.opens++; tour.tick(); assert.equal(tour.step, 4, 'a record opened');

// Reload at step 4 (QA-16): a fresh engine over the same storage resumes there.
const saved = JSON.parse(storage.m.get(TOUR_KEY));
assert.deepEqual([saved.active, saved.step], [true, 4]);
tour = make();
assert.equal(tour.running, false, 'nothing runs before the town is entered');
assert.equal(tour.resume(), true);
assert.equal(tour.step, 4, 'resumed at the same step');

// 05: a deeper layer opened during the step (a record already open does not count).
tour.tick(); assert.equal(tour.step, 4);
page.deeper++; tour.tick(); assert.equal(tour.step, 5, 'went deeper');

// 06: the Confidence view turned on during the step. Already on is not enough.
page.confidence = true; tour.tick(); assert.equal(tour.step, 5, 'on before the step began: no change, no credit');
page.confChanges++; tour.tick(); assert.equal(tour.step, 6, 'turned on');

// 07: Finish.
tour.tick(); assert.equal(tour.step, 6, 'step 07 waits for Finish');
assert.equal(views.at(-1).action, 'finish');
tour.press();
assert.equal(tour.running, false); assert.equal(finished, 1, 'Finish ends the tour');
assert.equal(views.at(-1), null, 'and the overlay goes');
assert.equal(tour.finished, true);
assert.equal(make().resume(), false, 'a finished tour does not resume');

// Skip at 6 (QA-16): ends cleanly, nothing resumes, and it can be replayed.
tour = make(); tour.start();
tour.press(); page.yawDeg += 90; tour.tick(); page.e += 10; tour.tick(); page.opens++; tour.tick(); page.deeper++; tour.tick();
assert.equal(tour.step, 5);
assert.equal(tour.skip(), true);
assert.equal(tour.running, false);
assert.equal(views.at(-1), null);
assert.equal(make().resume(), false, 'a skipped tour does not come back on reload');
assert.equal(make().start(), true, 'Replay starts it again from 01');

// Storage refused: the tour still runs, for this page.
const refusing = { getItem() { throw new Error('no'); }, setItem() { throw new Error('no'); } };
const bare = createTour({ probe: () => ({ ...page }), render() {}, storage: refusing });
assert.equal(bare.start(), true); assert.equal(bare.step, 0);

// ---- the page ----------------------------------------------------------------------------------
const html = read('renderers/web/index.html');
for (const id of ['tour', 'tour-count', 'tour-skip', 'tour-task', 'tour-bubble', 'tour-status', 'tour-next', 'tour-start']) {
  assert(html.includes(`id="${id}"`), `#${id} is on the page`);
}
const main = read('renderers/web/js/main.js');
assert(/if \(firstEntry && !api\.tour\?\.running\) api\.tour\?\.resume\(\);/.test(main), 'a reload resumes once back in the town');
assert(/onConfidence: \(on\) => \{ confidence\.set\(on\); tourCounts\.confChanges\+\+; \}/.test(main));
assert(/\[data-pop-tab\]'\)\) tourCounts\.deeper\+\+/.test(main), 'a card tab is a deeper layer');
const css = read('renderers/web/css/tour.css');
assert(/rgb\(0 0 0 \/ 55%\)/.test(css), 'the rest of the screen dims to 55 %');
assert(/prefers-reduced-motion: reduce/.test(css), 'and keeps still with reduced motion');
assert(/\.tour \{[^}]*pointer-events: none/.test(css) && /\.tour-card \{[^}]*pointer-events: auto/.test(css), 'only the card takes the pointer');

console.log('test_tour: seven steps, each on its own action; resume at 4, skip at 6, replay; bubbles of 14 words or fewer');
