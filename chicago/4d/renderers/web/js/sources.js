/** T-1276: on-demand public source catalog; no research files or derived assets. */
import { escapeHtml as esc } from './citations.js';
export const GRADES = ['attested', 'inferred', 'reconstructed'];
const ALIASES = ['DOC', 'INF', 'CONJ'];
const TYPES = ['book','newspaper','map','website','dataset','manuscript','illustration','photograph','legal','article'];
const USES = ['scene','other_scene','exclusion','research','unused'];
const words = s => String(s ?? '').replaceAll('_', ' ');
const norm = s => String(s ?? '').toLowerCase();
export function selectSources(rows, state) {
  const result = rows.filter(r => (state.all || r.use === 'scene') &&
    (!state.query || norm(r.citation + ' ' + r.source_id).includes(norm(state.query))) &&
    (!state.type || r.type === state.type) && (!state.tier || String(r.tier) === String(state.tier)) &&
    (!state.use || r.use === state.use));
  return result.sort((a,b) => (state.sort === 'claims' || state.sort === 'entities'
    ? b.counts[state.sort] - a.counts[state.sort]
    : state.sort === 'date' ? String(a.date ?? '').localeCompare(String(b.date ?? '')) : 0) || a.citation.localeCompare(b.citation));
}
export function gradeCounts(edges) {
  const claims = new Map(), entities = new Map();
  for (const e of edges) {
    const rank = GRADES.indexOf(e.confidence); if (rank < 0) continue;
    const entity = JSON.stringify([e.entity_type,e.entity_id]), claim = JSON.stringify([e.entity_type,e.entity_id,e.claim]);
    for (const [map,key] of [[claims,claim],[entities,entity]]) map.set(key,Math.min(rank,map.get(key) ?? 2));
  }
  return [claims,entities].map(m => GRADES.map((_,i) => [...m.values()].filter(v=>v===i).length));
}
export function issueGroups(edges) {
  const groups = new Map();
  for (const edge of edges) {
    const loc = typeof edge.locator === 'string' ? edge.locator : JSON.stringify(edge.locator ?? '');
    const issue = loc.match(/(?:chicago_[a-z_]+_)?(18\d{2})[_-](\d{2})[_-](\d{2})/);
    if (!issue) continue;
    const key = `${issue[1]}-${issue[2]}-${issue[3]}`;
    if (!groups.has(key)) groups.set(key,[]); groups.get(key).push(edge);
  }
  return [...groups].sort(([a],[b])=>a.localeCompare(b));
}
export function terrainCardId(edge, claims) {
  const id=edge.claim.replace(/\[([^\]]+)\]/g,'.$1').replace(/\.properties.*$/,'');
  const material=/^surface_materials\.(\d+)/.exec(id);
  if(material)return claims.filter(c=>c.id.startsWith('surface_materials.'))[Number(material[1])]?.id;
  return claims.find(c=>id===c.id || id.startsWith(c.id+'.') || (id.startsWith('features.') && c.id.endsWith('.'+id.slice(9))))?.id;
}
function chip(grade) { const i=GRADES.indexOf(grade);return `<span class="src-grade src-g${i}" title="${esc(grade)}">[${ALIASES[i] || '?'}]</span>`; }
function counts(row) {
  const [c,e] = row.counts.grades || [];
  const figures = a => a?.map((v,i)=>`${chip(GRADES[i])} ${v}`).join(' · ') || 'Confidence breakdown unavailable';
  const total = row.counts.entities;
  return `<div class="src-counts"><span><b>Claims: ${row.counts.claims}</b> — ${figures(c)}</span>` +
    `<span><b>Entities: ${total}</b> — ${figures(e)}</span></div>` +
    (e ? `<div class="src-bar" aria-label="Entities by strongest confidence: ${e.map((v,i)=>`${v} ${GRADES[i]}`).join(', ')}">${e.map((v,i)=>`<i class="src-g${i}" style="width:${total ? 100*v/total : 0}%"></i>`).join('')}</div>` : '');
}
function urlLink(url,label) {
  try { const u = new URL(url); if (!['https:','http:'].includes(u.protocol)) return '';return `<a href="${esc(u.href)}" target="_blank" rel="noopener noreferrer">${label}</a>`; } catch { return ''; }
}
export async function mountSources({root, dataBase, onTitle, onBack, onOpen, canOpen=()=>undefined, fetcher=fetch}) {
  const css=document.createElement('link');css.rel='stylesheet';css.href=new URL('../css/sources.css',import.meta.url);document.head.append(css);
  const scroll=root.closest('.panel-scroll') || root.parentElement;
  const state={query:'',all:false,type:'',tier:'',use:'',sort:'claims',filtersOpen:false,limit:40,scroll:0,detailScroll:0,detail:null};
  const cache=new Map();let rows=[], sequence=0;
  root.innerHTML='<p role="status">Loading source catalog…</p>';
  const api={state,show, get rows(){return rows;},open:openDetail};
  async function loadIndex() { try {
    const res=await fetcher(new URL('sidecars/1835/sources/index.json',dataBase));
    if(!res.ok)throw Error(`HTTP ${res.status}`);
    const data=await res.json();if(!Array.isArray(data.sources))throw Error('Invalid catalog');rows=data.sources;
    root.dataset.count=String(rows.length);root.removeAttribute('aria-busy');renderList();
  } catch {
    // Keep the tile unknown: failed transport is not a source count of zero.
    root.innerHTML='<p role="status">The source catalog could not be loaded. Other Evidence topics remain available.</p><button type="button" data-retry>Retry Sources</button>';
    root.querySelector('[data-retry]').onclick=loadIndex;
  }}
  await loadIndex();
  function title(){onTitle(state.detail ? 'Source details' : 'Sources',state.detail ? back : onBack);}
  function show(){title();const top=state.detail ? state.detailScroll : state.scroll;requestAnimationFrame(()=>{scroll.scrollTop=top;});}
  function back(){const top=state.scroll;sequence++;state.detail=null;renderList();requestAnimationFrame(()=>{scroll.scrollTop=top;});}
  function pills(key,values,label){return `<fieldset class="src-pills"><legend>${label}</legend>${['',...values].map(v=>`<button type="button" data-filter="${key}" data-value="${v}" aria-pressed="${String(String(state[key])===String(v))}">${esc(v ? words(v) : 'All')}</button>`).join('')}</fieldset>`;}
  function rowHtml(r){return `<article class="src-row" data-source-id="${esc(r.source_id)}"><button type="button" class="src-open" data-source="${esc(r.source_id)}">${esc(r.citation)}</button><p class="src-meta">${esc(r.date || 'Date not recorded')} · ${esc(r.type || 'Type not recorded')} · tier ${esc(r.tier ?? 'not recorded')} <span class="src-use">${esc(words(r.use))}</span></p>${counts(r)}</article>`;}
  function renderRows(){
    const chosen=selectSources(rows,state);root.querySelector('.src-status').textContent=`${chosen.length} sources · ${Math.min(chosen.length,state.limit)} shown`;
    root.querySelector('.src-rows').innerHTML=chosen.slice(0,state.limit).map(rowHtml).join('') || '<p>No sources match these filters.</p>';
    root.querySelector('[data-more]').hidden=chosen.length<=state.limit;
  }
  function renderList(){
    title();root.innerHTML=`<div class="src-controls"><label>Search citation or author<input type="search" class="src-search" value="${esc(state.query)}"></label><label class="src-all"><input type="checkbox" ${state.all?'checked':''}> All registered sources</label><details class="src-filters" ${state.filtersOpen?'open':''}><summary>Filter and sort${state.type || state.tier || state.use ? ' · filtered' : ''}</summary><p>Default: sources used in this scene. Counts cover each source’s recorded uses.</p>${pills('type',TYPES,'Type')}${pills('tier',[1,2,3,4,5,6],'Source tier')}${pills('use',USES,'Use')}<label>Sort<select class="src-sort">${['claims','entities','date','title'].map(s=>`<option ${state.sort===s?'selected':''}>${s}</option>`).join('')}</select></label><p class="src-key">[DOC] attested · [INF] inferred · [CONJ] reconstructed. Each entity is counted once at its strongest confidence; each distinct claim is counted separately.</p></details></div><p class="src-status" role="status"></p><div class="src-rows"></div><button type="button" data-more>Show 40 more sources</button>`;
    renderRows();
    root.querySelector('.src-filters').ontoggle=e=>{state.filtersOpen=e.target.open;};
    root.querySelector('.src-search').oninput=e=>{state.query=e.target.value;state.limit=40;renderRows();};
    root.querySelector('.src-all input').onchange=e=>{state.all=e.target.checked;state.limit=40;renderRows();};
    root.querySelector('.src-sort').onchange=e=>{state.sort=e.target.value;state.limit=40;renderRows();};
  }
  root.addEventListener('click',async e=>{
    const f=e.target.closest('[data-filter]');if(f){state[f.dataset.filter]=f.dataset.value;state.limit=40;renderList();return;}
    if(e.target.closest('[data-more]')){state.limit+=40;renderRows();return;}
    const source=e.target.closest('[data-source]');if(source){state.scroll=scroll.scrollTop;await openDetail(source.dataset.source);return;}
    const link=e.target.closest('[data-edge]');if(link){const edge=cache.get(state.detail).edges[Number(link.dataset.edge)];const top=scroll.scrollTop;state.detailScroll=top;
      const opened=await onOpen(edge,()=>{state.detailScroll=top;onTitle('Source details',back);requestAnimationFrame(()=>{scroll.scrollTop=top;});});
      if(opened===false){const note=document.createElement('p');note.setAttribute('role','status');note.textContent='No existing card is available for this record in this scene.';link.after(note);}}
  });
  scroll.addEventListener('scroll',()=>{
    if(root.closest('[hidden]'))return;
    if(state.detail){state.detailScroll=scroll.scrollTop;return;}
    if(!root.querySelector('[data-more]'))return;
    state.scroll=scroll.scrollTop;
    if(scroll.scrollTop+scroll.clientHeight>=scroll.scrollHeight-80 && !root.querySelector('[data-more]').hidden){state.limit+=40;renderRows();}
  },{passive:true});
  function edgeHtml(edge,index){
    const label=words(edge.entity_id),locator=typeof edge.locator==='string'?edge.locator:edge.locator?JSON.stringify(edge.locator):'No locator recorded';
    const supported=canOpen(edge) ?? ['structure','person','business','flora','fauna','terrain','exclusion','liberty'].includes(edge.entity_type);
    return `<li>${supported?`<button type="button" data-edge="${index}">${esc(label)}</button>`:`<b>${esc(label)} — decision summary</b>`} ${chip(edge.confidence)}<span>${esc(words(edge.claim))} · ${esc(words(edge.use))} · ${esc(locator)}</span></li>`;
  }
  function edgeList(edges,all){
    const list=document.createElement('ul');list.className='src-edges';let limit=0;
    const more=document.createElement('button');more.type='button';more.textContent='Show more uses';
    const append=()=>{list.insertAdjacentHTML('beforeend',edges.slice(limit,limit+40).map(e=>edgeHtml(e,all.indexOf(e))).join(''));limit+=40;more.hidden=limit>=edges.length;};
    append();more.onclick=append;const box=document.createElement('div');box.append(list,more);return box;
  }
  async function openDetail(id){
    const token=++sequence;state.detail=id;title();scroll.scrollTop=0;
    root.innerHTML='<p role="status">Loading this source’s uses…</p>';
    try {
      if(!cache.has(id)){const res=await fetcher(new URL(`sidecars/1835/sources/${encodeURIComponent(id)}.json`,dataBase));if(!res.ok)throw Error();cache.set(id,await res.json());}
      if(token!==sequence)return;
      const data=cache.get(id),s=data.source,row=rows.find(r=>r.source_id===id);
      const prose=value=>(Array.isArray(value)?value:[value]).filter(Boolean).map(v=>`<li>${esc(v)}</li>`).join('') || '<li>Not recorded.</li>';
      root.innerHTML=`<div class="src-detail" data-source-id="${esc(id)}"><h4>${esc(s.citation)}</h4>${counts(row)}<h4>What it supplies</h4><ul>${prose(s.what_it_supplies)}</ul><h4>What it does not supply</h4><ul>${prose(s.what_it_does_not_supply)}</ul><p>${urlLink(s.url,'Original') || 'No original link on record'} · ${urlLink(s.archived_url,'Archive copy') || 'no archive copy on record'}</p><div class="src-issues"></div><h4>Used for</h4><p>Claims are grouped by kind of record. Links open existing cards; other records remain decision summaries.</p><div class="src-groups"></div></div>`;
      if(row.type==='newspaper'){
        const box=root.querySelector('.src-issues');const groups=issueGroups(data.edges);
        box.innerHTML='<h4>Publication → issues</h4>'+(groups.length?'':'<p>No dated issue locators on record.</p>');
        for(const [date,edges]of groups){const fold=document.createElement('details');fold.innerHTML=`<summary>${date} · ${edges.length} source-use links</summary>`;fold.addEventListener('toggle',()=>{if(fold.open&&!fold.dataset.loaded){fold.dataset.loaded='true';fold.append(edgeList(edges,data.edges));}});box.append(fold);}
      }
      const groupRoot=root.querySelector('.src-groups');
      for(const kind of [...new Set(data.edges.map(e=>e.entity_type))].sort()){
        const edges=data.edges.filter(e=>e.entity_type===kind),fold=document.createElement('details');fold.innerHTML=`<summary>${esc(words(kind))} · ${edges.length} source-use links</summary>`;
        fold.addEventListener('toggle',()=>{if(fold.open&&!fold.dataset.loaded){fold.dataset.loaded='true';fold.append(edgeList(edges,data.edges));}});groupRoot.append(fold);
      }
      if(!data.edges.length)groupRoot.textContent='No recorded uses.';
    }catch{if(token===sequence)root.innerHTML='<p role="status">This source’s details could not be loaded. Use Back to return to the catalog.</p>';}
  }
  return api;
}

