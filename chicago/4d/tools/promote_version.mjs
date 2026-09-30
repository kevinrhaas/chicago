#!/usr/bin/env node
/**
 * promote_version.mjs — make one STRUCTURE VERSION the default, in one command (T-1727).
 *
 *   node tools/promote_version.mjs <structure_id> <label>            promote it
 *   node tools/promote_version.mjs <structure_id> <label> --dry-run  say what would move
 *     [--keep-as <label>]   what to call the old default (default: pre-<label>)
 *     [--bake]              if any mesh of the structure is missing or stale afterwards,
 *                           run tools/bake.sh --only <id> (needs Blender; the improve
 *                           runner has none — without this flag it prints the command
 *                           and exits 3, and the chicago-4d-bake workflow can do it)
 *     [--no-compile]        skip the sidecar recompile (the self-test uses this)
 *   node tools/promote_version.mjs --self-test                       prove it on a sandbox
 *
 * The owner builds several versions of a house (the Glessner House first — T-1729,
 * T-1730), opens them side by side with `?structure=<id>&version=<label>`, and picks
 * one. This is the pick: the chosen version's record becomes `data/structures/<id>.json`,
 * the old default is KEPT as `data/structures/versions/<id>/<keep>.json` (so the
 * comparison can still be made after the choice), and both meshes, their web
 * derivatives and all three build records move with them. The result is ONE diff: open
 * it as a pull request into `dev` and the owner's call is reviewable line by line.
 *
 * WHY NOTHING IS RE-BAKED IN THE ORDINARY CASE. A mesh's freshness is its inputs hash
 * (generators/mesh_inputs.py), taken over the structure id, the resolved builder
 * parameters and the code — not over the directory a record sits in, and not over the
 * `version` block, which no builder reads. So a version that was fresh as a version is
 * fresh as the default, byte for byte. `status` is asked afterwards anyway, and a
 * version that was never baked (or went stale) is caught there and baked, or named.
 *
 * The file moves are done by `tools/structure_versions.py promote` — in Python because
 * records must round-trip byte-compatibly with data/structures/ (JSON.stringify writes
 * 90.0 as 90, a different number in the builder's hash). This file orchestrates: move,
 * recompile the sidecars, check the meshes, and print what the PR needs.
 */

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const PY = path.join(ROOT, 'tools', 'structure_versions.py');

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { cwd: ROOT, encoding: 'utf8', ...opts });
  return { code: r.status ?? 1, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
}

function parse(argv) {
  const o = { positional: [], dryRun: false, bake: false, compile: true, keepAs: null, selfTest: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') o.dryRun = true;
    else if (a === '--bake') o.bake = true;
    else if (a === '--no-compile') o.compile = false;
    else if (a === '--self-test') o.selfTest = true;
    else if (a === '--keep-as') o.keepAs = argv[++i];
    else if (a.startsWith('--')) { console.error(`unknown option ${a}`); process.exit(2); }
    else o.positional.push(a);
  }
  return o;
}

function promote(opts) {
  const [id, label] = opts.positional;
  if (!id || !label) {
    console.error('usage: node tools/promote_version.mjs <structure_id> <label> [--keep-as <label>] [--dry-run] [--bake]');
    return 2;
  }
  const keep = opts.keepAs ?? `pre-${label}`;
  // A later replacement must relocate the canonical package as deliberately as
  // v4's incoming promotion. Never silently strand its reduced derivative.
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/manifest.json'), 'utf8'));
  if (Object.values(manifest.assets ?? {}).some(e => e.structure_id === id && e.web_lods)) {
    console.error('REFUSED: the current default has packaged detail assets; retarget its recovery and LOD contract before replacing it.');
    return 2;
  }
  const args = [PY, 'promote', id, label, '--keep-as', keep];
  if (opts.dryRun) args.push('--dry-run');
  const moved = run('python3', args);
  process.stdout.write(moved.out);
  if (moved.code !== 0) return moved.code;
  if (opts.dryRun) return 0;

  if (opts.compile) {
    const c = run('python3', ['tools/compile_scene.py', '--all']);
    process.stdout.write(c.out.split('\n').filter((l) => l.startsWith('scene ')).join('\n') + '\n');
    if (c.code !== 0) { console.error('compile_scene.py failed — the sidecars are stale'); return c.code; }
  }

  const st = run('python3', [PY, 'status', id]);
  process.stdout.write(st.out);
  if (st.code === 3) {
    if (!opts.bake) {
      console.log(`\nA mesh of ${id} needs Blender. Bake it with:\n  tools/bake.sh --only ${id}\n`
        + `or dispatch the chicago-4d-bake workflow with only=${id}, and land the GLBs in this PR.`);
      return 3;
    }
    const b = spawnSync('bash', ['tools/bake.sh', '--only', id], { cwd: ROOT, stdio: 'inherit' });
    if (b.status !== 0) return b.status ?? 1;
  } else if (st.code !== 0) {
    return st.code;
  }

  console.log(`\nPromoted: version '${label}' is now the default ${id}; the old default is version `
    + `'${keep}'.\nNext: ./tools/check.sh, a changelog entry (v: null, ts: ''), and one PR into dev.`
    + `\nCompare the two afterwards: ?structure=${id}&version=${keep}  vs  ?structure=${id}&version=default`);
  return 0;
}

/**
 * THE SELF-TEST: a sandbox tree with one structure, one version and fake meshes, promoted
 * for real through the same Python, then every claim checked — including that promoting
 * the kept default straight back restores the original record bytes.
 */
