#!/usr/bin/env node
/**
 * T-0235 — what the renderer gate COSTS on this machine, and which parts of it
 * cover the change you actually made.
 *
 *   node tools/smoke_budget.mjs                    # the measured cost of the whole gate
 *   node tools/smoke_budget.mjs --for <path>…      # the parts that cover those files
 *   node tools/smoke_budget.mjs --for-diff [ref]   # the same, off `git diff --name-only`
 *   node tools/smoke_budget.mjs --legs             # the nightly gate leg by leg, vs its cap
 *   node tools/smoke_budget.mjs --self-test        # the map has not rotted (check.sh)
 *
 * WHY THIS EXISTS. A steward run's single foreground command is capped at 600 s,
 * so no run can take the gate whole: it takes the parts that cover what it
 * touched, and until this tool nothing said which those are. A run therefore
 * either ran all fifteen commands — more than its whole budget — or picked by
 * feel.
 *
 * THERE ARE THREE CAPS AND THEY BOUND THREE DIFFERENT THINGS (T-0450). This
 * file used to say the 30-minute cap T-0170, T-0173 and T-0181 reason against
 * "describes some other machine", and offered the gate's 55 m 10 s whole-body
 * figure as the proof. It is not proof, because the two are not the same
 * quantity, and the machine is the same one:
 *   - 600 s   caps ONE FOREGROUND COMMAND in a steward run — this tool's budget;
 *   - 30 min  caps ONE LEG of the nightly gate (`chicago-4d-bake.yml` § `smoke`,
 *             `timeout-minutes`), one viewport over one range of parts, eight
 *             legs in parallel — which is the bound those three tickets take
 *             their margins against, correctly;
 *   - 90 min  caps the WHOLE body in one process (`chicago-4d-smoke.yml`
 *             § `smoke`, `timeout-minutes`), which has no per-leg cap at all,
 *             and is what the 55 m 10 s reading was taken under.
 * Neither of the last two bounds the other. `--legs` totals the record against
 * the per-leg cap; the default report totals it against the whole-body one.
 *
 * THE FIGURES ARE READ, NEVER ASSERTED. Every second printed here comes out of
 * `tools/dev-smoke-state.json`, the standing record T-0216 built, filtered to
 * readings taken ON THIS CLASS OF MACHINE (`host.kind: steward-runner`) against
 * the published mirror. Nothing here is a bar, a gate or a promise — it is the
 * record, summarised, with the parts it has no reading for named as such. When
 * the town grows and the parts get re-cut again, the numbers move on their own.
 *
 * THE MAP CAN ONLY EVER ADD PARTS. A path the map does not know maps to THE
 * WHOLE GATE, not to nothing — so a file nobody thought about makes the recipe
 * bigger rather than quietly making it smaller. `--self-test` holds that, holds
 * the part count against `smoke_renderer.mjs`'s own `PARTS`, and holds every
 * pattern in the map against the committed tree, so a renamed module shows up
 * here rather than as a part that silently stopped being recommended.
 *
 * THE NUMBERING CHANGED THREE TIMES ON 2026-08-30, and this tool holds every
 * epoch. T-0346 made old part 4 into 4 + 5 + 6 and old 5-9 into 7-11; T-0173
 * halved part 7 (8-11 -> 9-12); T-0170 halved part 10 (11-12 -> 12-13).
 * T-2044 APPENDED part 14, which renumbers nothing.
 * Readings filed before any of those are labelled in the numbering of their day,
 * and this tool RENUMBERS them rather than discarding them, pushing each reading
 * through every cut it predates — the content of old part 5 is the content of
 * new parts 7+8, so the reading is a reading of that group. Three readings
 * cannot be renumbered to a single part and are reported as the group they are:
 * old part 4 is 4+5+6, a T-0346-era part 7 is 7+8, and a T-0173-era part 10 is
 * 10+11.
 */

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');                 // chicago/4d
const REPO = path.resolve(APP, '..', '..');           // the monorepo root
const STATE = path.join(HERE, 'dev-smoke-state.json');
const SMOKE = path.join(HERE, 'smoke_renderer.mjs');

/** Parts of the smoke body. Mirrors `PARTS` in tools/smoke_renderer.mjs, and
 *  `--self-test` fails if the two ever disagree. */
// T-2044 APPENDED part 14 (the arrival-to-jaunt path). An append renumbers no
// reading, so no epoch is added below.
const PARTS = 14;

/** A steward run's single foreground command is capped at 600 s (ROADMAP § THE
 *  RUN BUDGET). Recipes are packed to a lower figure so a part that has grown
 *  since its last reading does not put the command over on its own. */
const CEILING_S = 600;
const PACK_TO_S = 480;

/** The two renumberings of 2026-08-30, newest last. A reading is renumbered
 *  through every cut it PREDATES, in order, so the arithmetic composes instead
 *  of having to be restated each time the body is cut again.
 *  T-0346: old part 4 is new 4+5+6, and old 5-9 are new 7-11.
 *  T-0173: old part 7 is new 7+8, and old 8-11 are new 9-12. */
const RENUMBERED_AT = Date.parse('2026-08-30T03:35:16Z');          // T-0346
const RENUMBERED_AGAIN_AT = Date.parse('2026-08-30T05:20:22Z');    // T-0173
const HALVED_AT = Date.parse('2026-08-30T06:14:00Z');              // T-0170

/** Which parts cover which change.
 *
 *  Each entry is a path prefix or a `*`-glob against the repo-relative path
 *  inside `chicago/4d/`, and the parts of the smoke body that read what it
 *  produces. The justification for each row is the part's own section headings
 *  in `smoke_renderer.mjs` — see docs/SMOKE-BUDGET.md, which lists them.
 *
 *  `ALL` means every part: the file feeds the whole scene, so no part can be
 *  ruled out. That is also what an UNKNOWN path maps to. */
const ALL = Array.from({ length: PARTS }, (_, i) => i + 1);

/** THE GATE'S OWN SHAPE, READ OUT OF THE WORKFLOWS RATHER THAN RESTATED HERE
 *  (T-0450). The nightly gate cuts each viewport into stage LEGS and caps each
 *  leg; the full-body workflow runs everything in one process and caps the job.
 *  Both figures were prose in docs/SMOKE-BUDGET.md, in three places, spelled in
 *  a part numbering that has been re-cut four times in 2026 — so they are read
 *  from the files that actually carry them, and `--self-test` holds the legs
 *  against `PARTS`. A checkout without `.github/` (a sparse one, say) gets
 *  `null` and a report that says so, never a guessed number. */
const BAKE_WF = path.join(REPO, '.github', 'workflows', 'chicago-4d-bake.yml');
const FULL_WF = path.join(REPO, '.github', 'workflows', 'chicago-4d-smoke.yml');