/** Navigation is lazy too: opening Sources is the only path that loads this code. */
export function attachSources({api,registry,hud,popup,dataBase,root}) {
  return mountSources({root,dataBase,
    canOpen: edge => edge.entity_type === 'terrain' ? !!terrainCardId(edge,api.ground?.claims || []) : undefined,
    onTitle: (text, back) => { if (api.evidenceHub.topic === 'sources') hud.setTitle(text, back); },
    onBack: () => api.evidenceHub.showHub({focusTile:'sources'}),
      onOpen: async (edge, restore) => {
        const returnToSource = () => {
          hud.setPanel(true); hud.selectTab('evidence'); api.evidenceHub.showTopic('sources'); restore();
        };
        if (edge.entity_type === 'structure') {
          const record = registry.get(edge.entity_id); if (!record) return false;
          hud.setPanel(false); popup.show(record);
          document.getElementById('popup')?.addEventListener('source-card-close', returnToSource, {once:true});
          return true;
        }
        if (edge.entity_type === 'person' || edge.entity_type === 'business') {
          const kind = edge.entity_type === 'person' ? 'people' : 'businesses';
          const opened = await api[kind]?.open(edge.entity_id); if (!opened) return false;
          hud.selectTab(kind);
          document.getElementById(kind === 'people' ? 'people-directory' : 'businesses-directory').addEventListener('source-card-close', returnToSource, {once:true});
          hud.setTitle('Record from this source', () => api[kind].close());
          return true;
        }
        const topic = {terrain:'ground',flora:'plants',fauna:'fauna',exclusion:'exclusions',liberty:'liberties'}[edge.entity_type];
        if (!topic) return false;
        api.evidenceHub.showTopic(topic);
        const mount = document.getElementById(topic);
        const targetId = edge.entity_type === 'terrain' ? terrainCardId(edge,api.ground?.claims || []) : edge.entity_id;
        const entry = [...mount.querySelectorAll('[data-source-entity]')].find(el => el.dataset.sourceEntity === targetId);
        if (entry) { entry.open=true; entry.scrollIntoView({block:'start'}); }
        hud.setTitle('Evidence from this source', returnToSource);
        return true;
      },
  });
}
