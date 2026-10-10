# Interface webfonts (T-2036)

Latin subsets of Google Fonts families, self-hosted so the interface makes no third-party
request. Every family is licensed under the SIL Open Font License 1.1
(https://openfontlicense.org): Barlow, Barlow Semi Condensed, Instrument Serif, IBM Plex Mono
(Control Room); Cormorant Garamond, Cormorant SC, Courier Prime (Precision Brass); League
Spartan, Jost, Space Mono (World's Fair); Saira, Share Tech Mono (Deep Space).
The `@font-face` rules are at the top of `css/skins.css`.

## Signboard faces (T-2282)

The `sign-*.woff2` files are the lettering of the 1835 town's signboards, painted into the
sign atlas by `js/signage.js` — not interface type. Latin subsets of Google Fonts families,
self-hosted for the same reason, every one under the SIL Open Font License 1.1: Old Standard TT
(regular, bold, italic — the signwriter's roman and the trade line's italic), Abril Fatface (the
fat face), Alfa Slab One (the Egyptian) and Anton (the condensed grotesque). Which period letter
each one stands in for, and that the choice is reconstructed, is docs/LIBERTIES.md L413.
