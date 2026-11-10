// SPDX-License-Identifier: GPL-3.0-or-later
// Reconstructed individual coats over the licensed source maps. No geometry,
// texture allocation, historical identity or photographic acceptance is implied.
const recipes = new Map(), applied = new WeakMap();
export const hashHorse = text => {
  let h = 2166136261;
  for (const c of String(text)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); }
  // Avalanche prevents neighbouring channel suffixes from giving all four legs
  // nearly identical sock choices. Fixed integer arithmetic, never Math.random.
  h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b);
  h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
};
const need = (ok, message) => { if (!ok) throw Error('horse appearance: '+message); };
const rgb = value => Array.isArray(value) && value.length === 3 && value.every(x => Number.isFinite(x) && x >= 0 && x <= 1);
export function validateHorseRecipe(recipe) {
  need(recipe?.schema === 'chicago4d_horse_coats_v1' && recipe.grade === 'reconstructed'
    && recipe.liberty === 'L-horse-individual-coats-2795' && recipe.body_vertices === 5595, 'explicit reconstructed source contract required');
  need(recipe.body_material === 'Material_HorseMain4k00.png' && recipe.hair_material === 'Material.003_Hair12Main2k.png' && recipe.eye_material === 'Eye_brown', 'protected source material names differ');
  need(Array.isArray(recipe.source_contract) && recipe.source_contract.length === 2
    && recipe.source_contract.every(s => /^[a-f0-9]{64}$/.test(s.sha256) && s.body_vertices === 5595
      && recipe.sources?.some(input => input.file === s.file && input.sha256 === s.sha256)
      && s.joint_names?.length === 26 && new Set(s.joint_names).size === 26), 'two immutable canonical26 sources required');
  need(recipe.palettes?.length >= 3 && recipe.palettes.every(p => rgb(p.linear_rgb)
    && (p.mane_linear_rgb === null || rgb(p.mane_linear_rgb)) && p.dapple_strength >= 0 && p.dapple_strength <= .1), 'bounded natural palette required');
  need(recipe.mask_choices && Array.isArray(recipe.scenes) && recipe.group_palettes, 'mask and stable group definitions required');
  for (const value of Object.values(recipe.mask_choices)) if (typeof value !== 'string') {
    need((Array.isArray(value) ? value : [value]).every(Number.isFinite), 'finite mask parameters required');
  }
  need(Object.keys(recipe.foot_centres_m ?? {}).sort().join(',') === 'fore_l,fore_r,hind_l,hind_r', 'four source-derived feet required');
  need(Object.values(recipe.foot_centres_m).every(p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite)), 'finite source-derived feet required');
  const m = recipe.mask_choices;
  for (const key of ['sock_top_range_m', 'face_y_range_m', 'muzzle_protect_z_m', 'muzzle_protect_y_m', 'dapple_body_y_m', 'dapple_front_fade_z_m', 'hair_upper_y_m', 'hair_tail_z_m']) {
    need(Array.isArray(m[key]) && m[key].length === 2 && m[key][1] > m[key][0], 'ordered painting ranges required');
  }
  need(m.protect_below_y_m >= .1 && m.sock_top_range_m[0] > m.protect_below_y_m
    && m.sock_top_range_m[1] <= .65 && m.sock_radius_m > 0 && m.sock_radius_m < .25
    && m.sock_transition_m > 0 && m.dapple_pitch_m >= .03 && m.dapple_pitch_m <= .2
    && [m.brown_reference_luminance, m.white_reference_luminance, m.hair_reference_luminance].every(x => x > 0 && x <= 1), 'bounded metric painting parameters required');
  need(new Set(recipe.palettes.map(p => p.id)).size === recipe.palettes.length
    && Object.values(recipe.group_palettes).every(id => recipe.palettes.some(p => p.id === id)), 'distinct declared palettes required');
  const seed = recipe.seed_contract, choices = recipe.individual_choices;
  need(seed?.algorithm === 'fnv1a32_murmur3_avalanche_v1' && seed.encoding === 'ASCII'
    && seed.uint32_divisor === 4294967296 && seed.channel_separator === '|'
    && seed.channels?.phase?.length === 3 && choices, 'portable seed contract required');
  need([choices.sock_absent_probability, choices.blaze_absent_probability].every(x => x >= 0 && x <= 1)
    && [choices.blaze_halfwidth_range_m, choices.blaze_offset_range_m, choices.phase_range].every(a => Array.isArray(a) && a.length === 2 && a.every(Number.isFinite) && a[1] > a[0]), 'bounded individual choices required');
  return recipe;
}
export function loadHorseRecipe(base, file = 'transport/horse-coats.json') {
  const url = new URL(file, base).href;
  if (!recipes.has(url)) recipes.set(url, fetch(url).then(r => {
    need(r.ok, `recipe HTTP${r.status}`); return r.json();
  }).then(validateHorseRecipe).catch(error => { recipes.delete(url); throw error; }));
  return recipes.get(url);
}
export function horseIdentity(recipe, { scene, row, individual, team = row }) {
  validateHorseRecipe(recipe);
  need(recipe.scenes.includes(String(scene)) && [row, individual, team].every(x => typeof x === 'string' && /^[a-z0-9_-]+$/.test(x)), 'stable scene/row/individual keys required');
  const group = `${scene}:${team}`, key = `${scene}:${row}:${individual}`;
  const seed = recipe.seed_contract, choices = recipe.individual_choices, channels = seed.channels;
  const sample = channel => hashHorse(key+seed.channel_separator+channel)/seed.uint32_divisor;
  const range = (values, channel) => values[0]+(values[1]-values[0])*sample(channel);
  const named = recipe.group_palettes[group];
  const palette = named ? recipe.palettes.find(p => p.id === named) : recipe.palettes[hashHorse(group)%recipe.palettes.length];
  need(palette, 'unknown declared group palette');
  const [lo, hi] = recipe.mask_choices.sock_top_range_m;
  return { key, palette: palette.id, linear_rgb: [...palette.linear_rgb],
    mane_linear_rgb: palette.mane_linear_rgb && [...palette.mane_linear_rgb], dapple_strength: palette.dapple_strength,
    socks_m: [0, 1, 2, 3].map(i => sample(channels.sock_enabled.replace('{index}', i)) < choices.sock_absent_probability
      ? recipe.mask_choices.protect_below_y_m : lo+(hi-lo)*sample(channels.sock_height.replace('{index}', i))),
    blaze: [sample(channels.blaze_enabled) < choices.blaze_absent_probability ? 0 : range(choices.blaze_halfwidth_range_m, channels.blaze_width), range(choices.blaze_offset_range_m, channels.blaze_offset)],
    phase: channels.phase.map(channel => range(choices.phase_range, channel)),
    grade: 'reconstructed', liberty: recipe.liberty, historical_individual: false };
}

