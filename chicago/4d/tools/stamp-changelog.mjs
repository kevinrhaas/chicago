// stamp-changelog.mjs — stamp ship time onto the newest changelog entry and
// regenerate every entry's human `date` from its `ts`.
//
// The self-improvement loop prepends a new CHANGELOG entry with an EMPTY `ts`
// (`ts: ''`). This script fills that first empty `ts` with the real deploy time
// so dates reflect when a change actually shipped and can't be fabricated. It
// then rewrites every `date:` to a Central Time alias derived from that entry's
// `ts`, keeping the fleet-standard shape ({v, title, ts, date, items}).
//
// Run before merging whenever renderers/web/js/changelog.js changed. Nothing
// stamps later in the pipeline — tools/publish.sh only copies the file to the
// public URLs the fleet parses, it never edits it.
import { readFile, writeFile } from 'node:fs/promises';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const FILE = new URL('../renderers/web/js/changelog.js', import.meta.url);
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const SOURCE = path.join(ROOT, 'renderers/web/js/changelog.js');
const nowIso = new Date().toISOString();

/**
 * THE PUBLISHED MIRRORS OF changelog.js — T-0155, the latent sibling of T-0154.
 *
 * The changelog is authored inside the app and published to TWO paths that
 * `tools/check_published.mjs` compares byte for byte: `js/changelog.js` (the
 * fleet-parsed contract URL Manager and the launcher fetch) and
 * `walk/js/changelog.js` (inside the copied renderer tree, which the What's-new
 * tab imports). This script REWRITES the source. So a run that stamps AFTER
 * `tools/publish.sh` — which nothing in AGENTS.md forbids, and which the
 * documented order for a bake or a late edit actually produces — lands in
 * exactly the state T-0154 fixed for tickets.json: the gate red, and the only
 * remedy a remembered second publish.
 *
 * So the writer of the file maintains its mirrors, on the same deliberately
 * narrow terms as T-0154's:
 *  - it copies ONLY when this tool actually changed the source bytes. A mirror
 *    somebody else made stale must still fail the gate, and a blanket refresh on
 *    every invocation would quietly launder exactly that.
 *  - it never creates a mirror directory. An unpublished checkout stays
 *    unpublished; `publish.sh` is what decides a mirror exists.
 *  - `tools/test_changelog_mirror.mjs` pins the two copy lines in publish.sh, so
 *    this list and that script cannot drift into two disagreeing copies of one
 *    fact.
 */

import { WALK_SHIM } from './changelog_shim.mjs';


/**
 * Each published path and what belongs at it: the fleet contract URL takes the
 * file, the walk copy takes the shim above.
 */
const MIRRORS = [
  { dest: path.resolve(ROOT, '../../site/chicago/4d/js/changelog.js'),
    bytes: (src) => src },
  { dest: path.resolve(ROOT, '../../site/chicago/4d/walk/js/changelog.js'),
    bytes: () => Buffer.from(WALK_SHIM) },
];
/** The lines in publish.sh these mirrors are the twins of. The test pins them. */
export const PUBLISH_PINS = [
  'cp -f renderers/web/js/changelog.js "$SITE/js/changelog.js"',
  'cp -a renderers/web "$SITE/walk"',
  'node tools/stamp-changelog.mjs --write-mirrors',
];

/**
 * Carry the changelog to the published paths publish.sh copies it to. Only the
 * ones that already exist, and only when the caller says the source moved.
 * Returns the paths it wrote, so the caller can say so.
 */
function mirrorChangelog() {
  const src = readFileSync(SOURCE);
  const wrote = [];
  for (const { dest, bytes } of MIRRORS) {
    if (!existsSync(path.dirname(dest))) continue;   // never published: leave it that way
    const want = bytes(src);
    if (existsSync(dest) && readFileSync(dest).equals(want)) continue;
    writeFileSync(dest, want);
    wrote.push(path.relative(path.resolve(ROOT, '../..'), dest));
  }
  return wrote;
}

/**
 * `--write-mirrors`: install both published forms and stop, without touching the
 * source. This is `tools/publish.sh` calling the tool that OWNS the shim rather
 * than keeping a second copy of it in a heredoc — two hand-kept copies of one
 * fact is the drift PUBLISH_PINS exists to catch, and not having a second copy
 * is better than catching it.
 *
 * It writes unconditionally, which the stamp path deliberately does not: publish
 * IS the writer of the mirror, so there is nothing here to launder. The
 * anti-laundering rule guards the STAMP path, where a blanket refresh would hide
 * a mirror somebody else made stale from check_published.
 */
