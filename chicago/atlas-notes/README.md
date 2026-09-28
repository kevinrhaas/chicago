# Atlas notes

Notes on the cards, maps, images and pages of the Chicago Building Atlas's
documentation sites (the landing page, `/pre-fire/`, `/rebuilding-1870s/` and
`/prairie-1904/` — **not** 4D). A light pencil opens a small panel listing the
notes filed against that item, newest first, with the date and who wrote it.

| who | sees | can |
|---|---|---|
| anyone | every note that is not archived; a pencil only where notes exist | read |
| an editor (holds a personal edit link) | everything, including archived notes and the IP / browser / device each note was written from; a pencil on every item | add, archive, restore |

Nothing is ever deleted: **archive** hides a note from the page and keeps it in
the database, with who archived it and when.

## Where the pieces are

- `site/notes/notes.js` + `notes.css` — the whole client. A page opts in with one
  `<script src="/notes/notes.js" data-page="…" defer>`; items opt in with
  `data-note="<key>" data-note-label="<name>"` (see the header of notes.js).
- `setup.sql` (this folder) — the database: two private tables and four public
  functions (`atlas_notes_list`, `atlas_notes_whoami`, `atlas_notes_add`, `atlas_notes_archive`). The
  browser only ever holds the project's publishable key; the tables are not
  reachable with it, only those functions are, and they enforce the table above.
- `smoke.mjs` (this folder) — drives every page at 390×780 and 1280×800 against a
  fake database that follows `setup.sql`'s rules.

The notes live in the two Supabase projects analytics.polecat.live already uses,
in their own `atlas_notes_private` schema — nothing of analytics' is touched:

| pages | project |
|---|---|
| chicago.polecat.live (production) | `polecat` (`lnngiprrrcxtsawamqei`) |
| the `/…/dev/…` previews and a local server | `polecat_dev` |

`PROJECTS` at the top of `site/notes/notes.js` holds each one's URL and
publishable key. An environment with no URL/key yet is unchanged: no pencils, no
button, no network calls. An edit link belongs to one project, so production and
dev each have their own links, remembered separately.

## Turning it on (once per project)

1. **In the project's SQL editor, paste all of `setup.sql` → Run.** Safe to run
   again later. It creates only `atlas_notes_private.*` and four
   `public.atlas_notes_*` functions.
2. **Create the editors** — in the same SQL editor, one line each:
   ```sql
   select atlas_notes_private.add_editor('Kevin');
   select atlas_notes_private.add_editor('Bill Tyre');
   ```
   Each returns a 64-character token **once** (only its SHA-256 is stored). That
   person's edit link is `https://chicago.polecat.live/?notes=<token>` for
   `polecat`, or a `/4d/dev/prairie-1904/viewer/?notes=<token>` preview address for
   `polecat_dev`. Opening it once remembers the editor on that device and removes
   the token from the address bar, so a URL copied afterwards never carries it.
   Notes are signed with the name given here.
3. **`polecat_dev` only:** put its *Project URL* and *publishable* key
   (`sb_publishable_…`, never the secret one) into `PROJECTS.dev`. Production's
   are already there — the same pair `app/workspaces.js` in analytics ships.

## Running it

- **Take a link away:** `update atlas_notes_private.editors set active = false where name = 'Bill Tyre';`
  — then `add_editor` again for a fresh one.
- **Sign out on a device:** the panel's *Sign out on this device*, or open any
  page with `?notes=signout`.
- **Read everything, archived included:**
  `select created_at, page, target_label, author, body, archived_at, ip from atlas_notes_private.notes order by created_at desc;`
- **What is recorded per note:** the page, the item's key and label, the text, the
  editor, the time, the URL path, the IP (`x-forwarded-for`, stamped by the
  database — the browser cannot see its own), the browser's user-agent, and a
  random per-device id. Only editors see the IP / browser / device.

## Checking a change

```sh
PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome node chicago/atlas-notes/smoke.mjs
```

`SHOTS=<dir>` also saves screenshots of each state.
