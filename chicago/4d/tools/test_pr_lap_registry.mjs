#!/usr/bin/env node
/**
 * test_pr_lap_registry.mjs — the lap merges the asset registries entry by entry (T-2892).
 *
 * WHY THIS EXISTS (owner, 2026-10-19). `assets/manifest.json` and
 * `assets/manifest.web.json` are one JSON object each for the whole town, keyed by GLB,
 * and every bake rewrites them whole. Two PRs that bake DIFFERENT structures therefore
 * conflict there without disagreeing about anything — #1104 conflicted with dev on
 * manifest.json and NOTHING ELSE on 2026-10-19, and the lap left it alone as a REAL
 * CONFLICT until a steward run spent a whole lap merging dev and rebaking.
 *
 * WHAT IS REAL HERE AND WHAT IS FAKED. As in test_pr_lap_publish.mjs: the lap is the REAL
 * `.github/steward/pr-lap.sh`, git is real, the remote is a real bare repository, and the
 * merge, commit and push are the genuine article. The registry merger is the REAL
 * tools/merge_asset_registry.py, copied into the fixture's tool tree because the lap runs
 * the one in the tree it laps. The rest of chicago/4d/tools/ is stubs.
 *
 *   1. dev and the PR each baked a different structure, and both new names sort into the
 *      same gap — git conflicts on both registries; the lap pushes, and the PR branch on
 *      the remote carries BOTH entries in each file.
 *   2. both rebaked the SAME structure — the lap leaves the PR alone, branch unmoved.
 *   3. a registry conflict beside a REAL one — left alone, the registry step never run.
 *   4. case 1 again with the registry step cut out of the lap — it must be left alone,
 *      so this suite is shown to see the thing it tests.
 *   5. a full derived rebuild beside the registries survives the later generated-file
 *      checkout and is pushed from both cleanly merged authored inputs.
 *   6. a real authored conflict still refuses that rebuild and leaves the branch alone.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync, copyFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const LAP = path.resolve(HERE, '..', '..', '..', '.github', 'steward', 'pr-lap.sh');
const MERGER = path.join(HERE, 'merge_asset_registry.py');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};
const git = (cwd, ...args) => {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`git ${args.join(' ')}\n${r.stdout}${r.stderr}`);
  return r.stdout;
};

// Written the way generators/build.py and tools/web_derivatives.sh write them:
// indent 2 and a final newline; the manifest with every key sorted, the web record
// with its own key order and the masters sorted.
const sortDeep = (v) => (v && typeof v === 'object' && !Array.isArray(v)
  ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, sortDeep(v[k])])) : v);
const entry = (n) => ({ bytes: n, inputs_sha256: n.toString(16).padStart(64, '0'), kind: 'generated' });
function writeRegistries(work, assets) {
  const dir = path.join(work, 'chicago', '4d', 'assets');
  mkdirSync(dir, { recursive: true });
  const man = { assets: Object.fromEntries(Object.entries(assets).map(([k, n]) => [k, entry(n)])),
                blender: '4.2.1', inputs_scheme: 'mesh-inputs-v3' };
  writeFileSync(path.join(dir, 'manifest.json'), `${JSON.stringify(sortDeep(man), null, 2)}\n`);
  const masters = Object.fromEntries(Object.keys(assets).sort().map((k) => [k, String(assets[k] % 10).repeat(64)]));
  const web = { $note: 'derived', written_by: 'tools/web_derivatives.sh', masters };
  writeFileSync(path.join(dir, 'manifest.web.json'), `${JSON.stringify(web, null, 2)}\n`);
}

function runLap({ ours, theirs, lapSource = null, clash = false, derived = false }) {
  const box = mkdtempSync(path.join(tmpdir(), 'prlapreg-'));
  const bare = path.join(box, 'remote.git');
  const work = path.join(box, 'work');
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });
  git(box, 'init', '--quiet', '--bare', '-b', 'dev', bare);
  git(box, 'clone', '--quiet', bare, work);
  git(work, 'config', 'user.name', 'fixture');
  git(work, 'config', 'user.email', 'fixture@example.com');

  const tools = path.join(work, 'chicago', '4d', 'tools');
  mkdirSync(tools, { recursive: true });
  writeFileSync(path.join(work, '.gitignore'), 'site/4d/\n');
  writeFileSync(path.join(work, '.gitattributes'), '# no merge drivers in the fixture\n');
  copyFileSync(MERGER, path.join(tools, 'merge_asset_registry.py'));
  // The derived layer owns nothing here: --resolvable says no, --run and --tail succeed.
  writeFileSync(path.join(tools, 'rederive.mjs'),
    "if (process.argv.includes('--resolvable')) process.exit(1);\nprocess.exit(0);\n");
  if (derived) {
    // Only this enumerated output is resolvable. Full regeneration reads the
    // genuinely merged authored source; the scene tail does not own this file.
    writeFileSync(path.join(tools, 'rederive.mjs'), `
import { readFileSync, writeFileSync } from 'node:fs';
if (process.argv.includes('--resolvable')) {
  const paths = process.argv.slice(process.argv.indexOf('--resolvable') + 1);
  process.exit(paths.length && paths.every(p => p === 'chicago/4d/data/liberties.json') ? 0 : 1);
}
if (process.argv.includes('--run')) {
  const source = readFileSync('docs/LIBERTIES.md', 'utf8');
  writeFileSync('data/liberties.json', JSON.stringify({pr: source.includes('PR: yes'), dev: source.includes('DEV: yes')}) + '\\n');
}
`);
    mkdirSync(path.join(work, 'chicago/4d/docs'), { recursive: true });
    mkdirSync(path.join(work, 'chicago/4d/data'), { recursive: true });
  }
  const derivedSource = (pr, dev) => `# fixture liberties\nPR: ${pr ? 'yes' : 'no'}\n${'unchanged evidence\n'.repeat(12)}DEV: ${dev ? 'yes' : 'no'}\n`;
  const writeDerived = (pr, dev) => {
    if (!derived) return;
    writeFileSync(path.join(work, 'chicago/4d/docs/LIBERTIES.md'), derivedSource(pr, dev));
    writeFileSync(path.join(work, 'chicago/4d/data/liberties.json'), JSON.stringify({pr, dev}) + '\n');
    const generated = path.join(work, 'chicago/4d/renderers/web/js');
    mkdirSync(generated, { recursive: true });
    writeFileSync(path.join(generated, 'changelog.js'), pr ? 'PR generated\n' : dev ? 'dev generated\n' : 'base generated\n');
  };
  writeDerived(false, false);
  writeFileSync(path.join(tools, 'publish.sh'), '#!/usr/bin/env bash\nmkdir -p ../../site/4d\necho published\n');
  writeFileSync(path.join(tools, 'ticket.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'stamp-changelog.mjs'), 'process.exit(0);\n');
  writeFileSync(path.join(tools, 'compile_scene.py'), 'pass\n');
  writeFileSync(path.join(tools, 'tickets.sh'), '#!/usr/bin/env bash\nexit 0\n');
  for (const f of ['publish.sh', 'tickets.sh']) chmodSync(path.join(tools, f), 0o755);
  const base = { 'a.glb': 1, 'b.glb': 2, 'c.glb': 3 };
  writeRegistries(work, base);
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'fixture: the tool tree and the registries');
  git(work, 'push', '--quiet', 'origin', 'dev');

  git(work, 'checkout', '--quiet', '-b', 'steward/t-9999');
  writeRegistries(work, { ...base, ...ours });
  writeDerived(true, false);
  if (clash) writeFileSync(path.join(work, 'chicago', '4d', 'source.txt'), 'the PR\'s reading\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'the PR baked its structure');
  git(work, 'push', '--quiet', 'origin', 'steward/t-9999');
  const branchHead = git(work, 'rev-parse', 'HEAD').trim();

  git(work, 'checkout', '--quiet', 'dev');
  writeRegistries(work, { ...base, ...theirs });
  writeDerived(false, true);
  if (clash) writeFileSync(path.join(work, 'chicago', '4d', 'source.txt'), 'dev\'s reading\n');
  git(work, 'add', '-A');
  git(work, 'commit', '--quiet', '-m', 'dev baked another');
  git(work, 'push', '--quiet', 'origin', 'dev');

  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
if [ "$1" = "api" ]; then printf '%b' '7\\tsteward/t-9999\\n'; fi
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);
  let lap = LAP;
  if (lapSource !== null) { lap = path.join(box, 'pr-lap.sh'); writeFileSync(lap, lapSource); }
  const r = spawnSync('bash', [lap, '--repo', 'kevinrhaas/chicago'], {
    cwd: work, encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, GH_TOKEN: 'fake', LAP_BASE: 'dev', LAP_ONLY: '' },
  });
  const after = git(box, '--git-dir', bare, 'rev-parse', 'refs/heads/steward/t-9999').trim();
  const show = (rel) => {
    const s = spawnSync('git', ['--git-dir', bare, 'show', `refs/heads/steward/t-9999:${rel}`], { encoding: 'utf8' });
    return s.status === 0 ? s.stdout : null;
  };
  const manifest = show('chicago/4d/assets/manifest.json');
  const web = show('chicago/4d/assets/manifest.web.json');
  const rebuilt = show('chicago/4d/data/liberties.json');
  const authored = show('chicago/4d/docs/LIBERTIES.md');
  const generated = show('chicago/4d/renderers/web/js/changelog.js');
  rmSync(box, { recursive: true, force: true });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  return { code: r.status, out, summary: (out.match(/^PR lap: .*$/m) || ['no summary line'])[0],
           moved: after !== branchHead, manifest, web, rebuilt, authored, generated };
}

console.log('pr-lap.sh — the asset registries merge entry by entry (T-2892)');

/* 1. Two different structures baked; the new names sort into one gap, so git conflicts. */
{
  const r = runLap({ ours: { 'a.glb': 11, 'b2.glb': 22 }, theirs: { 'b1.glb': 21, 'c.glb': 33 } });
  check('the lap pushes', /pushed=1/.test(r.out), r.summary);
  check('…and the PR branch really moved on the remote', r.moved);
  check('…and it says the registries were merged entry by entry', /asset registries merged entry by entry/.test(r.out));
  let m = null, w = null;
  try { m = JSON.parse(r.manifest); w = JSON.parse(r.web); } catch { /* reported below */ }
  check('both pushed registries are JSON (no conflict markers)', m !== null && w !== null);
  check('manifest.json carries ours\' and dev\'s bakes both',
        m && JSON.stringify(Object.keys(m.assets)) === JSON.stringify(['a.glb', 'b.glb', 'b1.glb', 'b2.glb', 'c.glb'])
        && m.assets['a.glb'].bytes === 11 && m.assets['b2.glb'].bytes === 22
        && m.assets['b1.glb'].bytes === 21 && m.assets['c.glb'].bytes === 33, m && Object.keys(m.assets).join(','));
  check('manifest.web.json the same, masters sorted',
        w && JSON.stringify(Object.keys(w.masters)) === JSON.stringify(['a.glb', 'b.glb', 'b1.glb', 'b2.glb', 'c.glb']));
  check('the lap exits clean', r.code === 0, `exit ${r.code}`);
}

