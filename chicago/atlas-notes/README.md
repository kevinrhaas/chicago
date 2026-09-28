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
  functions (`notes_list`, `notes_whoami`, `notes_add`, `notes_archive`). The
  browser only ever holds the project's publishable key; the tables are not
  reachable with it, only those functions are, and they enforce the table above.
- `smoke.mjs` (this folder) — drives every page at 390×780 and 1280×800 against a
  fake database that follows `setup.sql`'s rules.

Until `DB` in `site/notes/notes.js` has a URL and key, the pages are unchanged:
no pencils, no button, no network calls.

## Turning it on (once)

1. **Create a new Supabase project** for the notes (e.g. `chicago-atlas-notes`,
   region *East US (Ohio)*). Nothing else lives in it.
2. **SQL editor → paste all of `setup.sql` → Run.** Safe to run again later.
3. **Create the editors** — in the same SQL editor, one line each:
   ```sql
   select notes_private.add_editor('Kevin');
   select notes_private.add_editor('Bill Tyre');
   ```
   Each returns a 64-character token **once** (only its SHA-256 is stored). That
   person's edit link is
   `https://chicago.polecat.live/?notes=<token>` — it works on any Atlas page.
   Opening it once remembers the editor on that device and removes the token from
   the address bar, so a URL copied afterwards never carries it. Notes are signed
   with the name given here.
4. **Project Settings → API Keys**: copy the *Project URL* and the *publishable*
   key (`sb_publishable_…`, never the secret one) into the `DB` block at the top
   of `site/notes/notes.js`, and ship that through the usual `dev` → `main` path.

## Running it

- **Take a link away:** `update notes_private.editors set active = false where name = 'Bill Tyre';`
  — then `add_editor` again for a fresh one.
- **Sign out on a device:** the panel's *Sign out on this device*, or open any
  page with `?notes=signout`.
- **Read everything, archived included:**
  `select created_at, page, target_label, author, body, archived_at, ip from notes_private.notes order by created_at desc;`
- **What is recorded per note:** the page, the item's key and label, the text, the
  editor, the time, the URL path, the IP (`x-forwarded-for`, stamped by the
  database — the browser cannot see its own), the browser's user-agent, and a
  random per-device id. Only editors see the IP / browser / device.

## Checking a change

```sh
PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome node chicago/atlas-notes/smoke.mjs
```

`SHOTS=<dir>` also saves screenshots of each state.