/** The body of a top-level job in a workflow file: everything from `  <job>:`
 *  down to the next line at that indent. Sliced rather than matched, because a
 *  regex built by string concatenation is one escape away from silently
 *  matching nothing, and a budget tool that quietly reports no legs is exactly
 *  the failure T-0450 is about. */
function jobBlock(file, job) {
  let src;
  try { src = fs.readFileSync(file, 'utf8'); } catch { return null; }
  const lines = src.split('\n');
  const head = lines.findIndex((l) => l === `  ${job}:`);
  if (head < 0) return null;
  const body = [];
  for (let i = head + 1; i < lines.length; i++) {
    const l = lines[i];
    if (l.trim() && !/^ {3}/.test(l)) break;    // back out to the next job, or to column 0
    body.push(l);
  }
  return body.join('\n');
}

function gateShape() {
  const bake = jobBlock(BAKE_WF, 'smoke');
  const full = jobBlock(FULL_WF, 'smoke');
  const shape = { legCapS: null, wholeCapS: null, legs: null, viewports: null };
  if (bake) {
    const cap = /^ {4}timeout-minutes: (\d+)$/m.exec(bake);
    const stage = /^ {8}stage: \[([^\]]*)\]$/m.exec(bake);
    const view = /^ {8}viewport: \[([^\]]*)\]$/m.exec(bake);
    if (cap) shape.legCapS = Number(cap[1]) * 60;
    if (view) shape.viewports = view[1].split(',').map((t) => t.trim().replace(/^'|'$/g, '')).filter(Boolean);
    if (stage) {
      shape.legs = stage[1].split(',').map((t) => t.trim().replace(/^'|'$/g, '')).filter(Boolean)
        .map((label) => {
          const [lo, hi] = label.split('-');
          const a = Number(lo);
          const b = hi === undefined ? a : Number(hi);
          const parts = [];
          for (let i = a; i <= b; i++) parts.push(i);
          return { label, parts };
        });
    }
  }
  if (full) {
    const cap = /^ {4}timeout-minutes: (\d+)$/m.exec(full);
    if (cap) shape.wholeCapS = Number(cap[1]) * 60;
  }
  return shape;
}
/** NONE is not a gap. It is the map SAYING that no part of the smoke body reads
 *  this path, which is a different statement from "nobody wrote a row for it" —
 *  the second maps to the whole gate. A NONE-only change still runs one cheap
 *  staged pass per viewport, because boot, the page-error check and the vendor
 *  checks are taken in EVERY invocation whichever stage is asked for. */
