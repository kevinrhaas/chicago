// SPDX-License-Identifier: GPL-3.0-or-later
// Original finite segment and triangle unsigned distances; no inside/outside claim.
const sub=(a,b)=>[a.x-b.x,a.y-b.y,a.z-b.z],dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
export function segmentDistance(a,b,c,d){
 const u=sub(b,a),v=sub(d,c),w=sub(a,c),A=dot(u,u),B=dot(u,v),C=dot(v,v),D=dot(u,w),E=dot(v,w);let best=Infinity;
 const evalAt=(s,t)=>{const q=w.map((x,i)=>x+s*u[i]-t*v[i]);best=Math.min(best,dot(q,q));};
 const clamp=x=>Math.max(0,Math.min(1,x));
 evalAt(0,C>1e-24?clamp(E/C):0);evalAt(1,C>1e-24?clamp((E+B)/C):0);
 evalAt(A>1e-24?clamp(-D/A):0,0);evalAt(A>1e-24?clamp((B-D)/A):0,1);
 const den=A*C-B*B;if(den>1e-24*A*C){const s=(B*E-C*D)/den,t=(A*E-B*D)/den;if(s>=0&&s<=1&&t>=0&&t<=1)evalAt(s,t);}
 return Math.sqrt(Math.max(0,best));
}
export function triangleDistance(a,b){
 let best=Infinity;const av=[a.a,a.b,a.c],bv=[b.a,b.b,b.c];
 // An edge can pierce a face interior without reaching any opposite edge.
 for(const [source,target]of[[a,b],[b,a]]){const vertices=[source.a,source.b,source.c],normal=target.getNormal(target.a.clone());for(let i=0;i<3;i++){const x=vertices[i],y=vertices[(i+1)%3],dx=x.clone().sub(target.a).dot(normal),dy=y.clone().sub(target.a).dot(normal),den=dx-dy;if(Math.abs(den)<1e-15)continue;const t=dx/den;if(t>=0&&t<=1){const q=x.clone().lerp(y,t);if(target.containsPoint(q))return 0;}}}
 for(const p of av)best=Math.min(best,p.distanceTo(b.closestPointToPoint(p,p.clone())));
 for(const p of bv)best=Math.min(best,p.distanceTo(a.closestPointToPoint(p,p.clone())));
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)best=Math.min(best,segmentDistance(av[i],av[(i+1)%3],bv[j],bv[(j+1)%3]));
 return best;
}
