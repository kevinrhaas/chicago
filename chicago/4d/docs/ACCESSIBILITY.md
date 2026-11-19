# Accessibility — where 4D Chicago stands against WCAG 2.1 AA

T-3671, 2026-11-19. The owner asked for "the full accessibility pass": keyboard and
screen-reader paths through every menu and card, text size, colour-blind-safe confidence
colours, transcripts for narration, and motion-comfort settings. This page says what the
interface now does, criterion by criterion, which browser test holds it, and what still falls
short. It is a statement of work and its tests, **not a third-party audit**, and it makes no
legal conformance claim. PR 2197 (T-3658) was the first slice: native Navigator zoom, keyboard
picture viewers and the rail's Tab stop.

## The one thing that cannot be read aloud

The town itself is a WebGL canvas. A screen reader hears it as one picture named for its year
("Chicago in 1835, a walkable 3-D view"). Its contents reach a non-visual reader through text:
Home's "You are at" and "Right in front of you", the Interact key, Go to and the Map's lists,
the People directory, and every building and person card. Floating name cards are drawn in
WebGL too; the People directory and Interact are their text alternative.

## By success criterion

| WCAG 2.1 | What the interface does | Held by |
|---|---|---|
| 1.1.1 Non-text content | Card pictures and portraits carry alt text from their captions and credits; the canvas is a named image; decorative marks are hidden; the sources bar is a named image. | test_a11y_cards, test_a11y_menus |
| 1.2.1 Audio-only | Jaunt narration is recorded from the card's own words (clips are keyed by the hash of the text on screen). The words being read are highlighted while they play; when a reading-age tab shows other words, a Transcript disclosure shows the exact script. Withheld text is not voiced. | test_a11y_jaunts |
| 1.3.1 Info and relationships | Screens, cards and sections have real headings; tab strips are tablists with labelled tabpanels; notebook fields are tied to their entries. | test_a11y_menus, test_a11y_cards |
| 1.3.4 Orientation | Nothing locks orientation; no `maximum-scale`. | test_a11y_visual, test_accessibility_browser |
| 1.4.1 Use of colour | A grade is told by shape as well as colour everywhere: attested full dot / solid edge, inferred half dot / dashed edge / upright stripes, reconstructed ring / dotted edge / hatching. The town's Confidence view stripes and hatches buildings ("Grade patterns", on by default). The gold/silver/bronze palette stays at least ΔE 13.8 apart under protan, deutan and tritan simulation. | test_a11y_colour_motion, check_grade_colors |
| 1.4.2 Audio control | Sound is off until chosen; Settings › Sound has separate levels; the jaunt panel has Pause/Resume narration. | test_a11y_jaunts |
| 1.4.3 Contrast (minimum) | Text at 4.5:1 (large 3:1) measured against each panel laid over both a white and a black scene, in all four appearances and both tones. | test_a11y_visual, check_navigator_contrast |
| 1.4.4 Resize text | Settings › Display › Text size goes to 200 % and reaches the Navigator, rail, HUD, cards, jaunt panel, tour, arrival screen and name cards. Browser zoom to 200 % works. | test_a11y_visual |
| 1.4.10 Reflow | At 320 px wide and at 200 % text on a phone, panels wrap and stack rather than scroll sideways. | test_a11y_visual |
| 1.4.11 Non-text contrast | Field edges, lit keys and the focus ring at 3:1 or better. | test_a11y_visual |
| 1.4.12 Text spacing | No text clipped with WCAG's spacing overrides (two decorative device labels excepted). | test_a11y_visual |
| 1.4.13 Content on hover or focus | A term's meaning stays while hovered and closes on Esc without closing the card under it. | test_a11y_cards |
| 2.1.1 Keyboard | Every rail app, Navigator screen, Settings tab, jaunt control and card works by Tab, Enter, Space, arrows in tab strips and radio groups, Home/End, and Esc. People and Inspect rows open person cards by keyboard. | all six a11y tests |
| 2.1.2 No keyboard trap | Picture viewers contain focus and release it on Esc; cards and the tour do not trap. | test_accessibility_browser, test_a11y_cards, test_a11y_jaunts |
| 2.1.4 Character key shortcuts | Settings › Look › Letter keys: Off holds back every bare letter, number and symbol shortcut; arrows, Space, Enter and Esc still work. | test_a11y_letter_keys |
| 2.2.1 Timing adjustable | The jaunt's closing scene waits while the visitor touches, scrolls, presses a key or pauses the voice. | test_a11y_jaunts |
| 2.2.2 Pause, stop, hide | Settings › Look › Motion (System, Reduce, Full) stops the telemetry strip, pulses and blinks. | test_a11y_colour_motion |
| 2.3.1 Three flashes | Checked: the fastest flicker is a night-light flame at about 1.7 Hz; muzzle flashes are single. | (measured, T-3671 PR) |
| 2.4.1 Bypass blocks | A "Skip to the Navigator" link. | test_a11y_menus |
| 2.4.2 Page titled | "1835 · 4D Chicago", with the open screen named first. | test_a11y_menus |
| 2.4.3 Focus order | Opening a screen or card moves focus into it; closing returns focus to what opened it (the canvas, for a card opened from the town). | test_a11y_menus, test_a11y_cards |
| 2.4.6 / 2.4.7 | Labelled headings; one 2 px focus ring with a halo, visible on every Tab stop in every appearance. | test_a11y_visual |
| 2.5.3 Label in name | Every visible rail label is inside its key's accessible name. | test_a11y_menus |
| 3.2.1 / 3.2.2 | Arrow keys in a tab row stay within the open app; nothing switches app on focus. | test_a11y_menus |
| 3.3.2 Labels | Notebook notes and their Edit/Remove keys are labelled by their entry. | test_a11y_cards |
| 4.1.2 Name, role, value | Tabs, dialogs, toggles (aria-pressed / aria-expanded), radio groups and icon-only keys have roles, names and states. | all six a11y tests |
| 4.1.3 Status messages | One polite status line announces arriving in a year and screens opening and closing; the jaunt panel announces each stop. | test_a11y_menus, test_a11y_jaunts |

Motion beyond AA (2.3.3, asked for by the owner): Reduce also turns off the walking head bob,
turns fly-ins and the Jump and Recall rings into cuts, and stands the idle horses still.

## Known gaps

- The town canvas and its WebGL name cards are not themselves readable (above).
- With Letter keys Off, Interact's E and the flight keys Q/E have no keyboard stand-in other than
  the on-screen Interact and Move controls.
- Under Full motion on a device that asks for less, the stylesheet's own reduced-motion rules
  still apply; only scripted motion follows Full. Telemetry and blinks stop only under Reduce.
- On a phone at 200 % text the open sheet leaves about 300 px for its screen; the docked
  phone pill, the minimap and the compass letters keep their size.
- Jaunt captions do not name the speaker; arriving after the opening flight announces the stop
  without moving focus; the closing scene's advance has no setting to switch it off.
- Reading-age tabs swap the text in place, so they are a tablist without tabpanels. A "why"
  key's name has no row context; evidence tiles are named by title only.
- The visitor portrait canvas in Settings › You has no label.
- Not yet tried with a physical screen reader (NVDA, JAWS, VoiceOver) or on a Chromebook. The
  tests assert the accessibility tree and keyboard paths in Chromium only.

## Running the tests

    cd chicago/4d
    for t in menus cards jaunts visual colour_motion letter_keys; do node tools/test_a11y_$t.mjs; done
    node tools/test_accessibility_browser.mjs

Each is a Playwright fixture over the real markup, CSS and modules (no town load), at 390×780
and 1280×800, under a minute.
