/** T-2227: conservative rejection behind the buildings' opaque surfaces.
 * A whole instance box must fit INSIDE ONE projected triangle, with a two-pixel
 * inset, and BEHIND its plane. Target boxes crossing the near plane fail open.
 * This does not approximate a wall, combine coverage across openings, change
 * instance visibility, or affect shadow-camera draws / raycast geometry.
 */
import * as THREE from 'three';

const MAX_TRIANGLES = 64;
const DEPTH_GAP_M = 0.02;

// Rank by coverage inside the viewport. Large off-screen walls must not consume
// the bounded candidate list. Clipping only ranks; the original inset triangle
// still supplies the complete containment proof.
function visibleArea(points, width, height) {
  let polygon=points;
  for (const [axis,sign,limit] of [[0,1,width/2],[0,-1,width/2],[1,1,height/2],[1,-1,height/2]]) {
    const clipped=[];
    for(let i=0;i<polygon.length;i++) {
      const a=polygon[i],b=polygon[(i+1)%polygon.length];
      const da=limit-sign*a[axis],db=limit-sign*b[axis];
      if(da>=0)clipped.push(a);
      if((da>=0)!==(db>=0)) {
        const t=da/(da-db);
        clipped.push([a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])]);
      }
    }
    polygon=clipped;
    if(polygon.length<3)return 0;
  }
  return Math.abs(polygon.reduce((sum,p,i)=>{
    const q=polygon[(i+1)%polygon.length];return sum+p[0]*q[1]-p[1]*q[0];
  },0));
}

/** `confidenceAt(vertex)` reads a channel stored elsewhere than a float
 *  `_confidence` attribute — the structures batch packs it (T-2574). */
export function backingTriangles(geometry, matrix, side = THREE.DoubleSide, confidenceAt = null) {
  const p = geometry.attributes.position, ix = geometry.index;
  const attr=geometry.getAttribute('_confidence');
  const confidence=confidenceAt ? { getX: confidenceAt } : attr;
  if (!p?.array || (ix && !ix.array)) return [];
  const result = [], count = ix?.count ?? p.count;
  for (let i = 0; i < count; i += 3) {
    const points = [0, 1, 2].map(j => new THREE.Vector3()
      .fromBufferAttribute(p, ix ? ix.getX(i + j) : i + j).applyMatrix4(matrix));
    const normal = new THREE.Vector3().subVectors(points[1], points[0])
      .cross(new THREE.Vector3().subVectors(points[2], points[0]));
    const area = normal.length() / 2;
    const values=confidence ? [0,1,2].map(j=>confidence.getX(ix?ix.getX(i+j):i+j)) : null;
    const confidenceRange=values ? [Math.min(...values),Math.max(...values)] : null;
    if (area >= 0.5) result.push({ points, normal, area, side, confidenceRange });
  }
  return result;
}

function clipPlane(points, distance) {
  const result=[];
  for(let i=0;i<points.length;i++) {
    const a=points[i],b=points[(i+1)%points.length],da=distance(a),db=distance(b);
    if(da>=0)result.push(a);
    if((da>=0)!==(db>=0))result.push(a.clone().lerp(b,da/(da-db)));
  }
  return result;
}

/** Clip the actual triangle to the camera's near/far planes before projection.
 * The resulting convex polygon never adds coverage across an aperture. */
// T-2806: a phone ran this for every backing triangle on every frame the eye moved,
// and most triangles are turned away (back-facing, too small, off the screen) after
// allocating their clip vectors, polygons and closures: ~6 MB of garbage a frame
// while walking. Those rejections are now decided on scratch storage, by the same
// arithmetic in the same order, before anything is allocated; a triangle that
// passes them goes through the original path below unchanged.
const scratchEye = new THREE.Vector3(), scratchTo = new THREE.Vector3();
const scratchClip = [new THREE.Vector4(), new THREE.Vector4(), new THREE.Vector4()];
const scratchXY = new Float64Array(6);
const vpScratch = new THREE.Matrix4();