const NONE = [];
const COVERAGE = [
  // T-2200: the walk does not load this isolated comparison page. Its dedicated
  // qa_glessner_t2200.mjs covers both viewports; popup.js still selects stage 3.
  ['renderers/web/glessner-baseline.html', NONE, 'isolated page: qa_glessner_t2200.mjs'],
  ['renderers/web/js/glessner-baseline.js', NONE, 'isolated page: qa_glessner_t2200.mjs'],
  ['renderers/web/css/glessner-baseline.css', NONE, 'isolated page: qa_glessner_t2200.mjs'],
  ['data/comparisons/glessner/', NONE, 'isolated comparison data: qa_glessner_t2200.mjs'],
  // T-2265: the K01 component contract and the Glessner baseline measured against it.
  // Read by tools/k01_contract.mjs in check.sh; neither published nor fetched.
  ['data/components/', NONE, 'component contract + measured baseline: k01_contract.mjs --check'],
  // --- read by no part of the scene: the gate's own tooling, the backlog, the
  // --- prose. check.sh is what covers these, not the renderer.
  ['tools/', NONE, 'the gate\'s own tooling — not served to the browser'],
  ['generators/', NONE, 'the bake\'s generators — their output is the data rows below'],
  ['patches/', NONE, 'vendored patches applied at build time, not at run time'],
  ['tickets/', NONE, 'the backlog'],
  // T-1148. Committed READINGS — what an instrument saw, on a day, on a tree.
  // `tools/publish.sh` copies no part of this directory into the mirror and no
  // module under `renderers/` fetches a path in it, so the scene cannot load one
  // however wrong it is; `tools/check.sh` is what holds them, by re-deriving the
  // rule each one was taken for. Without this row a new reading is an unmapped
  // path, and an unmapped path prices at the whole gate — which is thirteen parts
  // per viewport to cover a JSON file nothing reads.
  ['data/render/', NONE, 'committed instrument readings — neither published nor fetched'],
  ['docs/', NONE, 'prose — except docs/LIBERTIES.md, which compiles into the scene'],
  // T-1786: the portable human contract. No scene reads it yet (L1 stands, nothing
  // is drawn); tools/human_contract.py holds it in check.sh.
  ['data/humans/', NONE, 'human contract + instance schema: human_contract.py --check'],
  ['README.md', NONE, 'prose'],
  ['AGENTS.md', NONE, 'prose'],
  // The changelog entry file a PR adds (owner, 2026-10-10). Nothing serves or imports
  // it: the fold on dev turns it into renderers/web/js/changelog.js after the merge,
  // and on the PR `changelog-entries.mjs --check` holds its shape and budget. Without
  // this row every PR, which now always carries one, would price at the whole gate.
  ['changelog.d/', NONE, 'changelog entry files — folded into changelog.js on dev, not served'],
  ['tools/smoke_renderer.mjs', ALL, 'the gate itself'],

  // --- the whole scene: geometry, the scene graph, the boot chain, the mirror
  ['assets/', ALL, 'meshes and the material sheet — every part draws them'],
  ['data/structures/', ALL, 'the records the whole town is built from'],
  ['data/scenes/', ALL, 'what the scene loads at all'],
  ['data/datum.json', ALL, 'the projection every metre in the scene is in'],
  ['data/exclusions.json', ALL, 'what the scene declares it is NOT drawing'],
  ['renderers/web/js/main.js', ALL, 'the boot chain'],
  ['renderers/web/js/scene-loader.js', ALL, 'the boot chain'],
  ['renderers/web/js/structure-versions.js', ALL, 'imported by the boot chain (scene-loader.js); the version switch itself is asserted in part 3 (T-1727)'],
  ['renderers/web/js/world.js', ALL, 'the world the parts all measure against'],
  ['renderers/web/js/geometry.js', ALL, 'shared geometry the parts all read'],
  ['renderers/web/index.html', ALL, 'the page itself'],
  ['renderers/web/css/', ALL, 'the chrome every panel check clicks'],
  ['data/reconstruction/', ALL, 'the infill programme the records are expanded from'],
  // T-1971. The housing deal's ledger reaches the scene only through the sidecars
  // compile_scene writes from it (`residents[]` on the building card), which are priced
  // by their own rows. No module under renderers/ fetches it.
  ['data/reconstruction/1835_housing_seats.json', NONE, 'the housing deal\u2019s ledger \u2014 read by compile_scene, fetched by no renderer'],

  // --- AND NO ROW FOR site/4d/ ANY MORE (T-0938). The published mirror had six
  // rows here, and every one of them existed to price a path that could appear in a diff.
  // The mirror is untracked and generated now, so it cannot: `--for-diff` below reads
  // `git diff --name-only` and an ignored tree is never in it. That deletes the hazard the
  // last two of those rows were written for rather than pricing it — publish.sh rewrote
  // the build sha and Central date into walk/index.html on EVERY run, so every publishing
  // PR touched it, and before the NONE row existed the mirror catch-all sent the stamp to
  // all 13 parts (run #1464, 2026-09-03: seven legs for two census page files). A PR is
  // priced on the source it changed, which is the only thing it changes now.

  // --- PART 1: the enclosure layer, the plantings inside it, and the signs
  ['renderers/web/js/enclosures.js', [1], 'the enclosure layer (T-0038)'],
  ['renderers/web/js/yards.js', [1], "the town's lot-line yard fences (T-0068)"],
  ['renderers/web/js/signage.js', [1], 'the business signs (T-0039, T-0066)'],
  ['data/enclosures/', [1], 'fences, the pound, the dooryard pickets'],
  ['data/signage/', [1], 'what the signs say'],
  ['renderers/web/js/wells.js', [1], "the fort's well head (T-0887)"],
  ['data/wells/', [1], 'the well records'],

  // --- PART 2: the trading frontages, the river's edge and what floats on it
  ['renderers/web/js/frontage.js', [2], 'the frontage layer (T-0082, T-0090)'],
  ['renderers/web/js/yard.js', [2], 'the yard goods at the trading frontages (T-0040)'],
  ['renderers/web/js/wharves.js', [2], 'the river wharves (T-0041) and walking one (T-0058)'],
  ['renderers/web/js/working-bank.js', [2], 'the worked river bank and its landing aprons (T-1771)'],
  ['renderers/web/js/boats.js', [2], 'the boats on the river (T-0063)'],
  ['renderers/web/js/confidence.js', [2, 3, 6], 'the confidence view, its card and its menu'],
  ['data/frontage/', [2], 'the frontage records'],
  ['data/wharves/', [2], 'the wharf records'],
  ['data/boats/', [2], 'the boat records'],
  ['data/yard/', [2], 'the yard goods'],

  // --- PART 3: the ground you stand on, and the card that says why
  ['renderers/web/js/ground.js', [3], 'the ground faces the sky (R-BUG3c)'],
  ['renderers/web/js/terrain.js', [3], 'the ground the town stands on'],
  // T-1055. terrain.js's ground tile, lifted into its own module so a tool can
  // measure it without a browser. Same part as the file it was lifted out of.
  ['renderers/web/js/prairie-tile.js', [3], 'the ground tile the prairie is painted from'],
  // T-2089. The grass grain the prairie's fine relief is read from: the same
  // ground, so the same part.
  ['renderers/web/js/grass-grain.js', [3], 'the grass grain the prairie\'s relief is lit from'],
  ['renderers/web/js/turf-tile.js', [3, 10, 11], 'the town turf: painted by the ground, thinned in the sward'],
  // T-1797. The ground-strip proof: imported only under `?proof=ground`, which
  // no part loads, so the boot chain never reaches it. Part 1 boots the scene
  // and holds it to zero pageerrors, which is the claim "not imported" rests on.
  ['renderers/web/js/ground-strip.js', [1], 'the ground-strip proof (T-1797), drawn only under ?proof=ground'],
  ['renderers/web/js/ground-strip-mask.js', [1], 'the ground-strip proof\'s layout and mask pixels (T-1797)'],
  ['renderers/web/js/citations.js', [3], 'pick -> provenance, and what kind of source'],
  ['renderers/web/js/liberties.js', [3, 13], 'the liberties on the card, and in the panel'],
  // T-1519. The People directory's person card is `householdHtml` from this module, and
  // that card is opened and read in PART 12 — so 12 joins the building card (3) and the
  // Evidence panel's household cards (13), which are this module's other two surfaces.
  ['renderers/web/js/residents.js', [3, 12, 13], 'who was here, the person a directory opens, and the people in the panel'],
  // T-1158. The per-attribute tier the household card draws its chip from. Same
  // surfaces as residents.js, which imports it — the building card's resident rows (3),
  // the People directory's person card and its tier filter (12, T-1519: this row said
  // 13 for the directory, which is where the directory is not), and the Evidence
  // panel's household cards (13) — and mapped on arrival, because an unmapped module
  // prices every diff that touches it at the whole gate.
  ['renderers/web/js/attribute-tiers.js', [3, 12, 13], 'which tier each attribute of a person stands on'],
  // T-1041. The agency relation renders on the BUILDING card (part 3) and on the man's
  // own household card in the Evidence panel (part 13) — one module, two surfaces, and
  // both are pinned. `people.js` is the directory itself, mapped for the first time
  // here: it was unmapped, so every diff touching it priced the whole gate.
  //
  // T-1519. It was mapped to part 13 on the belief that the directory is read there,
  // and it is not: every check that opens the People tab, filters it, or opens a person
  // card sits inside `stageOn(12)`. Part 13 touches the directory once, in a defensive
  // `api.people?.close?.()` that asserts nothing. A run that trusted the old row ran
  // part 13 and never opened the directory it had changed. ANCHORS below now holds it.
  ['renderers/web/js/agencies.js', [3, 13], 'the agency on the card, and on the person'],
  ['renderers/web/js/people.js', [12], 'the directory of everyone in the town'],
  // T-0438. The reader the cohort's rows go through once the mirror ships them packed:
  // a letter-list person opened from the directory (12) and a row of the Evidence
  // panel's letter-list group, whose body the smoke reads (13). No building card holds
  // a letter-list name, so part 3 never reaches it.
  ['renderers/web/js/letter-list-roster.js', [12, 13], 'how a letter-list household is read from the published roster'],
  ['data/reconstruction/1835_agencies.json', [3, 13], 'the compiled relation both cards read'],
  // T-1959. The placement policy is the seating and yard generators' rule book: what
  // it decides reaches the scene only through the records those generators write (the
  // structures, data/yard/), which are priced by their own rows. No module under
  // renderers/ fetches it, so it is priced as read by nothing rather than at the whole
  // gate that `data/reconstruction/` would otherwise charge a rule's every new column.
  ['data/reconstruction/1835_placement_policy.json', NONE, 'the generators\u2019 rule book \u2014 fetched by no renderer'],
  // T-1160. The Evidence hub is asserted in PART 12 (ten tiles since T-1292, each
  // counting its own mount) and its mounts are stress-measured for overflow in PART 13, so the
  // population profile and the hub itself are read by both and by nothing else.
  ['renderers/web/js/evidence.js', [12, 13], 'the Evidence hub and its tiles'],
  ['renderers/web/js/population.js', [12, 13], 'the town\u2019s people, profiled'],
  ['data/reconstruction/1835_population_profile.json', [12, 13], 'the profile the panel renders'],
  // T-1166. The order book's panel is the ninth tile, asserted in the same PART 12
  // hub check and overflow-measured in PART 13 alongside the profile it subtracts from.
  ['renderers/web/js/orderbook.js', [12, 13], 'what the town still owes, bucket by bucket'],
  ['data/reconstruction/1835_reconstruction_order_book.json', [12, 13], 'the quota the panel renders'],
  // T-1401. The business layer reaches a visitor on TWO surfaces and no others: the
  // building card's Use row, which names the firms in this roof and (since T-1401) the
  // anchored ones sited against it, and the Businesses directory itself, which part 12
  // searches, filters and opens a card from. Mapped on arrival — unmapped, every diff
  // touching a business record priced the whole gate, and the 196 records move together.
  ['renderers/web/js/businesses.js', [3, 12], 'the firms directory, and the crosswalk the card reads'],
  // T-1493. The address book's seat block, shared by the business card (the firms
  // directory) and the person card (the People directory) — and BOTH are part 12
  // (T-1519: this row said the People directory was part 13, which is how part 13
  // came to be pinned here; no check there reads a seat). The BUILDING card never
  // renders it — a roof is the seat, not a reading about one — so part 3 is not
  // pinned here even though `businesses.js` is pinned to it.
  ['renderers/web/js/seat.js', [12], 'the seat a card prints, and the way to it'],
  ['data/reconstruction/1835_address_book.json', [12, 13], 'the rung each household and firm is seated at'],
  ['data/businesses/', [3, 12], 'the compiled business records and their index'],
  ['data/businesses.schema.json', [3, 12], 'the shape those records are refused against'],
  ['renderers/web/js/display-name.js', [3], 'the prose may not name a level the record is not'],
  ['renderers/web/js/popup.js', [3], 'the card a visitor opens'],
  ['renderers/web/js/census.js', [12], 'the town census in Evidence → City'],
  ['data/terrain/', [3], 'the heightfield'],
  ['data/liberties.json', [3, 13], 'what we made up about THAT building'],
  ['docs/LIBERTIES.md', [3, 13], 'the source the liberties are compiled from'],
  ['data/residents/', [3, 12, 13], 'the resident cards and Evidence → City count'],
  ['data/sources/', [3], 'the citation -> its document'],
  ['data/sidecars/', [3], 'the record\'s own account, on the card'],

  // --- PARTS 4-6: standing, walking, the detail ladder and the chrome
  ['renderers/web/js/walker.js', [4, 5, 6], 'walking, standing, and the ladder they are measured on'],
  ['renderers/web/js/controls/', [4, 5, 6, 11, 12], 'the pick, the touch backend and the settings'],
  ['renderers/web/js/far-merge.js', [5, 8], 'the detail ladder and the batch merge, which T-0173 moved into part 8'],

  // --- PARTS 7-8: navigation, the roads, the aid and the merge the reach
  // --- stands on. T-0173 cut the third road station, the road-legibility aid
  // --- and the batch merge out of part 7 into part 8.
  ['renderers/web/js/navigation.js', [7], 'navigation and its readouts'],
  ['renderers/web/js/hud.js', [7], 'the readouts a visitor navigates by'],

  // --- PART 9: what the light does to the town
  ['renderers/web/js/facades.js', [9], 'T-0002, the facade tones'],
  ['renderers/web/js/buildings.js', [8, 9], 'the facades and the shadow reach they carry, and the merged batch part 8 reads the roughness channel out of'],
  ['renderers/web/js/roof-relief.js', [8, 9], 'T-1488, the roof coverings\' relief maps — it binds them inside buildings.js\'s own load loop and adds two batches to the merge part 8 counts'],
  ['renderers/web/js/wall-relief.js', [8, 9], 'T-1963, the walls\' relief maps — bound inside buildings.js\'s load loop like the roofs\', and two more batches for the merge part 8 counts'],
  ['renderers/web/js/wall-grain.js', [8, 9], 'T-1963, which walls take the relief and how much grain their finish shows'],

  // --- PARTS 10-11: what grows, what moves, and the streets a visitor reads
  ['renderers/web/js/flora.js', [10, 11], 'the flora census, and the boundary it fades at'],
  ['renderers/web/js/zone-blend.js', [10, 11], 'where the flora census asks a community, and its blended edge'],
  ['renderers/web/js/plants.js', [10, 11], 'the sward, and its ragged edge'],
  ['renderers/web/js/trees.js', [10], 'the horizon timber'],
  ['renderers/web/js/tree-surface.js', [10], 'the trees\' leaf-and-bark atlas and their shader patch (T-2110), drawn in the part trees.js is'],
  ['renderers/web/js/shrub-grain.js', [10, 11], 'the sward\'s grain'],
  ['renderers/web/js/fauna.js', [10, 13], 'the wildlife, drawn and in the panel'],
  ['renderers/web/js/streets.js', [2, 7, 8, 10, 11], 'the street edge, the roads read from two stations in part 7 and one in part 8 with the aid, and the street names'],
  ['data/flora/', [10, 11, 13], 'what grows here'],
  ['data/fauna/', [10, 13], 'the wildlife'],
  ['data/streets/', [2, 7, 8, 10, 11], 'the street records'],
  ['data/traces/', [2, 7, 8, 10, 11], 'the traced lines the streets and the bank are built from'],
  ['data/town_census.json', [12], 'the two ladders in Evidence → City'],
  ['data/render/town_completion_1835.json', [12], 'the completion row in Evidence → City'],

  // --- PART 12: the settings, the Go-to tab and What's-new
  ['renderers/web/js/whatsnew.js', [12], "what's new"],
  ['renderers/web/js/changelog.js', [12], "the entries What's-new reads"],
  ['renderers/web/js/units.js', [11, 12], 'the settings that change what the readouts say'],

  // --- PART 13: the Evidence panel and the air above the town
  ['data/research/', [13], 'researched, and still open — the third category'],
  // T-0474. The 1904 street grid is drawn only at the /1904/ door, which part 13 boots.
  ['renderers/web/js/street-grid.js', [13], 'the 1904 Prairie Avenue street grid (T-0474)'],
  ['data/street_grid/', [13], 'the 1904 carriageways, block faces, alleys and parcels'],
  // T-1728. What that grid is paved with, and the maps it is paved in.
  ['data/street_surfaces/', [13], 'the 1904 street surfaces: materials, tiers and sources'],
  ['assets/textures/prairie_1904_pbr/', [13], 'the 1904 street-surface texture library'],
  // T-2292. The K04 roof library is published by nothing and bound by no renderer until
  // T-2293 builds a roof from it, so no part draws it; tools/check_roof_library.py gates it.
  ['assets/textures/prairie_1904_roofs/', NONE, 'the K04 roof library — bound by no renderer yet: check_roof_library.py --check'],

  // --- PART 14: the arrival-to-jaunt path, on a fresh context (T-2044)
  // The jaunt modules are imported lazily, the first time the Jaunts menu opens, and
  // no part before 14 opens it: until this part they were unmapped, so a one-line
  // change to a jaunt priced at the whole gate while no part of that gate read it.
  // The boot modules the path also crosses (arrival.js, welcome.js, main.js) stay
  // whole-gate, because every part boots through them.
  ['renderers/web/js/jaunts.js', [14], 'the outing itself: its stops, its controls, End'],
  ['renderers/web/js/jaunt-panel.js', [14], 'the panel an outing is driven from'],
  ['renderers/web/js/jaunt-menu.js', [14], 'the Jaunts menu and its Start buttons'],
  ['renderers/web/js/jaunt-preview.js', [14], 'the menu\u2019s previews, Resume and the daybook'],
  ['renderers/web/js/jaunt-cards.js', [14], 'the card and the source a stop links to'],
  ['renderers/web/js/jaunt-context.js', [14], 'the road notes a ride carries'],
  ['renderers/web/js/jaunt-journal.js', [14], 'the outing\u2019s saved journal'],
  ['renderers/web/js/travel-estimate.js', [14], 'the estimate a change of mode moves'],
  ['data/jaunts/', [14], 'the authored jaunts'],
  ['data/sidecars/1835/jaunts/', [14], 'the compiled jaunts and their catalog'],
];

