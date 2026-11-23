#!/usr/bin/env node
// T-2663 (NAV-801): Tour mode, the Field Check. Drives the real engine (js/tour.js) over a
// fake page: each of the eleven steps completes only on its own action, taken during it;
// progress survives a reload (QA-16: resume at 4, skip at 6, replay); bubbles are 14 words
// or fewer. T-2954 made it the basics: select a building and release it, open Move, open
// Settings; no Confidence view step. T-3445 added People and the card's tabs. T-3642 put
// Interact (the town's one use key) and Jaunts in People's place; the count names only the
// steps that apply. T-3742 named stories, questions, mysteries, Language, Reading age and
// Graphics, and added Jump years (1871 and its Great Fire) before Ready. The smoke (part 13)
// runs it in a page by touch and by mouse.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTour, STEPS, TOUR_KEY, YAW_DEG, WALK_M } from '../renderers/web/js/tour.js';
import GUIDE from '../renderers/web/js/apps/guide.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const html0 = () => read('renderers/web/index.html');
const store = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), m }; };

// The page, as the probe reads it.
const page = { yawDeg: 0, e: 0, n: 0, opens: 0, selected: false, apps: {}, touch: false, level: 0, scene: '1904', front: 'Glessner House' };
const views = [];
let finished = 0;
const storage = store();
const make = () => createTour({ probe: () => ({ ...page, apps: { ...page.apps } }), render: (v) => views.push(v), onFinish: () => finished++, storage });
const openApp = (id) => { page.apps[id] = (page.apps[id] ?? 0) + 1; page.level = 1; };

// ---- the eleven steps, and their words -----------------------------------------------------
assert.equal(STEPS.length, 11);
assert.deepEqual(STEPS.map((s) => s.task), ['Your device', 'Look around', 'Walk', 'Select a building', 'Release it', 'Interact', 'Jaunts', 'Move', 'Settings', 'Jump years', 'Ready']);
assert(!STEPS.some((s) => /confidence/i.test(s.task + s.bubble({}))), 'no Confidence view step (T-2954)');
const words = (s) => s.split(/\s+/).filter(Boolean).length;
for (const scene of ['1904', '1835', '1812', '1871']) {
  for (const touch of [false, true]) {
    for (const level of [0, 1]) {
      for (const s of STEPS) {
        const b = s.bubble({ scene, touch, level, front: scene === '1904' ? null : 'Fort Dearborn Commandant\'s Quarters' });
        assert(words(b) <= 14, `${scene}: "${b}" is ${words(b)} words`);
        assert(!/[a-z0-9]+_[a-z0-9]+/i.test(b), b);
      }
    }
  }
}
assert.equal(STEPS[3].bubble({ scene: '1904' }), 'Click the Glessner House. Its card opens: Design, Timeline, Photos, Sources.', 'step 04 in 1904, with a mouse');
assert.equal(STEPS[3].bubble({ scene: '1904', touch: true }), 'Tap the Glessner House. Its card opens: Design, Timeline, Photos, Sources.', 'and on touch');
assert.equal(STEPS[3].bubble({ scene: '1835', front: 'Sauganash Hotel', touch: true }), 'Tap the Sauganash Hotel. Its card opens: Design, Timeline, Photos, Sources.', 'in 1835, the building in front of you');
assert.match(STEPS[4].bubble({}), /Esc/, 'release names Esc on a keyboard');
assert.match(STEPS[4].bubble({ touch: true, card: true }), /Tap Close/, 'and the card\'s Close on touch');
assert.match(STEPS[4].bubble({ touch: true }), /Tap Back/, 'and Inspect\'s Back where the building opened in Inspect (T-3022)');
assert(!/Esc/.test(STEPS[4].bubble({ touch: true })), 'a phone has no Esc key');
assert.equal(STEPS[4].target({ card: true }), '#popup:not([hidden]) .pop-close', 'release rings the card\'s Close');
assert.equal(STEPS[4].target({}), '#nav-app-inspect .insp-back', 'or Inspect\'s Back (T-3022)');
// T-3642: Look and Walk say how on each device, and how to run.
assert.match(STEPS[1].bubble({}), /Click the scene, then move the mouse/, 'look: click to look, with a mouse');
assert.match(STEPS[1].bubble({ touch: true }), /Drag the right side/, 'and a drag on touch');
assert.match(STEPS[2].bubble({}), /W A S D\. Hold Shift to run/, 'walk names W A S D and Shift');
assert.match(STEPS[2].bubble({ touch: true }), /left thumb\. Push it all the way to run/, 'and the thumb on touch');
// T-3642: Interact, the town's one use key. T-3742: said as talk — greet, a story, a question.
assert.equal(STEPS[5].bubble({ scene: '1835' }), 'Walk up to someone. Press R: greet them, hear a story, ask a question.');
assert.equal(STEPS[5].bubble({ scene: '1904', touch: true }), 'Walk up to someone. Tap Interact: greet, hear a story, ask a question.');
assert.equal(STEPS[5].target, '#btn-interact', 'Interact rings its key');
assert.equal(STEPS[5].done({ acts: 1 }, { acts: 0 }), true, 'a press during the step');
assert.equal(STEPS[5].done({ acts: 1 }, { acts: 1 }), false, 'not one before it');
// Jaunts: on the rail; T-3742: read aloud, mysteries (Make your case), parts to play.
assert.equal(STEPS[6].target({ touch: true, level: 0 }), '#navigator', 'on a docked phone, Jaunts rings the dock first');
assert.equal(STEPS[6].target({ touch: true, level: 1 }), '#navigator .nav-app[data-app="jaunts"]', 'then its rail key');
assert.equal(STEPS[6].bubble({}), 'Open Jaunts on the rail: stories read aloud, mysteries to solve, parts to play.');
// T-3629: Move left the rail for Home's Move tile; the ring goes to Home's key, then the tile.
assert.equal(STEPS[7].target({ touch: true, level: 0 }), '#navigator', 'on a docked phone, Move rings the dock first');
assert.equal(STEPS[7].target({ touch: true, level: 1 }), '#navigator .nav-app[data-app="home"]', 'then the Home key');
assert.equal(STEPS[7].target({ touch: true, level: 1, app: 'home' }), '#nav-tile-move', 'then Home\'s Move tile');
assert.equal(STEPS[8].target({ touch: false, level: 0 }), '#navigator .nav-app[data-app="settings"]', 'the desktop rail is always out');
assert.equal(STEPS[8].bubble({ touch: true, level: 0 }), 'Open the Navigator, then Settings: language, reading age, graphics, name cards, sound.',
  'Settings names Language, Reading age and Graphics (T-3742)');
