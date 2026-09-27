# Mobile welcome — T-1278

The loader settles into a welcome in the same dialog. Jaunts has an explicit
forthcoming notice; Explore on my own opens the shared destination inventory;
Enter Chicago starts at the scene's Sauganash spawn. The Start / Jaunts button
pauses world simulation and releases all movement input. Escape and Return to the
town restore focus to Start. The first-entry guide never covers the welcome.

No new settings are stored. Typing in the picker cannot change input backends or
capture the pointer. Entry unlocks audio but pointer capture waits for a canvas
click or movement key. Compact layout follows `visualViewport.height`, including
phone keyboards that leave the layout viewport unchanged.

## Recovery and integration

T-1278 was open, with no remote implementation branch or matching PR found.
Its dependency T-1277 was in draft chicago PR #129 at
`86ce9e29f4d24bccae6a74a8263a0747b6100133`. That implementation, tests and original
receipts are reused, with the dependency commit retained as a parent of this
integration. Existing dev research and geometry are preserved. The prior smoke
ledger is resolved to current dev plus this run's readings, rather than replacing
current measurements with an older branch's ledger. Both visitor changelog entries
are retained; existing dev release numbers are unchanged.

## Reproduction

From `chicago/4d/`, with Playwright installed and `PW_EXECUTABLE` set if needed:

```
bash tools/publish.sh
node tools/test_welcome.mjs
DESTINATIONS_EVIDENCE=docs/performance/shared-destinations/integration node tools/measure_destinations.mjs
SMOKE_STAGE=6 node tools/smoke_renderer.mjs --published
node tools/measure_boot_payload.mjs --check
./tools/preflight.sh
```

`test_welcome.mjs` covers cold mobile and desktop boot, structure/intersection/person
starts, paused input, default spawn, focus return, pointer capture only after entry,
reduced motion, saved light theme/wagon pace/horse travel mode, and internal list
scrolling at 320×568, 780×390 and a simulated 400-pixel visual viewport inside a
390×780 layout viewport. `results.json` and the PNGs are the browser receipts.
The final validation summary is in `validation.txt`. The final two-line touch-label
adjustment is covered by preflight; earlier screenshots label the same button Enter
Chicago, while touch visitors now see Tap to enter Chicago.

This is scoped entry/destination browser coverage, not all thirteen renderer parts.
No jaunt catalog, story playback, estimates or daybook is introduced here.