/** True when the original path below would certainly `continue` for this triangle. */
function rejectedEarly(points, vp, width, height) {
  for (let k = 0; k < 3; k++) {
    const c = scratchClip[k].set(points[k].x, points[k].y, points[k].z, 1).applyMatrix4(vp);
    // Clipped by the near or far plane: only the full path knows the polygon.
    if (!(c.z + c.w >= 0 && c.w - c.z >= 0)) return false;
  }
  for (let k = 0; k < 3; k++) {
    const c = scratchClip[k];
    if (!Number.isFinite(c.w) || c.w <= 0) return true;
    scratchXY[k * 2] = c.x / c.w * width / 2; scratchXY[k * 2 + 1] = c.y / c.w * height / 2;
  }
  let signedArea = 0;
  for (let k = 0; k < 3; k++) {
    const j = (k + 1) % 3;
    signedArea = signedArea + scratchXY[k * 2] * scratchXY[j * 2 + 1] - scratchXY[k * 2 + 1] * scratchXY[j * 2];
  }
  if (Math.abs(signedArea) < 16) return true;
  // Wholly past one edge of the viewport: visibleArea() clips it to nothing.
  for (const [axis, sign] of VIEW_EDGES) {
    const limit = axis ? height / 2 : width / 2;
    let out = true;
    for (let k = 0; k < 3 && out; k++) if (limit - sign * scratchXY[k * 2 + axis] >= 0) out = false;
    if (out) return true;
  }
  return false;
}
const VIEW_EDGES = [[0, 1], [0, -1], [1, 1], [1, -1]];

export function projectOccluders(triangles, camera, width, height) {
  if (!camera.isPerspectiveCamera || camera.reversedDepth
      || camera.coordinateSystem !== THREE.WebGLCoordinateSystem || width <= 0 || height <= 0) return [];
  const vp = vpScratch.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
  const eye = scratchEye.setFromMatrixPosition(camera.matrixWorld);
  const result = [];
  for (const triangle of triangles) {
    // This bound is for Chicago's metre frame, not arbitrary world scales.
    const tp = triangle.points;
    let far = false;
    for (let k = 0; k < tp.length && !far; k++) far = Math.max(Math.abs(tp[k].x),Math.abs(tp[k].y),Math.abs(tp[k].z))>8192;
    if (far) continue;
    const facing = triangle.normal.dot(scratchTo.subVectors(eye, tp[0]));
    if (triangle.side === THREE.FrontSide && facing <= 0) continue;
    if (triangle.side === THREE.BackSide && facing >= 0) continue;
    if (tp.length === 3 && rejectedEarly(tp, vp, width, height)) continue;
    let clip = triangle.points.map(p => new THREE.Vector4(p.x, p.y, p.z, 1).applyMatrix4(vp));
    clip=clipPlane(clip,p=>p.z+p.w);
    clip=clipPlane(clip,p=>p.w-p.z);
    if(clip.length<3 || clip.some(p=>!Number.isFinite(p.w)||p.w<=0))continue;
    // Include a 2 cm world-space rounding allowance on BOTH projected surfaces,
    // plus two raster pixels. This deliberately grows near the camera.
    const focal=Math.max(Math.abs(camera.projectionMatrix.elements[0])*width,
      Math.abs(camera.projectionMatrix.elements[5])*height)/2;
    const margin=2+2*DEPTH_GAP_M*focal/Math.min(...clip.map(p=>p.w));
    const points = clip.map(p => [p.x / p.w * width / 2, p.y / p.w * height / 2]);
    const signedArea = points.reduce((sum,p,i)=>{
      const q=points[(i+1)%points.length];return sum+p[0]*q[1]-p[1]*q[0];
    },0);
    if (Math.abs(signedArea) < 16) continue;
    const area=visibleArea(points,width,height);
    if(area<16)continue;
    if (signedArea < 0) points.reverse();
    const edges = points.map((p, i) => {
      const q = points[(i+1)%points.length], dx=q[0]-p[0], dy=q[1]-p[1];
      return { x:p[0], y:p[1], dx, dy, inset:margin*Math.hypot(dx,dy) };
    });
    // A slanting wall's farthest vertex can be much farther away than the part
    // covering an instance. Test the actual plane instead: the entire world box
    // must lie on the opposite side from the eye, with a metric safety gap.
    const normal=triangle.normal.clone().normalize().multiplyScalar(facing>=0?1:-1);
    result.push({ edges, normal, constant:-normal.dot(triangle.points[0]), area,
      minX:Math.min(...points.map(p=>p[0])),maxX:Math.max(...points.map(p=>p[0])),
      minY:Math.min(...points.map(p=>p[1])),maxY:Math.max(...points.map(p=>p[1])) });
  }
  return result.sort((a,b)=>b.area-a.area).slice(0,MAX_TRIANGLES);
}