// T-3742: Jump years, on the year chip (Home's Other years where Home is open), names 1871.
assert.equal(STEPS[9].bubble({}), 'Click the year to jump: 1812, 1835, 1871 and its Great Fire, 1904.');
assert.match(STEPS[9].bubble({ touch: true }), /^Tap the year/);
assert.equal(STEPS[9].target({ level: 0 }), '#year-badge', 'Jump rings the year chip');
assert.equal(STEPS[9].target({ level: 1, app: 'settings' }), '#year-badge', 'over another app too');
assert.equal(STEPS[9].target({ level: 1, app: 'home' }), '#nav-choice-years', 'or Home\'s Other years key, where Home is open');
assert.match(html0(), /id="year-badge"/, 'the year chip is on the page');
assert.match(html0(), /id="nav-choice-years"[^>]*data-app="jump"/, 'and Home\'s Other years opens Jump');
for (const scene of ['1812', '1835', '1871', '1904']) {
  assert.match(STEPS[10].bubble({ scene }), /photo/, 'Ready names Go to by photo (T-3436)');
  assert.match(STEPS[10].bubble({ scene }), /People/, 'and People, whose step Interact took');
}
assert.match(STEPS[10].bubble({ scene: '1904' }), /photo hunt/, 'and the photo hunt where the year has one (T-3742)');
assert.match(STEPS[10].bubble({ scene: '1835' }), /photo hunt/);
assert.doesNotMatch(STEPS[10].bubble({ scene: '1871' }), /hunt/, 'not where it has none');
assert.doesNotMatch(STEPS[10].bubble({ scene: '1812' }), /hunt/);