/* 2. Both rebaked the SAME structure: a real disagreement, left alone as before. */
{
  const r = runLap({ ours: { 'b.glb': 12 }, theirs: { 'b.glb': 13 } });
  check('the same master rebaked on both sides is left alone', /left-alone=1/.test(r.out), r.summary);
  check('…and the branch does not move', !r.moved);
  check('…and the refusal names the entry', /'b\.glb': both sides changed it differently/.test(r.out));
}

/* 3. A registry conflict beside a REAL one: left alone, and the registry never touched —
 *    the emitters must not read a tree with conflict markers in it (#1109, 2026-10-19). */
{
  const r = runLap({ ours: { 'a.glb': 11, 'b2.glb': 22 }, theirs: { 'b1.glb': 21, 'c.glb': 33 }, clash: true });
  check('a real conflict beside the registry still leaves the PR alone', /left-alone=1/.test(r.out), r.summary);
  check('…naming the real file', /REAL CONFLICT[\s\S]*chicago\/4d\/source\.txt/.test(r.out));
  check('…and the registry step did not run', !/merged entry by entry/.test(r.out));
  check('…and the branch does not move', !r.moved);
}

/* 4. The same suite, the registry step cut out of the lap: case 1 must be refused. */
{
  const raw = readFileSync(LAP, 'utf8');
  const GUARD = '[ -f chicago/4d/tools/merge_asset_registry.py ]';
  check('the registry step is guarded in one place, so cutting it is a fair simulation',
        raw.split(GUARD).length === 2, `${raw.split(GUARD).length - 1} occurrence(s)`);
  const r = runLap({ ours: { 'a.glb': 11, 'b2.glb': 22 }, theirs: { 'b1.glb': 21, 'c.glb': 33 },
                     lapSource: raw.replace(GUARD, 'false') });
  check('without it the PR is left alone for a REAL CONFLICT', /left-alone=1/.test(r.out) && /REAL CONFLICT/.test(r.out), r.summary);
  check('…and the branch does not move', !r.moved);
}

