// SPDX-License-Identifier: GPL-3.0-or-later
// Actual native loader/mixer/skinning inspection. No renderer or WebGL.
const fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const APP=path.resolve(__dirname,'..'),args=process.argv.slice(2);
function arg(name){const i=args.indexOf(name);if(i<0||!args[i+1])throw Error(`${name} required`);return path.resolve(args[i+1]);}
const candidate=arg('--candidate'),output=arg('--output'),controlOldIdle=args.includes('--control-old-idle'),witnessOnly=args.includes('--clearance-witness'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
let browser,server;const report={scope:'Actual native GLTFLoader/Meshopt/AnimationMixer/skin readback without WebGL; no visual/photographic or full continuous garment proof',files:[],passed:false};
(async()=>{
  await fs.mkdir(output,{recursive:false});
  const recipe=JSON.parse(await fs.readFile(path.join(APP,'data/humans/animations/natural-standing-v1.json'),'utf8'));
  const selectedIndex=args.indexOf('--files'),selectedNames=selectedIndex<0?recipe.parents.map(r=>r.file):String(args[selectedIndex+1]??'').split(',');
  if(!selectedNames.length||new Set(selectedNames).size!==selectedNames.length||selectedNames.some(name=>!recipe.parents.some(r=>r.file===name)))throw Error('--files must name a unique, explicit subset of the eight recipe paths');
  const selected=selectedNames.map(file=>recipe.parents.find(r=>r.file===file));report.selected_files=selectedNames;report.selected_scope_passed=false;report.all_eight_passed=false;
  const derivation=JSON.parse(await fs.readFile(path.join(candidate,'DERIVATION.json'),'utf8'));
  if(derivation.generator_sha256!==sha(await fs.readFile(path.join(APP,'tools/human_natural_idle.py')))||derivation.recipe_sha256!==sha(await fs.readFile(path.join(APP,'data/humans/animations/natural-standing-v1.json'))))throw Error('Candidate generation implementation/recipe mismatch');
  const before={};for(const row of recipe.parents){const p=path.join(candidate,row.file);before[row.file]=sha(await fs.readFile(p));}
  for(const row of derivation.files)if(before[row.file]!==row.sha256)throw Error('Candidate differs from actual derivation receipt');
  const implementation=['tools/human_natural_idle.py','tools/human_natural_idle_cpu.html','tools/human_natural_idle_cpu.cjs','tools/human_body_ray_grid.mjs','data/humans/animations/natural-standing-v1.json','renderers/web/js/humans.js','renderers/web/js/main.js','renderers/web/js/scene-loader.js','renderers/web/vendor/three-0.185.1/three.module.js','renderers/web/vendor/three-0.185.1/three.core.js','renderers/web/vendor/three-0.185.1/addons/loaders/GLTFLoader.js','renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js','renderers/web/vendor/three-0.185.1/addons/utils/SkeletonUtils.js'];
  const pins={};for(const p of [...implementation,...recipe.parents.map(r=>r.file)])pins[p]=sha(await fs.readFile(path.join(APP,p)));
  report.implementation_and_parent_pins_before=pins;
  report.anatomical_reference={file:recipe.parents[0].file,canonical_parent_sha256:recipe.parents[0].sha256,candidate_sha256:before[recipe.parents[0].file],scope:'Native closed master-LOD0 BODY posed at the identical old/new clip time; actual render BODY unsigned distance changes reported separately'};
  await fs.writeFile(path.join(output,'RESULT.json'),JSON.stringify(report,null,2)+'\n');
  const mime={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm','.glb':'model/gltf-binary'};
  server=http.createServer(async(req,res)=>{try{const url=new URL(req.url,'http://local'),isCandidate=url.pathname.startsWith('/candidate/'),root=isCandidate?candidate:APP,relative=isCandidate?url.pathname.slice(11):url.pathname.slice(1),file=path.resolve(root,decodeURIComponent(relative));if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]??'application/octet-stream');res.end(await fs.readFile(file));}catch{res.writeHead(404).end();}});
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  browser=await chromium.launch({executablePath:process.env.PW_EXECUTABLE||undefined,args:['--no-sandbox','--disable-gpu']});
  const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.stack??e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());else if(m.type()==='log')console.log(m.text());});
  await page.goto(`http://127.0.0.1:${server.address().port}/tools/human_natural_idle_cpu.html`);await page.waitForFunction(()=>window.cpuReady);
  report.lifecycle=await page.evaluate(()=>inspectLifecycle());
  if(witnessOnly)report.clearance_witness=await page.evaluate(file=>inspectClearanceWitness(file),recipe.parents[0].file);
  else for(const row of selected){
    console.log(`native CPU inspect ${row.file}${controlOldIdle?' ORIGINAL IDLE CONTROL':''}`);
    const result=await page.evaluate(({file,control,reference})=>inspectNatural(file,control,reference),{file:row.file,control:controlOldIdle,reference:recipe.parents[0].file});
    const after={};for(const p of Object.keys(pins)){after[p]=sha(await fs.readFile(path.join(APP,p)));if(after[p]!==pins[p])throw Error('Implementation/parent changed during native model readback: '+p);}
    const allCandidatesAfter={};for(const candidateRow of recipe.parents){const hash=sha(await fs.readFile(path.join(candidate,candidateRow.file)));allCandidatesAfter[candidateRow.file]=hash;if(hash!==before[candidateRow.file])throw Error('Candidate changed during native model readback');}
    const model={...result,sha256:before[row.file],implementation_and_parent_pins_before:pins,implementation_and_parent_pins_after:after,candidate_sha256_before_all:before,candidate_sha256_after_all:allCandidatesAfter,anatomical_reference:report.anatomical_reference};
    report.files.push(model);
    await fs.writeFile(path.join(output,row.file.replaceAll('/','__')+'.json'),JSON.stringify(model,null,2)+'\n');
    await fs.writeFile(path.join(output,'RESULT.json'),JSON.stringify(report,null,2)+'\n');
    if(!result.passed||controlOldIdle)break;
  }
  report.errors=errors;report.source_guards={};
  for(const row of recipe.parents){const exact=sha(await fs.readFile(path.join(candidate,row.file)))===before[row.file];report.source_guards[row.file]=exact;if(!exact)throw Error('Candidate changed during actual readback');}
  report.implementation_and_parent_pins_after={};for(const p of Object.keys(pins)){const hash=sha(await fs.readFile(path.join(APP,p)));report.implementation_and_parent_pins_after[p]=hash;if(hash!==pins[p])throw Error('Implementation/parent changed during native readback: '+p);}
  report.diagnostic_only=controlOldIdle||witnessOnly;
  report.selected_scope_passed=!controlOldIdle&&!witnessOnly&&errors.length===0&&report.lifecycle.passed&&report.files.length===selected.length&&report.files.every(r=>r.passed&&r.webgl_requests===0);
  report.all_eight_passed=report.selected_scope_passed&&selected.length===recipe.parents.length;
  report.passed=report.all_eight_passed;
  if(!report.selected_scope_passed)process.exitCode=1;
})().catch(e=>{report.error=e.stack??String(e);process.exitCode=1;}).finally(async()=>{await browser?.close();if(server)await new Promise(r=>server.close(r));await fs.writeFile(path.join(output,'RESULT.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({all_eight_passed:report.all_eight_passed??false,selected_scope_passed:report.selected_scope_passed??false,files:report.files.length,error:report.error??null}));});
