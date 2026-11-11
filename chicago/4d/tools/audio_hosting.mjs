// T-3532: publish only the small catalogue; verified media lives in R2.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
export function hostedCatalog({root=ROOT,tier=process.env.C4D_PUBLISH_TIER??'development'}={}) {
  const policy=read(path.join(root,'tools/audio-hosting.json'));
  const base=new URL(policy.public_base);
  if(policy.version!==1||base.protocol!=='https:'||base.username||base.password||base.search||base.hash)
    throw Error('Invalid audio hosting policy');
  if(tier==='production'&&(policy.scope!=='production'||base.hostname.endsWith('.r2.dev')))
    throw Error('Audio uses a development R2 endpoint; configure and verify a production media hostname before promotion.');
  const receipt=read(path.join(root,'tools/audio-host-verification.json'));
  if(!receipt.complete||receipt.errors?.length||receipt.public_base!==base.href||receipt.origin!==policy.origin)
    throw Error('Audio host verification does not match the configured host');
  const verified=new Map(receipt.verified.map(row=>[row.key,row]));
  const dir=path.join(root,'renderers/web/audio');
  const catalog=read(path.join(dir,'catalog.json'));
  const media=[];
  for(const asset of catalog.assets)for(const field of asset.kind==='music'?['opus','aac']:['url']) {
    const relative=asset[field];
    if(typeof relative!=='string'||path.isAbsolute(relative)||relative.split('/').some(p=>p==='..')||relative.includes(':'))
      throw Error(`Invalid local audio path: ${relative}`);
    const source=path.join(dir,relative),bytes=fs.readFileSync(source);
    const digest=createHash('sha256').update(bytes).digest('hex');
    const expected=asset.kind==='music'?asset.delivery[field]:asset.delivery;
    if(digest!==expected.sha256||bytes.length!==expected.bytes)throw Error(`Audio delivery changed: ${relative}`);
    const key=`media/${digest}${path.extname(relative)}`;
    if(verified.get(key)?.bytes!==bytes.length)throw Error(`Audio was not verified on the configured host: ${relative}`);
    asset[field]=new URL(key,base).href;
    media.push(relative);
  }
  catalog.hosting={scope:policy.scope,public_base:base.href,offline_audio:false};
  return {catalog,media};
}

export function publishAudio(site,{root=ROOT,tier}={}) {
  // Validate everything before removing any published media. Source/archive
  // files stay intact for authoring and reproducible upload packages.
  const {catalog,media}=hostedCatalog({root,tier});
  const dir=path.join(site,'walk/audio');
  fs.writeFileSync(path.join(dir,'catalog.json'),JSON.stringify(catalog)+'\n');
  for(const relative of media)fs.rmSync(path.join(dir,relative),{force:true});
  console.log(`audio: ${media.length} verified remote deliveries; catalogue only in the site`);
}

export function checkAudio(site,{root=ROOT}={}) {
  const {catalog,media}=hostedCatalog({root});
  const dir=path.join(site,'walk/audio');
  const actual=fs.readFileSync(path.join(dir,'catalog.json'),'utf8');
  if(actual!==JSON.stringify(catalog)+'\n')throw Error('Published audio catalogue does not match source, host policy and verification receipt');
  for(const relative of media)if(fs.existsSync(path.join(dir,relative)))throw Error(`Remote audio duplicated in the site: ${relative}`);
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const [mode,site]=process.argv.slice(2);
  if(mode==='--validate'){hostedCatalog();console.log('AUDIO HOST POLICY PASS');}
  else if(!site||!['--publish','--check'].includes(mode))throw Error('usage: audio_hosting.mjs --validate | --publish|--check <site>');
  else if(mode==='--publish')publishAudio(path.resolve(site));else{checkAudio(path.resolve(site));console.log('AUDIO PUBLICATION PASS');}
}
