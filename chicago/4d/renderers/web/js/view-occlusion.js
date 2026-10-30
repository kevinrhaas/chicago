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

const REJECT = 0, FULL = 1, SIMPLE = 2;
/**
 * REJECT when the original path (fullOccluder) would certainly turn this triangle
 * away; SIMPLE when neither plane cuts it, its screen corners are in scratchXY and its
 * signed area passed; FULL when only the original path can tell.
 */
function classify(points, vp, width, height) {
  let behindNear = 0, beyondFar = 0, inside = 0;
  for (let k = 0; k < 3; k++) {
    const c = scratchClip[k].set(points[k].x, points[k].y, points[k].z, 1).applyMatrix4(vp);
    const dn = c.z + c.w, df = c.w - c.z;
    if (dn < 0) behindNear++;
    if (df < 0) beyondFar++;
    if (dn >= 0 && df >= 0) inside++;
  }
  // Wholly behind the near plane (most of what is behind the eye), or wholly past the
  // far one: clipPlane() leaves nothing, and a cut by one plane stays on its side of
  // the other.
  if (behindNear === 3 || beyondFar === 3) return REJECT;
  // Cut by a plane: only the full path knows the polygon.
  if (inside < 3) return FULL;
  for (let k = 0; k < 3; k++) {
    const c = scratchClip[k];
    if (!Number.isFinite(c.w) || c.w <= 0) return REJECT;
    scratchXY[k * 2] = c.x / c.w * width / 2; scratchXY[k * 2 + 1] = c.y / c.w * height / 2;
  }
  let signedArea = 0;
  for (let k = 0; k < 3; k++) {
    const j = (k + 1) % 3;
    signedArea = signedArea + scratchXY[k * 2] * scratchXY[j * 2 + 1] - scratchXY[k * 2 + 1] * scratchXY[j * 2];
  }
  if (Math.abs(signedArea) < 16) return REJECT;
  return SIMPLE;
}
const VIEW_EDGES = [[0, 1], [0, -1], [1, 1], [1, -1]];

/** visibleArea() of the three corners in scratchXY, on scratch storage, by the same
 *  arithmetic in the same order. */
const polyA = new Float64Array(16), polyB = new Float64Array(16);
function scratchVisibleArea(width, height) {
  let src = polyA, dst = polyB, n = 3;
  for (let k = 0; k < 6; k++) src[k] = scratchXY[k];
  for (const [axis, sign] of VIEW_EDGES) {
    const limit = axis ? height / 2 : width / 2;
    let m = 0;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const a0 = src[i * 2], a1 = src[i * 2 + 1], b0 = src[j * 2], b1 = src[j * 2 + 1];
      const da = limit - sign * (axis ? a1 : a0), db = limit - sign * (axis ? b1 : b0);
      if (da >= 0) { dst[m * 2] = a0; dst[m * 2 + 1] = a1; m++; }
      if ((da >= 0) !== (db >= 0)) {
        const t = da / (da - db);
        dst[m * 2] = a0 + t * (b0 - a0); dst[m * 2 + 1] = a1 + t * (b1 - a1); m++;
      }
    }
    const swap = src; src = dst; dst = swap; n = m;
    if (n < 3) return 0;
  }
  let sum = 0;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    sum = sum + src[i * 2] * src[j * 2 + 1] - src[i * 2 + 1] * src[j * 2];
  }
  return Math.abs(sum);
}

/** The original path: the occluder this triangle makes, or null where it makes none. */
function fullOccluder(triangle, facing, vp, camera, width, height) {
    let clip = triangle.points.map(p => new THREE.Vector4(p.x, p.y, p.z, 1).applyMatrix4(vp));
    clip=clipPlane(clip,p=>p.z+p.w);
    clip=clipPlane(clip,p=>p.w-p.z);
    if(clip.length<3 || clip.some(p=>!Number.isFinite(p.w)||p.w<=0))return null;
    // Include a 2 cm world-space rounding allowance on BOTH projected surfaces,
    // plus two raster pixels. This deliberately grows near the camera.
    const focal=Math.max(Math.abs(camera.projectionMatrix.elements[0])*width,
      Math.abs(camera.projectionMatrix.elements[5])*height)/2;
    const margin=2+2*DEPTH_GAP_M*focal/Math.min(...clip.map(p=>p.w));
    const points = clip.map(p => [p.x / p.w * width / 2, p.y / p.w * height / 2]);
    const signedArea = points.reduce((sum,p,i)=>{
      const q=points[(i+1)%points.length];return sum+p[0]*q[1]-p[1]*q[0];
    },0);
    if (Math.abs(signedArea) < 16) return null;
    const area=visibleArea(points,width,height);
    if(area<16)return null;
    if (signedArea < 0) points.reverse();
    const edges = points.map((p, i) => {
      const q = points[(i+1)%points.length], dx=q[0]-p[0], dy=q[1]-p[1];
      return { x:p[0], y:p[1], dx, dy, inset:margin*Math.hypot(dx,dy) };
    });
    // A slanting wall's farthest vertex can be much farther away than the part
    // covering an instance. Test the actual plane instead: the entire world box
    // must lie on the opposite side from the eye, with a metric safety gap.
    const normal=triangle.normal.clone().normalize().multiplyScalar(facing>=0?1:-1);
    return { edges, normal, constant:-normal.dot(triangle.points[0]), area,
      minX:Math.min(...points.map(p=>p[0])),maxX:Math.max(...points.map(p=>p[0])),
      minY:Math.min(...points.map(p=>p[1])),maxY:Math.max(...points.map(p=>p[1])) };
}