// The callback visits tens of thousands of boxes per frame. Reuse double-
// precision scratch storage instead of allocating eight vectors and point
// arrays for every instance. These synchronous tests never retain the points.
const projectedBox = new Float64Array(16);
export function boxOccluded(box, vp, occluders, width, height) {
  if (box.isEmpty() || !occluders.length
      || Math.abs(box.min.x)>8192 || Math.abs(box.min.y)>8192 || Math.abs(box.min.z)>8192
      || Math.abs(box.max.x)>8192 || Math.abs(box.max.y)>8192 || Math.abs(box.max.z)>8192) return false;
  const m=vp.elements;
  let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
  for(let i=0;i<8;i++) {
    const x=i&4?box.max.x:box.min.x,y=i&2?box.max.y:box.min.y,z=i&1?box.max.z:box.min.z;
    // Same operation order as Vector4.applyMatrix4; preserve its exact boundary decisions.
    const w=m[3]*x+m[7]*y+m[11]*z+m[15],depth=m[2]*x+m[6]*y+m[10]*z+m[14];
    if (!Number.isFinite(w) || w<=0 || depth<=-w) return false;
    const px=(m[0]*x+m[4]*y+m[8]*z+m[12])/w*width/2;
    const py=(m[1]*x+m[5]*y+m[9]*z+m[13])/w*height/2;
    if (!Number.isFinite(px)||!Number.isFinite(py)) return false;
    projectedBox[i*2]=px;projectedBox[i*2+1]=py;
    minX=Math.min(minX,px);maxX=Math.max(maxX,px);minY=Math.min(minY,py);maxY=Math.max(maxY,py);
  }
  // Fail open at the viewport boundary. Real fixed-camera comparisons exposed
  // small edge-pixel contributions from clipped distant geometry; retaining
  // every boundary-crossing box avoids relying on that rasterization case.
  if(minX<=-width/2+2 || maxX>=width/2-2 || minY<=-height/2+2 || maxY>=height/2-2)return false;
  for(const o of occluders) {
    if (!(minX>o.minX && maxX<o.maxX && minY>o.minY && maxY<o.maxY
      && o.normal.x*(o.normal.x>=0?box.max.x:box.min.x)
      +o.normal.y*(o.normal.y>=0?box.max.y:box.min.y)
      +o.normal.z*(o.normal.z>=0?box.max.z:box.min.z)+o.constant < -DEPTH_GAP_M)) continue;
    let inside=true;
    for(let i=0;i<16 && inside;i+=2) for(const e of o.edges) {
      if (!(e.dx*(projectedBox[i+1]-e.y)-e.dy*(projectedBox[i]-e.x)>e.inset)) {inside=false;break;}
    }
    if(inside)return true;
  }
  return false;
}

/** The public BatchedMesh custom-sort hook supplies the already frustum-culled
 * draw ranges. Filtering that list leaves the batch's visibility and pick data
 * untouched. Ground decals retain insertion order; buildings retain Three's
 * depth order. Other cameras (the app's sun shadow) get the complete list.
 */
