let model;
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
function annualMaps(year){return model.maps.filter(m=>Number(m.reference_year)===year);}
function annualEvents(year){return model.events.filter(e=>Number(String(e.effective_start).slice(0,4))<=year&&Number(String(e.effective_end).slice(0,4))>=year);}
function render(){
 const year=Number($('year').value); $('yearOutput').textContent=year;
 const maps=annualMaps(year), select=$('mapVariant'), prior=select.value;
 select.innerHTML=maps.map(m=>`<option value="${esc(m.map_id)}">${esc(m.title)}</option>`).join('');
 select.value=maps.some(m=>m.map_id===prior)?prior:(maps[0]?.map_id||'');
 const map=maps.find(m=>m.map_id===select.value)||maps[0];
 if(map){$('mapTitle').textContent=map.title;$('mapYear').textContent=map.reference_year;$('mapImage').src=`../${map.local_image_path}`;$('mapImage').alt=`${map.title}, ${map.reference_year}`;$('mapLink').href=map.source_url;$('mapMeta').textContent=`${map.map_type.replaceAll('_',' ')} · ${map.credit_line} · ${map.rights_statement.replaceAll('_',' ')}`;$('mapNote').textContent=map.notes;}
 const events=annualEvents(year); $('eventName').textContent=events.map(e=>e.feature_or_name).join(' · ')||'No event cataloged'; $('eventNote').textContent=events.map(e=>e.description).join(' ');
 const city=model.cityModel.find(item=>Number(item.model_year)===year); $('modelName').textContent=city?city.geometry_status.replaceAll('_',' '):'No model row'; $('modelNote').textContent=city?`${city.city_extent_state} ${city.modeling_instruction}`:'';
 const q=$('search').value.toLowerCase().trim(); let rows=model.buildings.filter(r=>Number(r.research_year)===year); $('recordCount').textContent=rows.length.toLocaleString();
 if(q) rows=rows.filter(r=>[r.canonical_name,r.address_historical,r.architect_or_builder,r.building_type,r.construction_or_event_type].join(' ').toLowerCase().includes(q));
 rows.sort((a,b)=>a.canonical_name.localeCompare(b.canonical_name));
 $('buildingRows').innerHTML=rows.map(r=>`<tr><td><strong>${esc(r.canonical_name)}</strong>${r.needs_review==='true'?' <small>⚑ review</small>':''}</td><td>${esc([r.year_started,r.year_completed,r.year_opened].filter(Boolean).join(' → ')||'—')}</td><td>${esc((r.construction_or_event_type||'—').replaceAll('_',' '))}</td><td>${esc([r.building_type,r.structural_system].filter(Boolean).join(' · ')||'—')}</td><td>${esc(r.address_historical||'—')}</td><td>${esc(r.architect_or_builder||'—')}</td><td>${esc(r.predecessor_or_rebuild_of||'—')}</td><td>${esc(r.confidence)}</td></tr>`).join('');
}
fetch('data.json').then(r=>r.json()).then(data=>{model=data;$('year').addEventListener('input',render);$('search').addEventListener('input',render);$('mapVariant').addEventListener('change',render);document.querySelectorAll('[data-year]').forEach(b=>b.addEventListener('click',()=>{$('year').value=b.dataset.year;render();}));render();}).catch(error=>document.body.insertAdjacentHTML('beforeend',`<p>Could not load viewer data: ${esc(error.message)}</p>`));
