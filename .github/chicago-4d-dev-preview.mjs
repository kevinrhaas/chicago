// chicago-4d-dev-preview.mjs — fold the dev branch's 4D app into the production
// Pages artifact as a subdirectory.
//
//   node .github/chicago-4d-dev-preview.mjs <devWorktree> <sha> <committedIso>
//
// Adapted from kevinrhaas/jobtracker.polecat.live `.github/stage-preview.mjs`
// (the fleet pilot, docs/PIPELINE.md there). Three of the pilot's four jobs turn
// out to be unnecessary here, and saying why is the point of this comment —
// the next person will otherwise assume they were forgotten.
//
//   • NO PATH REWRITING. The pilot rewrites every root-absolute `/x` URL to
//     `/stage/x` because its app is served from the domain root. The 4D app has
//     ZERO root-absolute URLs — measured, not assumed: `walk/index.html` uses
//     `./css/…` and `./js/…`, and the data layer resolves by page path
//     (`scene-loader.js` computes `../data/` from `walk/`). Copying the whole
//     published `site/chicago/4d/` tree under `dev/` therefore preserves every
//     path by construction, which is exactly why the whole tree is mirrored
//     rather than just `walk/`.
//   • NO SERVICE-WORKER STUB. The pilot must neutralise an installed SW so a
//     preview never caches itself into a visitor's browser. The 4D walk app has
//     no service worker at all, so there is nothing to neutralise and a stub
//     would be a file that exists only to be confusing.
//   • NO CNAME / releases handling. `custom` is a monorepo of unrelated tenants
//     published from `site/`; this script touches ONLY `site/chicago/4d/`, and
//     the other tenants must never appear under a 4D preview.
//
// What it does do: copy, mark the copy as a preview so nobody mistakes it for
// production, keep it out of search, and stamp it so the build is identifiable.
import { readFile, writeFile, cp, rm, readdir, stat, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

const [srcRoot, sha = '', committedIso = ''] = process.argv.slice(2);
if (!srcRoot) {
  console.error('usage: node .github/chicago-4d-dev-preview.mjs <devWorktree> [sha] [committedIso]');
  process.exit(2);
}

/**
 * Central Time, the clock every date in this project is quoted in — same
 * format string the production stamp uses (`Aug 13, 2026, 11:59 PM CT`) so the
 * two gates read alike.
 *
 * Intl emits U+202F before AM/PM on current ICU where the shell's `date` emits
 * a plain space, and the two stamps sitting side by side in a screenshot should
 * not differ by an invisible character; both narrow and non-breaking spaces are
 * flattened.
 */
function ct(iso) {
  const d = new Date(iso);
  if (!iso || isNaN(d)) return '';
  return `${d.toLocaleString('en-US', {
    timeZone: 'America/Chicago', month: 'short', day: 'numeric', year: 'numeric',
    hour: 'numeric', minute: '2-digit',
  }).replace(/[  ]/g, ' ')} CT`;
}

const APP = 'site/chicago/4d';
const SRC = join(srcRoot, APP);
const OUT = join(APP, 'dev');

if (!existsSync(SRC)) {
  console.log(`dev-preview: ${SRC} does not exist on the dev ref — skipping`);
  process.exit(0);
}

// `dev` excluded so a preview can never nest inside itself if the dev branch
// ever carries one (it should not, but a recursive copy is an unpleasant way to
// discover that).
const EXCLUDE = new Set(['dev', '.git', 'node_modules']);

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });
for (const item of await readdir(SRC)) {
  if (EXCLUDE.has(item)) continue;
  await cp(join(SRC, item), join(OUT, item), { recursive: true });
}

const stamp = `dev${sha ? `@${sha}` : ''}`;

// The gate's stamp answers "which build am I looking at, and how old is it" —
// production shows `build <sha> · <when>`, so the preview shows the same pair.
//
// `when` is the DEV COMMIT'S OWN date, not the moment this script ran, and the
// difference matters: the preview is reassembled on every deploy of main, so an
// assembly time would tick forward on builds where dev did not change at all,
// and "the preview is three minutes old" would be a lie told about a
// day-old branch. The commit date moves only when dev does, which is the
// question the line is being asked. Production's stamp uses its deploy time,
// but there main is deployed within seconds of the commit, so the two readings
// agree; here they would not.
const when = ct(committedIso);
const gateStamp = `DEV PREVIEW · ${stamp}${when ? ` · ${when}` : ''}`;