/** T-1519 — WHERE A MODULE'S CHECKS ACTUALLY ARE, read off the gate rather than
 *  remembered. Each anchor is a literal only that module's surface puts in the
 *  smoke (a tab it owns, a class it renders, the ticket a check is filed under);
 *  `--self-test` finds every PART whose `stageOn(N)` block contains it and fails
 *  if the module's COVERAGE row leaves one out. That is the fault this exists for:
 *  people.js was mapped to part 13 while every People-directory check sat inside
 *  `stageOn(12)`, and nothing could tell, because the map was written from a
 *  belief about where the directory is read. An anchor gives a FLOOR, never a
 *  ceiling — a row may name parts its anchors do not reach — and an anchor found
 *  in no part at all has rotted, which also fails. */
const ANCHORS = [
  ['renderers/web/js/people.js', ['data-tab="people"', 'people-filters', 'people-card']],
  ['renderers/web/js/businesses.js', ['data-tab="businesses"']],
  ['renderers/web/js/seat.js', ['people-seat']],
  // householdHtml is the body of the People directory's person card (12) and of the
  // Evidence panel's household cards, mounted at #residents (13).
  ['renderers/web/js/residents.js', ['people-card', "getElementById('residents')"]],
  ['renderers/web/js/attribute-tiers.js', ['T-1158', 'people-card', "getElementById('residents')"]],
  ['renderers/web/js/agencies.js', ['.pop-agency']],
  ['renderers/web/js/evidence.js', ['data-tab="evidence"']],
  ['renderers/web/js/whatsnew.js', ['data-tab="whatsnew"']],
];

