/**
 * One decoded copy of an image that several buildings carry — T-2464.
 *
 * Every Prairie Avenue house built on the K01/K16 kits embeds the kit's own
 * stone, brick, mortar and painted-wood maps in its GLB. GLTFLoader shares an
 * image only inside one file, so on 13 Oct 2026 dev's 1904 scene decoded 666 MB
 * of house images of which 92 MB were different pictures (limestone_basecolor,
 * a 2048² map, nineteen times over), and the GPU held each of them again with
 * mipmaps. On a phone profile 1904 peaked at 2.29 GB (0.89 GB on release-v1562,
 * before the houses), and an iPhone killed the tab: "Can't open this page".
 *
 * So the loader is taught to recognise an image it has already decoded. Before
 * a GLB's embedded image is decoded its bytes are digested; an image whose bytes
 * match one already decoded for this scene is handed a clone of that texture
 * instead. A clone shares the decoded image (`texture.source`), and three.js
 * uploads one GPU texture per source and sampler setup, so the picture is the
 * same bytes on every device and the memory is paid once. Only images packed in
 * the GLB (`bufferView`) are matched; a URI image takes GLTFLoader's own path.
 *
 * `disposeLoadedAsset` closes a texture's ImageBitmap when its asset is retired.
 * A shared bitmap is closed only when the last asset that took it is retired —
 * `releaseSharedImage` says whether the caller may close it.
 */

/** image -> { users: number of loaded assets holding it, forget(): drop it from its cache } */
const shared = new WeakMap();

async function digest(view) {
  const subtle = globalThis.crypto?.subtle;
  if (subtle) {
    const hash = new Uint8Array(await subtle.digest('SHA-256', view));
    let hex = '';
    for (const b of hash) hex += b.toString(16).padStart(2, '0');
    return hex;
  }
  // No SubtleCrypto (an insecure origin): two independent 32-bit FNV-1a lanes.
  const bytes = new Uint8Array(view.buffer ?? view, view.byteOffset ?? 0, view.byteLength);
  let a = 0x811c9dc5, b = 0x01000193 ^ bytes.length;
  for (let i = 0; i < bytes.length; i++) {
    a = Math.imul(a ^ bytes[i], 0x01000193);
    b = Math.imul(b ^ bytes[bytes.length - 1 - i], 0x5bd1e995);
  }
  return `${(a >>> 0).toString(16)}${(b >>> 0).toString(16)}`;
}

/** Built out here so the entry's closure does not hold the parser that decoded it. */
function entryFor(byKey, key) {
  return { users: 0, forget: () => byKey.delete(key) };
}

/**
 * Teach `loader` (a GLTFLoader) to decode each distinct embedded image once for
 * every file it parses. Returns `{ stats }`, which counts images decoded and
 * images shared, for the tools that measure it.
 */
export function shareImageSources(loader) {
  const byKey = new Map();
  const stats = { decoded: 0, shared: 0 };
  loader.register((parser) => {
    const own = parser.loadImageSource.bind(parser);
    const held = new Set();
    parser.loadImageSource = function loadSharedImageSource(sourceIndex, imageLoader) {
      const def = parser.json.images?.[sourceIndex];
      if (!def || def.bufferView === undefined || parser.sourceCache[sourceIndex] !== undefined) {
        return own(sourceIndex, imageLoader);
      }
      const promise = parser.getDependency('bufferView', def.bufferView).then(async (view) => {
        const key = `${def.mimeType ?? ''}|${view.byteLength}|${await digest(view)}`;
        let original = byKey.get(key);
        if (original) {
          stats.shared++;
        } else {
          stats.decoded++;
          // The original is never handed out: every user, the first included,
          // gets a clone, so no user's sampler or colour space reaches another.
          // GLTFLoader's own path answers from `sourceCache` when it holds this
          // index, and it holds this very promise, so it is cleared first.
          delete parser.sourceCache[sourceIndex];
          original = own(sourceIndex, imageLoader).then((texture) => {
            shared.set(texture.image, entryFor(byKey, key));
            return texture;
          });
          byKey.set(key, original);
          original.catch(() => byKey.delete(key));
        }
        const texture = await original;
        const entry = shared.get(texture.image);
        if (entry && !held.has(texture.image)) { held.add(texture.image); entry.users++; }
        return texture.clone();
      });
      parser.sourceCache[sourceIndex] = promise;
      return promise;
    };
    return { name: 'chicago_shared_image_sources' };
  });
  return { stats };
}

/**
 * One loaded asset is letting go of `image`. True when nothing else holds it,
 * so the caller may close it; false while another asset still draws with it.
 */
export function releaseSharedImage(image) {
  const entry = shared.get(image);
  if (!entry) return true;
  entry.users = Math.max(0, entry.users - 1);
  if (entry.users > 0) return false;
  entry.forget();
  shared.delete(image);
  return true;
}
