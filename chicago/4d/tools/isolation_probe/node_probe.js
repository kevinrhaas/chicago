/**
 * Injected into every node gate step via NODE_OPTIONS=--require, to record what it
 * WRITES. The node counterpart of sitecustomize.py; node has no audit-hook API, so
 * the fs write entry points are wrapped instead.
 *
 * THE ARGUMENT POSITION IS THE WHOLE CARE HERE. A first pass at this wrapped
 * copyFileSync and recorded argument 0 — which is the SOURCE — and duly reported
 * resolve_id_collisions.mjs as writing tools/ticket.mjs when what it actually does
 * is copy that tool OUT of the repo into a tmpdir fixture. A probe that cannot tell
 * a read from a write manufactures findings, so each call below names which of its
 * arguments is the thing being written.
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.env.ISOLATION_ROOT;
const OUT = process.env.ISOLATION_OUT;
if (ROOT && OUT) {
  const root = fs.realpathSync(ROOT);
  const hits = new Set();
  // Captured BEFORE the wrapping below, so the probe's own report cannot be seen
  // by the probe — a measurement that records itself is not a measurement.
  const rawAppend = fs.appendFileSync.bind(fs);

  const note = (p) => {
    if (p === undefined || p === null || typeof p === 'number') return;
    let abs;
    try { abs = path.resolve(String(p instanceof URL ? p.pathname : p)); } catch { return; }
    // realpath the DIRECTORY, because the file itself may not exist yet.
    try { abs = path.join(fs.realpathSync(path.dirname(abs)), path.basename(abs)); } catch {}
    if (!abs.startsWith(root + path.sep)) return;      // a tempdir, and correct
    const rel = path.relative(root, abs);
    if (rel.split(path.sep)[0] === '.git') return;
    hits.add(rel);
  };

  // name -> index of the argument that is WRITTEN (dest), and whether a mode gate applies
  const TARGETS = {
    writeFile: 0, writeFileSync: 0, appendFile: 0, appendFileSync: 0,
    createWriteStream: 0, truncate: 0, truncateSync: 0,
    rm: 0, rmSync: 0, unlink: 0, unlinkSync: 0, mkdir: 0, mkdirSync: 0,
    rmdir: 0, rmdirSync: 0, utimes: 0, utimesSync: 0, chmod: 0, chmodSync: 0,
    rename: 1, renameSync: 1,          // dest; the source is removed too, noted below
    copyFile: 1, copyFileSync: 1,
    cp: 1, cpSync: 1,
    symlink: 1, symlinkSync: 1, link: 1, linkSync: 1,
  };
  const MODE_GATED = { open: 0, openSync: 0 };

  const wrap = (obj, name, idx, modeGated) => {
    const orig = obj[name];
    if (typeof orig !== 'function') return;
    obj[name] = function (...args) {
      if (modeGated) {
        const flags = args[1];
        if (flags === undefined || /[wax+]/.test(String(flags))) note(args[0]);
      } else {
        note(args[idx]);
        if (name === 'rename' || name === 'renameSync') note(args[0]);  // source vanishes
      }
      return orig.apply(this, args);
    };
  };

  for (const [n, i] of Object.entries(TARGETS)) { wrap(fs, n, i, false); if (fs.promises) wrap(fs.promises, n, i, false); }
  for (const [n, i] of Object.entries(MODE_GATED)) { wrap(fs, n, i, true); if (fs.promises) wrap(fs.promises, n, i, true); }

  // A row is written even when nothing was — see sitecustomize.py; "measured and
  // clean" and "never ran" must not look the same to the coverage gate.
  process.on('exit', () => {
    try {
      rawAppend(OUT, JSON.stringify({ argv: process.argv.slice(1), wrote: [...hits].sort() }) + '\n');
    } catch {}
  });
}