/** The parts whose `if (stageOn(N)) {` … `} // end PART N` block contains `needle`. */
function partsHolding(smoke, needle) {
  const found = new Set();
  let part = 0;
  for (const line of smoke.split('\n')) {
    const open = /^\s*if \(stageOn\((\d+)\)\) \{/.exec(line);
    if (open) part = Number(open[1]);
    else if (/^\s*\} \/\/ end PART \d+/.test(line)) part = 0;
    if (part && line.includes(needle)) found.add(part);
  }
  return [...found].sort((x, y) => x - y);
}

// ---------------------------------------------------------------------------

const fmt = (s) => (s == null ? '     —' : `${Math.floor(s / 60)}m ${String(Math.round(s % 60)).padStart(2, '0')}s`);
const key = (parts) => parts.join(',');

/** The current parts a reading covers, renumbering it if it predates T-0346. */
function currentParts(reading) {
  const taken = Date.parse(reading.takenAt);
  let parts = reading.parts || [];
  if (!parts.length) return null;
  // A reading is pushed through every cut it PREDATES, oldest first, so two
  // renumberings on one day compose rather than needing a combined table. A
  // reading with no parsable date is treated as older than all of them, which
  // is the safe direction: it widens the parts it claims to cover.
  const stale = (at) => !Number.isFinite(taken) || taken < at;
  if (stale(RENUMBERED_AT)) parts = parts.flatMap((p) => {   // T-0346
    if (p <= 3) return [p];
    if (p === 4) return [4, 5, 6];
    return [p + 2];
  });
  if (stale(RENUMBERED_AGAIN_AT)) parts = parts.flatMap((p) => {   // T-0173
    if (p <= 6) return [p];
    if (p === 7) return [7, 8];
    return [p + 1];
  });
  if (stale(HALVED_AT)) parts = parts.flatMap((p) => {             // T-0170
    if (p <= 9) return [p];
    if (p === 10) return [10, 11];
    return [p + 1];
  });
  return [...new Set(parts)].sort((a, b) => a - b);
}

/** Every measured group, per viewport: a set of current parts -> median seconds. */
function measured() {
  const state = JSON.parse(fs.readFileSync(STATE, 'utf8'));
  const groups = new Map();                     // "viewport|1,2" -> {viewport, parts, secs[]}
  for (const r of state.readings || []) {
    if (!r.wallSeconds) continue;               // a killed run reports none
    if ((r.host && r.host.kind) !== 'steward-runner') continue;
    if (r.target !== 'published') continue;     // the --published run is the one that matters
    const parts = currentParts(r);
    if (!parts) continue;
    const k = `${r.viewport}|${key(parts)}`;
    if (!groups.has(k)) groups.set(k, { viewport: r.viewport, parts, secs: [], renumbered: false });
    const g = groups.get(k);
    g.secs.push(r.wallSeconds);
    if (Date.parse(r.takenAt) < RENUMBERED_AT) g.renumbered = true;
  }
  for (const g of groups.values()) {
    const s = g.secs.slice().sort((a, b) => a - b);
    g.median = s[Math.floor(s.length / 2)];
    g.n = s.length;
  }
  return [...groups.values()];
}

/** Cover `want` with disjoint measured groups, cheapest-and-narrowest first.
 *  Returns the chosen groups and the parts nothing has a reading for. */