// ---- each step waits for its own action -----------------------------------------------------
let tour = make();
tour.start();
assert.equal(tour.step, 0);
assert.equal(views.at(-1).bubble, 'This is your Navigator. Every menu is a key on its rail.');
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
page.yawDeg = 120; page.e = 40; tour.tick(); assert.equal(tour.step, 3, 'turning and walking do not select');
page.touch = true; tour.tick();
assert.equal(views.at(-1).bubble, 'Tap the Glessner House. Its card opens: Design, Timeline, Photos, Sources.', 'a finger on the glass repaints the bubble');
page.opens++; page.selected = true; tour.tick(); assert.equal(tour.step, 4, 'a record opened');

// Reload at step 4 (QA-16): a fresh engine over the same storage resumes there.
const saved = JSON.parse(storage.m.get(TOUR_KEY));
assert.deepEqual([saved.active, saved.step], [true, 4]);
tour = make();
assert.equal(tour.running, false, 'nothing runs before the town is entered');
assert.equal(tour.resume(), true);
assert.equal(tour.step, 4, 'resumed at the same step');

// 05: released — the card closed (Esc, Close, or the scene touched).
tour.tick(); assert.equal(tour.step, 4, 'held while the card is open');
page.selected = false; tour.tick(); assert.equal(tour.step, 5, 'released');

// 06: Interact used during the step (T-3642).
assert.equal(views.at(-1).task, 'Interact');
assert.equal(views.at(-1).of, 11, 'eleven steps');
page.level = 1; openApp('people'); tour.tick(); assert.equal(tour.step, 5, 'opening a menu is not Interact');
page.acts = (page.acts ?? 0) + 1; tour.tick(); assert.equal(tour.step, 6, 'Interact used');

// 07: Jaunts, opened during the step.
assert.equal(views.at(-1).target, '#navigator .nav-app[data-app="jaunts"]');
openApp('move'); tour.tick(); assert.equal(tour.step, 6, 'another app is not Jaunts');
openApp('jaunts'); tour.tick(); assert.equal(tour.step, 7, 'Jaunts opened');

// 08: Move; on a docked phone the ring is on the dock, then the Home key.
page.level = 0; tour.tick();
assert.equal(views.at(-1).target, '#navigator');
page.level = 1; tour.tick();
assert.equal(tour.step, 7, 'opening the Navigator is not opening Move');
assert.equal(views.at(-1).target, '#navigator .nav-app[data-app="home"]', 'the ring moves to the Home key, where Move\'s tile is (T-3629)');
openApp('move'); tour.tick(); assert.equal(tour.step, 8, 'Move opened');

// 09: Settings, opened during the step (Move already open does not count).
openApp('move'); tour.tick(); assert.equal(tour.step, 8, 'another app is not Settings');
openApp('settings'); tour.tick(); assert.equal(tour.step, 9, 'Settings opened');

// 10: Jump years, opened during the step (T-3742).
assert.equal(views.at(-1).task, 'Jump years');
assert.equal(views.at(-1).target, '#year-badge');
openApp('settings'); tour.tick(); assert.equal(tour.step, 9, 'another app is not Jump');
openApp('jump'); tour.tick(); assert.equal(tour.step, 10, 'Jump opened');

// 11: Finish.
tour.tick(); assert.equal(tour.step, 10, 'step 11 waits for Finish');
assert.equal(views.at(-1).action, 'finish');
tour.press();
assert.equal(tour.running, false); assert.equal(finished, 1, 'Finish ends the tour');
assert.equal(views.at(-1), null, 'and the overlay goes');
assert.equal(tour.finished, true);
assert.equal(make().resume(), false, 'a finished tour does not resume');

// An app open before its step began does not complete it.
tour = make(); tour.start();
tour.press(); page.yawDeg += 90; tour.tick(); page.e += 10; tour.tick(); page.opens++; page.selected = true; tour.tick();
page.selected = false; tour.tick();
assert.equal(tour.step, 5);
page.acts += 1; tour.tick(); assert.equal(tour.step, 6);
openApp('settings'); tour.tick(); assert.equal(tour.step, 6, 'Settings during the Jaunts step is not Jaunts');

// Skip at 6 (QA-16): ends cleanly, nothing resumes, and it can be replayed.
assert.equal(tour.skip(), true);
assert.equal(tour.running, false);
assert.equal(views.at(-1), null);
assert.equal(make().resume(), false, 'a skipped tour does not come back on reload');
assert.equal(make().start(), true, 'Replay starts it again from 01');