/** Prepare the explicit organic cache variant BEFORE any shared lease is exposed.
 * Replace material objects; never mutate the parsed source definitions or maps. */
export function prepareHorseTemplate(asset, variant) {
  if (variant !== 'organic_dielectric_v1') return asset;
  const copies = new Map();
  asset.scene.traverse(node => {
    if (!node.isMesh) return;
    const copy = material => {
      if (material.metalness === 0) return material;
      if (!copies.has(material)) { const clone = material.clone(); clone.metalness = 0; copies.set(material, clone); }
      return copies.get(material);
    };
    node.material = Array.isArray(node.material) ? node.material.map(copy) : copy(node.material);
  });
  return asset;
}

const noise = `
varying vec3 vChiHorseP;
uniform vec4 chiHorseColor;
uniform vec4 chiHorseStyle;
uniform vec4 chiHorseSocks;
uniform vec4 chiHorseFace;
uniform vec3 chiHorsePhase;
float chiHorseHash(vec3 p) {
  p=fract(p*.1031); p+=dot(p,p.yzx+33.33); return fract((p.x+p.y)*p.z);
}
float chiHorseNoise(vec3 p) {
  vec3 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(mix(chiHorseHash(i),chiHorseHash(i+vec3(1,0,0)),f.x),
    mix(chiHorseHash(i+vec3(0,1,0)),chiHorseHash(i+vec3(1,1,0)),f.x),f.y),
    mix(mix(chiHorseHash(i+vec3(0,0,1)),chiHorseHash(i+vec3(1,0,1)),f.x),
    mix(chiHorseHash(i+vec3(0,1,1)),chiHorseHash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
float chiHorseBand(float x,float a,float b) { return smoothstep(a-.012,a,x)*(1.0-smoothstep(b,b+.012,x)); }
`;
function colourCode(recipe) {
  const m = recipe.mask_choices, f = x => { need(Number.isFinite(x), 'invalid GLSL scalar'); return x.toFixed(6); };
  const band = (axis, pair) => `chiHorseBand(${axis},${f(pair[0])},${f(pair[1])})`;
  const feet = ['fore_l', 'fore_r', 'hind_l', 'hind_r'].map((name, i) => {
    const p = recipe.foot_centres_m[name];
    return `sock=max(sock,(1.0-smoothstep(${f(m.sock_radius_m*.65)},${f(m.sock_radius_m)},length(p.xz-vec2(${f(p[0])},${f(p[2])}))))*(1.0-smoothstep(chiHorseSocks[${i}]+edge,chiHorseSocks[${i}]+edge+${f(m.sock_transition_m)},p.y)));`;
  }).join('\n');
  return `{
    vec3 p=vChiHorseP, source=diffuseColor.rgb;
    float lum=max(dot(source,vec3(.2126,.7152,.0722)),.0001);
    float n=chiHorseNoise(p/${f(m.dapple_pitch_m)}+chiHorsePhase);
    float white=smoothstep(.22,.5,lum)*(1.0-smoothstep(.035,.12,max(source.r,max(source.g,source.b))-min(source.r,min(source.g,source.b))));
    float detail=mix(clamp(lum/${f(m.brown_reference_luminance)},.4,1.7),clamp(lum/${f(m.white_reference_luminance)},.65,1.3),white);
    float muzzle=smoothstep(${f(m.muzzle_protect_z_m[0])},${f(m.muzzle_protect_z_m[1])},p.z)*(1.0-smoothstep(${f(m.muzzle_protect_y_m[0])},${f(m.muzzle_protect_y_m[1])},p.y));
    // Eyes use their own untouched material. Eyelid fur follows the coat;
    // protecting a BODY box here left a visible brown rectangle on grey horses.
    float paint=smoothstep(${f(m.protect_below_y_m)},${f(m.protect_below_y_m+.05)},p.y)*(1.0-muzzle);
    vec3 coat=chiHorseColor.rgb*detail;
    float fade=clamp(1.0-length(fwidth(p))/${f(m.dapple_pitch_m)}*2.0,0.0,1.0);
    coat*=1.0+chiHorseColor.a*(n-.5)*2.0*fade*smoothstep(${f(m.dapple_body_y_m[0])},${f(m.dapple_body_y_m[1])},p.y)*(1.0-smoothstep(${f(m.dapple_front_fade_z_m[0])},${f(m.dapple_front_fade_z_m[1])},p.z));
    float sock=0.0,edge=(n-.5)*.008;
    ${feet}
    float face=${band('p.y', m.face_y_range_m)}*smoothstep(${f(m.face_z_min_m)},${f(m.face_z_min_m+.05)},p.z)*(1.0-smoothstep(${f(m.face_halfwidth_m)},${f(m.face_halfwidth_m+.01)},abs(p.x)));
    float blaze=step(.0001,chiHorseFace.x)*face*(1.0-smoothstep(chiHorseFace.x,chiHorseFace.x+.012,abs(p.x-chiHorseFace.y-(n-.5)*.008)));
    coat=mix(coat,vec3(.58,.56,.51)*detail,max(sock,blaze));
    if(chiHorseStyle.x>0.5) {
      paint=max(smoothstep(${f(m.hair_upper_y_m[0])},${f(m.hair_upper_y_m[1])},p.y),1.0-smoothstep(${f(m.hair_tail_z_m[0])},${f(m.hair_tail_z_m[1])},p.z))*(1.0-smoothstep(.15,.3,lum));
      coat=chiHorseColor.rgb*clamp(lum/${f(m.hair_reference_luminance)},.4,1.8);
    }
    diffuseColor.rgb=mix(source,coat,paint);
  }`;
}