function cover(groups, viewport, want) {
  // Coverage first, cost second: a reading of parts 3-6 together is worth more
  // to this report than a cheaper reading of part 3 alone that leaves 4, 5 and
  // 6 with no figure at all.
  const pool = groups.filter((g) => g.viewport === viewport);
  const taken = new Set();
  const chosen = [];
  for (const p of want) {
    if (taken.has(p)) continue;
    const usable = pool.filter((c) => c.parts.includes(p) && !c.parts.some((q) => taken.has(q)));
    if (!usable.length) continue;
    usable.sort((a, b) => b.parts.length - a.parts.length || a.median - b.median);
    const g = usable[0];
    chosen.push(g);
    for (const q of g.parts) taken.add(q);
  }
  return { chosen, missing: want.filter((p) => !taken.has(p)) };
}

/** Pack `want` into commands that each stay under the pack budget. */
function recipe(groups, viewport, want) {
  const cost = new Map();
  for (const g of groups.filter((x) => x.viewport === viewport)) {
    if (g.parts.length === 1) cost.set(g.parts[0], g.median);
  }
  // A part with no reading of its own is priced at the mean of the ones that
  // have one — an estimate, printed as such, never a claim.
  const known = [...cost.values()];
  const fallback = known.length ? Math.round(known.reduce((a, b) => a + b, 0) / known.length) : null;
  const cmds = [];
  let cur = [];
  let curCost = 0;
  for (const p of want) {
    const c = cost.get(p) ?? fallback ?? 0;
    if (cur.length && curCost + c > PACK_TO_S) { cmds.push({ parts: cur, secs: curCost }); cur = []; curCost = 0; }
    cur.push(p);
    curCost += c;
  }
  if (cur.length) cmds.push({ parts: cur, secs: curCost });
  return { cmds, estimated: want.filter((p) => !cost.has(p)) };
}

/** `1,2,3,5` -> `1-3,5`, the form SMOKE_STAGE takes. */
function stageArg(parts) {
  const out = [];
  let i = 0;
  while (i < parts.length) {
    let j = i;
    while (j + 1 < parts.length && parts[j + 1] === parts[j] + 1) j++;
    out.push(i === j ? `${parts[i]}` : `${parts[i]}-${parts[j]}`);
    i = j + 1;
  }
  return out.join(',');
}

/** The part of `viewport` with the smallest measured reading of its own. */
function cheapestPart(groups, viewport) {
  const singles = groups.filter((g) => g.viewport === viewport && g.parts.length === 1)
    .sort((a, b) => a.median - b.median);
  return singles.length ? singles[0].parts[0] : 1;
}

