/**
 * The whole-city 1871 context: portable kit GLB + deterministic placement JSON.
 * Every building is reconstructed. Templates carry no historical identities.
 * Distance changes only the GLB tier, keeping every district and roof silhouette.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { dressStreetSurfaces, STREET_DECAL_ORDER } from './street-surfaces-1871.js';
import { buildFronts, shopFrames, facadeOf, facadeTint, jitterOf, FAMILY_ROW, FACADE_ROW, FRAME_PAINT } from './city-fronts.js';
import { planSigns, paintSigns, tradeWords } from './city-signs-1871.js';

async function json(url) {
  const response = await fetch(url, { cache: 'no-cache' });
  if (!response.ok) throw Error(`${response.status} ${url}`);
  return response.json();
}

const inside = (x, y, polygon) => {
  let result = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i], b = polygon[j];
    if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) result = !result;
  }
  return result;
};

/** Index the exact flat ribbons emitted with the city's road and walk meshes.
 * Walk offsets and heights are generator data, never reconstructed in the viewer.
 * A lookup examines only the local cell; it never scans the city's street list. */
export function createContextFloorIndex(surfaces = [], cellM = 64) {
  if (!Number.isFinite(cellM) || cellM <= 0) throw Error('1871 context: invalid floor index cell size');
  const cells=new Map();
  for (const surface of surfaces) {
    const {a,b,width_m:width,y}=surface;
    if (!Array.isArray(a) || !Array.isArray(b) || a.length!==2 || b.length!==2
      || ![...a,...b,width,y].every(Number.isFinite) || width<=0) throw Error('1871 context: invalid floor ribbon');
    const de=b[0]-a[0], dn=b[1]-a[1], length=Math.hypot(de,dn);
    if (length<=0) throw Error('1871 context: floor ribbon has no length');
    const ue=de/length, un=dn/length, half=width/2;
    const row={a,ue,un,length,half,y};
    const e0=Math.min(a[0],b[0])-Math.abs(un)*half, e1=Math.max(a[0],b[0])+Math.abs(un)*half;
    const n0=Math.min(a[1],b[1])-Math.abs(ue)*half, n1=Math.max(a[1],b[1])+Math.abs(ue)*half;
    for (let i=Math.floor(e0/cellM);i<=Math.floor(e1/cellM);i++) {
      for (let j=Math.floor(n0/cellM);j<=Math.floor(n1/cellM);j++) {
        const key=`${i},${j}`;
        if (!cells.has(key)) cells.set(key,[]);
        cells.get(key).push(row);
      }
    }
  }
  return {
    heightAt(e,n) {
      let y=null;
      for (const r of cells.get(`${Math.floor(e/cellM)},${Math.floor(n/cellM)}`) ?? []) {
        const de=e-r.a[0],dn=n-r.a[1];
        const along=de*r.ue+dn*r.un, across=-de*r.un+dn*r.ue;
        if (along < -1e-8 || along > r.length+1e-8 || Math.abs(across)>r.half+1e-8) continue;
        if (y===null || r.y>y) y=r.y;
      }
      return y;
    },
    clear() { cells.clear(); },
    get cells() { return cells.size; },
  };
}

/** A generated instance's card, distinct from a compiled structure sidecar.
 * The scene's declared liberty is runtime record metadata, like its instance id;
 * it does not add a field that the structure-sidecar compiler never emits. */
// T-3803: the sign forms in a visitor's words.
const SIGN_WORDS={fascia:'a signboard over the shop',band:'a board on the wall above the shop',frieze:'lettering in the cornice frieze',
  hanging:'a sign hung from an iron bracket',pier:'boards on the door piers',glass:'gilt letters on the window',valance:'lettering on the awning',
  upper:'an upstairs office\u2019s board between the windows'};