// T-3642: every step applies everywhere now; the count is the whole tour.
assert(STEPS.every((x) => !x.when), 'no step is passed over');

// Storage refused: the tour still runs, for this page.
const refusing = { getItem() { throw new Error('no'); }, setItem() { throw new Error('no'); } };
const bare = createTour({ probe: () => ({ ...page }), render() {}, storage: refusing });
assert.equal(bare.start(), true); assert.equal(bare.step, 0);

// ---- the page ----------------------------------------------------------------------------------
const html = read('renderers/web/index.html');
for (const id of ['tour', 'tour-count', 'tour-skip', 'tour-task', 'tour-bubble', 'tour-status', 'tour-next', 'tour-start']) {
  assert(html.includes(`id="${id}"`), `#${id} is on the page`);
}
// T-3021: the tour can be taken any time — its block leads Guide, whatever became of the offer.
assert(/id="guide-tour"[\s\S]{0,400}id="tour-start"[^>]*>Take the tour/.test(html), 'Guide\u2019s tour block carries Take the tour');
// Mount the real Guide: additional lazy sections must not change the tour's position.
// Reparenting keeps the existing tour element (and its bound start listener) intact.
const guideDoc = {
  createElement() {
    return {
      ownerDocument: guideDoc, children: [], parentElement: null, className: '',
      classList: { toggle() {} },
      append(...children) {
        for (const child of children) {
          if (child.parentElement) {
            const siblings = child.parentElement.children;
            siblings.splice(siblings.indexOf(child), 1);
          }
          this.children.push(child);
          child.parentElement = this;
        }
      },
    };
  },
  getElementById(id) { return ({ 'guide-tour': tourBlock, panel: guidePanel })[id] ?? null; },
  querySelectorAll() { return []; },
  querySelector() { return null; },
};
const tourBlock = guideDoc.createElement('div');
const guidePanel = guideDoc.createElement('div');
guidePanel.append(tourBlock);
const guideHost = guideDoc.createElement('div');
const guideScreen = GUIDE.load();
const guideContext = { api: { hud: { tab: 'controls', panelOpen: () => true } } };
try {
  guideScreen.mount(guideHost, guideContext);
  guideScreen.shown(guideHost, guideContext);
  assert.equal(guideHost.children[0], tourBlock, 'the existing tour block leads Guide');
  assert.equal(guideHost.children.filter(child => child === tourBlock).length, 1, 'the tour is moved exactly once');
  assert(!guidePanel.children.includes(tourBlock), 'the tour leaves the legacy panel');
  const controls = guideHost.children.filter(child => child.className === 'nav-guide-sheet');
  assert.equal(controls.length, 1, 'Guide mounts one controls sheet');
  assert(guideHost.children.indexOf(controls[0]) > 0, 'the controls sheet follows the tour');
  assert(guideHost.children.indexOf(guidePanel) > guideHost.children.indexOf(controls[0]), 'the hosted sections follow the controls sheet');
} finally {
  // Invalidate pending lazy imports before they try to paint this minimal DOM.
  guideScreen.hidden(guideHost, { api: {} });
  guideScreen.unmount();
}
const main = read('renderers/web/js/main.js');
assert(/if \(firstEntry && !api\.tour\?\.running\) api\.tour\?\.resume\(\);/.test(main), 'a reload resumes once back in the town');
assert(/tourCounts\.apps\[now\] = \(tourCounts\.apps\[now\] \?\? 0\) \+ 1/.test(main), 'each Navigator app opening is counted');
assert(/selected: !!popup\.openId/.test(main), 'the card on screen is the selection the release step waits on');
const css = read('renderers/web/css/tour.css');
assert(/rgb\(0 0 0 \/ 55%\)/.test(css), 'the rest of the screen dims to 55 %');
assert(/prefers-reduced-motion: reduce/.test(css), 'and keeps still with reduced motion');
assert(/\.tour \{[^}]*pointer-events: none/.test(css) && /\.tour-card \{[^}]*pointer-events: auto/.test(css), 'only the card takes the pointer');

console.log('test_tour: eleven steps, each on its own action (select, release, Interact, Jaunts, Move, Settings, Jump); resume at 4, skip at 6, replay; bubbles of 14 words or fewer');
