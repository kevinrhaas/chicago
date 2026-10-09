import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { cheapenGlass } from './glass.js';
const $=id=>document.getElementById(id), base=new URL('../../',import.meta.url), dataURL=new URL('data/comparisons/glessner/',base);
const loadJSON=async name=>{const r=await fetch(new URL(name,dataURL));if(!r.ok)throw Error(`${name}: HTTP ${r.status}`);return r.json()};
const referenceURL=path=>{const r=globalThis.ROOT_SERVED;return new URL(r?.dirs.some(d=>path.startsWith(d))?r.base+path:`prairie-1904/${path}`,base)};
const [data,report]=await Promise.all([loadJSON('observations.json'),loadJSON('report.json')]).catch(e=>{$('loading').textContent=`Unable to load the comparison data: ${e.message}`;throw e});
const scene=new THREE.Scene();scene.background=new THREE.Color('#d9ddd7');scene.add(new THREE.HemisphereLight(0xf4f4ee,0x555e51,2.3));const key=new THREE.DirectionalLight(0xffffff,2.4);key.position.set(35,65,45);scene.add(key);
const renderer=new THREE.WebGLRenderer({canvas:$('model'),antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;
const camera=new THREE.PerspectiveCamera(),loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);let object,active,serial=0;
const gltfVector=p=>new THREE.Vector3(p[0],p[2],-p[1]);
function setCamera(c){
 const [r,u,f]=c.basis_right_up_forward.map(gltfVector);camera.position.copy(gltfVector(c.position_m));camera.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(r,u,f.negate()));camera.updateMatrixWorld(true);
 const [w,h]=c.image_size,[cx,cy]=c.principal_px,n=c.near;camera.projectionMatrix.makePerspective(-cx/c.focal_px*n,(w-cx)/c.focal_px*n,cy/c.focal_px*n,-(h-cy)/c.focal_px*n,n,c.far);camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
}
function draw(){if(!active)return;const el=$('model-frame'),w=el.clientWidth,h=w*active.view.image_size[1]/active.view.image_size[0];renderer.setSize(w,h,false);setCamera(active.result.camera);renderer.render(scene,camera)}
const el=(tag,text)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;return n};
function overlay(host,points,model=false){host.replaceChildren();const [w,h]=active.view.image_size;host.setAttribute('viewBox',`0 0 ${w} ${h}`);if(!$('markers').checked)return;
 const size=w/200;
 for(const [i,p] of points.entries()){
  const [x,y]=p.predicted_px,[ox,oy]=p.observed_px,color=p.target_met?'#146a50':'#bb3c2b';
  const svg=(tag,attrs)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);host.append(n);return n};
  if(!model){svg('line',{x1:ox,y1:oy,x2:x,y2:y,stroke:color,'stroke-width':w/700});svg('circle',{cx:ox,cy:oy,r:size,fill:'none',stroke:'#147ca1','stroke-width':w/700});}
  svg('path',{d:`M${x-size},${y}h${2*size}M${x},${y-size}v${2*size}`,stroke:color,'stroke-width':w/650});
  const t=svg('text',{x:(model?x:ox)+size,y:(model?y:oy)-size,fill:'#111',stroke:'#fff','stroke-width':w/1300,'paint-order':'stroke','font-size':w/55,'font-family':'system-ui'});t.textContent=i+1;
 }
}
function select(id){
 const view=data.views.find(v=>v.id===id)||data.views[0],result=report.views.find(v=>v.id===view.id);active={view,result};$('view-select').value=view.id;history.replaceState(null,'',`#${view.id}`);
 $('view-title').textContent=view.title;$('date-rights').textContent=`Reference: ${view.source_date} · ${view.rights}`;$('limits').textContent=view.limitations;
 const source=new URL(`prairie-1904/viewer/#image=${view.library_id}`,base);$('source-link').href=source;$('catalog-link').href=view.catalog_url;
 const clear=['public domain','no known restrictions'].includes(view.rights),img=$('reference');img.hidden=true;img.removeAttribute('src');$('reference-note').textContent=clear?'Loading reference…':'This reference is not republished here. Open it in the research library or at its holder; the numerical source picks remain visible.';
 if(clear){img.alt=view.title;img.onload=()=>{if(active.view.id===view.id){img.hidden=false;$('reference-note').textContent=''}};img.onerror=()=>{$('reference-note').textContent='The reference image is temporarily unavailable. Its source links and measurements remain available.'};img.referrerPolicy='no-referrer';img.src=view.local_image?referenceURL(view.local_image):view.source_image_url;}
 for(const id of ['photo-frame','model-frame'])$(id).style.aspectRatio=view.image_size.join(' / ');
 $('summary').textContent=`${result.status}. ${result.fit_controls} camera controls; ${result.check_points} withheld checks. Control RMS ${result.fit_rms_px.toFixed(1)} px; check RMS ${result.check_rms_px.toFixed(1)} px. Projected width ${result.projected_width_px.toFixed(0)} px; observed span ${result.observed_span_px.toFixed(0)} px. Nominal lens ${view.nominal_lens_mm} mm on ${view.sensor_width_mm} mm width; height constrained to ${view.camera_height_assumption_m.join('–')} m. ${result.pose_bounds_active.length?'Fit touches assumed bounds: '+result.pose_bounds_active.join(', ')+'. Treat pose as uncertain.':'No pose bound is active.'}`;
 $('landmarks').replaceChildren();result.landmarks.forEach((p,i)=>{const row=el('tr');row.className=p.target_met?'pass':'exception';[`${i+1}. ${p.id}`,p.role,p.residual_px.toFixed(1),(100*p.fraction_projected_width).toFixed(2)+'%',(100*p.fraction_observed_span).toFixed(2)+'%',p.sensitivity_px.toFixed(1),p.association_distance_m.toFixed(3)+(p.association_warning?' — review':''),view.landmarks[i].tier_1904].forEach(x=>row.append(el('td',x)));$('landmarks').append(row)});
 overlay($('photo-overlay'),result.landmarks);overlay($('model-overlay'),result.landmarks,true);draw();window.__glessnerBaseline.active=view.id;
}
async function loadModel(detail){const my=++serial;$('loading').textContent=`Loading ${detail} model…`;const name=`glessner_house__as_built_1887${detail==='light'?'.light':''}.glb`,url=new URL(`data/gltf/${name}`,base);const r=await fetch(url);if(!r.ok)throw Error(`Model: HTTP ${r.status}`);const bytes=await r.arrayBuffer(),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');const expected=data.assets[`assets/web/${name}`].sha256;
 const gltf=await loader.parseAsync(bytes,new URL('data/gltf/',base).href);if(my!==serial){dispose(gltf.scene);return}if(object){scene.remove(object);dispose(object)}object=gltf.scene;object.traverse(o=>{if(o.material)o.material=Array.isArray(o.material)?o.material.map(m=>cheapenGlass(m,'dark')):cheapenGlass(o.material,'dark')});scene.add(object);draw();
 $('asset').textContent=`Loaded ${detail}: SHA-256 ${digest}. Frozen baseline ${expected}. ${digest===expected?'Exact baseline bytes.':'Asset has changed: frozen cameras remain useful, but the recorded residuals describe the earlier baseline only. Re-measure the candidate.'}`;$('loading').textContent=digest===expected?'Ready · baseline model verified':'Different model loaded — the cameras and displayed residuals belong to the frozen baseline. Measure this candidate before judging improvements.';window.__glessnerBaseline.ready=true;window.__glessnerBaseline.detail=detail;window.__glessnerBaseline.hashMatches=digest===expected;
}
function dispose(root){const materials=new Set(),textures=new Set();root.traverse(o=>{o.geometry?.dispose();for(const m of(Array.isArray(o.material)?o.material:[o.material]))if(m){materials.add(m);for(const v of Object.values(m))if(v?.isTexture)textures.add(v)}});for(const t of textures)t.dispose();for(const m of materials)m.dispose()}
window.__glessnerBaseline={ready:false,data,report,select,loadModel,project:p=>{const q=gltfVector(p).project(camera);return[(q.x+1)*active.view.image_size[0]/2,(1-q.y)*active.view.image_size[1]/2]}};
for(const v of data.views){const o=el('option',v.title);o.value=v.id;$('view-select').append(o)}
$('metric').append(el('p',`${data.frame.origin}; ${data.frame.axes}. ${data.frame.from_building_ft}. North-grade/door transfer uncertainty: ±${data.frame.datum_uncertainty_ft} ft.`));for(const d of data.dimensions)$('metric').append(el('p',`${d.name}: ${d.value_ft} ft — ${d.locator}. ${d.tier}; ${d.carryback}.`));
for(const p of data.phase_rules)$('phases').append(el('p',`${p.phase} · ${p.status}. ${p.note}`));for(const v of data.unmatched_views)$('missing').append(el('p',`${v.title}: ${v.reason} Repeatable stand: ${v.position_m.join(', ')} m; target ${v.target_m.join(', ')} m; lens ${v.lens_mm} mm. No residual or matched-view count is invented.`));
$('view-select').addEventListener('change',()=>select($('view-select').value));$('reset').addEventListener('click',()=>select(active.view.id));$('markers').addEventListener('change',()=>select(active.view.id));$('detail').addEventListener('change',()=>loadModel($('detail').value).catch(error));new ResizeObserver(draw).observe($('model-frame'));
function error(e){$('loading').textContent=`Unable to complete model load: ${e.message}`;window.__glessnerBaseline.error=e.message;console.error(e)}
$('detail').value=innerWidth>700?'full':'light';select(location.hash.slice(1));loadModel($('detail').value).catch(error);
