#!/usr/bin/env node
/**
 * A SHIPPED RELEASE NOTE KEEPS ITS NUMBER, AND STAYS IN THE FILE (T-1380).
 *
 * `check-changelog.mjs` reads the file it is given. It can see a duplicate number,
 * a gap, a title written twice and a bracket out of place; it cannot see an entry
 * that is no longer there, or a number that has quietly changed hands. Both have
 * happened on `dev`, and both read "contract OK":
 *
 *   * DROPPED AND RE-USED. 2026-09-19: #1502 (T-1366) shipped "Six dates that would
 *     not stick" as v971 at 06:06. #1504 (T-1370) had branched before it, resolved
 *     its changelog conflict by taking its own side whole, and was stamped v971 at
 *     06:31. The first entry was gone and v971 named a different release — after
 *     Manager and the launcher had already read it.
 *   * RENUMBERED. Six times on this repository's own `dev` between 2026-09-23 and
 *     2026-10-04 (05ac72c34, fa4b23d88, 4f6585852, 17756b47c, and c602f4988 twice) a
 *     merge kept a shipped entry and moved it to another number, so the number the
 *     feed had read now named somebody else's release.
 *
 * Neither leaves a mark in the result that a file-only check can read: the numbers
 * are still dense and descending and every title is still unique. What gives them
 * away is the BASE. So this holds the tree to it:
 *
 *   every entry the base carries with a number and a stamp must still be here,
 *   under the SAME number.
 *
 * An entry is known by its `ts`, not its title. The stamp is written once, by the
 * stamper, when the entry ships, and nothing rewrites a stamped one; a title can be
 * corrected after the fact and still be the same release. So an edited title
 * passes, and a re-used number is caught even though the number itself is still
 * present — the stamp under it is a different one.
 *
 * WHICH BASE: the merge base of HEAD with the branch it will merge into
 * (`origin/$GITHUB_BASE_REF`, else `origin/dev`), the same choice and the same two
 * states as tools/check_rulings_not_lost.py (T-1124): with C4D_GATE_REQUIRE_BASE=1
 * (CI) a base that will not resolve is RED; without it (a sandbox, a shallow clone)
 * it is a WARNING naming what went unasked. A gate may not count a skip as a pass.
 * The tree compared is the WORKING TREE, so a bad conflict resolution is refused
 * before it is committed, which is the moment it is made.
 *
 * Entries the branch wrote itself are not in the base, so the stamper may number
 * and re-number them freely; the base's entries are settled history, which is
 * exactly the rule tools/merge-changelog.mjs already follows ("theirs ... taken
 * whole and never renumbered").
 *
 *   node tools/changelog-history.mjs               hold the tree to its base
 *   node tools/changelog-history.mjs --base REF    hold it to a different ref
 *   node tools/changelog-history.mjs --self-test   prove each refusal fires
 */
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const HERE = fileURLToPath(new URL('..', import.meta.url));      // chicago/4d/
const REL = 'renderers/web/js/changelog.js';

/**
 * RETIRED numbers are the one sanctioned gap, and each says why. A number goes
 * here only when the entry it was stamped onto was a COPY of another entry and
 * was removed — never to make room for a dropped one, which is what the gap
 * check exists to catch. A shipped number is never re-used, so it is retired.
 * Lives here, and check-changelog.mjs imports it, because both checks must agree
 * on which numbers may leave the file.
 */
export const RETIRED = new Map([
  // T-2083: the merge driver could not read the double-quoted title of v1397
  // ("Kelsey's boarding-house on the sand hills is painted yellow"), so laps
  // put it back on top as new and the stamper numbered each copy. Removed.
  [1411, 'T-2083: a merge-driver copy of v1397'],
  [1421, 'T-2083: a merge-driver copy of v1397'],
  [1422, 'T-2083: a merge-driver copy of v1397'],
  [1423, 'T-2083: a merge-driver copy of v1397'],
  [1424, 'T-2083: a merge-driver copy of v1397'],
]);

