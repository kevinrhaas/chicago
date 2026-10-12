// test_repo_file.mjs — repo_file.mjs reads a file the checkout lacks from the commit
// under test, in the checkout the bake workflow's smoke legs actually make (T-2331).
//
// That checkout is `fetch-depth: 1`, `filter: blob:none`, sparse on chicago/4d/tools/
// (.github/workflows/chicago-4d-bake.yml § smoke). It is rebuilt here from a scratch
// repository, and the blob is proved ABSENT before the read, so a pass means the
// on-demand fetch was taken — not that the file happened to be on disk.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { readRepoJson } from './repo_file.mjs';

let failed = 0;
const ok = (name, cond, detail = '') => {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? ` — ${detail}` : ''}`);
  if (!cond) failed += 1;
};
const git = (cwd, ...args) => execFileSync('git', ['-C', cwd, ...args],
  { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'repo-file-'));
try {
  const src = path.join(tmp, 'src');
  fs.mkdirSync(path.join(src, 'chicago/4d/tools'), { recursive: true });
  fs.mkdirSync(path.join(src, 'chicago/4d/data/traces'), { recursive: true });
  fs.writeFileSync(path.join(src, 'chicago/4d/tools/x.json'), '{"in":"tree"}\n');
  fs.writeFileSync(path.join(src, 'chicago/4d/data/traces/gcp.json'), '{"fit":{"a":1.5}}\n');
  git(tmp, 'init', '-q', src);
  git(src, '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '.');
  git(src, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'scratch');
  git(src, 'config', 'uploadpack.allowFilter', 'true');

  const leg = path.join(tmp, 'leg');
  git(tmp, 'clone', '-q', '--depth', '1', '--filter=blob:none', '--no-checkout',
    `file://${src}`, leg);
  git(leg, 'sparse-checkout', 'set', '--no-cone', '/chicago/4d/tools/');
  git(leg, 'checkout', '-q');
  const root4d = path.join(leg, 'chicago/4d');

  ok('the leg\'s checkout carries tools/ and not data/',
    fs.existsSync(path.join(root4d, 'tools/x.json'))
      && !fs.existsSync(path.join(root4d, 'data/traces/gcp.json')));
  const missing = git(leg, 'rev-list', '--objects', '--missing=print', 'HEAD')
    .split('\n').filter((l) => l.startsWith('?')).length;
  ok('the data blob is not in the clone before the read', missing >= 1,
    `${missing} blob(s) missing`);

  const fromTree = readRepoJson(root4d, 'tools/x.json');
  ok('a file in the checkout is read from the tree', fromTree.from === 'tree'
    && fromTree.value.in === 'tree', fromTree.from);

  const fromCommit = readRepoJson(root4d, 'data/traces/gcp.json');
  ok('a file outside the sparse set is read from the commit under test',
    fromCommit.from === 'commit' && fromCommit.value.fit.a === 1.5, fromCommit.from);

  let message = '';
  try { readRepoJson(root4d, 'data/not_committed.json'); } catch (err) { message = err.message; }
  ok('a file in neither refuses, naming the file', /data\/not_committed\.json/.test(message),
    message || 'no error raised');
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}

if (failed) {
  console.log(`test_repo_file: ${failed} FAILED`);
  process.exit(1);
}
console.log('test_repo_file: all passed');
