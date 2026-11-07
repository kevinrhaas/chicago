// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import * as T from '../renderers/web/vendor/three-0.185.1/three.module.js';
import {rayTriangleCandidates} from './human_body_ray_grid.mjs';
function build(geometry,cell){
  const p=geometry.attributes.position.array,index=geometry.index.array,grid=new Map(),minimum=[Infinity,Infinity,Infinity],maximum=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<p.length;i++) {minimum[i%3]=Math.min(minimum[i%3],p[i]);maximum[i%3]=Math.max(maximum[i%3],p[i]);}
  for(let i=0;i<index.length;i+=3){const b=[0,1,2].map(a=>[Math.floor(Math.min(p[index[i]*3+a],p[index[i+1]*3+a],p[index[i+2]*3+a])/cell),Math.floor(Math.max(p[index[i]*3+a],p[index[i+1]*3+a],p[index[i+2]*3+a])/cell)]);for(let x=b[0][0];x<=b[0][1];x++)for(let y=b[1][0];y<=b[1][1];y++)for(let z=b[2][0];z<=b[2][1];z++){const k=`${x},${y},${z}`;if(!grid.has(k))grid.set(k,[]);grid.get(k).push(i);}}
  return {p,index,grid,minimum,maximum};
}
let checked=0,totalFull=0,totalSelected=0;
for(const geometry of [new T.BoxGeometry(1,1,1),new T.SphereGeometry(.5,32,16)])for(const cell of [.035,.1,.25]){
  const {p,index,grid,minimum,maximum}=build(geometry,cell),a=new T.Vector3(),b=new T.Vector3(),c=new T.Vector3(),hit=new T.Vector3();
  const points=[[0,0,0],[.51,.51,0],[2,2,2],[-2,-2,-2],[.5,.5,.5],[0,.5,0],[-.5,-.5,-.5],...Array.from({length:60},(_,i)=>[Math.sin(i*3.7)*1.1,Math.cos(i*2.3)*1.1,Math.sin(i*5.1)*1.1])];
  for(const point of points)for(const direction of [[1,.381,.627],[-.27,1,.431],[.183,-.361,1],[1,0,0],[0,-1,0],[1,1,1],[-1,-1,0]]){
    const origin=new T.Vector3(...point),dir=new T.Vector3(...direction).normalize(),ray=new T.Ray(origin,dir);
    const candidates=rayTriangleCandidates(grid,minimum,maximum,point,dir.toArray(),cell);
    function hits(ids){const out=[];for(const i of ids){a.fromArray(p,index[i]*3);b.fromArray(p,index[i+1]*3);c.fromArray(p,index[i+2]*3);if(ray.intersectTriangle(a,b,c,false,hit))out.push(i);}return out.sort((a,b)=>a-b);}
    const expected=hits(Array.from({length:index.length/3},(_,i)=>i*3)),actual=hits(candidates);
    assert.deepEqual(actual,expected,JSON.stringify({point,direction,cell,shape:geometry.type}));checked++;totalFull+=index.length/3;totalSelected+=candidates.length;
  }
}
console.log(JSON.stringify({passed:true,actual_native_ray_comparisons:checked,full_triangle_candidates:totalFull,conservative_grid_candidates:totalSelected,reduction:totalFull/totalSelected}));
