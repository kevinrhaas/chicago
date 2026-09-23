---
id: T-0108
title: The confidence menu's clicks fall through to the world, and nothing closes a panel from the keyboard
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-19
pr: 265
claimed_by: run 8/19/2026, 1:56:06 PM CT
blocked_on: null
needs_bake: false
---

The confidence menu's clicks fall through to the world, and nothing closes a panel from
the keyboard.

**The owner, 2026-08-19, two asks he suggested could ride together:** *"when you drop down
confidence drop down you cant click on the things in the drop down because that is still
like navigation? like when you click on the check box to turn it on or off you lose the
drop down window and nothing happens"* — and *"from the keyboard side, would be nice if
there was a key maybe escape unless that messes with something? from when you have an
inspection panel open to close it so you dont have to scroll up and hit the close button
maybe there is a toggle on toggle off for that."*

They are one unit: both are the control layer failing to take an input it should.

## 1. The menu is not clickable, and the diagnosis is exact

His guess — "that is still like navigation" — is right, and it is one missing line.

`.hud` carries `pointer-events: none` (css/styles.css ≈ 204) so the 3D view stays live
under the overlay, and each interactive piece re-enables it: `.badge` has
`pointer-events: auto`, `.chip` has it — **`.confidence-menu` does not.** So every click
on a checkbox passes THROUGH the menu to the canvas, and two things then happen at once:

- `canvas.addEventListener('click', …)` in `js/main.js` re-locks the pointer, which is
  the "that is still like navigation" he felt; and
- the click-away handler in `js/hud.js` (≈ line 191) sees `e.target` is the canvas, which
  is not inside `#confidence-group`, so it closes the menu.

Hence: the window vanishes and nothing toggles. The checkbox never received the click at
all. `.confidence-menu { pointer-events: auto; }` is the fix; check its siblings while
there (the Go-to and What's-new panels ride the same overlay — anything that re-enables
pointer events only on `.chip` has the same hole).

## 2. A key that closes the panel

Escape is the natural one and it does **not** clash with anything this app owns — but it
IS the browser's own pointer-lock release, which cannot be overridden, so the handler must
cooperate rather than fight: act on Escape only when a panel is open, and let the browser
have it otherwise. He also floated a toggle, which is the better fit for the key that
opened the thing: **E (and Space) inspect — pressing the same key with a panel open should
close it**, so the reach that opened the card also closes it. Do both: Escape closes,
the inspect key toggles.

Neither may fire while typing in the Go-to box (`isTyping` already guards the other key
handlers — use it).

**Acceptance:** with the confidence menu open, clicking a level's checkbox hides that
level and the menu STAYS OPEN, at desktop and at 390×780; and with an inspection panel
open, Escape closes it and a second press of the inspect key closes it, neither firing
while typing in Go-to. A smoke assertion for the checkbox click (it is a one-line CSS
regression that no gate would otherwise catch) and one for the key. Zero pageerrors.

**Links:** `renderers/web/css/styles.css` (`.hud` pointer-events, `.confidence-menu` ≈
1213) · `renderers/web/js/hud.js` (`setConfMenu`, the click-away at ≈ 191) ·
`renderers/web/js/main.js` (the canvas re-lock click, the capture keydown at ≈ 620) ·
`renderers/web/js/controls/pointerlock.js` (`isTyping`, the E/Space inspect binding).
