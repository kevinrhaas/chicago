import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {hostedCatalog,publishAudio,checkAudio} from './audio_hosting.mjs';
const root=fs.mkdtempSync(path.join(os.tmpdir(),'audio-hosting-'));
const put=(p,data)=>{const f=path.join(root,p);fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,typeof data==='string'?data:JSON.stringify(data));};
try{
 const base='https://test.r2.dev/';
 const policy={version:1,scope:'development',public_base:base,origin:'https://chicago.polecat.live'};
 const files={'1835/score.ogg':'opus fixture','1835/score.m4a':'aac fixture','river.mp3':'river fixture'};
 const integrity=Object.fromEntries(Object.entries(files).map(([p,s])=>[p,{sha256:createHash('sha256').update(s).digest('hex'),bytes:Buffer.byteLength(s)}]));
 const receipt={public_base:base,origin:policy.origin,complete:true,errors:[],verified:Object.keys(files).map(p=>({key:`media/${integrity[p].sha256}${path.extname(p)}`,bytes:integrity[p].bytes}))};
 const catalog={version:1,assets:[{id:'score',kind:'music',era:'1835',opus:'1835/score.ogg',aac:'1835/score.m4a',delivery:{opus:integrity['1835/score.ogg'],aac:integrity['1835/score.m4a']}},{id:'river',kind:'environment',url:'river.mp3',delivery:integrity['river.mp3']}]};
 put('tools/audio-hosting.json',policy);put('tools/audio-host-verification.json',receipt);put('renderers/web/audio/catalog.json',catalog);
 for(const [p,s] of Object.entries(files)){put('renderers/web/audio/'+p,s);put('site/walk/audio/'+p,s);}
 const site=path.join(root,'site');publishAudio(site,{root});checkAudio(site,{root});
 const published=JSON.parse(fs.readFileSync(path.join(site,'walk/audio/catalog.json')));
 assert.equal(published.assets[0].era,'1835');assert.match(published.assets[0].opus,/^https:\/\/test.r2.dev\/media\/[a-f0-9]{64}\.ogg$/);
 assert(fs.existsSync(path.join(root,'renderers/web/audio/river.mp3')),'authoring file retained');
 assert.throws(()=>hostedCatalog({root,tier:'production'}),/development R2/);
 put('site/walk/audio/river.mp3',files['river.mp3']);assert.throws(()=>checkAudio(site,{root}),/duplicated/);fs.unlinkSync(path.join(site,'walk/audio/river.mp3'));
 put('renderers/web/audio/river.mp3','changed');assert.throws(()=>hostedCatalog({root}),/delivery changed/);put('renderers/web/audio/river.mp3',files['river.mp3']);
 put('tools/audio-host-verification.json',{...receipt,verified:receipt.verified.slice(0,2)});assert.throws(()=>hostedCatalog({root}),/not verified/);
 put('tools/audio-host-verification.json',{...receipt,public_base:'https://other.example/'});assert.throws(()=>hostedCatalog({root}),/does not match/);
 put('tools/audio-host-verification.json',receipt);
 put('site/walk/audio/catalog.json',{...published,assets:[]});assert.throws(()=>checkAudio(site,{root}),/catalogue does not match/);
 console.log('AUDIO HOSTING PASS: immutable URLs, exact receipt/source binding, source preservation, duplicate rejection, production guard and catalogue parity');
}finally{fs.rmSync(root,{recursive:true,force:true});}
