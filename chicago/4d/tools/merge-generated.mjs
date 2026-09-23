#!/usr/bin/env node
/**
 * The git merge driver for this repo's BUILD PRODUCTS.
 *
 * WHAT IT DOES: keeps OURS, prints the command that regenerates the file, and
 * exits 0. That is the whole driver. The value is not in the merge — it is in
 * refusing to spend a hand resolution on a file whose contents are a function of
 * other files.
 *
 * WHY, AND IT IS A LOG RATHER THAN AN ARGUMENT (T-0831). PR #906 was open for
 * about seventy minutes. `dev` moved FIVE times under it — #904, #907, #908,
 * #905, #858 — and every one of the five merges conflicted, always in generated
 * files and never once in the substantive diff:
 *
 *   lap 1  #904   BOARD.md, tickets.json x2, build.json, walk/index.html
 *   lap 2  #907   the same five (plus STATUS.md, a real conflict, hand-merged)
 *   lap 3   --    the same five, measured with merge-tree before the lap
 *   lap 4  #905   the same five
 *   lap 5  #858   BOARD.md, tickets.json x2
 *
 * check.sh, QUEUE.md, changelog.js and every ticket source auto-merged every
 * time, because those carry a driver or are hand-authored. Two other PRs report
 * the same independently: #894 ("each one collides on the same four generated
 * files", four rebases paid and the fifth is where its clock ran out) and #850
 * ("Every conflict so far has been in a generated file... The substantive diff
 * has merged cleanly every time", rebased twice, gate run three times on three
 * bases, then parked on `hold` with finished green work). #850 prices it: ~19
 * minutes of honest verification per lap, during which dev took three more
 * merges.
 *
 * WHY KEEPING OURS IS SAFE HERE AND NOWHERE ELSE. Every file this driver is
 * declared on is ALREADY REFUSED BY THE GATE WHEN STALE — verified by reading
 * check.sh, not assumed:
 *
 *   tickets/BOARD.md            ticket.mjs check    refuses a stale board
 *   tickets/tickets.json        ticket.mjs check    same
 *   site/.../tickets.json       test_ticket_mirror  asserts a stale mirror fails
 *   site/.../build.json         check_published     traces to a source or a
 *   site/.../walk/index.html    check_published     declared transform, or fails
 *
 * So the conflict was never what protected these files; the gate was. That is
 * exactly the reasoning docs/LIBERTIES.md's own .gitattributes note sets out for
 * the liberty register — "a conflict is safe because it stops you... and the
 * check is what stands in for the conflict." Here the check already stands there,
 * and the conflict is pure cost.
 *
 * IT IS NOT `merge=union`, WHICH IS BANNED HERE ON MEASURED GROUNDS. Union is a
 * LINE union; it turned five loud changelog conflicts into five silent
 * corruptions in one day (2026-08-15). This driver never merges content at all.
 *
 * IT MUST NOT BE DECLARED ON A LEDGER. tools/dev-smoke-state.json looks like a
 * generated file and is not one: it is an append-only register of smoke readings
 * whose rows carry no id and which NO step of check.sh reads. Keeping ours there
 * would silently drop the other side's readings with nothing to catch it. That
 * file gets merge-smoke-state.mjs, which unions the readings instead.
 *
 * SO IT PRINTS. A driver that quietly keeps ours also quietly removes the merge's
 * own reminder that the file now needs rebuilding — and the next stale mirror is
 * a gate failure nobody expected. merge-changelog.mjs solves this by printing the
 * follow-up command; so does this.
 *
 * Registered by tools/setup-merge-drivers.sh (merge.generated.driver), declared
 * in the repo's .gitattributes. NOT registered? git falls back to the ordinary
 * text merge and you get conflict markers — the old behaviour, never something
 * worse.
 *
 * Usage (git's driver contract):  merge-generated.mjs %O %A %B %P
 * %A already holds OURS on entry, so success is: touch nothing, exit 0.
 */
import path from 'node:path';

const [, , , ours, , placeholder] = process.argv;
const rel = (placeholder || ours || '').replace(/\\/g, '/');
const name = path.basename(rel);

/**
 * What rebuilds each file. Keyed on the basename so the entry is found whether
 * git hands over the repo-relative path (%P) or a temp file, and so a path that
 * moves does not silently lose its advice.
 */
const REBUILD = {
  'BOARD.md': 'node chicago/4d/tools/ticket.mjs board',
  'tickets.json': 'node chicago/4d/tools/ticket.mjs board   (writes the site mirror too)',
  'build.json': 'bash chicago/4d/tools/publish.sh',
  'index.html': 'bash chicago/4d/tools/publish.sh',
};

const how = REBUILD[name];
console.error(
  `merge-generated: kept OURS for ${rel || name} — it is a build product, not a source.`
  + (how ? `\n  REGENERATE IT BEFORE COMMITTING:  ${how}` : '')
  + '\n  (the gate refuses a stale one, so this is a reminder and not the only guard)');
process.exit(0);
