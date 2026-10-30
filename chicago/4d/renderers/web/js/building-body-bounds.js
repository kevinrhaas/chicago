/** Read-only size diagnostic for a declared exterior sapling sign.
 * Inputs are the same stored/decoded local positions that instanceBounds measures.
 * The complete bounds remain authoritative for placement/overall-size checks.
 * No declaration or unknown roles: nothing is exempted from those measurements.
 */
export function buildingBodyBounds(sidecar, samples, quantStep) {
  const attrs = sidecar?.attributes ?? {};
  const pose = attrs.sign_pole_set_out?.value;
  if (pose == null) return null;
  const errors = [];
  const fail = reason => ({ valid: false, errors: [reason], samples: samples.length });
  const tuple = (a, n) => Array.isArray(a) && a.length === n && a.every(Number.isFinite);
  const polygon = sidecar.footprint?.polygon;
  if (sidecar.archetype !== 'log_dwelling' || attrs.compound_joint?.value !== 'elbow'
      || attrs.sign_mount?.value !== 'sapling_pole' || !attrs.sign?.value
      || !tuple(pose.base_xy, 2) || !tuple(pose.head_xyz, 3)
      || !tuple(pose.arm_vector_xyz, 3) || !tuple(pose.board_wh, 2)
      || !Number.isFinite(pose.hanger_drop_m) || !Array.isArray(polygon)
      || polygon.length < 3 || !polygon.every(p => tuple(p, 2))) return fail('unsupported or malformed exterior sign declaration');
  const [bx, by] = pose.base_xy, [tx, ty, top] = pose.head_xyz;
  const arm = pose.arm_vector_xyz, [bw, bh] = pose.board_wh, drop = pose.hanger_drop_m;
  const reach = Math.hypot(arm[0], arm[1]);
  if (top < 7 || top > 14 || Math.hypot(tx-bx,ty-by) > top*.25
      || reach < 1 || reach > 3.5 || Math.abs(arm[2]) > 1.5
      || bw < .8 || bw > 2.4 || bh < .5 || bh > 1.5 || drop < .1 || drop > .6
      || !(quantStep > 0 && quantStep < .003)) return fail('exterior sign or stored-position precision outside bounded contract');
  const add=(a,b)=>a.map((v,i)=>v+b[i]), mul=(a,s)=>a.map(v=>v*s);
  const sub=(a,b)=>add(a,mul(b,-1)), dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
  const unit=a=>mul(a,1/Math.hypot(...a));
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const at=z=>[bx+(tx-bx)*z/top,by+(ty-by)*z/top,z];
  const tolerance=Math.max(.002,quantStep*3);
  const inFootprint = p => {
    let inside=false;
    for(let i=0,j=polygon.length-1;i<polygon.length;j=i++) {
      const a=polygon[j],b=polygon[i],dx=b[0]-a[0],dy=b[1]-a[1];
      const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));
      if(Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)<=tolerance)return true;
      if((a[1]>p[1])!==(b[1]>p[1]) && p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
    }
    return inside;
  };
  if(inFootprint([bx,by]) || inFootprint([tx,ty]))return fail('sign shaft is not exterior to the occupied footprint');
  const distanceToFootprint=p=>Math.min(...polygon.map((b,i)=>{const a=polygon[(i+polygon.length-1)%polygon.length],dx=b[0]-a[0],dy=b[1]-a[1];const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);}));
  const overhang=attrs.compound_roof_overhang_m?.value ?? 0;
  if(!Number.isFinite(overhang) || overhang<0 || overhang>.30)return fail('unsupported body fringe declaration');
  const bodyFringe=Math.max(.12,overhang)+tolerance;
  const near=(p,a,b,r)=>{const d=sub(b,a);const t=Math.max(0,Math.min(1,dot(sub(p,a),d)/dot(d,d)));return Math.hypot(...sub(p,add(a,mul(d,t))))<=r+tolerance;};
  const origin=at(top-.4), e=unit(arm), up=unit(add([0,0,1],mul(e,-e[2]))), normal=cross(e,up);
  const centre=add(add(origin,mul(arm,.65)),mul(up,-drop));
  const board=(u,v)=>add(add(centre,mul(e,u)),mul(up,v));
  // Surface-section bounds, not a reconstructed mesh: 105/72 mm shaft,
  // 55 mm arm, 35 mm brace, 18 mm hangers and 55 mm board + 6 mm device.
  const timber=p=>near(p,at(-.4),at(top*.56),.105)
    || near(p,at(top*.56),at(top),.072)
    || near(p,add(origin,mul(e,-.35)),add(origin,arm),.055)
    || near(p,at(top-1.6),add(origin,mul(arm,.45)),.035);
  const hanger=p=>[-bw*.34,bw*.34].some(u=>near(p,board(u,0),board(u,drop+.035),.018));
  const onBoard=p=>{const q=sub(p,centre),u=dot(q,e),v=dot(q,up),n=dot(q,normal);return Math.abs(u)<=bw/2+tolerance && v>=-bh-tolerance && v<=tolerance && Math.abs(n)<=.055/2+.006+tolerance;};
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  let bodyCount=0,excluded=0,wallCount=0,wallTop=-Infinity,logExcluded=0,boardExcluded=0;
  for(const {point,role} of samples) {
    if(!tuple(point,3))return fail('non-finite stored body position');
    // glTF local x,y,z -> declaration x,y,height. No bbox centering.
    const p=[point[0],-point[2],point[1]];
    const shaft=role==='log' && !inFootprint(p) && timber(p);
    const sign=(role==='sign' || role==='paint') && onBoard(p);
    const iron=role==='dark' && hanger(p);
    if(shaft || sign || iron) {excluded++;if(shaft)logExcluded++;if(sign)boardExcluded++;continue;}
    if(((role==='log' || role==='dark') && !inFootprint(p) && distanceToFootprint(p)>bodyFringe)
        || role==='sign' || role==='paint') {
      if(!errors.includes('unaccounted exterior sign geometry'))errors.push('unaccounted exterior sign geometry');
    }
    bodyCount++;
    for(let k=0;k<3;k++){min[k]=Math.min(min[k],point[k]);max[k]=Math.max(max[k],point[k]);}
    if(role==='log' && inFootprint(p)){wallCount++;wallTop=Math.max(wallTop,point[1]);}
  }
  const size=max.map((v,i)=>v-min[i]);
  const span=k=>Math.max(...polygon.map(p=>p[k]))-Math.min(...polygon.map(p=>p[k]));
  const wall=attrs.wall_height_m?.value;
  if(bodyCount<24 || wallCount<12 || !(Number.isFinite(wall) && wall>0) || wallTop<wall*.9
      || min[1]>.1*wall || size[0]<span(0)*.9 || size[2]<span(1)*.9)errors.push('missing or collapsed occupied building-body samples');
  if(!logExcluded || !boardExcluded)errors.push('declared exterior shaft and sign were not both measured');
  // A point outside the bounded appendage remains body geometry. The unchanged
  // wall-height guard will reject it if it inflates the apparent building.
  return {valid:errors.length===0,errors,size,min,max,samples:bodyCount,excluded,wallSamples:wallCount,wallTop,quantStep};
}
