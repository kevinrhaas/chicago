const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto'),{execFileSync}=require('child_process');
const {chromium}=require('/tmp/t1766-browser/node_modules/playwright');
const APP='/workspace/scratch/834d2e70e9c9/chicago/chicago/4d',ROOT=path.resolve(APP,'../../site/4d');
const OUT='/tmp/t1766-t1793-whatsnew.json',TITLE='Stores and workshops on the Canal approach',RESEARCH='How many farms the West Side prairie could hold',LATEST=1248;
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const receipt={scope:'Published1904 HTML/CSS with actual createHud and whatsnew modules at both viewports. Main3D startup intercepted; empty GoTo inventory fixture. Component semantics only, not a scene smoke. Prior actual1904 first-visit semantics passed; supplemental width failure preserved separately.',startedAt:new Date().toISOString(),head:execFileSync('git',['rev-parse','HEAD'],{cwd:APP,encoding:'utf8'}).trim(),uncommittedTree:!!execFileSync('git',['status','--porcelain'],{cwd:APP,encoding:'utf8'}).trim(),publishedRoot:ROOT,publishedChangelogSha256:hash(ROOT+'/js/changelog.js'),publishedChangelogReexportSha256:hash(ROOT+'/walk/js/changelog.js'),sourceChangelogSha256:hash(APP+'/renderers/web/js/changelog.js'),viewports:[],failures:[]};
assert.equal(receipt.publishedChangelogSha256,receipt.sourceChangelogSha256);
const types={'.html':'text/html','.js':'text/javascript','.json':'application/json','.wasm':'application/wasm','.css':'text/css','.glb':'model/gltf-binary','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=path.join(ROOT,decodeURIComponent(req.url.split('?')[0]));if(fs.existsSync(p)&&fs.statSync(p).isDirectory())p=path.join(p,'index.html');if(!p.startsWith(ROOT)||!fs.existsSync(p)){res.writeHead(404);res.end();return;}res.writeHead(200,{'content-type':types[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(res);});
const save=()=>fs.writeFileSync(OUT,JSON.stringify(receipt,null,2)+'\n');
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({executablePath:'/tmp/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']});
try{for(const mobile of [true,false]){
 const viewport=mobile?{width:390,height:780}:{width:1280,height:800};const context=await browser.newContext({viewport,deviceScaleFactor:mobile?2:1,hasTouch:mobile,isMobile:false});const page=await context.newPage();page.setDefaultTimeout(90000);const errors=[];page.on('pageerror',e=>errors.push(String(e)));const result={viewport:mobile?'mobile':'desktop',...viewport,deviceScaleFactor:mobile?2:1};receipt.viewports.push(result);save();
 async function ready(){return page.evaluate(async()=>{const {createHud}=await import('./js/hud.js');document.getElementById('gate').hidden=true;const root=document.getElementById('hud');root.hidden=false;window.testHud=createHud({root,scene:{id:'1904'},destinations:{targets:[],groups:[],search:()=>[]},isTouch:innerWidth<500});return {component:'actual createHud',sceneStartup:'blocked',fixture:'empty unused GoTo inventory'};});}
 await page.route('**/js/main.js',r=>r.fulfill({status:200,contentType:'text/javascript',body:'/* focused component scope: no3D */'}));
  const clickChrome = async (sel) => {
    const why = await page.evaluate(async (s) => {
      const el = document.querySelector(s);
      if (!el) return `nothing matches ${s}`;
      if (el.disabled) return `${s} is disabled`;
      // T-0701: the drawer SLIDES. `#panel[hidden]` keeps its layout and sits at
      // translateX(102%), and opening it is a .24 s transform — so for a quarter
      // of a second after `setPanel(true)` a tab has a real box whose centre is
      // off the right edge of the viewport, and `elementFromPoint` answers
      // `null` for it. A visitor clicks a drawer that has arrived; so does this.
      // Waited for, never assumed: the hit-test below still runs on the settled
      // box, and a control that is genuinely covered still fails here.
      const drawer = el.closest('#panel');
      if (drawer) {
        for (let i = 0; i < 40 && getComputedStyle(drawer).transform !== 'none'; i++) {
          await new Promise((r) => setTimeout(r, 50));
        }
      }
      // The same scroll `page.click` would do, in the same round trip as the
      // reading — a result row far down the Go-to list is off the panel's
      // viewport until this runs, and `elementFromPoint` would then answer for
      // whatever is at those coordinates instead.
      el.scrollIntoView({ block: 'center', inline: 'center' });
      const b = el.getBoundingClientRect();
      if (b.width < 1 || b.height < 1) {
        return `${s} has no box (${Math.round(b.width)}x${Math.round(b.height)})`;
      }
      const top = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
      if (!top || !(top === el || el.contains(top))) {
        const cls = top && typeof top.className === 'string' ? top.className : '';
        // NAME THE OVERLAY, NOT JUST THE TAG IT ENDS IN (T-0369). The first
        // report of this failure said only `<h2>`, and an `<h2>` is a heading
        // inside something — the thing worth naming is the panel that heading
        // belongs to. Walking up to the nearest ancestor carrying an id turns
        // "covered by <h2>" into "covered by <h2> inside #popup", which is the
        // whole diagnosis of a stale overlay left open by an earlier stage.
        let owner = top;
        while (owner && !owner.id && owner !== document.body) owner = owner.parentElement;
        const inside = owner && owner.id && owner !== el ? ` inside #${owner.id}` : '';
        return `${s} is covered at its own centre by `
          + `<${top ? top.tagName.toLowerCase() : 'nothing'}${cls ? ` class="${cls}"` : ''}>${inside}`;
      }
      // A real mouse press FOCUSES a focusable control, and an untrusted
      // `.click()` does not — which is a difference the suite already depends on
      // and which this helper got wrong on its first run, honestly and visibly.
      // Part 8 closes the panel and then presses `g`, and `g` only reaches the
      // window shortcut if focus has left the Go-to search box first: the shared
      // `isTyping(e.target)` guard swallows it otherwise, which is the whole
      // point of that guard. Without this line the panel stayed shut, `g` did
      // nothing, and the next reading was a result row with a 0x0 box. So this
      // is fidelity to the click being replaced, not a convenience.
      if (typeof el.focus === 'function') el.focus({ preventScroll: true });
      el.click();
      return null;
    }, sel);
    if (why) throw new Error(`clickChrome: ${why}`);
  };

 async function open(){await clickChrome('#btn-help');await clickChrome('.panel-tab[data-tab="whatsnew"]');await page.waitForFunction(()=>!document.getElementById('whatsnew')?.hidden&&document.querySelectorAll('#whatsnew .wn-entry').length>0);}
 async function contents(){return page.evaluate(({research})=>{const host=document.getElementById('whatsnew'),rows=[...host.querySelectorAll('.wn-entry')],r=rows.find(x=>x.querySelector('.wn-title')?.textContent===research);return{entries:rows.length,items:host.querySelectorAll('.wn-items li').length,newest:host.querySelector('.wn-title')?.textContent,newestMeta:host.querySelector('.wn-meta')?.textContent,research:r?{title:r.querySelector('.wn-title').textContent,items:[...r.querySelectorAll('.wn-items li')].map(x=>x.textContent),date:r.querySelector('.wn-meta').textContent}:null,flagged:rows.filter(x=>x.classList.contains('is-new')).map(x=>x.querySelector('.wn-title').textContent),chipCleared:document.getElementById('help-dot').hidden,tabCleared:document.getElementById('whatsnew-dot').hidden,seen:localStorage.getItem('chicago4d.whatsnew.seen'),fits:host.scrollWidth<=host.clientWidth+1};},{research:RESEARCH});}
 await page.goto('http://127.0.0.1:'+server.address().port+'/1904/',{waitUntil:'domcontentloaded'});result.scene=await ready();console.log(result.viewport+' firstboot ready');
 result.unread=await page.evaluate(()=>({chip:!document.getElementById('help-dot').hidden,tab:!document.getElementById('whatsnew-dot').hidden}));assert(result.unread.chip&&result.unread.tab);
 await open();result.first=await contents();const a=result.first;assert.equal(a.entries,LATEST);assert(a.items>=a.entries);assert.equal(a.newest,TITLE);assert(/CT$/.test(a.newestMeta));assert(a.research);assert.equal(a.research.items.length,3);assert(/Oct 1, 2026, 1:56 AM CT$/.test(a.research.date));assert.equal(a.flagged.length,0);assert(a.chipCleared&&a.tabCleared);assert.equal(Number(a.seen),LATEST);result.layoutComparison=await page.evaluate(()=>{const host=document.getElementById('whatsnew'),rows=[...host.querySelectorAll('.wn-entry')],r=rows.find(x=>x.querySelector('.wn-title')?.textContent==='How many farms the West Side prairie could hold');const box=e=>{const b=e.getBoundingClientRect(),c=getComputedStyle(e);return {width:b.width,left:b.left,right:b.right,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,overflowX:c.overflowX}};const snapshot=()=>({host:box(host),panel:box(document.getElementById('panel')),scroll:box(document.getElementById('panel-scroll')),document:box(document.documentElement)});const before=snapshot(),research=box(r),next=r.nextSibling,parent=r.parentNode;r.remove();const withoutResearch=snapshot();parent.insertBefore(r,next);const inheritedWideItems=[...host.querySelectorAll('.wn-items li')].filter(x=>x.scrollWidth>x.clientWidth+1).slice(0,12).map(x=>({title:x.closest('.wn-entry').querySelector('.wn-title').textContent,text:x.textContent,box:box(x)}));const list=host.querySelector('.wn-list');list.style.display='block';const intrinsicRows=rows.map(x=>{x.style.width='min-content';const width=x.getBoundingClientRect().width;x.style.width='';return {title:x.querySelector('.wn-title').textContent,minContentWidth:width};}).sort((a,b)=>b.minContentWidth-a.minContentWidth).slice(0,5);list.style.display='';return {before,withoutResearch,research,inheritedWideItems,intrinsicRows,extraWidthAssertionPassed:host.scrollWidth<=host.clientWidth+1};});save();
 await page.evaluate(()=>localStorage.setItem('chicago4d.whatsnew.seen','1246'));await page.reload({waitUntil:'domcontentloaded'});await ready();result.returningUnread=await page.evaluate(()=>({chip:!document.getElementById('help-dot').hidden,tab:!document.getElementById('whatsnew-dot').hidden}));assert(result.returningUnread.chip&&result.returningUnread.tab);await open();result.returning=await contents();assert.deepEqual(result.returning.flagged,[TITLE,RESEARCH]);assert.equal(Number(result.returning.seen),LATEST);assert(result.returning.chipCleared&&result.returning.tabCleared);assert.equal(errors.length,0,errors.join('\n'));result.pageErrors=errors;result.pass=true;save();console.log(result.viewport+' PASS:1248entries, latestCanal, research3items/date, first/returning unreadstates, zeropageerrors; extra width observation recorded separately');await context.close();
 }
 receipt.pass=true;
}catch(e){receipt.failures.push(String(e.stack||e));receipt.pass=false;console.error(e);process.exitCode=1;}finally{receipt.finishedAt=new Date().toISOString();save();await browser.close();server.close();}})().catch(e=>{receipt.pass=false;receipt.failures.push(String(e));save();console.error(e);server.close();process.exitCode=1});
