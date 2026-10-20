// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import * as T from '../renderers/web/vendor/three-0.185.1/three.module.js';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('./human_teamster.html',import.meta.url),'utf8');
const context=vm.createContext({T});
vm.runInContext(source.slice(source.indexOf('function fitInspectionCamera'),source.indexOf("function view(name=")),context);
function corners(w,h,d,offsetY=0){const points=[];for(const x of[-w/2,w/2])for(const y of[offsetY,offsetY+h])for(const z of[-d/2,d/2])points.push(x,y,z);return points;}
let count=0;
for(const [width,height,headerBottom]of[[390,780,210],[1280,800,170],[320,640,245]]){
  for(const theta of[0,Math.PI/4,Math.PI/2]){
    for(const points of[corners(.6,1.9,.4,-.03),corners(1.3,1.8,.5),corners(.22,.29,.24,1.6)]){
      const camera=new T.PerspectiveCamera(32,width/height,.03,50),before=[...points],detail=points[1]>1;
      const fit=context.fitInspectionCamera(camera,points,{width,height,headerBottom,theta,minHeightFraction:detail?.2:0});
      assert.ok(fit.inside);
      const projected=[];
      for(let i=0;i<points.length;i+=3){
        const world=new T.Vector3().fromArray(points,i),depth=-world.clone().applyMatrix4(camera.matrixWorldInverse).z,ndc=world.project(camera);
        const x=(ndc.x+1)/2,y=(1-ndc.y)/2;
        assert.ok(x>=.02&&x<=.98&&y>=headerBottom/height+.02&&y<=.98,'independent actual camera projection clears viewport and header');
        assert.ok(depth>camera.near&&depth<camera.far);projected.push(y);
      }
      if(detail)assert.ok(Math.max(...projected)-Math.min(...projected)>=.2);
      assert.ok(camera.getWorldDirection(new T.Vector3()).dot(new T.Vector3(Math.sin(theta),0,Math.cos(theta)))<-.999999);
      assert.deepEqual(points,before,'camera fitting must not reposition the person or align its soles');count++;
    }
  }
}
assert.throws(()=>context.fitInspectionCamera(new T.PerspectiveCamera(32,1,.03,50),corners(.2,.3,.2),{width:320,height:640,headerBottom:630}),/header/);
console.log(`PASS ${count} independent Three CPU projection fits and impossible-header refusal; no resident/browser acceptance`);