// Candidates in triangle order: their index, area and facing, and the occluder where
// the full path already made one. Ranked as `result.sort(by area).slice(0, 64)` was
// (a stable sort, so ties keep triangle order); only the 64 kept are built.
let candIndex = new Int32Array(1024), candArea = new Float64Array(1024), candFacing = new Float64Array(1024);
const candBuilt = [], candOrder = [];

export function projectOccluders(triangles, camera, width, height) {
  if (!camera.isPerspectiveCamera || camera.reversedDepth
      || camera.coordinateSystem !== THREE.WebGLCoordinateSystem || width <= 0 || height <= 0) return [];
  const vp = vpScratch.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
  const eye = scratchEye.setFromMatrixPosition(camera.matrixWorld);
  let count = 0;
  for (let t = 0; t < triangles.length; t++) {
    const triangle = triangles[t];
    // This bound is for Chicago's metre frame, not arbitrary world scales.
    const tp = triangle.points;
    let far = false;
    for (let k = 0; k < tp.length && !far; k++) far = Math.max(Math.abs(tp[k].x),Math.abs(tp[k].y),Math.abs(tp[k].z))>8192;
    if (far) continue;
    const facing = triangle.normal.dot(scratchTo.subVectors(eye, tp[0]));
    if (triangle.side === THREE.FrontSide && facing <= 0) continue;
    if (triangle.side === THREE.BackSide && facing >= 0) continue;
    const kind = tp.length === 3 ? classify(tp, vp, width, height) : FULL;
    if (kind === REJECT) continue;
    let area, built = null;
    if (kind === SIMPLE) {
      area = scratchVisibleArea(width, height);
      if (area < 16) continue;
    } else {
      built = fullOccluder(triangle, facing, vp, camera, width, height);
      if (!built) continue;
      area = built.area;
    }
    if (count === candIndex.length) {
      const grow = (a) => { const b = new a.constructor(a.length * 2); b.set(a); return b; };
      candIndex = grow(candIndex); candArea = grow(candArea); candFacing = grow(candFacing);
    }
    candIndex[count] = t; candArea[count] = area; candFacing[count] = facing; candBuilt[count] = built;
    count++;
  }
  candOrder.length = count;
  for (let i = 0; i < count; i++) candOrder[i] = i;
  candOrder.sort((a, b) => candArea[b] - candArea[a] || a - b);
  const result = [];
  for (let r = 0; r < count && result.length < MAX_TRIANGLES; r++) {
    const c = candOrder[r];
    const o = candBuilt[c] ?? fullOccluder(triangles[candIndex[c]], candFacing[c], vp, camera, width, height);
    if (o) result.push(o);
  }
  candBuilt.length = 0;
  return result;
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

/** T-3152: is the box hidden behind a proven planar cover (planar-occluders.js)?
 * The box lies wholly on the far side of the plane from the eye, so the rays from the
 * eye to it cross the plane, and its shadow cast from the eye onto the plane is the hull
 * of its eight corners' shadows. Every grid cell under that hull's bounds, grown by two
 * pixels at the farthest crossing plus the plane's `tol` and the filter's 2 cm, must be a
 * proven cell; and every crossing must lie beyond the near plane, where the cover is drawn.
 * `plane` is in the world frame: `o` on it, `n` its unit normal, `u`/`v` its grid axes.
 */
const shadowU=new Float64Array(8),shadowV=new Float64Array(8);
/** boxOccluded's own entry rule: every corner in front of the near plane and two pixels
 *  inside the viewport, where T-2227's comparisons found clipped boxes still reach. */
export function boxInView(box, vp, width, height) {
  if (box.isEmpty()) return false;
  const m=vp.elements;
  for(let i=0;i<8;i++) {
    const x=i&4?box.max.x:box.min.x,y=i&2?box.max.y:box.min.y,z=i&1?box.max.z:box.min.z;
    const w=m[3]*x+m[7]*y+m[11]*z+m[15],depth=m[2]*x+m[6]*y+m[10]*z+m[14];
    if (!Number.isFinite(w) || w<=0 || depth<=-w) return false;
    const px=(m[0]*x+m[4]*y+m[8]*z+m[12])/w*width/2, py=(m[1]*x+m[5]*y+m[9]*z+m[13])/w*height/2;
    if (!(px>-width/2+2 && px<width/2-2 && py>-height/2+2 && py<height/2-2)) return false;
  }
  return true;
}
export function planeOccluded(box, eye, forward, near, pixelAngle, plane) {
  const {o,n,u,v}=plane;
  const se=n.x*(eye.x-o.x)+n.y*(eye.y-o.y)+n.z*(eye.z-o.z);
  if (!(Math.abs(se)>DEPTH_GAP_M)) return false;
  const sign=se>0?1:-1;
  let maxDist=0,minCos=1;
  for(let i=0;i<8;i++) {
    const x=i&4?box.max.x:box.min.x,y=i&2?box.max.y:box.min.y,z=i&1?box.max.z:box.min.z;
    const sc=n.x*(x-o.x)+n.y*(y-o.y)+n.z*(z-o.z);
    if (!(sign*sc < -DEPTH_GAP_M)) return false;
    const dx=x-eye.x,dy=y-eye.y,dz=z-eye.z,len=Math.hypot(dx,dy,dz);
    const t=se/(se-sc);
    const qx=eye.x+t*dx,qy=eye.y+t*dy,qz=eye.z+t*dz;
    if (!((qx-eye.x)*forward.x+(qy-eye.y)*forward.y+(qz-eye.z)*forward.z > near*1.01+DEPTH_GAP_M)) return false;
    maxDist=Math.max(maxDist,t*len);
    minCos=Math.min(minCos,Math.abs(n.x*dx+n.y*dy+n.z*dz)/len);
    shadowU[i]=u.x*(qx-o.x)+u.y*(qy-o.y)+u.z*(qz-o.z);
    shadowV[i]=v.x*(qx-o.x)+v.y*(qy-o.y)+v.z*(qz-o.z);
  }
  // A grazing sight line turns the plane's own tolerance into a long slide across it.
  if (minCos<0.2) return false;
  const margin=(2*pixelAngle*maxDist+plane.tol+DEPTH_GAP_M)/minCos;
  let u0=Infinity,u1=-Infinity,v0=Infinity,v1=-Infinity;
  for(let i=0;i<8;i++){u0=Math.min(u0,shadowU[i]);u1=Math.max(u1,shadowU[i]);v0=Math.min(v0,shadowV[i]);v1=Math.max(v1,shadowV[i]);}
  const gx0=Math.floor((u0-margin-plane.umin)/plane.res),gx1=Math.floor((u1+margin-plane.umin)/plane.res);
  const gy0=Math.floor((v0-margin-plane.vmin)/plane.res),gy1=Math.floor((v1+margin-plane.vmin)/plane.res);
  if (gx0<0||gy0<0||gx1>=plane.W||gy1>=plane.H) return false;
  const W1=plane.W+1,sat=plane.sat;
  const covered=sat[(gy1+1)*W1+gx1+1]-sat[gy0*W1+gx1+1]-sat[(gy1+1)*W1+gx0]+sat[gy0*W1+gx0];
  return covered===(gx1-gx0+1)*(gy1-gy0+1);
}

/** The public BatchedMesh custom-sort hook supplies the already frustum-culled
 * draw ranges. Filtering that list leaves the batch's visibility and pick data
 * untouched. Ground decals retain insertion order; buildings retain Three's
 * depth order. Other cameras (the app's sun shadow) get the complete list.
 */
// The same order as `b.z-a.z` / `a.z-b.z` (a difference of distinct doubles is never
// zero), returned as small integers: a returned double is boxed, ~1 MB a frame here.
const farFirst=(a,b)=>(b.z<a.z?-1:b.z>a.z?1:0), nearFirst=(a,b)=>(a.z<b.z?-1:a.z>b.z?1:0);

export function createViewOcclusion({ camera, renderer, triangles, batches, planes = [], allow = () => true }) {
  let enabled=true, cachedKey=null, cachedFrame=null, occluders=[];
  const tests=[], active=[], keyBuf=new Float64Array(34);
  let flags=new Uint8Array(0), testOf=new Int32Array(0), answers=new Uint8Array(0);
  const vp=new THREE.Matrix4(),size=new THREE.Vector2(),instance=new THREE.Matrix4();
  const box=new THREE.Box3(),undos=[];
  const stats={ tested:0,culled:0,triangles:0,planeCulled:0,planeTriangles:0 };
  // T-3152: the planar covers standing this frame, and the eye they are cast from.
  const livePlanes=[],eye=new THREE.Vector3(),forward=new THREE.Vector3();
  let pixelAngle=0,near=0;
  function prepare() {
    const frame=renderer.info?.render?.frame;
    if (frame!==undefined && frame===cachedFrame) return;
    cachedFrame=frame;stats.tested=0;stats.culled=0;stats.triangles=0;stats.planeCulled=0;stats.planeTriangles=0;
    livePlanes.length=0;
    if (!enabled || !allow() || renderer.clippingPlanes?.length) {occluders=[];cachedKey=null;return;}
    // The covers' test is the camera's own perspective; any other camera fails open.
    if (camera.isPerspectiveCamera && !camera.reversedDepth && camera.coordinateSystem===THREE.WebGLCoordinateSystem) {
      for(const p of planes) if(p.active())livePlanes.push(p);
      eye.setFromMatrixPosition(camera.matrixWorld);
      camera.getWorldDirection(forward);
      near=camera.near;
      renderer.getDrawingBufferSize(size);
      const pm=camera.projectionMatrix.elements;
      // The widest pixel is the one at the centre of the view.
      pixelAngle=Math.max(2/(Math.abs(pm[0])*size.x),2/(Math.abs(pm[5])*size.y));
    }
    // T-2806: the key is compared number by number in reused storage. As a string it
    // was 34 numbers and a character per backing triangle, built every frame.
    // Each distinct `active` test is asked once a frame, as before; which triangle
    // shares which test is worked out once, not rebuilt as a Map every frame.
    if (flags.length!==triangles.length || testOf.length!==triangles.length) {
      flags=new Uint8Array(triangles.length);
      testOf=new Int32Array(triangles.length);
      const index=new Map(); tests.length=0;
      triangles.forEach((t,i)=>{
        if(!t.active){testOf[i]=-1;return;}
        if(!index.has(t.active)){index.set(t.active,tests.length);tests.push(t.active);}
        testOf[i]=index.get(t.active);
      });
      answers=new Uint8Array(tests.length);
    }
    for(let k=0;k<tests.length;k++) answers[k]=tests[k]()?1:0;
    let flagsChanged=false;
    for(let i=0;i<triangles.length;i++) {
      const v=testOf[i]<0?1:answers[testOf[i]];
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
      // Filled in place: emptying it first gave back its storage, regrown every frame.
      let n=0;
      for(let i=0;i<triangles.length;i++) if(flags[i]) active[n++]=triangles[i];
      active.length=n;
      occluders=projectOccluders(active,camera,size.x,size.y);
    }
  }
  for (const batch of batches) {
    if (!batch?.isBatchedMesh) continue;
    const previous=batch.customSort,sorted=batch.sortObjects;
    const hook=function(list,passCamera) {
      if (previous) previous.call(this,list,passCamera);
      else if (sorted) list.sort(passCamera===camera && this.material.transparent ? farFirst : nearFirst);
      if (passCamera!==camera) return;
      const m=this.material;
      // Geometry bounds do not bound a displaced or depth-biased raster, and
      // stencil writes can have side effects even when a surface is hidden.
      if(m.displacementMap||m.polygonOffset||m.wireframe||!m.depthTest||m.stencilWrite
          || ![THREE.LessDepth,THREE.LessEqualDepth].includes(m.depthFunc))return;
      prepare(); if (!occluders.length && !livePlanes.length) return;
      let keep=0;
      for (const item of list) {
        const geometry=this.getGeometryIdAt(item.index);
        this.getBoundingBoxAt(geometry,box);
        this.getMatrixAt(item.index,instance);
        box.applyMatrix4(instance).applyMatrix4(this.matrixWorld);
        stats.tested++;
        if (boxOccluded(box,vp,occluders,size.x,size.y)) {
          stats.culled++;stats.triangles+=item.count/3;
        } else if (livePlanes.length && boxInView(box,vp,size.x,size.y) && livePlanes.some(p=>planeOccluded(box,eye,forward,near,pixelAngle,p))) {
          stats.planeCulled++;stats.planeTriangles+=item.count/3;
        } else list[keep++]=item;
      }
      list.length=keep;
    };
    batch.sortObjects=true;batch.setCustomSort(hook);
    undos.push(()=>{if(batch.customSort===hook){batch.setCustomSort(previous);batch.sortObjects=sorted;}});
  }
  return {
    get stats(){return {...stats,active:enabled&&allow(),occluders:occluders.length,planes:livePlanes.length};},
    setEnabled(on){enabled=!!on;cachedFrame=null;return enabled;},
    get enabled(){return enabled;},
    dispose(){for(const undo of undos)undo();undos.length=0;},
  };
}