export function cityContextCard(r, doc, definition, sign = null) {
  const id=`context:1871:${r.id}`;
  const libertyIds=typeof doc.liberty==='string' && doc.liberty ? [doc.liberty] : [];
  if (r.isTree) {
    return {id,libertyIds:[...libertyIds,'L-1871-grown-context-3760'],sidecar:{name:'Reconstructed deciduous tree',phase:null,
      change_note:definition.vegetation_note,
      placement:{symbolic_location:'City context planting',position_confidence:'reconstructed',position_sources:doc.sources ?? [],position_note:'Sparse district planting chosen for the context city; no individual historical tree is identified.'},
      attributes:{height:{value:`${r.h.toFixed(1)} m`,confidence:'reconstructed',sources:[],note:'A context dimension, not a measured historical tree.'}},
      citations:doc.citations ?? definition.citations ?? [],research_note:'Generic deciduous form, recorded among the city baseline liberties. Its seasonal appearance is a viewing choice; no individual species is identified.'}};
  }
  const district=doc.districts?.[r.district] ?? {};
  const sources=[...new Set([...(definition.sources ?? []),...(district.sources ?? [])])];
  // T-3803: a shop front round the stops carries the firm the 1871 directory lists on it.
  const firmAttrs={};
  if (sign?.firm) {
    const f=sign.firm, at=f.listings.map(l=>`${l.section} directory p. ${l.page}`).join('; ');
    firmAttrs.firm={value:`${f.name} — ${f.trade ?? f.heading ?? 'merchant'}`,confidence:'attested',sources:['edwards_chicago_directory_1871'],
      note:`Listed at ${f.address} in Edwards' 1871 directory (${at}): "${f.listings[0]?.text ?? ''}".`};
    firmAttrs.firm_place={value:`${f.address}, on this block face`,confidence:'inferred',sources:['edwards_chicago_directory_1871','nypl_carbutt_lake_street_east_from_clark_stereo'],
      note:'Placed by the city\u2019s pre-1909 street numbering, read from the directory itself (the Court House square\u2019s gaps, corner listings) and Carbutt\u2019s Lake Street view; its place along the block is its number\u2019s share of the block, not a surveyed lot. The front it is lettered on is a generated front.'};
    if (sign.upper) firmAttrs.upstairs={value:`${sign.upper.name} — ${sign.upper.trade ?? ''} (${sign.upper.address})`,confidence:'attested',sources:['edwards_chicago_directory_1871'],
      note:`An office upstairs, listed at ${sign.upper.address} (${sign.upper.listings.map(l=>`${l.section} directory p. ${l.page}`).join('; ')}): "${sign.upper.listings[0]?.text ?? ''}".`};
    firmAttrs.signs={value:sign.signs.map(x=>SIGN_WORDS[x.kind] ?? x.kind).join('; '),confidence:'reconstructed',sources:[],note:'The sign forms, colours and lettering are reconstructed from the period street views (L-1871-directory-signs).'};
  } else if (sign?.trade) {
    firmAttrs.signs={value:`${sign.signs.map(x=>SIGN_WORDS[x.kind] ?? x.kind).join('; ')}: ${sign.trade}`,confidence:'reconstructed',sources:['edwards_chicago_directory_1871'],note:'No firm the 1871 directory lists falls on this front; it carries a trade the classified directory lists on this street, lettered in a reconstructed form (L-1871-directory-signs).'};
  }
  const libs=Object.keys(firmAttrs).length ? [...libertyIds,'L-1871-directory-signs'] : libertyIds;
  return {id,libertyIds:libs,sidecar:{name:sign?.firm ? `${sign.firm.name}, ${tradeWords(sign.firm.trade).toLowerCase() || 'merchants'}` : r.t.name,phase:null,
    change_note:`A reconstructed ${r.t.name.toLowerCase()} in ${district.name ?? r.district}. Its footprint, height, facade and exact position are context choices, not an identified historical parcel.`,
    placement:{symbolic_location:district.name ?? r.district,position_confidence:'reconstructed',position_sources:district.sources ?? [],position_note:district.note ?? doc.source_limit ?? 'District-scale reconstruction from the pre-fire city evidence.'},
    attributes:{...firmAttrs,form:{value:`${r.t.storeys} storeys; ${r.t.roof} roof; ${r.t.material}`,confidence:'reconstructed',sources,note:definition.source_limit},dimensions:{value:`${r.w.toFixed(1)} × ${r.d.toFixed(1)} m; ${r.h.toFixed(1)} m to eaves`,confidence:'reconstructed',sources:[],note:'Bounded dimensions chosen for this context building; no parcel survey is claimed.'}},
    citations:doc.citations ?? definition.citations ?? [],research_note:'The whole-city context is a liberty recorded in the project’s liberties register. Named, documented structures can replace these forms as research and modelling continue.'}};
}

/**
 * Doc columns are declared in fields.buildings, enums.kit names kit templates.
 * Width/depth/eave scale the template's physical reference dimensions. Front is
 * local -Z; bearing is clockwise from north. Optional base_m is a terrain sample.
 * Infrastructure arrives in world ENU (x=e,y=datum,z=-n), never transformed here.
 */