export function createViewOcclusion({ camera, renderer, triangles, batches, allow = () => true }) {
  let enabled=true, cachedKey=null, cachedFrame=null, occluders=[];
  const states=new Map(), active=[], keyBuf=new Float64Array(34);
  let flags=new Uint8Array(0);
  const vp=new THREE.Matrix4(),size=new THREE.Vector2(),instance=new THREE.Matrix4();
  const box=new THREE.Box3(),undos=[];
  const stats={ tested:0,culled:0,triangles:0 };
  function prepare() {
    const frame=renderer.info?.render?.frame;
    if (frame!==undefined && frame===cachedFrame) return;
    cachedFrame=frame;stats.tested=0;stats.culled=0;stats.triangles=0;
    if (!enabled || !allow() || renderer.clippingPlanes?.length) {occluders=[];cachedKey=null;return;}
    // T-2806: the key is compared number by number in reused storage. As a string it
    // was 34 numbers and a character per backing triangle, built every frame.
    states.clear();
    if (flags.length!==triangles.length) flags=new Uint8Array(triangles.length);
    let flagsChanged=false;
    for(let i=0;i<triangles.length;i++) {
      const t=triangles[i];
      let on=true;
      if(t.active){ if(!states.has(t.active))states.set(t.active,!!t.active()); on=states.get(t.active); }
      const v=on?1:0;
      if(flags[i]!==v){flags[i]=v;flagsChanged=true;}
    }
    renderer.getDrawingBufferSize(size);
    const pm=camera.projectionMatrix.elements, vm=camera.matrixWorldInverse.elements;
    let same=cachedKey!==null && !flagsChanged;
    for(let i=0;i<16 && same;i++) same=Object.is(keyBuf[i],pm[i]) || keyBuf[i]===pm[i];
    for(let i=0;i<16 && same;i++) same=Object.is(keyBuf[16+i],vm[i]) || keyBuf[16+i]===vm[i];
    same=same && keyBuf[32]===size.x && keyBuf[33]===size.y;
    if (!same) {
      cachedKey=true;
      for(let i=0;i<16;i++){keyBuf[i]=pm[i];keyBuf[16+i]=vm[i];}
      keyBuf[32]=size.x;keyBuf[33]=size.y;
      vp.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
      active.length=0;
      for(let i=0;i<triangles.length;i++) if(flags[i]) active.push(triangles[i]);
      occluders=projectOccluders(active,camera,size.x,size.y);
    }
  }
  for (const batch of batches) {
    if (!batch?.isBatchedMesh) continue;
    const previous=batch.customSort,sorted=batch.sortObjects;
    const hook=function(list,passCamera) {
      if (previous) previous.call(this,list,passCamera);
      else if (sorted) list.sort(passCamera===camera && this.material.transparent
        ? (a,b)=>b.z-a.z : (a,b)=>a.z-b.z);
      if (passCamera!==camera) return;
      const m=this.material;
      // Geometry bounds do not bound a displaced or depth-biased raster, and
      // stencil writes can have side effects even when a surface is hidden.
      if(m.displacementMap||m.polygonOffset||m.wireframe||!m.depthTest||m.stencilWrite
          || ![THREE.LessDepth,THREE.LessEqualDepth].includes(m.depthFunc))return;
      prepare(); if (!occluders.length) return;
      let keep=0;
      for (const item of list) {
        const geometry=this.getGeometryIdAt(item.index);
        this.getBoundingBoxAt(geometry,box);
        this.getMatrixAt(item.index,instance);
        box.applyMatrix4(instance).applyMatrix4(this.matrixWorld);
        stats.tested++;
        if (boxOccluded(box,vp,occluders,size.x,size.y)) {
          stats.culled++;stats.triangles+=item.count/3;
        } else list[keep++]=item;
      }
      list.length=keep;
    };
    batch.sortObjects=true;batch.setCustomSort(hook);
    undos.push(()=>{if(batch.customSort===hook){batch.setCustomSort(previous);batch.sortObjects=sorted;}});
  }
  return {
    get stats(){return {...stats,active:enabled&&allow(),occluders:occluders.length};},
    setEnabled(on){enabled=!!on;cachedFrame=null;return enabled;},
    get enabled(){return enabled;},
    dispose(){for(const undo of undos)undo();undos.length=0;},
  };
}
