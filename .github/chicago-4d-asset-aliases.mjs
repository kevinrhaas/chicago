// MAIN publication assembly only. No production APP code or logical asset IDs change.
import { readdir, lstat, readFile, writeFile, mkdir, rename, rm, mkdtemp, realpath } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

export const CAPABILITY = 'c4d-published-assets/1';
export const PAGE_BYTES_LIMIT = 1_000_000_000;
export const PREBUILT = new Set(['ground', 'frontage', 'streets.full', 'streets.light', 'base']
  .map(name => `data/prebuilt/1835/${name}.bin.gz`));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const need = (condition, why) => { if (!condition) throw Error(`DEV asset publication: ${why}`); };
const clean = rel => typeof rel === 'string' && /^[A-Za-z0-9_./-]+$/.test(rel)
  && !rel.startsWith('/') && !rel.includes('..') && rel.split('/').every(p => p && p !== '.' && p !== '..');
export const eligiblePath = rel => clean(rel) && (/^data\/gltf\/.+\.(glb|ktx2)$/.test(rel) || PREBUILT.has(rel));
export const aliasIdInput = aliases => JSON.stringify(Object.keys(aliases).sort()
  .map(rel => [rel, aliases[rel].source, aliases[rel].sha256, aliases[rel].bytes]));

async function digest(file) {
  const h = createHash('sha256');
  for await (const bytes of createReadStream(file)) h.update(bytes);
  return h.digest('hex');
}
export async function inventory(root, exclude = null) {
  const files = new Map();
  async function walk(dir, prefix = '') {
    for (const name of (await readdir(dir)).sort()) {
      const rel = prefix ? `${prefix}/${name}` : name;
      if (exclude?.(rel)) continue;
      const file = path.join(dir, name), stat = await lstat(file);
      need(!stat.isSymbolicLink(), `symbolic link in publication: ${rel}`);
      if (stat.isDirectory()) await walk(file, rel);
      else { need(stat.isFile() && stat.nlink === 1, `non-regular or hard-linked publication file: ${rel}`); files.set(rel, stat.size); }
    }
  }
  await walk(root); return files;
}
export function sizeReport(files) {
  const partitions = { production4d: { files: 0, bytes: 0 }, dev4d: { files: 0, bytes: 0 }, other: { files: 0, bytes: 0 } };
  let regularFileBytes = 0;
  for (const [rel, bytes] of files) {
    regularFileBytes += bytes;
    const p = partitions[rel.startsWith('4d/dev/') ? 'dev4d' : rel.startsWith('4d/') ? 'production4d' : 'other']; p.files++; p.bytes += bytes;
  }
  return { regularFiles: files.size, regularFileBytes, limitBytes: PAGE_BYTES_LIMIT,
    reserveBytes: PAGE_BYTES_LIMIT-regularFileBytes, partitions };
}
export async function assertSiteBudget(site) {
  const report = sizeReport(await inventory(site));
  need(report.regularFileBytes <= PAGE_BYTES_LIMIT,
    `all site regular files total ${report.regularFileBytes}B > ${PAGE_BYTES_LIMIT}B; copies retained when support is unavailable`);
  return report;
}
function glbDocument(bytes) {
  need(bytes.length >= 20 && bytes.readUInt32LE(0) === 0x46546c67 && bytes.readUInt32LE(4) === 2
    && bytes.readUInt32LE(8) === bytes.length && bytes.readUInt32LE(16) === 0x4e4f534a, 'invalid GLB container');
  const n = bytes.readUInt32LE(12); need(n <= bytes.length-20, 'invalid GLB JSON length');
  const doc = JSON.parse(bytes.subarray(20, 20+n)); need(doc.asset?.version === '2.0', 'unsupported glTF version'); return doc;
}
/** The native parser retains the LOGICAL GLB base. Dependencies stay logical DEV
 * files or separately validated aliases. Only native-qualified complete KTX2 image
 * buffers may be external; geometry buffers stay excluded. */
