// Narrow publication fixtures. Copies real native code into a disposable local Git pin.
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, rm, access, link, symlink, truncate, cp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { nativeCapability, publishAliases, planAliases, safeGlbClosure, inventory, assertSiteBudget, PAGE_BYTES_LIMIT, withAliasPointer } from './chicago-4d-asset-aliases.mjs';
const native = process.argv[2];
assert(native, 'usage: node test-chicago-4d-asset-aliases.mjs <actual-native-candidate>');
const root = await mkdtemp(path.join(tmpdir(), 'c4d-publisher-test-'));
const hash = b => createHash('sha256').update(b).digest('hex');
let checks = 0;
const ok = (condition, label) => { assert(condition, label); checks++; };
const put = async (file, bytes) => { await mkdir(path.dirname(file), { recursive: true }); await writeFile(file, bytes); };
const exists = async file => { try { await access(file); return true; } catch { return false; } };
const run = (cwd, cmd, args) => execFileSync(cmd, args, { cwd, encoding: 'utf8', stdio: ['ignore','pipe','pipe'], timeout: 20000 });
const glb = doc => {
  const json = Buffer.from(JSON.stringify({ asset: { version: '2.0' }, ...doc }));
  const pad = Buffer.alloc(Math.ceil(json.length/4)*4, 32); json.copy(pad);
  const head = Buffer.alloc(20); head.writeUInt32LE(0x46546c67); head.writeUInt32LE(2,4); head.writeUInt32LE(20+pad.length,8); head.writeUInt32LE(pad.length,12); head.writeUInt32LE(0x4e4f534a,16);
  return Buffer.concat([head,pad]);
};
try {
  const repo = path.join(root,'candidate'); await mkdir(repo);
  const copied = new Set();
  async function copyModule(rel) {
    if (copied.has(rel)) return; copied.add(rel);
    let bytes;
    try { bytes = await readFile(path.join(native,rel)); }
    catch { bytes = Buffer.from(run(native,'git',['show',`HEAD:${rel}`])); }
    await put(path.join(repo,rel),bytes);
    for (const m of bytes.toString().matchAll(/^\s*(?:import|export)[^;]*?from\s*['"]([^'"]+)['"]/gm))
      if (m[1].startsWith('.')) await copyModule(path.posix.normalize(path.posix.join(path.posix.dirname(rel),m[1])));
  }
  const names = ['published-assets','scene-loader','terrain','ktx2','frontage','streets','yards','year-pack'];
  await copyModule('chicago/4d/tools/write_year_packs.mjs');
  await copyModule('chicago/4d/offline/sw.js');
  for (const name of names) await copyModule(`chicago/4d/renderers/web/js/${name}.js`);
  await put(path.join(repo,'package.json'),'{"type":"module"}\n');
  run(repo,'git',['init','-q']); run(repo,'git',['add','.']);
  run(repo,'git',['-c','user.name=Publication fixture','-c','user.email=fixture@invalid','commit','-qm','Pinned actual native fixture']);
  const pin = run(repo,'git',['rev-parse','HEAD']).trim();
  const site = path.join(root,'site'), prod = path.join(site,'4d'), dev = path.join(prod,'dev');
  for (const name of names) await put(path.join(dev,`walk/js/${name}.js`),await readFile(path.join(repo,`chicago/4d/renderers/web/js/${name}.js`)));
  for (const year of ['1812','1835','1904']) {
    await put(path.join(dev,`${year}/index.html`),'<html><head></head><body>door</body></html>');
    await put(path.join(dev,`data/scenes/${year}.json`),'{}');
    await put(path.join(dev,`data/sidecars/${year}/models.json`),JSON.stringify({ file:'gltf/shared.glb' }));
  }
  await put(path.join(dev,'walk/index.html'),'<html><head></head><body>walk</body></html>');
  await put(path.join(dev,'build.json'),'{"tier":"dev"}');
  const implicit = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n<title>Transport</title>\n<header>study</header>\n</html>';
  await put(path.join(dev,'walk/transport/index.html'),implicit);
  const testTag = '<meta name="c4d-asset-aliases" content="/4d/dev/test.json">';
  ok(withAliasPointer(implicit,testTag).includes('<html lang="en">\n'+testTag+'\n<meta charset="utf-8">'),'implicit head metadata inserted before original metadata');
  ok(withAliasPointer('<!doctype html><title>omitted html and head</title>',testTag).startsWith('<!doctype html>\n'+testTag),'omitted html/head retains doctype first');
  ok(withAliasPointer('<title>fragment</title>',testTag).startsWith(testTag),'implicit document prefix supports fragment HTML');

  const shared = glb({ images:[{uri:'sheets/equal.ktx2'},{uri:'sheets/local.png'}] });
  const rows = {'data/gltf/shared.glb':shared,'data/gltf/sheets/equal.ktx2':Buffer.from('ktx2fixture'),
    'data/prebuilt/1835/ground.bin.gz':Buffer.from('compressed-fixture')};
  for (const [rel,bytes] of Object.entries(rows)) { await put(path.join(prod,rel),bytes); await put(path.join(dev,rel),bytes); }
  await put(path.join(dev,'data/gltf/sheets/local.png'),'DEV retained image');
  await put(path.join(prod,'data/gltf/different.ktx2'),'abcd'); await put(path.join(dev,'data/gltf/different.ktx2'),'efgh');
  await put(path.join(dev,'data/gltf/missing.ktx2'),'missing production');
  const external = glb({buffers:[{uri:'buffer.bin'}]});
  await put(path.join(prod,'data/gltf/external.glb'),external); await put(path.join(dev,'data/gltf/external.glb'),external);
  const c = await nativeCapability(repo,pin,dev);
  ok(c.supported === true && c.commit === pin,'actual pinned native candidate and exact published consumers supported');
  ok(!(await nativeCapability(repo,'0000000',dev)).supported,'wrong requested pin unsupported');
  const consumer = path.join(dev,'walk/js/scene-loader.js'), consumerBefore = await readFile(consumer);
  await writeFile(consumer,Buffer.concat([consumerBefore,Buffer.from('\n// stale published copy')]));
  ok(!(await nativeCapability(repo,pin,dev)).supported,'changed published consumer unsupported'); await writeFile(consumer,consumerBefore);
  const source = path.join(repo,'chicago/4d/renderers/web/js/published-assets.js'), before = await readFile(source);
  await writeFile(source,Buffer.concat([before,Buffer.from('\n// dirty source')]));
  ok(!(await nativeCapability(repo,pin,dev)).supported,'uncommitted actual source is unsupported'); await writeFile(source,before);
  const cli = path.join(repo,'chicago/4d/tools/write_year_packs.mjs'), cliBefore = await readFile(cli);
  await writeFile(cli,Buffer.concat([cliBefore,Buffer.from('\n// dirty owner')]));
  ok(!(await nativeCapability(repo,pin,dev)).supported,'uncommitted owning CLI is unsupported'); await writeFile(cli,cliBefore);
  const files = await inventory(dev);
  for (const uri of ['../../../../escape.png','https://elsewhere/x.png','sheets/missing.ktx2','sheets/%2e%2e/x.png'])
    ok(!safeGlbClosure(glb({images:[{uri}]}),'data/gltf/test.glb',files,c).safe,`unsafe/missing closure retained: ${uri}`);
  ok(!safeGlbClosure(external,'data/gltf/test.glb',files,c).safe,'external buffer unsupported');
  const sheet = 'sheets/0123456789abcdef.ktx2', sheetRel = 'data/gltf/'+sheet;
  const textureDoc = {buffers:[{uri:sheet,byteLength:12}],bufferViews:[{buffer:0,byteLength:12}],images:[{bufferView:0,mimeType:'image/ktx2'}]};
  const textureFiles = new Map([[sheetRel,12]]), qualified = {...c,textureBufferAliases:true};
  const closure = doc => safeGlbClosure(glb(doc),'data/gltf/model.glb',textureFiles,qualified);
  ok(closure(textureDoc).safe,'qualified complete KTX2 texture-buffer closure accepted');
  ok(!safeGlbClosure(glb(textureDoc),'data/gltf/model.glb',textureFiles,{...qualified,textureBufferAliases:false}).safe,'missing native texture-buffer capability retains owning GLB');
  for (const [label,edit] of [
    ['geometry buffer URI',d=>d.buffers[0].uri='geometry.bin'],
    ['sheet path escape',d=>d.buffers[0].uri='../sheets/0123456789abcdef.ktx2'],
    ['declared size mismatch',d=>d.buffers[0].byteLength=13],
    ['partial image',d=>d.bufferViews[0].byteLength=11],
    ['offset image',d=>d.bufferViews[0].byteOffset=1],
    ['non KTX2 MIME',d=>d.images[0].mimeType='image/png'],
    ['mixed image MIME shares view',d=>d.images.push({bufferView:0,mimeType:'image/png'})],
    ['accessor shares image view',d=>d.accessors=[{bufferView:0}]],
    ['sparse accessor shares image view',d=>d.accessors=[{sparse:{values:{bufferView:0}}}]],
    ['meshopt uses image buffer',d=>d.bufferViews.push({buffer:1,byteLength:1,extensions:{EXT_meshopt_compression:{buffer:0}}})],
    ['unused external buffer',d=>d.images=[]],
    ['unknown extension repeats sheet URI',d=>d.extensions={UNSUPPORTED:{uri:sheet}}],
  ]) { const doc=structuredClone(textureDoc);edit(doc);ok(!closure(doc).safe,'unsafe texture-buffer refused: '+label); }
  ok(!safeGlbClosure(glb(textureDoc),'data/gltf/model.glb',new Map(),qualified).safe,'missing logical texture-buffer retained');
  const plan = await planAliases(prod,dev,c);
  ok(plan.matchingFiles === 3 && plan.savedBytes === Object.values(rows).reduce((n,b)=>n+b.length,0),'exact full hash and safe image closure eligibility');
  ok(!plan.catalogue.aliases['data/gltf/different.ktx2'] && !plan.catalogue.aliases['data/gltf/external.glb'],'different bytes and external buffers retained');
  const assembly = path.join(root,'assembler');
  await cp(dev,path.join(repo,'site/4d'),{recursive:true});
  for(const [rel,bytes] of Object.entries(rows))await put(path.join(assembly,'site/4d',rel),bytes);
  await put(path.join(assembly,'site/4d/index.html'),'<html><head></head><body>production</body></html>');
  await put(path.join(assembly,'site/other/index.html'),'other root portal');
  run(assembly,process.execPath,[new URL('./chicago-4d-dev-preview.mjs',import.meta.url).pathname,repo,pin,'2026-11-10T00:00:00Z']);
  const assembled = path.join(assembly,'site/4d/dev');
  ok(!(await exists(path.join(assembled,'data/gltf/shared.glb'))) && JSON.parse(await readFile(path.join(assembled,'build.json'))).sha===pin,'real assembler copy/mark/stamp hooks verified native alias stage');
  ok((await readFile(path.join(assembly,'site/4d/index.html'),'utf8')).includes('production')
    && (await readFile(path.join(assembly,'site/other/index.html'),'utf8'))==='other root portal','real assembler retains production and other portals');
  const api = {siteRoot:site,productionRoot:prod,devRoot:dev};
  const unsupported = await publishAliases({...api,capability:{supported:false,why:'old DEV'}});
  ok(unsupported.removed === 0 && await exists(path.join(dev,'data/gltf/shared.glb')),'old DEV retains copies and no catalogue');
  await assert.rejects(publishAliases({...api,devRoot:prod,capability:c}),/ownership/); checks++;
  const oldCatalogueFile = path.join(dev,`asset-aliases.${plan.catalogue.id}.json`);
  await writeFile(oldCatalogueFile,'existing catalogue sentinel');
  const originalHTML = await readFile(path.join(dev,'walk/index.html'));
  let calls=0;
  await assert.rejects(publishAliases({...api,capability:c,writePacks:async()=>{
    await put(path.join(dev,'packs/new.json'),'new'); await put(path.join(dev,'sw.js'),'new worker');
    if (++calls === 2) throw Error('strict check fixture failure');
  }}),/strict check fixture failure/); checks++;
  ok(await exists(path.join(dev,'data/gltf/shared.glb')) && !(await exists(path.join(dev,'packs/new.json'))) && !(await exists(path.join(dev,'sw.js'))),'rollback restores binary and removes new pack metadata');
  ok((await readFile(path.join(dev,'walk/index.html'))).equals(originalHTML),'rollback restores HTML');
  ok((await readFile(oldCatalogueFile,'utf8')) === 'existing catalogue sentinel','rollback preserves preexisting same-ID catalogue bytes');
  await rm(oldCatalogueFile);
  const prodHashes = new Map(); for(const [rel] of await inventory(prod,r=>r==='dev'||r.startsWith('dev/'))) prodHashes.set(rel,hash(await readFile(path.join(prod,rel))));
  const owner = async (dir,{catalogueFile,canonicalRoot}={}) => {
    const extra = catalogueFile ? ['--asset-aliases',catalogueFile,'--canonical-root',canonicalRoot] : [];
    run(repo,process.execPath,[cli,dir,...extra]); run(repo,process.execPath,[cli,'--check',dir,...extra]);
  };
  let strictCalls = 0;
  await assert.rejects(publishAliases({...api,capability:c,writePacks:async(dir,options)=>{
    await owner(dir,options);
    if (++strictCalls === 2) {
      await writeFile(path.join(dir,'sw.js'),'corrupted generated worker');
      const extra = ['--asset-aliases',options.catalogueFile,'--canonical-root',options.canonicalRoot];
      run(repo,process.execPath,[cli,'--check',dir,...extra]); // Real owning checker must reject.
    }
  }}),/Command failed/); checks++;
  ok(await exists(path.join(dev,'data/gltf/shared.glb')) && !(await exists(path.join(dev,'sw.js')))
    && (await readFile(path.join(dev,'walk/index.html'))).equals(originalHTML),'real native strictcheck failure rolls back generated metadata, binary and HTML');
  const result = await publishAliases({...api,capability:c,writePacks:owner});
  ok(result.removed===3 && !(await exists(path.join(dev,'data/gltf/shared.glb'))) && await exists(path.join(dev,'data/gltf/sheets/local.png')),'real native pack strictcheck permits logical aliases while local image stays');
  for(const [rel,h] of prodHashes) assert.equal(hash(await readFile(path.join(prod,rel))),h); checks++;
  for(const year of ['1812','1835','1904']) {
    const pack = JSON.parse(await readFile(path.join(dev,`packs/${year}.json`)));
    ok(pack.files.some(r=>r[0]==='data/gltf/shared.glb' && r[2]===shared.length),'removed GLB logical bytes preserved in actual pack '+year);
    ok(pack.files.some(r=>r[0]==='data/prebuilt/1835/ground.bin.gz')===(year==='1835'),'prebuilt original year membership '+year);
  }
  const generated = new Map(); for(const [rel] of await inventory(dev)) if(rel.startsWith('packs/')||rel==='sw.js') generated.set(rel,hash(await readFile(path.join(dev,rel))));
  owner(dev); for(const [rel,h] of generated) assert.equal(hash(await readFile(path.join(dev,rel))),h); checks++;
  const bad = path.join(root,'bad'); await mkdir(bad); await put(path.join(bad,'a'),'x'); await link(path.join(bad,'a'),path.join(bad,'b'));
  await assert.rejects(inventory(bad),/hard-linked/); checks++;
  await rm(path.join(bad,'b')); await symlink(path.join(bad,'a'),path.join(bad,'s'));
  await assert.rejects(inventory(bad),/symbolic link/); checks++;
  const budget = path.join(root,'budget'); await mkdir(budget); await put(path.join(budget,'other-portal.bin'),''); await truncate(path.join(budget,'other-portal.bin'),PAGE_BYTES_LIMIT);
  ok((await assertSiteBudget(budget)).reserveBytes===0,'all-site exact 1GB boundary accepted'); await truncate(path.join(budget,'other-portal.bin'),PAGE_BYTES_LIMIT+1);
  await assert.rejects(assertSiteBudget(budget),/1000000001B/); checks++;
  console.log(JSON.stringify({status:'PASS',checks,actualNativeModules:copied.size,pin,aliasFiles:result.removed,savedAssetBytes:result.savedAssetBytes,siteBytes:result.regularFileBytes}));
} finally { await rm(root,{recursive:true,force:true}); }
