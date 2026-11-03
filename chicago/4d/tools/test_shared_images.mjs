#!/usr/bin/env node
// T-2464: identical embedded images are decoded once per scene and shared, and a shared
// bitmap is closed only by the last asset that holds it. Drives renderers/web/js/
// shared-images.js against a stand-in for GLTFLoader's parser (no WebGL, no three.js
// beyond what the module itself touches), so it runs in the gate in well under a second.
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const { shareImageSources, releaseSharedImage, glbImageSource } = await import(
  pathToFileURL(path.join(ROOT, 'renderers/web/js/shared-images.js')).href);

let failures = 0;
function check(label, ok, detail) {
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${label}${ok || detail === undefined ? '' : ` — ${detail}`}`);
  if (!ok) failures++;
}

// A texture with what the module reads: `image`, and `clone()` sharing it — and, as
// three's Texture does, a `source` every clone shares (T-2598 keys on it).
let decodes = 0;
class FakeTexture {
  constructor(image, source = { data: image }) { this.image = image; this.source = source; }
  clone() { return new FakeTexture(this.image, this.source); }
}
// GLTFParser's image path, reduced: the bytes of a bufferView become one decoded image
// per call, and a source already in `sourceCache` is answered from it.
class FakeParser {
  constructor(views) {
    this.json = { images: views.map((_, i) => ({ bufferView: i, mimeType: 'image/png' })) };
    this.views = views.map((s) => new TextEncoder().encode(s).buffer);
    this.sourceCache = {};
  }
  getDependency(kind, i) { return Promise.resolve(this.views[i]); }
  loadImageSource(i) {
    if (this.sourceCache[i] !== undefined) return this.sourceCache[i].then((t) => t.clone());
    const p = this.getDependency('bufferView', this.json.images[i].bufferView).then(() => {
      decodes++;
      return new FakeTexture({ id: `bitmap-${decodes}`, closed: false });
    });
    this.sourceCache[i] = p;
    return p;
  }
}
class FakeLoader {
  constructor() { this.plugins = []; }
  register(cb) { this.plugins.push(cb); return this; }
  parser(views) { const p = new FakeParser(views); for (const cb of this.plugins) cb(p); return p; }
}

const loader = new FakeLoader();
const { stats } = shareImageSources(loader);
const houseA = loader.parser(['limestone', 'brick']);
const houseB = loader.parser(['limestone', 'oak', 'limestone']);
const a0 = await houseA.loadImageSource(0);
const a1 = await houseA.loadImageSource(1);
const b0 = await houseB.loadImageSource(0);
const b1 = await houseB.loadImageSource(1);
const b2 = await houseB.loadImageSource(2);
const again = await houseB.loadImageSource(0);

check('two houses carrying the same picture decode it once', decodes === 3, `${decodes} decodes`);
check('…and both hold the very same decoded image', a0.image === b0.image && b2.image === a0.image);
check('…each through its own texture, never the original', a0 !== b0 && a0 !== b2 && again !== b0);
check('different pictures stay different', a1.image !== a0.image && b1.image !== a0.image);
check('the counts say so', stats.decoded === 3 && stats.shared === 2, JSON.stringify(stats));

check('retiring house A keeps the bitmap house B still draws with', releaseSharedImage(a0.image) === false);
check('…retiring house B lets the last holder close it', releaseSharedImage(b0.image) === true);
const houseC = loader.parser(['limestone']);
await houseC.loadImageSource(0);
check('a picture whose bitmap was closed is decoded afresh, not shared closed', decodes === 4, `${decodes} decodes`);
check('an image the module never shared may always be closed', releaseSharedImage({}) === true);

// Two different pictures of equal length are NOT the same picture: the match is on bytes.
{
  const before = decodes;
  const l2 = new FakeLoader(); shareImageSources(l2);
  const x = await l2.parser(['granite1']).loadImageSource(0);
  const y = await l2.parser(['granite2']).loadImageSource(0);
  check('same length, different bytes: two decodes', decodes === before + 2 && x.image !== y.image);
}

// T-2598: texture residency learns from the module which pictures a GLB brought in, and
// on a phone (keepEncoded) the bytes to decode one again after its bitmap was closed.
{
  check('a GLB picture is recorded against the source its clones share',
    glbImageSource(a0.source) !== null && glbImageSource(b0.source) === glbImageSource(a0.source));
  check('…without its bytes by default', glbImageSource(a0.source).encoded === null);
  check('a texture the module never saw has no record', glbImageSource({}) === null);
  const lk = new FakeLoader(); shareImageSources(lk, { keepEncoded: true });
  const k = await lk.parser(['marble']).loadImageSource(0);
  const rec = glbImageSource(k.source)?.encoded;
  check('keepEncoded keeps the bytes and their mime type to decode from again',
    rec && rec.view.byteLength === 'marble'.length && rec.mimeType === 'image/png');
  const lt = new FakeLoader(); shareImageSources(lt);
  // A parser whose own path yields a texture with no `source`, wrapped by the plugin.
  const p2 = new FakeParser(['sourceless']);
  const raw = p2.loadImageSource.bind(p2);
  p2.loadImageSource = (i, il) => raw(i, il).then((t) => { t.source = undefined; return t; });
  for (const cb of lt.plugins) cb(p2);
  let threw = null;
  try { await p2.loadImageSource(0); } catch (e) { threw = e; }
  check('a texture with no source is shared, not a TypeError', threw === null, String(threw));
}

// The same embedded-image owner also holds light mip policy and uploaded-level recovery.
await import('./test_texture_residency.mjs');

console.log(`${failures} failure(s)`);
process.exit(failures ? 1 : 0);
