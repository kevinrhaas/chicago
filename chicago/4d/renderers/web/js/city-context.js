/**
 * The whole-city 1871 context: portable kit GLB + deterministic placement JSON.
 * Every building is reconstructed. Templates carry no historical identities.
 * Distance changes only the GLB tier, keeping every district and roof silhouette.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

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
export function cityContextCard(r, doc, definition) {
  const id=`context:1871:${r.id}`;
  const libertyIds=typeof doc.liberty==='string' && doc.liberty ? [doc.liberty] : [];
  if (r.isTree) {
    return {id,libertyIds,sidecar:{name:'Reconstructed deciduous tree',phase:null,
      change_note:definition.vegetation_note,
      placement:{symbolic_location:'City context planting',position_confidence:'reconstructed',position_sources:doc.sources ?? [],position_note:'Sparse district planting chosen for the context city; no individual historical tree is identified.'},
      attributes:{height:{value:`${r.h.toFixed(1)} m`,confidence:'reconstructed',sources:[],note:'A context dimension, not a measured historical tree.'}},
      citations:doc.citations ?? definition.citations ?? [],research_note:'Generic deciduous form with early-autumn colour, recorded among the city baseline liberties.'}};
  }
  const district=doc.districts?.[r.district] ?? {};
  const sources=[...new Set([...(definition.sources ?? []),...(district.sources ?? [])])];
  return {id,libertyIds,sidecar:{name:r.t.name,phase:null,
    change_note:`A reconstructed ${r.t.name.toLowerCase()} in ${district.name ?? r.district}. Its footprint, height, facade and exact position are context choices, not an identified historical parcel.`,
    placement:{symbolic_location:district.name ?? r.district,position_confidence:'reconstructed',position_sources:district.sources ?? [],position_note:district.note ?? doc.source_limit ?? 'District-scale reconstruction from the pre-fire city evidence.'},
    attributes:{form:{value:`${r.t.storeys} storeys; ${r.t.roof} roof; ${r.t.material}`,confidence:'reconstructed',sources,note:definition.source_limit},dimensions:{value:`${r.w.toFixed(1)} × ${r.d.toFixed(1)} m; ${r.h.toFixed(1)} m to eaves`,confidence:'reconstructed',sources:[],note:'Bounded dimensions chosen for this context building; no parcel survey is claimed.'}},
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
      const castShadow=layer==='bridges';
      // One atlas/material per portable primitive. Group by attribute layout as
      // well as material and shadow behaviour, retaining every authored channel.
      const layout=Object.entries(object.geometry.attributes).sort(([a],[b])=>a.localeCompare(b))
        .map(([name,a])=>`${name}:${a.itemSize}:${a.normalized}:${a.array.constructor.name}`).join('|');
      const key=`${object.material.uuid}:${castShadow}:${!!object.geometry.index}:${layout}`;
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
  out.census.infrastructureMeshes=infrastructureMeshes.length;
  const templates = new Map([...definition.templates,...(definition.vegetation ?? [])].map(t => [t.id, t]));
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
  out.footprintsNear = (e,n) => collisions.get(`${Math.floor(e/collisionCellM)},${Math.floor(n/collisionCellM)}`) ?? [];
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
  // The city's own sparse planting positions, with generic portable deciduous
  // crowns. No other year's species palette or planting record is imported.
  const treeFields=Object.fromEntries((doc.fields?.trees ?? []).map((key,index)=>[key,index]));
  for (const [index,row] of (doc.trees ?? []).entries()) {
    const read=(key,fallback)=>Array.isArray(row)?(treeFields[key]==null?fallback:row[treeFields[key]]):(row[key] ?? fallback);
    const family=definition.vegetation?.[index%(definition.vegetation?.length || 1)];
    if (!family) continue;
    const e=+read('e'),n=+read('n'),h=+read('height_m'),radius=+read('crown_m',h*.32);
    if (![e,n,h,radius].every(Number.isFinite) || h<=0 || radius<=0) throw Error('1871 context: invalid tree dimensions');
    const t=templates.get(family.id), bearing=(index*137.507)%360;
    const r={row,t,e,n,w:radius*2,d:radius*2,h,base:+read('base_m',terrain.surfaceHeight(e,n)),bearing,
      id:read('id',`tree_${index}`),isTree:true};
    const key=`${Math.floor(e/tileM)},${Math.floor(n/tileM)}`;
    if (!tiles.has(key)) tiles.set(key,{e:(Math.floor(e/tileM)+.5)*tileM,n:(Math.floor(n/tileM)+.5)*tileM,sets:new Map()});
    const tile=tiles.get(key);
    if (!tile.sets.has(t.id)) tile.sets.set(t.id,[]);
    tile.sets.get(t.id).push(r); out.census.trees++;
  }
  const matrix=new THREE.Matrix4(), quaternion=new THREE.Quaternion(), up=new THREE.Vector3(0,1,0);
  const position=new THREE.Vector3(), scale=new THREE.Vector3(), color=new THREE.Color();
  const transformed=new THREE.Vector3(), normalMatrix=new THREE.Matrix3();
  const meshes=[];
  const farMaterial=kit.scene.getObjectByName(definition.templates[0].nodes.far).material.clone();
  farMaterial.vertexColors=true; confidence?.patch(farMaterial); materials.add(farMaterial);
  const place=r=>{
    position.set(r.e,r.base,-r.n); quaternion.setFromAxisAngle(up,-r.bearing*Math.PI/180);
    scale.set(r.w/r.t.width_m,r.h/r.t.eave_m,r.d/r.t.depth_m);
    matrix.compose(position,quaternion,scale); normalMatrix.getNormalMatrix(matrix);
    const tone=Number(value(r.row,'tone',0));
    const jitter=((Math.sin(r.e*12.9898+r.n*78.233)*43758.5453)%1+1)%1;
    color.setRGB(.84+.14*jitter,.84+.12*jitter+.012*(tone%3),.80+.14*jitter+.018*(tone%5));
    if (r.isTree) color.setRGB(.83+.17*jitter,.82+.15*jitter,.72+.16*jitter);
  };
  for (const tile of tiles.values()) {
    tile.nearMeshes=[];
    const farParts=[];
    for (const [name,rows] of tile.sets) {
      const t=templates.get(name);
      {
        const source=kit.scene.getObjectByName(t.nodes.near);
        if (!source?.isMesh) throw Error(`1871 context: missing portable mesh ${t.nodes.near}`);
        const mesh=new THREE.InstancedMesh(source.geometry,source.material,rows.length);
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
      for (const row of rows) farParts.push({geometry:source.geometry,row});
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
      place(part.row);
      const g=part.geometry, a=g.attributes;
      ranges.push({first:index/3,count:g.index.count/3,row:part.row});
      for (let i=0;i<a.position.count;i++) {
        transformed.fromBufferAttribute(a.position,i).applyMatrix4(matrix).toArray(pbuf,(vertex+i)*3);
        transformed.fromBufferAttribute(a.normal,i).applyMatrix3(normalMatrix).normalize().toArray(nbuf,(vertex+i)*3);
        uvbuf[(vertex+i)*2]=a.uv.getX(i); uvbuf[(vertex+i)*2+1]=a.uv.getY(i);
        cbuf.set([Math.round(color.r*255),Math.round(color.g*255),Math.round(color.b*255)],(vertex+i)*3);
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
  out.census.meshes=meshes.length;
  out.census.triangles=meshes.reduce((sum,m)=>sum+m.userData.triangles,0);
  out.census.kitBytes=definition.asset_bytes;
  out.census.templates=definition.templates.length;
  out.census.treeTemplates=definition.vegetation?.length ?? 0;
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
    out.census.visibleTriangles=activeTriangles; out.census.visibleMeshes=activeMeshes;
    out.census.visibleBuildings=activeBuildings; out.census.nearTiles=nearTiles; out.census.farTiles=farTiles;
    out.census.visibleTrees=activeTrees;
  };
  // These trees already draw here; handing stems to a second layer duplicates them.
  out.treeStems=()=>[];
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
    const record=cityContextCard(r,doc,definition);
    return {id:record.id,record,point:hit.point.clone(),distance:hit.distance};
  };
  let disposed=false;
  out.dispose=()=>{
    if (disposed) return; disposed=true;
    for (const mesh of meshes) mesh.dispose?.();
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
    for (const texture of textures) { texture.dispose(); texture.source?.data?.close?.(); }
    depthMaterials.clear(); collisions.clear(); tiles.clear(); floors.clear(); group.clear();
  };
  return out;
}
