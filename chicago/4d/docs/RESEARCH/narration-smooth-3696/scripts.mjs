// SPDX-License-Identifier: GPL-3.0-or-later
// T-3696: print the voiced scripts of the named jaunts (narration.js narrationScripts on the compiled jaunt) as JSON, for smooth.py.
import fs from 'node:fs'; import path from 'node:path';
const R = new URL('../../..', import.meta.url).pathname.replace(/\/$/, '');
const { narrationScripts } = await import(R + '/renderers/web/js/narration.js');
const out = {};
for (const id of process.argv.slice(2)) {
  const src = JSON.parse(fs.readFileSync(path.join(R, 'data/jaunts', id + '.json'), 'utf8'));
  const j = JSON.parse(fs.readFileSync(path.join(R, 'data/sidecars', src.scene, 'jaunts', id + '.json'), 'utf8'));
  out[id] = narrationScripts(j).map(s => ({ key: `${s.part}:${s.id}`, speaker: s.speaker, text: s.text }));
}
console.log(JSON.stringify(out));
