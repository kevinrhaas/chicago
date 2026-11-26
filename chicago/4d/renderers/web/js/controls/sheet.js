/**
 * The controls, as the Guide's controls sheet lists them (T-2661, NAV-803).
 *
 * Three sheets, one per control scheme (intent.js § controlScheme): touch, where the left
 * thumb walks and the right side of the screen looks, keyboard and mouse, and (T-3749) a
 * game controller. Each row
 * is `[keys, what it does]`; a keyboard row's keys are shown as keys. These are the
 * bindings the page actually has — js/controls/pointerlock.js, hud.js's key handler and
 * navigator.js's (N, 1–9, T-2622) — and tools/test_nav_guide.mjs holds the keyboard
 * sheet to every key the drawer's own list names. T-3445: people, the Interact key (R,
 * js/interact.js) and Go to's photos.
 */
export const CONTROL_SHEETS = {
  touch: {
    title: 'Touch',
    intro: 'Your left thumb walks; the right side of the screen looks.',
    rows: [
      [['Left thumb'], 'walk: touch the lower left and push the way you want to go'],
      [['Push it all the way'], 'run'],
      [['Drag the right side'], 'look around'],
      [['Tap a building'], 'its card: Design, Timeline, Photos, Sources'],
      [['Tap a person'], 'their card; Follow walks you alongside them'],
      [['Interact'], 'shows when a gate is in reach; tap it to open or shut it'],
      [['Fly'], 'rise above the town; ▲ and ▼ appear on the right to climb and descend'],
      [['Go to'], 'a viewpoint, a building or a photo; pick one to go there'],
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
      [['Click', 'E'], 'inspect a building or a person: its card'],
      [['R'], 'interact: open or shut a gate in reach'],
      [['F'], 'fly, or back to walking'],
      [['Space', 'Q'], 'climb and descend, while flying'],
      [['C'], 'the Confidence view'],
      [['G'], 'go to a viewpoint, a building, a corner or a photo'],
      [['M'], 'the whole map'],
      [['P'], 'change your pace'],
      [['N'], 'open or close the Navigator'],
      [['1–9'], 'open a Navigator app, in the order of its rail'],
      [['H'], 'the menu'],
      [['Esc'], 'give the cursor back, or close what is open'],
    ],
  },
  // T-3749: a Bluetooth or cable game controller (js/controls/gamepad.js, its BINDINGS).
  controller: {
    title: 'Controller',
    intro: 'Pair a Bluetooth controller with this device and press any button. The left stick walks; the right stick looks.',
    rows: [
      [['Left stick'], 'walk'],
      [['RT'], 'run on foot; climb while flying'],
      [['LT'], 'descend while flying'],
      [['Right stick'], 'look around'],
      [['A'], 'inspect a building or a person under the crosshair: its card'],
      [['B'], 'go back: close what is open'],
      [['X'], 'interact: open or shut a gate in reach'],
      [['Y'], 'fly, or back to walking'],
      [['LB', 'RB'], 'on a jaunt, the stop before or the next stop'],
      [['Menu'], 'open or close the Navigator'],
      [['View'], 'the whole map'],
      [['D-pad down'], 'go to a viewpoint, a building, a corner or a photo'],
      [['D-pad up'], 'reach the keys on screen: the D-pad moves between them, A presses, B goes back'],
    ],
  },
};

/** The schemes, in the order the sheet offers them. */
export const SCHEMES = ['touch', 'keyboard', 'controller'];