function selfTest() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'promote-'));
  const w = (rel, body) => {
    fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
    fs.writeFileSync(path.join(dir, rel), body);
  };
  const rd = (rel) => fs.readFileSync(path.join(dir, rel), 'utf8');
  const has = (rel) => fs.existsSync(path.join(dir, rel));
  const canonical = { id: 'house', name: 'A House', archetype: 'frame_dwelling',
    phases: [{ id: 'p1', position: { rotation_deg: 90.0 } }] };
  // Python writes 90.0; the literal below is what data/structures/ holds.
  const canonText = JSON.stringify(canonical, null, 2).replace('"rotation_deg": 90', '"rotation_deg": 90.0') + '\n';
  w('data/structures/house.json', canonText);
  const v2 = { ...canonical, name: 'A House, hall plan', version: { label: 'v2', summary: 'the hall plan' } };
  w('data/structures/versions/house/v2.json', JSON.stringify(v2, null, 2) + '\n');
  w('assets/gltf/house__p1.glb', 'OLD-MASTER');
  w('assets/web/house__p1.glb', 'OLD-WEB');
  w('assets/gltf/versions/house/v2/house__p1.glb', 'NEW-MASTER');
  w('assets/web/versions/house/v2/house__p1.glb', 'NEW-WEB');
  w('assets/manifest.json', JSON.stringify({ assets: { 'house__p1.glb': {
    structure_id: 'house', phase_id: 'p1', inputs_sha256: 'old' } } }, null, 2) + '\n');
  w('assets/manifest.web.json', JSON.stringify({ $note: 'n', masters: { 'house__p1.glb': 'oldweb' } }, null, 2) + '\n');
  w('assets/manifest.versions.json', JSON.stringify({ assets: { 'versions/house/v2/house__p1.glb': {
    structure_id: 'house', version_label: 'v2', phase_id: 'p1', inputs_sha256: 'new',
    web_master_sha256: 'newweb' } } }, null, 2) + '\n');

  const fails = [];
  const ok = (name, cond, detail = '') => {
    console.log(`   self-test | ${cond ? 'ok  ' : 'FAIL'} ${name}${cond || !detail ? '' : ` — ${detail}`}`);
    if (!cond) fails.push(name);
  };
  const py = (args) => run('python3', [PY, ...args, '--root', dir, '--today', '2026-01-01']);

  const refused = py(['promote', 'house', 'nope']);
  ok('a label with no version record is refused', refused.code !== 0 && /no version record/.test(refused.out), refused.out);
  const badKeep = py(['promote', 'house', 'v2', '--keep-as', 'Not_A_Label']);
  ok('a --keep-as that breaks the label rule is refused', badKeep.code !== 0 && /REFUSED/.test(badKeep.out), badKeep.out);
  ok('…and a refusal moved nothing', rd('assets/gltf/house__p1.glb') === 'OLD-MASTER' && has('data/structures/versions/house/v2.json'));

  const dry = py(['promote', 'house', 'v2', '--dry-run']);
  ok('--dry-run lists the moves and changes nothing', dry.code === 0 && /would move/.test(dry.out)
    && rd('assets/gltf/house__p1.glb') === 'OLD-MASTER', dry.out);

  const done = py(['promote', 'house', 'v2']);
  ok('the promotion runs', done.code === 0, done.out);
  const now = JSON.parse(rd('data/structures/house.json'));
  ok('the version is now the canonical record, without its version block',
    now.name === 'A House, hall plan' && !('version' in now));
  ok('the old default is kept as version pre-v2, labelled and summarised',
    has('data/structures/versions/house/pre-v2.json')
    && JSON.parse(rd('data/structures/versions/house/pre-v2.json')).version?.label === 'pre-v2'
    && JSON.parse(rd('data/structures/versions/house/pre-v2.json')).name === 'A House');
  ok('the promoted version file is gone', !has('data/structures/versions/house/v2.json'));
  ok('the meshes swapped places — master and derivative both',
    rd('assets/gltf/house__p1.glb') === 'NEW-MASTER' && rd('assets/web/house__p1.glb') === 'NEW-WEB'
    && rd('assets/gltf/versions/house/pre-v2/house__p1.glb') === 'OLD-MASTER'
    && rd('assets/web/versions/house/pre-v2/house__p1.glb') === 'OLD-WEB');
  ok('the emptied version mesh directories are removed',
    !has('assets/gltf/versions/house/v2') && !has('assets/web/versions/house/v2'));
  const m = JSON.parse(rd('assets/manifest.json')).assets['house__p1.glb'];
  const wm = JSON.parse(rd('assets/manifest.web.json')).masters['house__p1.glb'];
  const vm = JSON.parse(rd('assets/manifest.versions.json')).assets;
  ok('the build records moved with the meshes, hashes intact',
    m?.inputs_sha256 === 'new' && !('version_label' in m) && wm === 'newweb'
    && vm['versions/house/pre-v2/house__p1.glb']?.inputs_sha256 === 'old'
    && vm['versions/house/pre-v2/house__p1.glb']?.web_master_sha256 === 'oldweb'
    && !vm['versions/house/v2/house__p1.glb'], JSON.stringify({ m, wm, vm }));

  const back = py(['promote', 'house', 'pre-v2', '--keep-as', 'v2']);
  ok('promoting the kept default straight back works', back.code === 0, back.out);
  ok('…and restores the original canonical record byte for byte (90.0 stays 90.0)',
    rd('data/structures/house.json') === canonText, rd('data/structures/house.json').slice(0, 200));

  fs.rmSync(dir, { recursive: true, force: true });
  console.log(`   self-test | ${fails.length} failure(s)`);
  return fails.length ? 1 : 0;
}

const opts = parse(process.argv.slice(2));
process.exit(opts.selfTest ? selfTest() : promote(opts));
