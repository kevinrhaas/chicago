/**
 * The controls, as the Guide's controls sheet lists them (T-2661, NAV-803).
 *
 * Two sheets, one per control scheme (intent.js § controlScheme): touch, where the left
 * thumb walks and the right side of the screen looks, and keyboard and mouse. Each row
 * is `[keys, what it does]`; a keyboard row's keys are shown as keys. These are the
 * bindings the page actually has — js/controls/pointerlock.js, hud.js's key handler and
 * navigator.js's (N, 1–9, T-2622) — and tools/test_nav_guide.mjs holds the keyboard
 * sheet to every key the drawer's own list names.
 */
export const CONTROL_SHEETS = {
  touch: {
    title: 'Touch',
    intro: 'Your left thumb walks; the right side of the screen looks.',
    rows: [
      [['Left thumb'], 'walk: touch the lower left and push the way you want to go'],
      [['Push it all the way'], 'run'],
      [['Drag the right side'], 'look around'],
      [['Tap a building'], 'inspect it: what it was, and the sources for it'],
      [['Fly'], 'rise above the town; ▲ and ▼ appear on the right to climb and descend'],
      [['Tap the small map'], 'the whole field'],
      [['The Navigator'], 'tap the pill at the bottom, or swipe it up, to open it; swipe down to drop it a level'],
    ],
  },
  keyboard: {
    title: 'Keyboard',
    intro: 'Click the scene once and the mouse looks around; Esc gives the cursor back.',
    rows: [
      [['W', 'A', 'S', 'D'], 'walk (the arrow keys work too)'],
      [['Shift'], 'hurry: a run on foot, a gallop on a horse'],
      [['Mouse'], 'look around'],
      [['Click', 'E'], 'inspect a building: what it was, and the sources for it'],
      [['F'], 'fly, or back to walking'],
      [['Space', 'Q'], 'climb and descend, while flying'],
      [['C'], 'the Confidence view'],
      [['G'], 'go to a viewpoint, a building or a street corner'],
      [['M'], 'the whole map'],
      [['P'], 'change your pace'],
      [['N'], 'open or close the Navigator'],
      [['1–9'], 'open a Navigator app, in the order of its rail'],
      [['H'], 'the menu'],
      [['Esc'], 'give the cursor back, or close what is open'],
    ],
  },
};

/** The two schemes, in the order the sheet offers them. */
export const SCHEMES = ['touch', 'keyboard'];
