#!/usr/bin/env node
/**
 * changelog_shim.mjs — the text of the published walk/js/changelog.js, and
 * nothing else.
 *
 * IT IS ITS OWN MODULE BECAUSE IMPORTING A TOOL RUNS IT. `stamp-changelog.mjs`
 * writes this shim and `test_changelog_mirror.mjs` asserts it, and the test must
 * be able to ask the writer what the shim IS without the writer stamping the
 * repository's real changelog as a side effect — which is the trap
 * test_changelog_mirror.mjs already names when it reads PUBLISH_PINS out of the
 * stamper's source text rather than importing them. One constant, no side
 * effects, one place the bytes are decided.
 */

/**
 * AND THE SECOND MIRROR IS NO LONGER THE FILE — T-0722.
 *
 * Both published paths carried the changelog VERBATIM until 2026-09-05, which
 * meant the site shipped the same 1.31 MB twice: 4.1 % of its 32 MB budget spent
 * on a byte-for-byte copy, growing at twice the rate of the record, because every
 * entry cost the payload double. It is what put `dev` at 31.999 MB with nothing
 * left for any PR to add.
 *
 * The two URLs both stay — one is the fleet contract, one is what the What's-new
 * tab imports — but only the fleet one holds the file. The walk copy is this
 * shim, which re-exports it. `whatsnew.js` imports `./changelog.js` and asks only
 * for CHANGELOG and LATEST_VERSION; inside the mirror, `../../js/changelog.js`
 * resolves. Nothing under `renderers/web/` changes: the dev tree still holds the
 * authored file at the path the app imports, which is the whole reason the
 * changelog is authored inside the app.
 *
 * `tools/check_published.mjs` carries the matching TRANSFORMED row, because a
 * published file that is not its source has to say so there or the mirror gate
 * reads it as stale.
 */
export const WALK_SHIM = `/**
 * changelog.js — in the PUBLISHED MIRROR ONLY, a re-export (T-0722).
 *
 * The changelog is authored at renderers/web/js/changelog.js, because the
 * walkthrough's What's-new tab imports it and a page cannot import from its own
 * publish mirror. tools/publish.sh copies that file to <site>/js/changelog.js,
 * which is the path Manager and the polecat.live launcher parse and which must
 * not move.
 *
 * It used to also arrive here verbatim, so the mirror shipped 1.31 MB twice —
 * 4.1 % of the site budget, growing at double the rate of the record itself.
 * This re-exports the fleet copy instead. Same module interface, half the bytes.
 *
 * Do not edit: tools/stamp-changelog.mjs writes this file, and tools/publish.sh
 * calls it to. The changelog itself lives at
 * chicago/4d/renderers/web/js/changelog.js.
 */
export { CHANGELOG, LATEST_VERSION } from '../../js/changelog.js';
`;