export async function createCityContext({ doc, dataBase, terrain, confidence = null,
  detail = 'full', footprints = [], problems = [] } = {}) {
  const group = new THREE.Group(); group.name = 'context:1871';
  const out = {
    group, doc, decks: doc.walk_decks ?? [],
    census: { buildings: 0, dropped: 0, trees: 0, triangles: 0, meshes: 0, visibleTriangles: 0, visibleMeshes: 0,
      visibleBuildings: 0, visibleTrees: 0, nearTiles: 0, farTiles: 0, styleCounts: {}, districtCounts: {} },
    pickAt: () => null, treeStems: () => [], setSeason: () => {}, update: () => {}, dispose: () => {},
  };
  const loader = new GLTFLoader();
  const infrastructure = doc.infrastructure_glbs ?? (doc.infrastructure_glb ? [doc.infrastructure_glb] : []);
  let definition, kit, streets;
  try {
    [definition, kit, ...streets] = await Promise.all([
      json(new URL(doc.kit_definition ?? 'context/1871/kit.json', dataBase)),
      loader.loadAsync(new URL(doc.kit_glb ?? 'context/1871/kit.glb', dataBase).href),
      ...infrastructure.map(path => loader.loadAsync(new URL(path, dataBase).href)),
    ]);
  } catch (error) {
    problems.push(`1871 context: ${error.message}`);
    return out;
  }
  // T-3686: the jaunt stops' detail rings. Optional: without them every front
  // keeps its instanced stand-in.
  let rings=null;
  if (doc.detail_rings && definition.fronts) {
    try { rings=await json(new URL(doc.detail_rings,dataBase)); }
    catch (error) { problems.push(`1871 context detail rings: ${error.message}`); }
  }
  const geometries = new Set(), materials = new Set(), textures = new Set();
  // Confidence must discard/dither the sun's depth pass as well as the colour
  // pass. Keep one depth owner per colour material, as buildings.js does: a
  // global shared owner can retain another caster's cached map uniforms.
  const depthMaterials = new Map();
  const depthFor = material => {
    let depth = depthMaterials.get(material);
    if (!depth) {
      depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
      confidence?.patch(depth);
      Object.assign(depth, {
        visible: material.visible, wireframe: material.wireframe,
        // Native getDepthMaterial still chooses PCF/VSM shadow sidedness.
        side: material.shadowSide !== null ? material.shadowSide : material.side,
        map: material.map, alphaMap: material.alphaMap,
        alphaTest: material.alphaToCoverage === true ? 0.5 : material.alphaTest,
        clipShadows: material.clipShadows, clippingPlanes: material.clippingPlanes,
        clipIntersection: material.clipIntersection,
        displacementMap: material.displacementMap,
        displacementScale: material.displacementScale, displacementBias: material.displacementBias,
        wireframeLinewidth: material.wireframeLinewidth, linewidth: material.linewidth,
      });
      depthMaterials.set(material, depth);
      materials.add(depth);
    }
    return depth;
  };
  const remember = root => root.traverse(object => {
    if (!object.isMesh) return;
    if (!object.geometry.getAttribute('_confidence')) throw Error(`1871 context mesh ${object.name} lacks confidence`);
    geometries.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      if (materials.has(material)) continue;
      materials.add(material); confidence?.patch(material);
      for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
    }
  });
  remember(kit.scene);
  const floors=createContextFloorIndex(doc.walk_surfaces ?? []);
  out.floorHeight=(e,n)=>floors.heightAt(e,n);
  out.census.walkSurfaces=doc.walk_surfaces?.length ?? 0;
  out.census.floorCells=floors.cells;
  const infrastructureMeshes=[];
  let walkMaterial=null;
  out.census.infrastructureSourceMeshes=0;
  out.census.infrastructureTriangles=0;
  for (const asset of streets) {
    remember(asset.scene);
    asset.scene.updateMatrixWorld(true);
    const batches=new Map(), sourceGeometries=new Set();
    asset.scene.traverse(object => {
      if (!object.isMesh) return;
      if (Array.isArray(object.material)) throw Error('1871 infrastructure: portable primitives must each have one material');
      const layer=object.userData.layer ?? object.parent?.userData.layer ?? 'infrastructure';
      if (layer==='walks' && !walkMaterial) walkMaterial=object.material;
      const castShadow=layer==='bridges';
      // One atlas/material per portable primitive. Group by attribute layout as
      // well as material and shadow behaviour, retaining every authored channel.
      const layout=Object.entries(object.geometry.attributes).sort(([a],[b])=>a.localeCompare(b))
        .map(([name,a])=>`${name}:${a.itemSize}:${a.normalized}:${a.array.constructor.name}`).join('|');
      // T-3685 follow-up: the street layers (roadways, walks, crossings) draw as ground
      // decals in a fixed order (street-surfaces-1871.js STREET_DECAL_ORDER), so the
      // walks and the crossings, which share the plank material, each get their own batch.
      const decal=STREET_DECAL_ORDER[layer]!=null ? `:${layer}` : '';
      const key=`${object.material.uuid}:${castShadow}:${!!object.geometry.index}:${layout}${decal}`;
      if (!batches.has(key)) batches.set(key,{material:object.material,castShadow,parts:[],layers:new Set(),sources:new Set()});
      const batch=batches.get(key);
      // A GLB node transform is part of the asset. Bake it into this assembled
      // draw buffer once; position, normal, tangent and all other attributes keep
      // their meanings, including the custom confidence and original UVs.
      batch.parts.push(object.geometry.clone().applyMatrix4(object.matrixWorld));
      batch.layers.add(layer);
      for (const source of object.userData.sources ?? object.parent?.userData.sources ?? []) batch.sources.add(source);
      sourceGeometries.add(object.geometry);
      out.census.infrastructureSourceMeshes++;
    });
    for (const batch of batches.values()) {
      const geometry=mergeGeometries(batch.parts,false);
      for (const part of batch.parts) part.dispose();
      if (!geometry) throw Error('1871 infrastructure: incompatible portable geometry attributes');
      geometry.computeBoundingBox(); geometry.computeBoundingSphere(); geometries.add(geometry);
      const mesh=new THREE.Mesh(geometry,batch.material);
      mesh.name=`context:1871:infrastructure:${[...batch.layers].join('+')}:${batch.material.name}`;
      mesh.receiveShadow=true; mesh.castShadow=batch.castShadow;
      if (mesh.castShadow) mesh.customDepthMaterial=depthFor(batch.material);
      mesh.userData={layer:'infrastructure',layers:[...batch.layers],sources:[...batch.sources],confidence:'reconstructed',
        sourceMeshes:batch.parts.length,triangles:(geometry.index?.count ?? geometry.attributes.position.count)/3};
      infrastructureMeshes.push(mesh); group.add(mesh);
      out.census.infrastructureTriangles+=mesh.userData.triangles;
    }
    // The original draw objects are no longer used. Only the merged buffers
    // remain resident; shared materials/textures are released with the layer.
    for (const geometry of sourceGeometries) { geometry.dispose(); geometries.delete(geometry); }
  }
  // T-3685: the streets' painted surfaces (wood block, boulders, dirt, planks)
  // and the raised walks' kerb boards and crossing steps, from the floors.
  const surfacing=dressStreetSurfaces(infrastructureMeshes,{walkSurfaces:doc.walk_surfaces ?? [],
    heights:doc.surface_heights_m ?? {},detail,confidence});
  for (const texture of surfacing.textures) textures.add(texture);
  for (const material of surfacing.materials) materials.add(material);
  for (const mesh of surfacing.meshes) {
    geometries.add(mesh.geometry); infrastructureMeshes.push(mesh); group.add(mesh);
    out.census.infrastructureTriangles+=mesh.userData.triangles;
  }
  out.census.streetSurfaces=surfacing.census;
  out.census.infrastructureMeshes=infrastructureMeshes.length;
  const templates = new Map(definition.templates.map(t => [t.id, t]));
  const columns = Object.fromEntries((doc.fields?.buildings ?? []).map((key, index) => [key, index]));
  const value = (row, key, fallback) => Array.isArray(row) ? (columns[key] == null ? fallback : row[columns[key]]) : (row[key] ?? fallback);
  const enumValue = (kind, v) => typeof v === 'number' ? doc.enums?.[kind]?.[v] : v;
  const tileM = doc.tile_m ?? 640;
  const tiles = new Map(), collisions = new Map();
  const collisionCellM = 64;
  const placed = footprints.filter(f => f.pts?.length >= 3).map(f => ({ ...f,
    e0: Math.min(...f.pts.map(p => p[0])), e1: Math.max(...f.pts.map(p => p[0])),
    n0: Math.min(...f.pts.map(p => p[1])), n1: Math.max(...f.pts.map(p => p[1])),
  }));
  const droppedByStructure = r => placed.some(f => r.e+r.radius >= f.e0 && r.e-r.radius <= f.e1
    && r.n+r.radius >= f.n0 && r.n-r.radius <= f.n1 && (inside(r.e,r.n,f.pts)
      || f.pts.some(([e,n]) => contains(r,e,n,0))));
  function contains(r,e,n,pad=.25) {
    const dx=e-r.e, dz=-(n-r.n);
    const x=r.cos*dx-r.sin*dz, z=r.sin*dx+r.cos*dz;
    return Math.abs(x)<r.w/2+pad && Math.abs(z)<r.d/2+pad;
  }
  for (const row of doc.buildings ?? []) {
    const name = enumValue('kit', value(row, 'kit'));
    const t = templates.get(name);
    if (!t) throw Error(`1871 context: unknown kit ${name}`);
    const e=+value(row,'e'), n=+value(row,'n'), w=+value(row,'width_m'), d=+value(row,'depth_m'), h=+value(row,'eave_m');
    const bearing=+value(row,'bearing_deg',0), radians=-bearing*Math.PI/180;
    if (![e,n,w,d,h,bearing].every(Number.isFinite) || Math.min(w,d,h)<=0) throw Error('1871 context: invalid placement dimensions');
    const base=+value(row,'base_m',terrain.surfaceHeight(e,n));
    const r={row,t,e,n,w,d,h,base,bearing,cos:Math.cos(radians),sin:Math.sin(radians),radius:Math.hypot(w,d)/2,
      id:value(row,'id',`${e},${n}`), district:enumValue('district',value(row,'district','city'))};
    r.pts=[[-w/2,-d/2],[w/2,-d/2],[w/2,d/2],[-w/2,d/2]].map(([x,z])=>[e+r.cos*x+r.sin*z,n+r.sin*x-r.cos*z]);
    if (droppedByStructure(r)) { out.census.dropped++; continue; }
    const key=`${Math.floor(e/tileM)},${Math.floor(n/tileM)}`;
    if (!tiles.has(key)) tiles.set(key,{e:(Math.floor(e/tileM)+.5)*tileM,n:(Math.floor(n/tileM)+.5)*tileM,sets:new Map(),pairs:[]});
    const tile=tiles.get(key);
    if (!tile.sets.has(name)) tile.sets.set(name,[]);
    tile.sets.get(name).push(r);
    // One spatial index serves future walker collision; no per-frame city scan.
    for (let i=Math.floor((e-r.radius)/collisionCellM);i<=Math.floor((e+r.radius)/collisionCellM);i++) {
      for (let j=Math.floor((n-r.radius)/collisionCellM);j<=Math.floor((n+r.radius)/collisionCellM);j++) {
        const cell=`${i},${j}`;
        if (!collisions.has(cell)) collisions.set(cell,[]);
        collisions.get(cell).push(r);
      }
    }
    out.census.buildings++;
    out.census.styleCounts[name]=(out.census.styleCounts[name] ?? 0)+1;
    out.census.districtCounts[r.district]=(out.census.districtCounts[r.district] ?? 0)+1;
  }
  out.containsBuilding = (e,n,pad=.25) => (collisions.get(`${Math.floor(e/collisionCellM)},${Math.floor(n/collisionCellM)}`) ?? []).some(r=>contains(r,e,n,pad));
  // T-3734: what a flight must clear, each building's outline and its roof's top (the kit's
  // eave-to-ridge rise scaled as the building is, and a metre for its chimneys).
  out.skyline = () => {
    const list = [];
    for (const tile of tiles.values()) for (const rows of tile.sets.values()) for (const r of rows) {
      if (r.isTree || !r.pts) continue;
      list.push({ pts:r.pts, top:r.base + r.h * (1 + (Number(r.t?.rise_m) || 0) / Math.max(Number(r.t?.eave_m) || r.h, 0.1)) + 1 });
    }
    return list;
  };
  out.footprintsNear = (e,n) => collisions.get(`${Math.floor(e/collisionCellM)},${Math.floor(n/collisionCellM)}`) ?? [];
  // T-3691 (the owner, 2026-11-21, on The Last Sunday: "we ran into a wall ... the default walk
  // should follow sidewalks etc"): the route planner is handed what the walker meets here, the
  // buildings, and what a walk keeps to, the streets with their plank walks and crossings, for
  // the box it plans over. Without them a route crossed the city's blocks straight, through
  // the buildings the walker then stopped against.
  out.routeFeatures = (box) => {
    const hit = (e0,e1,n0,n1) => e1>=box.e0 && e0<=box.e1 && n1>=box.n0 && n0<=box.n1;
    const seen = new Set(), footprints = [];
    for (let i=Math.floor(box.e0/collisionCellM);i<=Math.floor(box.e1/collisionCellM);i++) {
      for (let j=Math.floor(box.n0/collisionCellM);j<=Math.floor(box.n1/collisionCellM);j++) {
        for (const r of collisions.get(`${i},${j}`) ?? []) {
          if (seen.has(r)) continue;
          seen.add(r);
          if (hit(r.e-r.radius,r.e+r.radius,r.n-r.radius,r.n+r.radius)) footprints.push({ id:r.id, pts:r.pts });
        }
      }
    }
    const line = (a,b) => Array.isArray(a) && Array.isArray(b)
      && hit(Math.min(a[0],b[0]),Math.max(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[1],b[1]));
    const streets = [];
    for (const r of doc.streets ?? []) {
      if (Array.isArray(r) || !line(r.a,r.b) || !(r.width_m>0)) continue;
      streets.push({ id:r.street_id, path:[r.a,r.b], track_width_m:r.width_m, corridor_width_m:r.width_m+2*(r.walk_m ?? 0) });
    }
    const walks = [];
    for (const w of doc.walk_surfaces ?? []) {
      if ((w.kind!=='walk' && w.kind!=='crossing') || !line(w.a,w.b)) continue;
      walks.push({ centreline_local_enu_m:[w.a,w.b], width_m:w.width_m, kind:w.kind==='crossing' ? 'board_crossing' : 'walk' });
    }
    return { footprints, streets, walks };
  };
  out.streetLines = () => {
    const fields=Object.fromEntries((doc.fields?.streets ?? []).map((key,index)=>[key,index]));
    return (doc.street_lines ?? doc.streets ?? []).map(row=>{
      if (!Array.isArray(row)) return { ...row, e0:row.e0 ?? row.a?.[0], n0:row.n0 ?? row.a?.[1],
        e1:row.e1 ?? row.b?.[0], n1:row.n1 ?? row.b?.[1] };
      const get=key=>row[fields[key]];
      return {name:enumValue('street',get('name')) ?? get('name'),e0:get('e0'),n0:get('n0'),e1:get('e1'),n1:get('n1')};
    }).filter(r=>[r.e0,r.n0,r.e1,r.n1].every(Number.isFinite));
  };
  // T-3684: where two named 1871 streets meet, `[e, n, name, name]`, for the
  // where card's "State and Madison streets".
  out.junctions = () => (doc.junctions ?? []).filter(j=>Array.isArray(j) && j.length>=4 && Number.isFinite(j[0]) && Number.isFinite(j[1]));
  // T-3760: retain the city's own planting records, but hand their stems to the
  // shared seasonal renderer. No portable blob crown is drawn over it here.
  const treeStems=[];
  const treeFields=Object.fromEntries((doc.fields?.trees ?? []).map((key,index)=>[key,index]));
  for (const [index,row] of (doc.trees ?? []).entries()) {
    const read=(key,fallback)=>Array.isArray(row)?(treeFields[key]==null?fallback:row[treeFields[key]]):(row[key] ?? fallback);
    const e=+read('e'),n=+read('n'),h=+read('height_m'),radius=+read('crown_m',h*.32);
    if (![e,n,h,radius].every(Number.isFinite) || h<=0 || radius<=0) throw Error('1871 context: invalid tree dimensions');
    const r={row,e,n,w:radius*2,d:radius*2,h,base:+read('base_m',terrain.surfaceHeight(e,n)),
      id:read('id',`tree_${index}`),isTree:true};
    treeStems.push({id:`context:1871:${r.id}`,e,n,y:r.base,h,crownW:radius*2,
      card:()=>cityContextCard(r,doc,definition)});
    out.census.trees++;
  }
  const matrix=new THREE.Matrix4(), quaternion=new THREE.Quaternion(), up=new THREE.Vector3(0,1,0);
  const position=new THREE.Vector3(), scale=new THREE.Vector3(), color=new THREE.Color();
  const transformed=new THREE.Vector3(), normalMatrix=new THREE.Matrix3();
  const meshes=[];
  const tint=[1,1,1];
  const farMaterial=kit.scene.getObjectByName(definition.templates[0].nodes.far).material.clone();
  farMaterial.vertexColors=true; confidence?.patch(farMaterial); materials.add(farMaterial);
  const place=(r,t=r.t)=>{
    position.set(r.e,r.base,-r.n); quaternion.setFromAxisAngle(up,-r.bearing*Math.PI/180);
    scale.set(r.w/t.width_m,r.h/t.eave_m,r.d/t.depth_m);
    matrix.compose(position,quaternion,scale); normalMatrix.getNormalMatrix(matrix);
    const tone=Number(value(r.row,'tone',0));
    const jitter=jitterOf(r.e,r.n);
    color.setRGB(.84+.14*jitter,.84+.12*jitter+.012*(tone%3),.80+.14*jitter+.018*(tone%5));
    // T-3683: a frame house wears its own paint over the pale weatherboard:
    // mostly white, some buff, grey or drab, a few unpainted or barn red.
    // Reconstructed colours (L-1871-city-baseline), not a recorded house.
    if (r.t.material==='timber') { const [pr,pg,pb]=FRAME_PAINT[tone%FRAME_PAINT.length]; color.setRGB(pr*(.95+.05*jitter),pg*(.95+.05*jitter),pb*(.95+.05*jitter)); }
    // T-3686: a row front wears its facade's tint (brick, cream stone, painted
    // brick or painted weatherboard), the same tint its detail wears in a ring.
    const facade=r.isTree?null:value(r.row,'facade',null);
    if (facade) { facadeTint(facade,tone,jitter,tint); color.setRGB(tint[0],tint[1],tint[2]); }
    if (r.isTree) color.setRGB(.83+.17*jitter,.82+.15*jitter,.72+.16*jitter);
  };
  // T-3686: a front whose facade is not its template's family wears the
  // facade's atlas row: the near form moves its wall cells' UVs by whole rows
  // per instance (aFacade = from, to), the far form takes the composite of a
  // shop form of that family with the nearest storey count.
  const facadeRows=r=>{
    const facade=r.isTree?null:value(r.row,'facade',null);
    if (!facade) return null;
    const from=FAMILY_ROW[r.t.material], to=FACADE_ROW[facadeOf(facade,r.t.material)];
    return from==null||to==null||from===to?null:[from,to];
  };
  const shopForms=[...templates.values()].filter(t=>t.shop&&!t.vegetation);
  const farTemplate=r=>{
    const rows=facadeRows(r);
    if (!rows) return r.t;
    const family=rows[1]===FAMILY_ROW.stone?'stone':rows[1]===FAMILY_ROW.brick?'brick':rows[1]===FAMILY_ROW.timber?'timber':null;
    let best=r.t, gap=Infinity;
    for (const t of shopForms) if (t.material===family && Math.abs((t.storeys??1)-(r.t.storeys??1))<gap) { best=t; gap=Math.abs((t.storeys??1)-(r.t.storeys??1)); }
    return best;
  };
  const facadeMaterials=new Map();
  const facadeMaterial=source=>{
    let material=facadeMaterials.get(source);
    if (material) return material;
    material=source.clone();
    material.onBeforeCompile=shader=>{
      shader.vertexShader='attribute vec2 aFacade;\n'+shader.vertexShader.replace('#include <uv_vertex>',`#include <uv_vertex>
  float facadeShift=abs(floor(uv.y*8.0)-aFacade.x)<0.5?(aFacade.y-aFacade.x)*0.125:0.0;
  #ifdef USE_MAP
  vMapUv.y+=facadeShift;
  #endif
  #ifdef USE_NORMALMAP
  vNormalMapUv.y+=facadeShift;
  #endif
  #ifdef USE_AOMAP
  vAoMapUv.y+=facadeShift;
  #endif
  #ifdef USE_METALNESSMAP
  vMetalnessMapUv.y+=facadeShift;
  #endif
  #ifdef USE_ROUGHNESSMAP
  vRoughnessMapUv.y+=facadeShift;
  #endif`);
    };
    material.customProgramCacheKey=()=>'chicago4d-1871-facade-rows';
    confidence?.patch(material); materials.add(material); facadeMaterials.set(source,material);
    return material;
  };
  for (const tile of tiles.values()) {
    tile.nearMeshes=[];
    const farParts=[];
    for (const [name,rows] of tile.sets) {
      const t=templates.get(name);
      {
        const source=kit.scene.getObjectByName(t.nodes.near);
        if (!source?.isMesh) throw Error(`1871 context: missing portable mesh ${t.nodes.near}`);
        const shifts=t.vegetation?null:rows.map(facadeRows);
        let geometry=source.geometry, material=source.material;
        if (shifts?.some(Boolean)) {
          // Share the kit's buffers; only the per-instance rows are this tile's.
          geometry=new THREE.BufferGeometry();
          for (const [key,attribute] of Object.entries(source.geometry.attributes)) geometry.setAttribute(key,attribute);
          geometry.setIndex(source.geometry.index);
          geometry.boundingBox=source.geometry.boundingBox; geometry.boundingSphere=source.geometry.boundingSphere;
          const facadeAttr=new Float32Array(rows.length*2);
          shifts.forEach((shift,index)=>{ if (shift) facadeAttr.set(shift,index*2); });
          geometry.setAttribute('aFacade',new THREE.InstancedBufferAttribute(facadeAttr,2));
          geometries.add(geometry); material=facadeMaterial(source.material);
        }
        const mesh=new THREE.InstancedMesh(geometry,material,rows.length);
        mesh.name=`context:1871:${name}:near`;
        rows.forEach((r,index)=>{
          place(r); mesh.setMatrixAt(index,matrix); mesh.setColorAt(index,color);
        });
        mesh.instanceMatrix.needsUpdate=true; mesh.instanceColor.needsUpdate=true;
        mesh.computeBoundingSphere(); mesh.computeBoundingBox();
        mesh.receiveShadow=true; mesh.castShadow=false; mesh.visible=false;
        mesh.customDepthMaterial=depthFor(source.material);
        mesh.userData.rows=rows; mesh.userData.contextTier='near';
        mesh.userData.triangles=t.triangles.near*rows.length;
        mesh.userData.buildingCount=t.vegetation?0:rows.length;
        mesh.userData.treeCount=t.vegetation?rows.length:0;
        tile.nearMeshes.push(mesh); meshes.push(mesh); group.add(mesh);
      }
      const source=kit.scene.getObjectByName(t.nodes.far);
      if (!source?.isMesh) throw Error(`1871 context: missing portable mesh ${t.nodes.far}`);
      for (const row of rows) {
        const form=t.vegetation?t:farTemplate(row);
        const geometry=form===t?source.geometry:kit.scene.getObjectByName(form.nodes.far)?.geometry ?? source.geometry;
        farParts.push({geometry,row,form});
      }
    }
    // All far forms share one atlas, so assemble the portable geometry into ONE
    // draw per tile. Keep every source normal/UV/confidence and a pick range.
    const vertexCount=farParts.reduce((sum,p)=>sum+p.geometry.attributes.position.count,0);
    const indexCount=farParts.reduce((sum,p)=>sum+p.geometry.index.count,0);
    const pbuf=new Float32Array(vertexCount*3), nbuf=new Float32Array(vertexCount*3);
    const uvbuf=new Float32Array(vertexCount*2), cbuf=new Uint8Array(vertexCount*3);
    const conf=new Float32Array(vertexCount), indices=new Uint32Array(indexCount), ranges=[];
    let vertex=0,index=0;
    for (const part of farParts) {
      place(part.row,part.form);
      // The owner, 2026-11-26 ("distance ones should not look so bad"): a tint over 1 (the
      // pale stone and painted fronts run to 1.08) wrapped round in this byte buffer, so a
      // cream front far off drew cyan or blue. Clamp to the byte, as the near tier's float
      // colour saturates to white.
      const cr=Math.min(255,Math.round(color.r*255)), cg=Math.min(255,Math.round(color.g*255)), cb=Math.min(255,Math.round(color.b*255));
      const g=part.geometry, a=g.attributes;
      ranges.push({first:index/3,count:g.index.count/3,row:part.row});
      for (let i=0;i<a.position.count;i++) {
        transformed.fromBufferAttribute(a.position,i).applyMatrix4(matrix).toArray(pbuf,(vertex+i)*3);
        transformed.fromBufferAttribute(a.normal,i).applyMatrix3(normalMatrix).normalize().toArray(nbuf,(vertex+i)*3);
        uvbuf[(vertex+i)*2]=a.uv.getX(i); uvbuf[(vertex+i)*2+1]=a.uv.getY(i);
        cbuf[(vertex+i)*3]=cr; cbuf[(vertex+i)*3+1]=cg; cbuf[(vertex+i)*3+2]=cb;
        conf[vertex+i]=a._confidence.getX(i);
      }
      for (let i=0;i<g.index.count;i++) indices[index+i]=g.index.getX(i)+vertex;
      vertex+=a.position.count; index+=g.index.count;
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.BufferAttribute(pbuf,3));
    geometry.setAttribute('normal',new THREE.BufferAttribute(nbuf,3));
    geometry.setAttribute('uv',new THREE.BufferAttribute(uvbuf,2));
    geometry.setAttribute('color',new THREE.BufferAttribute(cbuf,3,true));
    geometry.setAttribute('_confidence',new THREE.BufferAttribute(conf,1));
    geometry.setIndex(new THREE.BufferAttribute(indices,1)); geometry.computeBoundingSphere(); geometry.computeBoundingBox();
    geometries.add(geometry);
    const mesh=new THREE.Mesh(geometry,farMaterial);
    mesh.name=`context:1871:tile:${tile.e},${tile.n}:far`; mesh.receiveShadow=true;
    mesh.userData.contextTier='far'; mesh.userData.ranges=ranges;
    mesh.userData.rows=farParts.map(p=>p.row); mesh.userData.triangles=indexCount/3;
    mesh.userData.buildingCount=farParts.filter(p=>!p.row.isTree).length;
    mesh.userData.treeCount=farParts.length-mesh.userData.buildingCount;
    tile.farMesh=mesh; meshes.push(mesh); group.add(mesh);
  }
  // T-3686: a row front stands back of its street's walk by the corridor's
  // margin; that strip is paved in the walk's own planking, front to walk,
  // so the business streets read as built up, not as lawns before shops.
  const apronMeshes=[];
  // T-3685 raises the walks on planks: the apron meets the walk at its own
  // height (just under it, so the two never fight), not a step below it.
  const apronWalkY=+(doc.surface_heights_m?.walk);
  if (walkMaterial) {
    for (const tile of tiles.values()) {
      const p=[], nrm=[], uv=[], idx=[];
      for (const rows of tile.sets.values()) for (const r of rows) {
        const gap=r.isTree?0:+value(r.row,'walk_gap_m',0);
        if (!(gap>.05)) continue;
        const reach=gap+.35, y=Number.isFinite(apronWalkY)?apronWalkY-.005:r.base+.1, base=p.length/3;
        for (const [x,z] of [[-r.w/2,-r.d/2],[r.w/2,-r.d/2],[r.w/2,-r.d/2-reach],[-r.w/2,-r.d/2-reach]]) {
          const e=r.e+r.cos*x+r.sin*z, n=r.n+r.sin*x-r.cos*z;
          p.push(e,y,-n); nrm.push(0,1,0); uv.push(e/2,-n/2);
        }
        // Wind the quad to face up, whichever way the front's bearing turns it.
        const ax=p[base*3+3]-p[base*3], az=p[base*3+5]-p[base*3+2];
        const bx=p[base*3+6]-p[base*3], bz=p[base*3+8]-p[base*3+2];
        if (az*bx-ax*bz>0) idx.push(base,base+1,base+2,base,base+2,base+3);
        else idx.push(base,base+2,base+1,base,base+3,base+2);
      }
      if (!idx.length) continue;
      const geometry=new THREE.BufferGeometry();
      geometry.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
      geometry.setAttribute('normal',new THREE.Float32BufferAttribute(nrm,3));
      geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
      geometry.setAttribute('_confidence',new THREE.Float32BufferAttribute(new Float32Array(p.length/3).fill(1),1));
      geometry.setIndex(idx); geometry.computeBoundingSphere(); geometry.computeBoundingBox();
      geometries.add(geometry);
      const mesh=new THREE.Mesh(geometry,walkMaterial);
      mesh.name=`context:1871:tile:${tile.e},${tile.n}:aprons`; mesh.receiveShadow=true;
      // The walk's planking draws as a ground decal after everything opaque; its apron with it.
      mesh.renderOrder=STREET_DECAL_ORDER.walks;
      mesh.userData={layer:'infrastructure',confidence:'reconstructed',triangles:idx.length/3};
      apronMeshes.push(mesh); group.add(mesh);
    }
  }
  out.census.apronMeshes=apronMeshes.length;
  out.census.apronTriangles=apronMeshes.reduce((sum,m)=>sum+m.userData.triangles,0);
  // T-3686: full detail within the jaunt stops' rings (city-fronts.js).
  let fronts=null;
  const frontNode=definition.fronts && kit.scene.getObjectByName(definition.fronts.node);
  if (rings && frontNode) {
    const byName=new Map();
    frontNode.traverse(object=>{ if (object.isMesh) for (const m of [object.material].flat()) byName.set(m.name,m); });
    const frontMaterials=new Map();
    for (const [key,entry] of Object.entries(definition.fronts.materials)) {
      const material=byName.get(entry.material);
      if (!material) continue;
      material.vertexColors=true; material.needsUpdate=true;
      frontMaterials.set(key,material);
    }
    const rows=[];
    for (const tile of tiles.values()) for (const set of tile.sets.values()) for (const r of set) if (!r.isTree) rows.push(r);
    // T-3803: the firms of 1871 on the shops round the stops, lettered at runtime.
    let signs=null;
    if (rings.directory_fronts) {
      try {
        const directory=await json(new URL(rings.directory_fronts,new URL(doc.detail_rings,dataBase)));
        const frames=shopFrames({rows,rings,detail,value});
        const cellOf=new Map(frames.map(f=>[f.r.id,f.cell]));
        const planned=planSigns(directory,frames,detail);
        const painted=await paintSigns(planned.plans,id=>cellOf.get(id),detail,problems);
        (painted.textures ?? []).forEach((map,k)=>{
          const material=new THREE.MeshStandardMaterial({map,alphaTest:.5,roughness:.85,metalness:0,name:`context-1871-signs-${k}`});
          confidence?.patch(material); materials.add(material); textures.add(map);
          frontMaterials.set(`sign${k}`,material);
        });
        signs={plans:planned.plans};
        out.census.signs={...planned.census,pages:painted.pages,density:painted.density,textureMiB:+((painted.bytes ?? 0)/1048576).toFixed(1)};
      } catch (error) { problems.push(`1871 shop signs: ${error.message}`); }
    }
    fronts=buildFronts({rows,rings,fronts:definition.fronts,materials:frontMaterials,detail,value,signs});
    for (const mesh of fronts.meshes) { geometries.add(mesh.geometry); group.add(mesh); }
    out.census.detail={...fronts.census,showM:fronts.showM};
  }
  out.census.meshes=meshes.length;
  out.census.triangles=meshes.reduce((sum,m)=>sum+m.userData.triangles,0);
  out.census.kitBytes=definition.asset_bytes;
  out.census.templates=definition.templates.length;
  out.census.treeTemplates=0;
  out.census.treeRepresentation='shared-grown-seasonal';
  out.census.handedOffTrees=treeStems.length;
  out.census.tiles=tiles.size;
  const frustum=new THREE.Frustum(), viewProjection=new THREE.Matrix4();
  out.setDetail=level=>{ if (['full','balanced','light'].includes(level)) detail=level; };
  out.update=(_dt,camera)=>{
    if (!camera) return;
    camera.updateMatrixWorld();
    frustum.setFromProjectionMatrix(viewProjection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));
    const nearReach=detail==='light'?430:detail==='balanced'?650:850;
    let activeTriangles=0, activeMeshes=0, activeBuildings=0, activeTrees=0, nearTiles=0, farTiles=0;
    for (const tile of tiles.values()) {
      const distance=Math.hypot(tile.e-camera.position.x,-tile.n-camera.position.z,camera.position.y);
      const near=distance<nearReach+tileM*.35;
      let inView=false;
      tile.farMesh.visible=!near;
      for (const mesh of tile.nearMeshes) {
        mesh.visible=near; mesh.castShadow=near && detail!=='light' && distance<580;
      }
      for (const active of near?tile.nearMeshes:[tile.farMesh]) {
        if (frustum.intersectsObject(active)) {
          inView=true; activeTriangles+=active.userData.triangles; activeMeshes++;
          activeBuildings+=active.userData.buildingCount; activeTrees+=active.userData.treeCount;
        }
      }
      if (inView) { if (near) nearTiles++; else farTiles++; }
    }
    let detailTriangles=0, detailMeshes=0;
    if (fronts) {
      for (const cell of fronts.cells) {
        const show=Math.hypot(cell.e-camera.position.x,-cell.n-camera.position.z)<fronts.showM && camera.position.y<fronts.showM;
        for (const mesh of cell.meshes) {
          mesh.visible=show;
          if (show && frustum.intersectsObject(mesh)) { detailTriangles+=mesh.userData.triangles; detailMeshes++; }
        }
      }
      activeTriangles+=detailTriangles; activeMeshes+=detailMeshes;
    }
    out.census.detailVisibleTriangles=detailTriangles; out.census.detailVisibleMeshes=detailMeshes;
    out.census.visibleTriangles=activeTriangles; out.census.visibleMeshes=activeMeshes;
    out.census.visibleBuildings=activeBuildings; out.census.nearTiles=nearTiles; out.census.farTiles=farTiles;
    out.census.visibleTrees=activeTrees;
  };
  out.treeStems=()=>treeStems;
  const raycaster=new THREE.Raycaster();
  out.pickAt=(ndc,camera)=>{
    if (!camera || !group.visible || confidence?.hidden?.reconstructed) return null;
    raycaster.setFromCamera(ndc ?? new THREE.Vector2(),camera);
    raycaster.far=Math.max(600,camera.position.y*5);
    const hit=raycaster.intersectObjects(meshes.filter(m=>m.visible),false)[0];
    if (!hit) return null;
    const r=hit.instanceId!=null?hit.object.userData.rows[hit.instanceId]
      :hit.object.userData.ranges.find(range=>hit.faceIndex>=range.first&&hit.faceIndex<range.first+range.count)?.row;
    if (!r) return null;
    const record=cityContextCard(r,doc,definition,fronts?.signPlans?.get(r.id) ?? null);
    return {id:record.id,record,point:hit.point.clone(),distance:hit.distance};
  };
  let disposed=false;
  out.dispose=()=>{
    if (disposed) return; disposed=true;
    for (const mesh of meshes) mesh.dispose?.();
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
    for (const texture of textures) { texture.dispose(); texture.source?.data?.close?.(); }
    depthMaterials.clear(); collisions.clear(); tiles.clear(); floors.clear(); treeStems.length=0; group.clear();
  };
  return out;
}
