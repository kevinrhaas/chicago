# chicago — 4D Chicago

A year-parameterized, walkable, source-cited reconstruction of early Chicago —
a research dataset with renderers attached. Live at
**[chicago.polecat.live](https://chicago.polecat.live/)**.

| URL | what it is |
|---|---|
| [`/`](https://chicago.polecat.live/) | the Chicago Building Atlas landing page |
| [`/4d/`](https://chicago.polecat.live/4d/) | the 4D walkthrough — opens on the target year, 1835 |
| [`/4d/1835/`](https://chicago.polecat.live/4d/1835/), `/4d/1812/`, `/4d/1880/` | a year's front door (a year with no scene yet says so) |
| [`/4d/dev/`](https://chicago.polecat.live/4d/dev/), `/4d/dev/1835/` | the `dev` branch's preview — not production, not indexed |
| `/4d/?year=1835&debug=1` | query parameters sit on top of any door; further state (a structure to open, a camera) goes in more parameters, never more path |
| [`/pre-fire/viewer/`](https://chicago.polecat.live/pre-fire/viewer/), [`/rebuilding-1870s/viewer/`](https://chicago.polecat.live/rebuilding-1870s/viewer/) | the Atlas's two map viewers |

## Where things are

| path | what it is |
|---|---|
| `chicago/4d/` | **the 4D project** — data, generators, renderers, tools, docs. Start at [`chicago/4d/AGENTS.md`](chicago/4d/AGENTS.md) |
| `chicago/reference/` | the research corpus the 4D data cites (large originals live on the Internet Archive; see `CORPUS_MANIFEST.csv`) |
| `chicago/pre_fire_v1/`, `chicago/postfire_1870s_v1/` | the Atlas datasets behind the two viewers |
| `site/` | the Pages root. `site/4d/` is **generated** by `chicago/4d/tools/publish.sh` and never committed |
| `.github/` | deploy (single deploy authority), the 4D dev gate, bake, promotion and PR-lap workflows |

**Tickets are not in this repo.** They live in
[kevinrhaas/chicago-tickets](https://github.com/kevinrhaas/chicago-tickets) — tickets
in folders of 250, `QUEUE.md` at its root — and are cloned into `chicago/4d/tickets/`
(gitignored here) by `bash chicago/4d/tools/tickets.sh`. Every ticket change is a
direct commit to that repo's `main`, so a code PR never carries, or conflicts on, a
ticket or the queue.

## History

This project was split out of [kevinrhaas/custom](https://github.com/kevinrhaas/custom)
on 2026-09-23, where it lived at `chicago/` and was served at
`custom.polecat.live/chicago/` (those URLs now redirect here). Its full commit history
— every PR a ticket's `pr:` field names from before that date — is in that repository;
this one starts from a snapshot of it (`main` from custom's `main`, `dev` from custom's
`dev`), with the paths inside `chicago/` unchanged so every tool and document still
reads the same.