/**
 * The problems with `head` as a successor of `base`. Both are CHANGELOG arrays.
 * Only entries the base has STAMPED (a numeric `v` and a non-empty `ts`) are held:
 * an unstamped one has not shipped and has no number to keep.
 */
export function compareShipped(base, head, retired = RETIRED) {
  const problems = [];
  const byTs = new Map();
  for (const e of head) if (e.ts) byTs.set(e.ts, [...(byTs.get(e.ts) || []), e]);
  const byV = new Map(head.map((e) => [e.v, e]));
  const short = (t) => `"${String(t ?? '').slice(0, 60)}"`;
  for (const e of base) {
    if (typeof e.v !== 'number' || !e.ts || retired.has(e.v)) continue;
    const here = byTs.get(e.ts) || [];
    if (!here.length) {
      const same = head.filter((h) => h.title === e.title);
      if (same.length) {
        problems.push(`v${e.v} ${short(e.title)} (stamped ${e.ts}) is v${same.map((h) => `${h.v} stamped `
          + `${h.ts || '(none)'}`).join(', v')} here — a shipped entry was re-stamped`
          + (same.some((h) => h.v === e.v) ? '' : ' and renumbered, so the number the feed already read now '
            + 'names another release')
          + '. Put the base\'s entry back verbatim; only this branch\'s own entries are stamped');
        continue;
      }
      const now = byV.get(e.v);
      problems.push(`v${e.v} ${short(e.title)} (stamped ${e.ts}) shipped in the base and is gone from `
        + 'this tree — a merge dropped it'
        + (now ? `, and v${e.v} now names ${short(now.title)}: one number, two releases` : '')
        + '. Put the base\'s entry back verbatim; only this branch\'s own entries are re-numbered');
      continue;
    }
    if (!here.some((h) => h.v === e.v)) {
      problems.push(`v${e.v} ${short(e.title)} shipped in the base as v${e.v} and is v`
        + `${here.map((h) => h.v).join('/v')} here — a shipped entry was renumbered, so the number the `
        + 'feed already read now names another release. Keep the base\'s numbers; re-stamp only this '
        + 'branch\'s own entries');
    }
  }
  return problems;
}

/** Load a changelog module from its source text, without touching the file. */
export async function loadSource(src) {
  const mod = await import('data:text/javascript;base64,' + Buffer.from(src).toString('base64'));
  return mod.CHANGELOG;
}

const git = (...args) => {
  try {
    return execFileSync('git', args, { cwd: HERE, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'],
      maxBuffer: 64 << 20 });
  } catch { return null; }
};

/** The first ref that exists, in the order a run actually has one. */
export function resolveBase(explicit) {
  const candidates = explicit ? [explicit]
    : [...(process.env.GITHUB_BASE_REF ? [`origin/${process.env.GITHUB_BASE_REF}`] : []),
      'origin/dev', 'dev'];
  for (const ref of candidates) {
    if (git('rev-parse', '--verify', '--quiet', `${ref}^{commit}`) !== null) return { ref, candidates };
  }
  return { ref: null, candidates };
}

/**
 * Hold the working tree's changelog (`head`, already loaded) to its base.
 * Returns { problems, warnings, note }.
 */
export async function holdToBase(head, { base: explicit } = {}) {
  const { ref, candidates } = resolveBase(explicit);
  if (!ref) {
    const what = `no base ref resolved (tried ${candidates.join(', ')}), so nothing can say whether `
      + 'a shipped release note was dropped or renumbered';
    return process.env.C4D_GATE_REQUIRE_BASE
      ? { problems: [`${what} — a GATE may not count a skip as a pass: fetch the base ref`], warnings: [] }
      : { problems: [], warnings: [`${what}. This is a sandbox or a shallow clone, so the check goes on; `
        + 'CI sets C4D_GATE_REQUIRE_BASE=1 and would be red here']};
  }
  const mb = (git('merge-base', ref, 'HEAD') || '').trim() || ref;
  const src = git('show', `${mb}:./${REL}`);
  if (src === null) return { problems: [], warnings: [`the base ${ref} (${mb.slice(0, 9)}) carries no ${REL}`] };
  let base;
  try { base = await loadSource(src); } catch (err) {
    return { problems: [], warnings: [`the base's changelog at ${mb.slice(0, 9)} does not load (${err.message}); `
      + 'nothing to hold this tree to']};
  }
  return { problems: compareShipped(base, head), warnings: [],
    note: `held to ${ref} at ${mb.slice(0, 9)}: ${base.filter((e) => typeof e.v === 'number' && e.ts).length} shipped entries` };
}

