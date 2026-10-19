// SPDX-License-Identifier: GPL-3.0-or-later
// Small technical-study guards; no human model, animation engine or scene population.
export const SUPPORTED_W01_SHA256='f415e6fb79c9df9372c5b2ec6cb77c9a305117de3fa8e9c704c87d5c09a6aeb0';
export async function parseVerifiedSeatedWagon(bytes,parse,base='') {
  if(!(bytes instanceof ArrayBuffer))throw Error('Actual fetched W01 ArrayBuffer required');
  const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(sha256!==SUPPORTED_W01_SHA256)throw Error(`Supported W01 GLB hash mismatch: ${sha256}`);
  // Parse exactly the ArrayBuffer whose bytes were verified; no second fetch or substitution.
  return {gltf:await parse(bytes,base),sha256};
}
export function cleanupSeatedStudy(resources) {
  const errors=[];
  const attempt=(name,fn)=>{try{fn();}catch(error){errors.push({name,error:String(error)});}};
  if(resources.actor){const actor=resources.actor;resources.actor=null;attempt('actor',()=>actor.dispose());}
  if(resources.inspectionLease){resources.inspectionLease=false;attempt('inspectionLease',()=>resources.assets.release(resources.asset,0));}
  if(resources.wagon){const wagon=resources.wagon;resources.wagon=null;attempt('wagonScene',()=>wagon.scene?.removeFromParent?.());attempt('wagon',()=>resources.disposeLoadedAsset(wagon));}
  if(resources.renderer){const renderer=resources.renderer;resources.renderer=null;attempt('renderer',()=>renderer.dispose());attempt('canvas',()=>renderer.domElement?.remove());}
  const remaining=resources.assets?.loaded??[];
  return {passed:errors.length===0&&remaining.length===0,errors,remaining_human_asset_leases:remaining};
}
