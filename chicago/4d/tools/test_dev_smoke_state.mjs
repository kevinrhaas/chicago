#!/usr/bin/env node
// Exercise the actual CLI in an isolated repository, including its ignored mirror.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

if (process.argv.length !== 3 || process.argv[2] !== '--self-test') {
  console.error('usage: test_dev_smoke_state.mjs --self-test');
  process.exit(2);
}

const here = path.dirname(fileURLToPath(import.meta.url));
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'c4d-smoke-hash-'));
const tool = 'chicago/4d/tools/dev-smoke-state.mjs';
const page = 'site/4d/walk/index.html';
const notes = 'chicago/4d/renderers/web/js/changelog.js';
const meta = '<meta name="c4d-releases" content="1-3">';
const html = `${meta}<p>build abcdef0 · initial</p><main>town</main>`;
const write = (name, value) => {
  const target = path.join(root, name);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, value);
};
const git = (...args) => execFileSync('git', args, { cwd: root, stdio: 'pipe' });
const read = () => JSON.parse(execFileSync(process.execPath, [tool, 'hash', '--json'],
  { cwd: root, encoding: 'utf8' }));
let checks = 0;
const check = (label, fn) => { fn(); checks++; console.log(`PASS ${label}`); };

try {
  write(tool, fs.readFileSync(path.join(here, 'dev-smoke-state.mjs')));
  write('.gitignore', '/site/\n');
  write(notes, 'export const CHANGELOG = [{v: 3}];\n');
  const inputs = {
    'chicago/4d/renderers/web/js/town.js': 'export const town = 1;\n',
    'chicago/4d/data/town.json': '{"town":1}\n',
    'chicago/4d/assets/town.glb': 'fixture asset bytes',
    'chicago/4d/tools/smoke_renderer.mjs': '// fixture probe\n',
  };
  for (const [name, body] of Object.entries(inputs)) write(name, body);
  write(page, html);
  git('init', '-q');
  git('add', '.');
  git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
    'commit', '-q', '-m', 'fixture');
  const base = read();
  check('clean fixture has two hashes', () => {
    assert.match(base.hash, /^sha256:[0-9a-f]{16}$/);
    assert.match(base.changelogHash, /^sha256:[0-9a-f]{16}$/);
    assert.equal(base.dirty, false);
  });
  write(page, html.replace('abcdef0 · initial', '1234567 · later'));
  check('build stamp changes neither partition', () => assert.deepEqual(read(), base));
  for (const value of ['1-4', 'wrong', '3-1', '']) {
    write(page, html.replace('content="1-3"', `content="${value}"`));
    check(`actual release value ${JSON.stringify(value)} changes only notes`, () => {
      const got = read();
      assert.equal(got.hash, base.hash);
      assert.notEqual(got.changelogHash, base.changelogHash);
      assert.equal(got.dirty, false);
    });
  }
  const structural = {
    missing: html.replace(meta, ''),
    duplicate: meta + html,
    renamed: html.replace('name="c4d-releases"', 'name="other"'),
    attributes: html.replace(meta, '<meta name="c4d-releases" data-extra="1" content="1-3">'),
    html: html.replace('<main>town</main>', '<main>different town</main>'),
  };
  for (const [label, body] of Object.entries(structural)) {
    write(page, body);
    check(`${label} page change invalidates global input hash`, () => {
      const got = read();
      assert.notEqual(got.hash, base.hash);
      if (label !== 'html') assert.notEqual(got.changelogHash, base.changelogHash);
    });
  }
  write(page, html);
  write(notes, 'export const CHANGELOG = [{v: 4}];\n');
  git('add', notes);
  check('canonical notes change only their partition', () => {
    const got = read();
    assert.equal(got.hash, base.hash);
    assert.notEqual(got.changelogHash, base.changelogHash);
  });
  git('reset', '-q', 'HEAD', '--', notes);
  git('checkout', '--', notes);
  for (const [name, body] of Object.entries(inputs)) {
    write(name, body + '\nchanged\n');
    check(`unstaged ${name} cannot license reuse`, () => assert.equal(read().dirty, true));
    git('add', name);
    check(`staged ${name} changes global hash`, () => assert.notEqual(read().hash, base.hash));
    git('reset', '-q', 'HEAD', '--', name);
    git('checkout', '--', name);
  }
  check('restored fixture returns to exact original hashes', () => assert.deepEqual(read(), base));
  console.log(`${checks} smoke-input partition checks passed`);
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
