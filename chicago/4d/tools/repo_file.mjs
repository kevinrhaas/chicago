// repo_file.mjs — read a SOURCE file of chicago/4d, from the working tree when it
// is there and from the commit under test when it is not (T-2331).
//
// The smoke's oracles are source records (a GCP fit, a lot frame, a structure
// record), deliberately never the mirror under test. The bake workflow's smoke legs
// check out `chicago/4d/tools/` alone — sparse, `filter: blob:none`, at the baked
// commit — so a plain readFileSync on `data/…` ends the part ENOENT there while a
// full clone never notices. On a file the tree does not carry this asks git for the
// committed blob of HEAD, which a blob-less partial clone fetches on demand. It is
// the same bytes the bake published from; nothing here reads the mirror.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

// `from` is 'tree' or 'commit', so a caller can say which one it stood on.
export function readRepoFile(root4d, rel) {
  const file = path.join(root4d, rel);
  if (fs.existsSync(file)) return { text: fs.readFileSync(file, 'utf8'), from: 'tree' };
  let text;
  try {
    text = execFileSync('git', ['-C', root4d, 'show', `HEAD:./${rel}`],
      { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (err) {
    const why = String(err.stderr || err.message).trim().split('\n')[0];
    throw new Error(`${rel} is neither in this checkout nor readable from HEAD (${why})`);
  }
  return { text, from: 'commit' };
}

export function readRepoJson(root4d, rel) {
  const { text, from } = readRepoFile(root4d, rel);
  return { value: JSON.parse(text), from };
}