for (const file of await htmlFiles(OUT)) {
  let html = await readFile(file, 'utf8');

  // Out of the index. A preview that ranks is a preview that gets cited.
  if (/<meta[^>]*name="robots"/i.test(html)) {
    html = html.replace(/<meta[^>]*name="robots"[^>]*\/?>/gi,
      '<meta name="robots" content="noindex,nofollow">');
  } else {
    html = html.replace(/<head([^>]*)>/i,
      `<head$1>\n  <meta name="robots" content="noindex,nofollow">`);
  }

  // The build stamp the gate shows, re-marked so a screenshot from the preview
  // is never mistaken for production. deploy.yml stamps production's copy with
  // the same element; this overwrites the dev copy's with a dev-flagged one.
  html = html.replace(
    /<p class="gate-build" id="gate-build"[^>]*>.*?<\/p>/s,
    `<p class="gate-build" id="gate-build">${gateStamp}</p>`);

  if (!html.includes('id="__dev"')) {
    html = html.replace(/<\/body>/i, `${banner(stamp)}\n</body>`);
  }
  await writeFile(file, html);
}

// A machine-readable marker beside the human one, so a smoke test can assert
// which tier it is looking at without scraping a banner.
await writeFile(join(OUT, 'build.json'), `${JSON.stringify({
  tier: 'dev',
  app: 'chicago/4d',
  ref: 'refs/heads/dev',
  sha,
  // When the dev HEAD was committed, machine-readable beside the CT rendering
  // the gate shows. `assembledAt` is deliberately absent: it would differ from
  // this on every main deploy and there is no question it answers.
  committedAt: committedIso || null,
  committedCT: when || null,
  note: 'Integration preview. Production is at ../walk/ and is promoted only on '
    + 'owner dispatch (chicago-4d-promote-to-prod.yml).',
}, null, 2)}\n`);

// Keep crawlers out from the production robots.txt as well as per-page.
const ROBOTS = 'site/robots.txt';
if (existsSync(ROBOTS)) {
  let robots = await readFile(ROBOTS, 'utf8');
  if (!robots.includes('Disallow: /chicago/4d/dev/')) {
    robots = /User-agent: \*/.test(robots)
      ? robots.replace(/(User-agent: \*\n)/, '$1Disallow: /chicago/4d/dev/\n')
      : `${robots.trimEnd()}\n\nUser-agent: *\nDisallow: /chicago/4d/dev/\n`;
    await writeFile(ROBOTS, robots);
  }
} else {
  await writeFile(ROBOTS, 'User-agent: *\nDisallow: /chicago/4d/dev/\n');
}

console.log(`dev-preview: assembled ${OUT} from ${SRC}${sha ? ` (${sha})` : ''}`);

async function htmlFiles(dir) {
  const out = [];
  for (const item of await readdir(dir)) {
    const p = join(dir, item);
    if ((await stat(p)).isDirectory()) out.push(...await htmlFiles(p));
    else if (item.endsWith('.html')) out.push(p);
  }
  return out;
}

function banner(rev) {
  const FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif";
  // Fixed to the TOP here, unlike the pilot's bottom bar: this app puts its
  // touch controls and its street readout along the bottom edge, and a bar
  // across them would cover the thing the preview exists to let you look at.
  return `<div id="__dev" role="status" style="position:fixed;left:0;right:0;top:0;z-index:2147483000;display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;padding:5px 40px 5px 12px;font:600 12px ${FONT};color:#1a1503;background:linear-gradient(135deg,#fbbf24,#d97706);box-shadow:0 4px 16px rgba(0,0,0,.3)">
  <span><b>DEV PREVIEW</b> — ${rev} · not production, not indexed</span>
  <a href="../walk/?year=1835" style="color:#1a1503;text-decoration:underline">open production</a>
  <button id="__devmin" aria-label="Collapse the dev preview banner" title="Collapse" style="position:absolute;right:6px;top:50%;transform:translateY(-50%);width:24px;height:24px;border:0;border-radius:50%;background:rgba(0,0,0,.22);color:#1a1503;font:700 13px/1 ${FONT};cursor:pointer">&times;</button>
</div>
<button id="__devpill" aria-label="Expand the dev preview banner" title="Dev preview" style="position:fixed;right:8px;top:8px;z-index:2147483000;display:none;border:0;border-radius:999px;padding:5px 11px;font:800 10px ${FONT};letter-spacing:.06em;color:#1a1503;background:linear-gradient(135deg,#fbbf24,#d97706);box-shadow:0 3px 12px rgba(0,0,0,.35);cursor:pointer">DEV</button>
<script>(function(){var K="__dev.min",b=document.getElementById("__dev"),p=document.getElementById("__devpill");function set(m){b.style.display=m?"none":"flex";p.style.display=m?"inline-block":"none";try{localStorage.setItem(K,m?"1":"0")}catch(e){}}document.getElementById("__devmin").onclick=function(){set(true)};p.onclick=function(){set(false)};try{if(localStorage.getItem(K)==="1")set(true)}catch(e){}})();</script>`;
}