/** Own only required coat/mane material copies. Texture and geometry pointers
 * stay shared. An existing private owner (standing) may supply ownedMaterials. */
export function applyHorseAppearance(root, { recipe, sourceSha, scene, row, individual, team = row,
  confidence = null, ownedMaterials = null } = {}) {
  if (!recipe) return { identity: null, dispose() {} }; // Legacy adapters remain compatible.
  validateHorseRecipe(recipe);
  need(recipe.source_contract.some(s => s.sha256 === sourceSha), 'unbound source; do not guess a geometry mask');
  const identity = horseIdentity(recipe, { scene: String(scene), row, individual, team });
  if (applied.has(root)) {
    const existing = applied.get(root);
    need(existing.identity.key === identity.key && existing.identity.source_sha256 === sourceSha, 'live root already belongs to another individual');
    return existing;
  }
  identity.source_sha256 = sourceSha;
  const materials = new Map(), changes = [], owned = new Set();
  let bodies = 0;
  try {
    root.traverse(node => {
      if (!node.isMesh || Array.isArray(node.material)) return;
      const original = node.material, body = original.name === recipe.body_material;
      const hair = original.name === recipe.hair_material && identity.mane_linear_rgb;
      if (!body && !hair) return; // Eye material is never decorated or tinted.
      if (body) { bodies++; need(node.geometry.attributes.position.count === 5595 && node.skeleton?.bones.length === 26, 'BODY/rig differs'); }
      let material = materials.get(original);
      if (!material) {
        material = ownedMaterials?.has(original) ? original : original.clone();
        if (material !== original) owned.add(material);
        materials.set(original, material);
        // clone() copies userData, NOT onBeforeCompile. Never trust a copied marker.
        confidence?.patch?.(material);
        const prior = material.onBeforeCompile, hadKey = Object.hasOwn(material, 'customProgramCacheKey');
        const priorKey = hadKey ? String(material.customProgramCacheKey()) : prior.toString();
        const uniforms = { chiHorseColor: { value: [...(hair ? identity.mane_linear_rgb : identity.linear_rgb), hair ? 0 : identity.dapple_strength] },
          chiHorseStyle: { value: [hair ? 1 : 0, 0, 0, 0] }, chiHorseSocks: { value: identity.socks_m },
          chiHorseFace: { value: [...identity.blaze, 0, 0] }, chiHorsePhase: { value: identity.phase } };
        material.onBeforeCompile = function(shader, renderer) {
          prior.call(this, shader, renderer);
          need(shader.vertexShader.includes('#include <begin_vertex>') && shader.fragmentShader.includes('#include <map_fragment>'), 'shader anchors missing');
          Object.assign(shader.uniforms, uniforms);
          shader.vertexShader = 'varying vec3 vChiHorseP;\n'+shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n vChiHorseP=position;');
          shader.fragmentShader = noise+shader.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n'+colourCode(recipe));
        };
        const codeKey = hashHorse(JSON.stringify([recipe.mask_choices, recipe.foot_centres_m]));
        material.customProgramCacheKey = () => `${priorKey}|chicago-horse-coat-v1:${codeKey}`;
        material.userData.chicagoHorseCoat = { ...identity, source_sha256: sourceSha };
        material.needsUpdate = true;
      }
      node.material = material; changes.push([node, original]);
    });
    need(bodies === 1, 'one actual classified BODY is required');
  } catch (error) {
    for (const [node, material] of changes) node.material = material;
    for (const material of owned) material.dispose();
    throw error;
  }
  let disposed = false;
  const result = { identity, dispose() {
    if (disposed) return; disposed = true;
    for (const [node, material] of changes) node.material = material;
    for (const material of owned) material.dispose(); // Borrowed maps/geometry are NOT disposed.
    applied.delete(root);
  } };
  applied.set(root, result);
  return result;
}