/* 5. A derived conflict beside the registries: the full rebuild must survive
 *    the later generated-conflict checkout. Both authored edits merge cleanly. */
{
  const r = runLap({ ours: { 'a.glb': 11, 'b2.glb': 22 }, theirs: { 'b1.glb': 21, 'c.glb': 33 }, derived: true });
  check('a derived conflict actually runs the full rebuild', /conflict\(s\) in the derived research layer/.test(r.out));
  check('the real lap pushes its merge', /pushed=1/.test(r.out) && r.moved, r.summary);
  check('both independent authored edits survive', r.authored && r.authored.includes('PR: yes') && r.authored.includes('DEV: yes'));
  check('the pushed derived artifact reflects both merged inputs', r.rebuilt === JSON.stringify({pr: true, dev: true}) + '\n', r.rebuilt && r.rebuilt.trim());
  check('unrelated generated conflicts retain their existing ours-then-regenerate handling', r.generated === 'PR generated\n');
  const m = JSON.parse(r.manifest);
  check('the accompanying registry union survives the rebuild', m.assets['b1.glb'].bytes === 21 && m.assets['b2.glb'].bytes === 22);
}

/* 6. A true conflict still refuses the whole merge before any full rebuild. */
{
  const r = runLap({ ours: { 'b.glb': 12 }, theirs: { 'b.glb': 13 }, derived: true, clash: true });
  check('an authored conflict beside derived outputs is still refused', /left-alone=1/.test(r.out) && /REAL CONFLICT/.test(r.out), r.summary);
  check('the refused branch stays unchanged', !r.moved);
  check('the unsafe full rebuild never runs', !/conflict\(s\) in the derived research layer/.test(r.out));
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);