if (process.argv.includes('--write-mirrors')) {
  const src = readFileSync(SOURCE);
  for (const { dest, bytes } of MIRRORS) {
    if (!existsSync(path.dirname(dest))) continue;
    writeFileSync(dest, bytes(src));
    console.log(`   changelog.js published to ${path.relative(path.resolve(ROOT, '../..'), dest)} (T-0722)`);
  }
  process.exit(0);
}

function ctAlias(iso){
  const d = new Date(iso);
  if(isNaN(d)) return '';
  return d.toLocaleString('en-US',{ timeZone:'America/Chicago', month:'short',
    day:'numeric', year:'numeric', hour:'numeric', minute:'2-digit' }) + ' CT';
}

let src = await readFile(FILE, 'utf8');
const before = src;

// 1) Fill the first empty ts (newest entry sits at the top of the array).
let stamped = false;
src = src.replace(/ts:\s*(['"])\1/g, () => { stamped = true; return `ts: '${nowIso}'`; });

// 2) Regenerate every `date:` from the ts on the same entry. We walk entries by
//    matching each `ts: '<iso>'` and rewriting the `date: '...'` that follows it.
//
//    An entry written the way the contract describes it — `ts: ''`, no date, let
//    the stamper do the rest — has no `date:` to rewrite, so this used to skip it
//    and hand back a file the contract check then rejected for a missing date.
//    An author following the documented rule got a failure and no hint which
//    half of the rule was wrong, so the key is created when it is absent.
src = src.replace(/ts:\s*'([^']*)'(\s*,\s*)date:\s*'[^']*'/g,
  (_, iso, sep) => `ts: '${iso}'${sep}date: '${ctAlias(iso)}'`);
src = src.replace(/ts:\s*'([^']*)'(?!\s*,\s*date:)/g,
  (_, iso) => `ts: '${iso}', date: '${ctAlias(iso)}'`);


// ---- version assignment (fleet contract, 2026-08-10) ----------------------
// Authors write `v: null`; the number is assigned HERE, after any merge, where
// the real answer is knowable. Two branches that each prepend an entry both
// compute the same "top + 1", and whichever merges second is silently wrong.
// See polecat-platform docs/SHELL-API.md, and the `merge=union` half of the fix
// in .gitattributes — deriving the number alone does not stop the conflict.
//
// Numbered by POSITION, top being newest, because this tool patches text rather
// than parsing entries: re-serialising the file to sort by ts would reformat
// entries it did not author. Entries that already have a version are never
// touched — Manager keys release rows on `v` and every reader's "seen" marker
// compares against it, so renumbering history would re-notify everyone.
{
  const nulls = [...src.matchAll(/v:\s*null/g)];
  if (nulls.length) {
    const firstNumbered = src.match(/v:\s*(\d+)/);
    const base = firstNumbered ? Number(firstNumbered[1]) : 0;
    for (let i = nulls.length - 1, n = base; i >= 0; i--) {
      const m = nulls[i];
      src = src.slice(0, m.index) + `v: ${++n}` + src.slice(m.index + m[0].length);
    }
    console.log(`Assigned ${nulls.length} changelog version(s) from v${base}.`);
  }
  // A stamper that emits a duplicate version is worse than one that stops: the
  // duplicate ships and the contract check only catches it later, if at all.
  const vs = [...src.matchAll(/v:\s*(\d+)/g)].map((m) => Number(m[1]));
  for (let i = 1; i < vs.length; i++) {
    if (vs[i - 1] <= vs[i]) {
      console.error(`changelog: versions not strictly decreasing (v${vs[i - 1]} then `
        + `v${vs[i]}) — refusing to write.`);
      process.exit(1);
    }
  }
}

await writeFile(FILE, src);
console.log(stamped ? `Stamped newest changelog entry: ${nowIso}` : 'No empty changelog timestamp to stamp; dates refreshed.');

// T-0155: this tool is the WRITER of changelog.js, so it carries the file to the
// two published paths publish.sh copies it to. Only on a real rewrite — see
// MIRRORS' note on why a blanket refresh would weaken check_published.
if (src !== before) {
  const wrote = mirrorChangelog();
  for (const w of wrote) console.log(`   changelog.js mirrored to ${w} (T-0155)`);
}
