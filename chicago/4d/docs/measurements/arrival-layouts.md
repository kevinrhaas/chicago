# Arrival and jaunts — layouts (T-2046)

Piece 3 of 4 of T-1272. The reading is `arrival-layouts.json` beside this page, written
by `node tools/measure_arrival_layouts.mjs --layout <name> --write` against the
published mirror (`./tools/publish.sh` first). One layout per command: each takes
230-320 s in software, so the four together do not fit one 600 s foreground call.

**Acceptance, stated before the work:** on the published mirror, the path from the
welcome through Starting At…, the Jaunts menu, a jaunt's first stop, its place card and
its source, and back, passes at 320 px, at 780x390 landscape, with an on-screen keyboard
open in the picker, under safe-area insets, and at 1280x800 for focus. Passing means no
sideways scroll, every control the path owns at least 44x44 on touch, no overlap among
the place card, the drawer, the jaunt panel, the HUD's controls and the thumb's strip,
the path's panels inside the insets, at least 88 px of the stop's story showing with its
first link tappable, and focus never left on `<body>` and restored on Return.

| layout | viewport | insets (CDP override) | result |
|---|---|---|---|
| narrow-320 | 320x640 touch | top 47, bottom 34 | PASS, 8 steps |
| landscape | 780x390 touch | left 47, right 47, bottom 21 | PASS, 8 steps |
| keyboard-390 | 390x780 touch, 336 px keyboard in the picker | none | PASS, 9 steps |
| desktop | 1280x800 mouse and keyboard | none | PASS, 7 steps |

The desktop Tab order from the welcome's title is Jaunts → I'll Explore Myself → Sources
& City → Tap to enter → All coordinates → the appearance dial, all inside the welcome.

## What failed first, and what changed

Read with an exploratory version of the same walk on `dev` at ab1ee8f7, before any change:

1. **Landscape, at a stop:** the panel had 171 px, and the controls took all of it. The
   stop's story was clipped to a sliver and its first link was covered by the controls
   (`covered … by NAV.jaunt-controls`). Held sideways, the controls now stand in a column
   to the right of the story, in the order focus takes (`jaunt.css`).
2. **320 px, a card or source opened from a stop:** it started at 64 px + inset and covered
   the HUD's wrapped second row (pace, fly, theme, Menu). On a phone held upright it now
   starts where the panel does, 100 px + inset.
3. **Landscape, Starting At…:** the picker's minimum height was more than the card had,
   and it spilled out of its box under *Tap to enter Chicago*. The welcome now keeps its
   natural height in the explore region, and the card scrolls.
4. **Landscape, opening Jaunts:** the compact rule that hides the two actions lived in the
   lazily loaded `jaunt.css`. It landed a beat after the tap and hid the button that had
   focus, so focus fell to the page. The rule now lives in `walk.css` beside the
   picker's twin, and focus moves to the region it opened.
5. **Every layout, opening a card or source from a stop:** the link that opened it is hidden
   with the story, so focus fell to `<body>`. It now goes to Return, and Return gives it
   back to the link, which was already true.
6. **Targets:** the picker's *All* kind (35 px wide), the collapsed bar's End (43 px), the
   welcome's *All coordinates* link (15 px tall) and dial (32 px), and the place card's
   firm buttons on touch (32 px). All are now at least 44 px.
7. **Side insets:** the jaunt panel and the overlays now keep clear of a landscape notch
   (`max(8px, env(safe-area-inset-left/right))`).

The keyboard-open picker already passed: the search and the first result stay above a
336 px keyboard.

## Reported, not gated: a successor

Some controls on the path are owned by other surfaces. They are measured and listed in
each layout's `elsewhere`, and they are not passed or failed here:

- the HUD chips, 38 px tall;
- the drawer's Back and Close, 30x30, and its tabs, 37 px wide at 320 px;
- the place card's `why` toggles, 19x17.

The finding is written into T-2047, the acceptance report that names this section's
successors. The queue was at 204 lines against its ceiling of 140, so no new line was
filed.

**Not covered by this reading:** the emulated keyboard shrinks the layout viewport (the
`resizes-content` case). The visual-viewport-only case is the gentler one and is not read
separately. The safe-area insets come from Chromium's `Emulation.setSafeAreaInsetsOverride`
and were not checked on a device. The stills go to `/tmp/arrival-layouts` and are not
committed.