export function safeGlbClosure(bytes, logical, devFiles, capability) {
  const doc = glbDocument(bytes), dependencies = [];
  const external = new Set(), imageViews = new Set(), imageObjects = new Set(doc.images ?? []);
  for (const [index, buffer] of (doc.buffers ?? []).entries()) {
    if (!buffer.uri || buffer.uri.startsWith('data:')) continue;
    if (capability.textureBufferAliases !== true || !capability.ktx2Aliases
      || !/^sheets\/[a-f0-9]{16}\.ktx2$/.test(buffer.uri)) return { safe: false, why: 'external buffer unsupported' };
    const rel = path.posix.join(path.posix.dirname(logical),buffer.uri);
    if (!/^data\/gltf\/sheets\/[a-f0-9]{16}\.ktx2$/.test(rel) || !Number.isSafeInteger(buffer.byteLength) || buffer.byteLength <= 0 || devFiles.get(rel) !== buffer.byteLength)
      return { safe: false, why: 'texture buffer size or logical dependency differs' };
    const views = (doc.bufferViews ?? []).map((view,i)=>({view,i})).filter(({view})=>view.buffer===index);
    if (!views.length || views.some(({view,i})=> (view.byteOffset ?? 0)!==0 || view.byteLength!==buffer.byteLength
      || view.byteStride !== undefined || view.target !== undefined || view.extensions !== undefined
      || !(doc.images ?? []).some(image=>image.bufferView===i)
      || (doc.images ?? []).some(image=>image.bufferView===i && image.mimeType!=='image/ktx2')))
      return { safe: false, why: 'external texture buffer must contain complete image views only' };
    external.add(index); for (const {i} of views) imageViews.add(i); dependencies.push(rel);
  }
  let nonImageUse = false;
  const inspect = value => {
    if (!value || typeof value !== 'object') return;
    for (const [key,child] of Object.entries(value)) {
      if (key==='bufferView' && imageViews.has(child) && !imageObjects.has(value)) nonImageUse=true;
      if (key==='buffer' && external.has(child) && !(doc.bufferViews ?? []).some(view=>view===value && imageViews.has(doc.bufferViews.indexOf(view)))) nonImageUse=true;
      inspect(child);
    }
  };
  inspect(doc);
  if (nonImageUse) return { safe:false, why:'external texture buffer used outside images' };

  const imageURIs = new Set((doc.images ?? []).map(x => x.uri).filter(Boolean));
  const sheetURIs = new Set([...external].map(i=>doc.buffers[i].uri));
  const allURIs = [];
  const visit = value => { if (!value || typeof value !== 'object') return;
    for (const [key, child] of Object.entries(value)) { if (key === 'uri' && typeof child === 'string') allURIs.push({owner:value,uri:child}); else visit(child); } };
  visit(doc);
  for (const {owner,uri} of allURIs) {
    if (uri.startsWith('data:')) continue;
    if (sheetURIs.has(uri) && external.has((doc.buffers ?? []).indexOf(owner))) continue;
    if (!imageObjects.has(owner) || !imageURIs.has(uri) || !capability.logicalGltfResources || /[\\%?#\x00-\x20]/.test(uri)
      || uri.startsWith('/') || /^[a-z][a-z0-9+.-]*:/i.test(uri)) return { safe: false, why: 'unsupported resource URI' };
    const url = new URL(uri, `https://publication.invalid/4d/dev/${logical}`);
    if (!url.pathname.startsWith('/4d/dev/') || url.search || url.hash) return { safe: false, why: 'resource escapes DEV app' };
    const rel = url.pathname.slice('/4d/dev/'.length);
    if (!clean(rel) || !devFiles.has(rel) || !/\.(ktx2|png|jpe?g|webp)$/i.test(rel)) return { safe: false, why: 'missing or unsupported image' };
    if (rel.endsWith('.ktx2') && !capability.ktx2Aliases) return { safe: false, why: 'KTX2 consumer unavailable' };
    dependencies.push(rel);
  }
  return { safe: true, dependencies };
}

/** Verify code against the requested immutable DEV commit before executing its
 * readonly capability flag. Old code without the marker is never invoked. */
export async function nativeCapability(devWorktree, requestedSha, devSite) {
  const unsupported = why => ({ supported: false, why });
  try {
    const git = args => execFileSync('git', args, { cwd: devWorktree, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
    const commit = git(['rev-parse', 'HEAD']).trim();
    if (!/^[a-f0-9]{7,40}$/.test(requestedSha) || !commit.startsWith(requestedSha)) return unsupported('DEV commit does not match requested pin');
    const cliRel = 'chicago/4d/tools/write_year_packs.mjs', cli = path.join(devWorktree, cliRel);
    const expected = git(['show', `${commit}:${cliRel}`]);
    if (!expected.includes(`export const ASSET_ALIAS_CAPABILITY = '${CAPABILITY}';`)) return unsupported('DEV has no native publication-alias capability');
    const pinned = new Set();
    async function verifyModule(rel) {
      if (pinned.has(rel)) return; need(clean(rel), 'unsafe native module path'); pinned.add(rel);
      const actual = await readFile(path.join(devWorktree, rel));
      need(sha(actual) === sha(Buffer.from(git(['show', `${commit}:${rel}`]))), `dirty native module: ${rel}`);
      for (const m of actual.toString().matchAll(/^\s*(?:import|export)[^;]*?from\s*['"]([^'"]+)['"]/gm)) {
        if (m[1].startsWith('.')) await verifyModule(path.posix.normalize(path.posix.join(path.posix.dirname(rel), m[1])));
      }
    }
    await verifyModule(cliRel);
    const c = JSON.parse(execFileSync(process.execPath, [cli, '--asset-alias-capability'], { encoding: 'utf8', timeout: 15000 }));
    need(c.capability === CAPABILITY && c.schema === 1 && c.catalogue === 'c4d-published-assets'
      && c.meta === 'c4d-asset-aliases' && c.logicalPackSources === true && c.logicalGltfResources === true && c.ktx2Aliases === true
      && Array.isArray(c.consumers) && c.consumers.length >= 10, 'unsupported native capability contract');
    need(JSON.stringify(c.supportedPaths) === JSON.stringify(['data/gltf/**/*.glb','data/gltf/**/*.ktx2','data/prebuilt/YYYY/*.bin.gz']), 'unsupported path capability');
    need(c.consumers.some(x => x.source === 'offline/sw.js' && x.published === 'sw.js' && x.transform === 'native-swText')
      && c.consumers.some(x => x.source === 'tools/write_year_packs.mjs' && x.published === null && x.transform === 'source-only'), 'missing owning worker/pack consumers');
    const required = ['published-assets.js','scene-loader.js','terrain.js','ktx2.js','frontage.js','streets.js','yards.js','year-pack.js'];
    for (const name of required) need(c.consumers.some(x => x.source === `renderers/web/js/${name}` && x.published === `walk/js/${name}` && x.transform === 'copy'), `missing consumer ${name}`);
    for (const item of c.consumers) {
      need(clean(item.source), 'unsafe consumer source'); const rel = `chicago/4d/${item.source}`; await verifyModule(rel);
      if (item.transform === 'copy') {
        need(clean(item.published), 'unsafe published consumer');
        need(sha(await readFile(path.join(devSite, item.published))) === sha(await readFile(path.join(devWorktree, rel))), `stale published consumer ${item.published}`);
      } else need(['native-swText','source-only'].includes(item.transform), 'unknown native consumer transform');
    }
    return { ...c, supported: true, commit, cli, pinnedModules: [...pinned].sort() };
  } catch (error) { return unsupported(error.message); }
}

async function productionFingerprint(root) {
  const rows = [];
  for (const [rel, bytes] of await inventory(root, rel => rel === 'dev' || rel.startsWith('dev/'))) rows.push([rel, bytes, await digest(path.join(root, rel))]);
  return sha(JSON.stringify(rows));
}
export async function planAliases(productionRoot, devRoot, capability) {
  const prod = await inventory(productionRoot, rel => rel === 'dev' || rel.startsWith('dev/')), dev = await inventory(devRoot);
  const aliases = Object.create(null), kept = []; let savedBytes = 0;
  for (const [rel, bytes] of dev) {
    if (!eligiblePath(rel)) continue;
    if (PREBUILT.has(rel) && !capability.prebuiltAliases) { kept.push({ rel, why: 'prebuilt consumer unavailable' }); continue; }
    if (prod.get(rel) !== bytes) { kept.push({ rel, why: 'production missing or byte count differs' }); continue; }
    const hash = await digest(path.join(devRoot, rel));
    if (hash !== await digest(path.join(productionRoot, rel))) { kept.push({ rel, why: 'production bytes differ' }); continue; }
    if (rel.endsWith('.glb')) {
      let closure;
      try { closure = safeGlbClosure(await readFile(path.join(devRoot, rel)), rel, dev, capability); }
      catch (error) { closure = { safe: false, why: error.message }; }
      if (!closure.safe) { kept.push({ rel, why: closure.why }); continue; }
    }
    aliases[rel] = { source: `/4d/${rel}`, sha256: hash, bytes }; savedBytes += bytes;
  }
  const id = sha(aliasIdInput(aliases));
  return { catalogue: { schema: 1, scope: '/4d/dev/', productionScope: '/4d/', id, aliases },
    savedBytes, kept, matchingFiles: Object.keys(aliases).length };
}
const metaPattern = /<meta\s+name=["']c4d-asset-aliases["'][^>]*>\s*/gi;
export function withAliasPointer(html, tag) {
  html = html.replace(metaPattern, '');
  // HTML permits omitted head tags. Before its first metadata/body token the
  // parser creates an implicit head; do not require source pages to spell it.
  for (const start of [/<head\b[^>]*>/i, /<html\b[^>]*>/i, /<!doctype\b[^>]*>/i])
    if (start.test(html)) return html.replace(start, match => match+'\n'+tag);
  return tag+'\n'+html;
}

const isMetadata = rel => rel.endsWith('.html') || rel.startsWith('packs/') || rel === 'sw.js' || rel === 'build.json' || /(^|\/)app\.webmanifest$/.test(rel);
async function metadataSnapshot(devRoot) {
  const snapshot = new Map();
  for (const [rel] of await inventory(devRoot)) if (isMetadata(rel)) snapshot.set(rel, await readFile(path.join(devRoot, rel)));
  return snapshot;
}
/** Low-level producer API; the assembler supplies only nativeCapability's verified
 * adapter. Fixtures can exercise ownership and real owning-pack integration. */
export async function publishAliases({ siteRoot, productionRoot, devRoot, capability, writePacks }) {
  siteRoot = await realpath(siteRoot); productionRoot = await realpath(productionRoot); devRoot = await realpath(devRoot);
  need(productionRoot === path.join(siteRoot, '4d') && devRoot === path.join(productionRoot, 'dev'), 'publication ownership must be site/4d and its dev child');
  if (!capability?.supported) return { status: 'identity-unsupported', why: capability?.why ?? 'no capability', removed: 0, ...(await assertSiteBudget(siteRoot)) };
  need(capability.capability === CAPABILITY && capability.logicalPackSources && capability.logicalGltfResources && typeof writePacks === 'function', 'verified native adapter required');
  const productionBefore = await productionFingerprint(productionRoot), plan = await planAliases(productionRoot, devRoot, capability);
  const snapshot = await metadataSnapshot(devRoot), filename = `asset-aliases.${plan.catalogue.id}.json`;
  let priorCatalogue = null;
  try { priorCatalogue = await readFile(path.join(devRoot, filename)); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const stage = await mkdtemp(path.join(path.dirname(siteRoot), '.dev-alias-stage-')), moved = [];
  try {
    if (plan.matchingFiles) {
      await writeFile(path.join(devRoot, filename), JSON.stringify(plan.catalogue, null, 2)+'\n');
      const tag = `<meta name="c4d-asset-aliases" content="/4d/dev/${filename}" data-sha256="${plan.catalogue.id}">`;
      for (const [rel, bytes] of snapshot) if (rel.endsWith('.html')) {
        await writeFile(path.join(devRoot, rel), withAliasPointer(bytes.toString(), tag));
      }
    }
    const options = plan.matchingFiles ? { catalogueFile: path.join(devRoot, filename), canonicalRoot: productionRoot } : {};
    await writePacks(devRoot, options); // Native rebuild AND strict check before any deletion.
    for (const rel of Object.keys(plan.catalogue.aliases)) {
      const backup = path.join(stage, rel); await mkdir(path.dirname(backup), { recursive: true });
      await rename(path.join(devRoot, rel), backup); moved.push(rel);
    }
    await writePacks(devRoot, options); // Verify logical bytes/membership with physical DEV copies absent.
    need(await productionFingerprint(productionRoot) === productionBefore, 'production payload changed');
    const report = await assertSiteBudget(siteRoot);
    return { status: plan.matchingFiles ? 'aliased' : 'identity-no-matches', catalogue: plan.matchingFiles ? filename : null,
      catalogueId: plan.matchingFiles ? plan.catalogue.id : null, removed: moved.length, savedAssetBytes: plan.savedBytes,
      kept: plan.kept, matchingFiles: plan.matchingFiles, ...report };
  } catch (error) {
    for (const rel of moved) { await mkdir(path.dirname(path.join(devRoot, rel)), { recursive: true }); await rename(path.join(stage, rel), path.join(devRoot, rel)); }
    for (const [rel] of await inventory(devRoot)) if (isMetadata(rel) && !snapshot.has(rel)) await rm(path.join(devRoot, rel));
    for (const [rel, bytes] of snapshot) await writeFile(path.join(devRoot, rel), bytes);
    if (plan.matchingFiles) {
      if (priorCatalogue !== null) await writeFile(path.join(devRoot, filename), priorCatalogue);
      else await rm(path.join(devRoot, filename), { force: true });
    }
    throw error;
  } finally { await rm(stage, { recursive: true, force: true }); }
}
export async function assembleAssetAliases({ siteRoot, devWorktree, requestedSha }) {
  const productionRoot = path.join(siteRoot, '4d'), devRoot = path.join(productionRoot, 'dev');
  const capability = await nativeCapability(devWorktree, requestedSha, devRoot);
  const writePacks = async (site, { catalogueFile, canonicalRoot } = {}) => {
    const extra = catalogueFile ? ['--asset-aliases', catalogueFile, '--canonical-root', canonicalRoot] : [];
    for (const args of [[site, ...extra], ['--check', site, ...extra]]) execFileSync(process.execPath, [capability.cli, ...args], { stdio: 'inherit', timeout: 90000 });
  };
  return publishAliases({ siteRoot, productionRoot, devRoot, capability, writePacks });
}