// ---------------------------------------------------------------------------
// the self-test — the check.sh convention (T-0763): prove each refusal FIRES,
// on the shapes that actually happened, and that the lawful ones still pass.
function selfTest() {
  const e = (v, title, ts) => ({ v, title, ts, items: ['x'] });
  const base = [
    e(971, 'Six dates that would not stick', '2026-09-19T06:06:11.774Z'),
    e(970, 'Three hundred and eight working people', '2026-09-19T05:23:09.295Z'),
  ];
  const cases = [
    ['the T-1380 incident: dropped, and its number given to the next release', 1,
      [e(971, 'How many people each tavern and boarding house could sleep', '2026-09-19T06:31:00.000Z'),
        base[1]], /gone from this tree.*now names/],
    ['dropped, number not re-used', 1, [base[1]], /gone from this tree/],
    ['re-stamped and renumbered (c602f4988: a lap reset a shipped entry and the stamper re-numbered it)', 1,
      [e(972, base[0].title, '2026-09-19T07:00:00.000Z'), base[1]], /re-stamped and renumbered/],
    ['renumbered (c602f4988: two shipped entries each moved up one)', 2,
      [e(973, 'Mine', '2026-09-19T07:00:00.000Z'), { ...base[0], v: 972 }, { ...base[1], v: 971 }],
      /renumbered/],
    ['a branch entry on top, base kept verbatim', 0, [e(972, 'Mine', '2026-09-19T07:00:00.000Z'), ...base]],
    ['an unstamped branch entry on top', 0, [{ ...e(null, 'Mine', ''), v: null }, ...base]],
    ['a shipped title corrected in place', 0, [{ ...base[0], title: 'Six dates that would not hold' }, base[1]]],
    ['a retired copy removed', 0, base, null, [e(1411, 'copy', '2026-10-04T08:31:00.000Z'), ...base]],
    ['an unstamped base entry is not held', 0, base, null, [{ ...e(null, 'draft', ''), v: null }, ...base]],
  ];
  let bad = 0;
  for (const [name, want, head, re, baseOver] of cases) {
    const got = compareShipped(baseOver || base, head);
    const ok = got.length === want && (!re || got.every((p) => re.test(p)));
    if (!ok) bad++;
    console.log(`   ${ok ? 'ok  ' : 'FAIL'}  ${name}: ${got.length} refusal(s), want ${want}`);
    if (!ok) for (const p of got) console.log(`          ${p}`);
  }
  // check-changelog.mjs must still call this; a contract check that stopped asking
  // the base would read green on exactly the merge this file was written for.
  const cc = readFileSync(new URL('./check-changelog.mjs', import.meta.url), 'utf8');
  const wired = /holdToBase\(/.test(cc) && /from '\.\/changelog-history\.mjs'/.test(cc);
  if (!wired) bad++;
  console.log(`   ${wired ? 'ok  ' : 'FAIL'}  check-changelog.mjs holds the tree to its base`);
  if (bad) { console.error(`changelog-history self-test FAILED: ${bad}`); process.exit(1); }
  console.log('changelog-history self-test OK');
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) selfTest();
  else {
    const i = args.indexOf('--base');
    const head = await loadSource(readFileSync(new URL(`../${REL}`, import.meta.url), 'utf8'));
    const { problems, warnings, note } = await holdToBase(head, { base: i >= 0 ? args[i + 1] : undefined });
    for (const w of warnings) console.warn(`  WARN  ${w}`);
    for (const p of problems) console.error(`  FAIL  ${p}`);
    if (problems.length) process.exit(1);
    console.log(`shipped release notes intact${note ? ` — ${note}` : ''}`);
  }
}