function partsFor(paths) {
  const hits = [];
  const want = new Set();
  let unknown = 0;
  for (const raw of paths) {
    // Accept a repo-root path (chicago/4d/…) or an app-relative one.
    const p = raw.replace(/^chicago\/4d\//, '');
    // Specificity, so a general prefix cannot drown a row written about one
    // file: an exact-path row beats every prefix row, and the longest prefix
    // beats the shorter ones it sits inside.
    const exact = COVERAGE.filter(([pat]) => !pat.endsWith('/') && p === pat);
    let rows = exact;
    if (!rows.length) {
      const pre = COVERAGE.filter(([pat]) => pat.endsWith('/') && p.startsWith(pat));
      const longest = Math.max(0, ...pre.map(([pat]) => pat.length));
      rows = pre.filter(([pat]) => pat.length === longest);
    }
    if (!rows.length) {
      unknown++;
      hits.push({ path: p, parts: ALL, why: 'NOT IN THE MAP — the whole gate, because nothing here can rule a part out' });
      for (const n of ALL) want.add(n);
      continue;
    }
    const ps = [...new Set(rows.flatMap(([, parts]) => parts))].sort((a, b) => a - b);
    hits.push({ path: p, parts: ps, why: rows.map(([, , why]) => why).join('; '), none: ps.length === 0 });
    for (const n of ps) want.add(n);
  }
  return { hits, want: [...want].sort((a, b) => a - b), unknown };
}

// --- the reports -----------------------------------------------------------

function reportCost(groups) {
  console.log('THE GATE, AS MEASURED ON THE STEWARD RUNNER');
  console.log('Read from tools/dev-smoke-state.json — steward-runner readings against');
  console.log(`the published mirror. A record, not a bar. Foreground ceiling ${CEILING_S} s.\n`);
  for (const viewport of ['desktop', 'mobile']) {
    const { chosen, missing } = cover(groups, viewport, ALL);
    const total = chosen.reduce((a, g) => a + g.median, 0);
    console.log(`  ${viewport}`);
    for (const g of chosen.sort((a, b) => a.parts[0] - b.parts[0])) {
      const flag = g.parts.length > 1 ? '  (one reading of the group, not of each part)' : '';
      const era = g.renumbered ? ' †' : '';
      console.log(`    part ${stageArg(g.parts).padEnd(5)} ${fmt(g.median).padStart(8)}   n=${g.n}${era}${flag}`);
    }
    if (missing.length) console.log(`    no reading at all for part(s) ${stageArg(missing)}`);
    console.log(`    ${'measured total'.padEnd(11)} ${fmt(total).padStart(8)}   over ${chosen.length} command(s)`
      + (missing.length ? `, and ${missing.length} part(s) unmeasured` : ''));
    console.log('');
  }
  const both = ['desktop', 'mobile'].reduce((a, v) => a + cover(groups, v, ALL).chosen.reduce((x, g) => x + g.median, 0), 0);
  const shape = gateShape();
  console.log(`  BOTH VIEWPORTS, EVERY PART: ${fmt(both)}`);
  console.log('  † renumbered from a reading filed before the T-0346 cut (2026-08-30).');
  console.log('');
  console.log('  THIS TOTAL IS A WHOLE-BODY FIGURE, and the only cap it is comparable with');
  console.log(`  is the one on the whole body: ${capText(shape.wholeCapS)} for both viewports in one process,`);
  console.log(`  ${wf(FULL_WF)} § smoke, timeout-minutes.`);
  console.log(`  The nightly gate's ${capText(shape.legCapS)} caps ONE LEG and not this — see --legs (T-0450).`);
  console.log('');
  console.log(`  And a steward run's single foreground command may not exceed ${CEILING_S} s,`);
  console.log('  so a run takes the parts that cover its change: --for <path>…');
}

const wf = (f) => path.relative(REPO, f);
const capText = (s) => (s == null ? '(unread)' : `${Math.round(s / 60)} min`);

/** The nightly gate as it is actually RUN: legs, each under its own cap.
 *  T-0450 — the default report above totals the whole body, which is the wrong
 *  quantity to compare with a per-leg timeout, and this project spent three
 *  tickets' margins on the confusion. */
function reportLegs(groups) {
  const shape = gateShape();
  if (!shape.legs) {
    console.log('THE NIGHTLY GATE\'S LEGS — cannot be read.');
    console.log(`  ${wf(BAKE_WF)} is not in this checkout, or its smoke job's`);
    console.log('  matrix no longer looks like `stage: [...]`. No figure is guessed here.');
    return;
  }
  const viewports = shape.viewports || ['mobile', 'desktop'];
  console.log('THE NIGHTLY GATE, LEG BY LEG');
  console.log(`Legs and cap read from ${wf(BAKE_WF)} § smoke. Seconds read from`);
  console.log('tools/dev-smoke-state.json, the same steward-runner readings as the default');
  console.log(`report. ${viewports.length} viewport(s) x ${shape.legs.length} stage range(s) = `
    + `${viewports.length * shape.legs.length} legs, IN PARALLEL,`);
  console.log(`each capped at ${capText(shape.legCapS)}. A leg's cap bounds the leg and nothing else.\n`);
  let worst = null;
  for (const viewport of viewports) {
    console.log(`  ${viewport}`);
    for (const leg of shape.legs) {
      const { chosen, missing } = cover(groups, viewport, leg.parts);
      const total = chosen.reduce((a, g) => a + g.median, 0);
      const spill = [...new Set(chosen.flatMap((g) => g.parts))].filter((q) => !leg.parts.includes(q))
        .sort((a, b) => a - b);
      const notes = [];
      if (missing.length) notes.push(`part(s) ${stageArg(missing)} unmeasured`);
      // A reading that spans the leg boundary prices this leg HIGH, so the
      // margin beside it is a floor on the real margin, never a ceiling.
      if (spill.length) notes.push(`cost is an UPPER bound, margin a LOWER one — the only readings also cover part(s) ${stageArg(spill)}`);
      const margin = shape.legCapS == null || missing.length ? null : shape.legCapS - total;
      if (margin != null && !spill.length && (worst == null || margin < worst.margin)) {
        worst = { margin, viewport, label: leg.label };
      }
      console.log(`    stage ${leg.label.padEnd(6)} ${fmt(total).padStart(8)}`
        + `   margin ${margin == null ? '     —' : fmt(margin)}`
        + (notes.length ? `   (${notes.join('; ')})` : ''));
    }
    console.log('');
  }
  if (worst) {
    console.log(`  WORST FULLY MEASURED MARGIN: ${viewportLabel(worst)} at ${fmt(worst.margin)}.`);
  }
  console.log('  A margin is a margin against the machine that measured it — these readings');
  console.log('  were taken on the improve runner, and T-0215 put a factor of twenty on what');
  console.log('  contention does to them. ROADMAP § THE RUN BUDGET is the record of that.');
}

const viewportLabel = (w) => `${w.viewport} ${w.label}`;

function reportFor(paths) {
  const groups = measured();
  const { hits, want, unknown } = partsFor(paths);
  console.log('WHAT YOU CHANGED, AND THE PARTS THAT COVER IT\n');
  for (const h of hits) {
    console.log(`  ${h.path}\n      ${h.none ? 'NO PART' : `parts ${stageArg(h.parts)}`} — ${h.why}`);
  }
  if (!want.length) {
    // Every path was a NONE row. The scene did not change, so no part of the
    // body has anything to say about it — but boot, the page-error check and
    // the vendor checks are taken in every invocation, so one cheap staged
    // pass per viewport still proves the page comes up clean.
    console.log('\n  NO PART OF THE SMOKE BODY READS ANY OF THIS. check.sh is the gate that');
    console.log('  covers it. Take the always-on scaffolding anyway — boot, the page-error');
    console.log('  check and the vendor checks run in EVERY invocation:\n');
    const groups = measured();
    for (const viewport of ['mobile', 'desktop']) {
      const { cmds } = recipe(groups, viewport, [cheapestPart(groups, viewport)]);
      const c = cmds[0];
      console.log(`    SMOKE_VIEWPORT=${viewport} SMOKE_STAGE=${stageArg(c.parts)} node tools/smoke_renderer.mjs --published`
        + `\n        ≈ ${fmt(c.secs)} measured, the cheapest part of that viewport`);
    }
    console.log('');
    console.log('  A staged run is NOT the gate and says so on its first line.');
    return;
  }
  console.log(`\n  parts to run: ${stageArg(want)}`
    + (unknown ? `  (${unknown} path(s) not in the map, so the whole gate)` : ''));
  console.log('\n  RUN, from chicago/4d/ (each command packed under the foreground ceiling):\n');
  for (const viewport of ['mobile', 'desktop']) {
    const { cmds, estimated } = recipe(groups, viewport, want);
    for (const c of cmds) {
      console.log(`    SMOKE_VIEWPORT=${viewport} SMOKE_STAGE=${stageArg(c.parts)} node tools/smoke_renderer.mjs --published`
        + `\n        ≈ ${fmt(c.secs)} measured, ${fmt(CEILING_S - c.secs)} of margin`);
    }
    if (estimated.length) {
      console.log(`    (part ${stageArg(estimated.filter((p) => want.includes(p)))} has no reading of its own; `
        + 'priced at the mean of those that do)');
    }
  }
  console.log('\n  A staged run is NOT the gate and says so on its first line. The gate is');
  console.log('  both viewports, every part — see the cost of that with no arguments.');
  console.log('  File what you ran: node tools/dev-smoke-state.mjs record <log>');
  console.log('  And redirect to a FILE, not a pipe: node block-buffers stdout to a pipe,');
  console.log('  so a piped smoke log stays at zero bytes until the process exits — which');
  console.log('  is how a run at 41 minutes was killed one minute from its finish (T-0235).');
}

function selfTest() {
  const fails = [];
  const smoke = fs.readFileSync(SMOKE, 'utf8');
  const m = /^const PARTS = (\d+);$/m.exec(smoke);
  if (!m) fails.push('cannot find `const PARTS = N;` in tools/smoke_renderer.mjs');
  else if (Number(m[1]) !== PARTS) fails.push(`smoke_renderer.mjs has PARTS=${m[1]}, this map is built for ${PARTS}`);

  const seen = new Set();
  for (const [pat, parts, why] of COVERAGE) {
    // An empty row is deliberate — NONE — and must say why in the same breath.
    if (!parts.length && !why) fails.push(`${pat}: maps to no part and gives no reason`);
    for (const p of parts) {
      if (!Number.isInteger(p) || p < 1 || p > PARTS) fails.push(`${pat}: part ${p} is not 1..${PARTS}`);
      seen.add(p);
    }
    if (!why) fails.push(`${pat}: no reason given`);
    // `site/4d/` is the published mirror and lives at the repo root;
    // every other pattern is relative to chicago/4d/.
    const target = pat.startsWith('site/') ? path.join(REPO, pat) : path.join(APP, pat);
    if (!fs.existsSync(target)) fails.push(`${pat}: no such path in the tree — the map has rotted`);
  }
  for (const p of ALL) if (!seen.has(p)) fails.push(`part ${p} is covered by no row of the map`);

  // T-1519 — every anchored module's row names every part its anchors are found in.
  for (const [pat, needles] of ANCHORS) {
    const row = COVERAGE.find(([p]) => p === pat);
    if (!row) { fails.push(`${pat}: anchored but has no row of its own in the map`); continue; }
    for (const needle of needles) {
      const holding = partsHolding(smoke, needle);
      if (!holding.length) fails.push(`${pat}: anchor ${JSON.stringify(needle)} is in no part of the gate — the anchor has rotted`);
      const missing = holding.filter((p) => !row[1].includes(p));
      if (missing.length) {
        fails.push(`${pat}: maps to [${row[1].join(', ')}] but its anchor ${JSON.stringify(needle)} `
          + `is checked in part ${missing.join(', ')} — a run that trusts the row runs the wrong leg`);
      }
    }
  }

  // The published mirror can no longer reach this map at all (T-0938), and that is
  // asserted rather than assumed: it is untracked and .gitignored, so `--for-diff`'s
  // `git diff --name-only` never names it. Two self-test cases used to hold the mirror
  // rows in place — the publish stamp must price at NONE, a mirrored renderer module at
  // the whole gate — and both are replaced by this one, which holds the precondition
  // they rested on. If the mirror is ever tracked again this fails and the rows come back.
  {
    const tracked = execFileSync('git', ['ls-files', '--', 'site/4d'],
      { cwd: REPO, encoding: 'utf8' }).trim();
    if (tracked) fails.push('site/4d is tracked again — the published mirror is back on the '
      + 'PR surface, so it can appear in a diff and this map needs its rows back (T-0938)');
  }

  // The map may only ever ADD parts: an unknown path is the whole gate.
  const unknown = partsFor(['renderers/web/js/no-such-module-at-all.js']);
  if (unknown.want.length !== PARTS) fails.push('an unknown path must map to the whole gate, not to a subset');

  // The renumbering is the one piece of arithmetic here, so assert it directly.
  const old = (parts, when) => currentParts({ parts, takenAt: when });
  const before = '2026-08-29T12:00:00Z';
  const after = '2026-08-30T12:00:00Z';
  const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  // Between the two cuts of 2026-08-30: T-0173 applies, T-0346 does not.
  const between = '2026-08-30T04:00:00Z';
  if (!eq(old([3], before), [3])) fails.push('old part 3 must renumber to 3');
  if (!eq(old([4], before), [4, 5, 6])) fails.push('old part 4 must renumber to 4,5,6');
  if (!eq(old([5], before), [7, 8])) fails.push('old part 5 must renumber to 7,8 through both cuts');
  if (!eq(old([7, 8, 9], before), [10, 11, 12, 13])) fails.push('old parts 7-9 must renumber to 10-13');
  if (!eq(old([7], between), [7, 8])) fails.push('T-0346-era part 7 must renumber to 7,8');
  if (!eq(old([8, 11], between), [9, 13])) fails.push('T-0346-era parts 8 and 11 must renumber to 9 and 13');
  // …and the epoch between T-0173 and T-0170, which is the one a renumbering
  // that composes only the first two cuts gets wrong.
  const between2 = '2026-08-30T05:40:00Z';
  if (!eq(old([10], between2), [10, 11])) fails.push('a T-0173-era part 10 must renumber to 10,11');
  if (!eq(old([11], between2), [12])) fails.push('a T-0173-era part 11 must renumber to 12');
  if (!eq(old([7], between2), [7])) fails.push('a T-0173-era part 7 must not be renumbered again');
  if (!eq(old([4], after), [4])) fails.push('a reading filed after all three cuts must not be renumbered');

  if (!eq(stageArg([1, 2, 3, 5, 7, 8]), '1-3,5,7-8')) fails.push('stageArg does not fold contiguous runs');

  // T-0450 — the nightly gate's legs must tile the parts exactly once, which is
  // what makes "the union of the legs is the gate" checkable rather than
  // asserted. The workflow comment has said so since T-0171 and nothing held it.
  // A checkout without `.github/` is a skip, not a failure: the tool reports the
  // legs as unreadable there and guesses nothing.
  const shape = gateShape();
  if (shape.legs) {
    const covered = shape.legs.flatMap((l) => l.parts);
    const once = [...new Set(covered)].sort((a, b) => a - b);
    if (covered.length !== once.length) fails.push(`the ${wf(BAKE_WF)} smoke legs overlap: ${shape.legs.map((l) => l.label).join(' ')}`);
    if (!eq(once, ALL)) fails.push(`the ${wf(BAKE_WF)} smoke legs do not tile parts 1..${PARTS}: ${shape.legs.map((l) => l.label).join(' ')}`);
    if (!shape.legCapS) fails.push(`no timeout-minutes on the ${wf(BAKE_WF)} smoke job — the per-leg cap cannot be read`);
    if (!shape.wholeCapS) fails.push(`no timeout-minutes on the ${wf(FULL_WF)} smoke job — the whole-body cap cannot be read`);
  }

  // Every group in the record must renumber into current parts.
  for (const g of measured()) {
    if (g.parts.some((p) => p < 1 || p > PARTS)) fails.push(`a reading renumbers outside 1..${PARTS}: ${key(g.parts)}`);
  }

  if (fails.length) {
    for (const f of fails) console.error(`  FAIL ${f}`);
    console.error(`smoke budget self-test: ${fails.length} failure(s)`);
    process.exit(1);
  }
  const legs = gateShape().legs;
  console.log(`smoke budget self-test: the map covers all ${PARTS} parts, `
    + `${COVERAGE.length} patterns all exist, ${ANCHORS.length} anchored modules sit in their parts, the renumbering holds`
    + (legs ? `, the ${legs.length} gate legs tile 1-${PARTS} exactly once` : ', gate legs not in this checkout'));
}

const argv = process.argv.slice(2);
if (argv[0] === '--self-test') selfTest();
else if (argv[0] === '--legs') reportLegs(measured());
else if (argv[0] === '--for') reportFor(argv.slice(1));
else if (argv[0] === '--for-diff') {
  const ref = argv[1] || 'origin/dev';
  const out = execFileSync('git', ['diff', '--name-only', `${ref}...HEAD`], { cwd: APP, encoding: 'utf8' });
  // `chicago/4d/` only: the published mirror is untracked and generated (T-0938), so it
  // is never in a diff and there is nothing under site/ left to price.
  const paths = out.split('\n').map((s) => s.trim()).filter((s) => s.startsWith('chicago/4d/'));
  if (!paths.length) console.log(`nothing under chicago/4d/ changed against ${ref}`);
  else reportFor(paths.map((p) => p.replace(/^chicago\/4d\//, '')));
} else if (argv.length && argv[0].startsWith('-')) {
  console.error('usage: smoke_budget.mjs [--legs | --for <path>… | --for-diff [ref] | --self-test]');
  process.exit(2);
} else reportCost(measured());
