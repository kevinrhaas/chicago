#!/usr/bin/env node
// T-2629 (NAV-305): Settings › About — the build stamp, and the DEV mark on a dev build
// only (js/about.js); the dev chrome's phone rule (walk.css) is the smoke's, part 13.
import assert from 'node:assert/strict';
import { isDevBuild, buildStamp, paintAbout } from '../renderers/web/js/about.js';

function page({ stamp = '', pill = false, banner = false } = {}) {
  const nodes = new Map();
  const node = (id, extra = {}) => { const n = { id, hidden: true, textContent: '', ...extra }; nodes.set(id, n); return n; };
  node('s-about-build'); node('s-about-dev'); node('s-about-dev-note');
  node('gate-build', { textContent: stamp });
  if (pill) node('__devpill');
  if (banner) node('__dev');
  return { getElementById: (id) => nodes.get(id) ?? null, nodes };
}
const prod = { pathname: '/4d/walk/' }, devPath = { pathname: '/4d/dev/walk/' };

const p = page({ stamp: 'build 7e0a4b1 · Oct 18, 2026, 3:53 AM CT' });
assert.equal(isDevBuild(p, prod), false, 'production is not a dev build');
assert.deepEqual(paintAbout({ doc: p, loc: prod }), { dev: false, build: 'build 7e0a4b1 · Oct 18, 2026, 3:53 AM CT' });
assert.equal(p.nodes.get('s-about-dev').hidden, true, 'no DEV mark on production');
assert.equal(p.nodes.get('s-about-dev-note').hidden, true);

const d = page({ stamp: 'DEV PREVIEW · dev@7e0a4b1 · Oct 18, 2026, 3:53 AM CT', pill: true });
assert.equal(paintAbout({ doc: d, loc: devPath }).dev, true, 'the preview pill makes it a dev build');
assert.equal(d.nodes.get('s-about-dev').hidden, false, 'the DEV mark shows');
assert.equal(d.nodes.get('s-about-dev-note').hidden, false, 'with its note');
assert.equal(d.nodes.get('s-about-build').textContent, 'DEV PREVIEW · dev@7e0a4b1 · Oct 18, 2026, 3:53 AM CT');
assert.equal(isDevBuild(page({ banner: true }), prod), true, 'the banner alone says dev too');
assert.equal(isDevBuild(page(), devPath), true, 'and so does the /4d/dev/ path');

assert.equal(buildStamp(page(), '0.1.0'), 'build 0.1.0', 'before publish the stamp is the version');
assert.ok(buildStamp(page()).length > 0, 'and never empty');
assert.equal(paintAbout({ doc: { getElementById: () => null }, loc: prod }), null, 'no About row, nothing painted');

console.log('ABOUT PASS — the build stamp in Settings › About, the DEV mark on a dev build only');
