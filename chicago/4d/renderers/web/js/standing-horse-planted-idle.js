// SPDX-License-Identifier: GPL-3.0-or-later
// Play one explicit glTF planted-standing clip; no procedural bone motion/blend.
export const LEGACY_PLANTED_SHA = '925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48';
export const LID_PLANTED_SHA = '5a2b2e87c3931e3ab82be3ce3bc69724a0a088aac30920cea9ad348bbaf8fad5';
export const PLANTED_MODE = 'upper_orbital_transition_v1';
export const PLANTED_SHA = 'e49b6f1c9f7b70f1fcdf19fa7f6dddf54048b32256b4d8030d6238d6dfe79d49';
export const PLANTED_BYTES = 4159196;
export const PLANTED_MASTERS = Object.freeze({
  anatomy_r3: Object.freeze({ sha256: LEGACY_PLANTED_SHA, bytes: 4158016 }),
  canonical_socket_interface_v1: Object.freeze({ sha256: LID_PLANTED_SHA, bytes: 4158848,
    qualification_sha256: '5fb50fed07a041c76e2a1300a9040600628f59671b8a27d7f4483bc8dc880ca1' }),
  upper_orbital_transition_v1: Object.freeze({ sha256: PLANTED_SHA, bytes: PLANTED_BYTES,
    qualification_sha256: '72506859017d1f1aea57ad248d877a88bb07e701d4ec82c31e509dbb97e8d7a0' }),
});
export const PLANTED_TRIANGLES = 17390;
export const PLANTED_CLIP = 'sevket_reconstructed_planted_posture_v1';
const ROTATIONS = [7, 8, 9, 12, 13, 14, 17, 18, 19, 22, 23, 24];
const NAMES = { 1: 'horse_body', 7: 'fore_l_elbow', 8: 'fore_l_carpus', 9: 'fore_l_fetlock',
  12: 'fore_r_elbow', 13: 'fore_r_carpus', 14: 'fore_r_fetlock', 17: 'hind_l_stifle',
  18: 'hind_l_hock', 19: 'hind_l_fetlock', 22: 'hind_r_stifle', 23: 'hind_r_hock', 24: 'hind_r_fetlock' };
const OWNER = Symbol('plantedStandingOwner');
const check = (ok, message) => { if (!ok) throw Error('HorseStandingContract: ' + message); };
const hash = text => { let h = 2166136261; for (const c of text) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };

/** Bytes are SHA-verified by caller before this metadata/inventory guard. */
export function validatePlantedStandingHeader(bytes, spec) {
  const mode = spec.runtime_asset?.source_qualification_mode ?? 'anatomy_r3';
  const master = Object.hasOwn(PLANTED_MASTERS, mode) ? PLANTED_MASTERS[mode] : null;
  check(master && spec.runtime_asset?.sha256 === master.sha256 && spec.runtime_asset.bytes === master.bytes,
    'explicit standing asset identity and qualification mode required');
  if (master.qualification_sha256) check(spec.runtime_asset.qualification_sha256 === master.qualification_sha256,
    'exact source socket qualification required');
  check(spec.runtime_scale_m_per_unit === 1 && spec.runtime_origin_m?.length === 3
    && spec.runtime_origin_m.every(v => v === 0), 'canonical metres require unit scale and zero origin');
  check(bytes.byteLength === master.bytes && bytes.byteLength <= 4 * 1024 * 1024, 'standing byte budget changed');
  const view = new DataView(bytes);
  check(view.getUint32(0, true) === 0x46546c67 && view.getUint32(4, true) === 2
    && view.getUint32(8, true) === bytes.byteLength && view.getUint32(16, true) === 0x4e4f534a,
  'expected complete glTF2 binary');
  const length = view.getUint32(12, true);
  check(length > 0 && length <= bytes.byteLength - 20, 'invalid JSON chunk');
  const json = JSON.parse(new TextDecoder().decode(new Uint8Array(bytes, 20, length)));
  check(json.asset?.extras?.chicago4d_anatomy_master_v2?.parent_sha256
    === 'd4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914',
  'source-bound anatomy parent required');
  if (mode === PLANTED_MODE || mode === 'canonical_socket_interface_v1') {
    const lid = json.asset?.extras?.chicago4d_upper_lid_strip_v1;
    check(lid?.parent_sha256 === LEGACY_PLANTED_SHA
      && lid.original_d454_sha256 === 'd4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914'
      && lid.recipe_sha256 === 'f77e115a340a6cbb8d6efb1b7887c8cdba001a47f493b97be6ffb0eee72dd133'
      && JSON.stringify(lid.internal_BODY_UV_repair_rows) === '[2410,2412]',
    'source-bound upper-lid parent/recipe/UV ownership required');
  }
  if (mode === PLANTED_MODE) {
    const orbital = json.asset?.extras?.upper_orbital_transition_v1;
    check(orbital?.parent_sha256 === LID_PLANTED_SHA
      && orbital.recipe_sha256 === '23850a915289ac7d73ea6619a7b68d07c9c240e177917f10f4488f996f66db70'
      && orbital.position_rows === 10 && orbital.affected_faces === 44,
    'explicit upper-orbital parent/recipe/source region required');
  }
  check(!json.extensionsRequired?.length && json.buffers.length === 1 && !json.buffers[0].uri,
    'embedded reviewed standing buffer required');
  check(json.images.length === 6 && json.images.every(i => Number.isInteger(i.bufferView) && !i.uri)
    && json.materials.length === 3, 'standing image/material inventory changed');
  check(json.skins.length === 1 && json.skins[0].joints.length === 26
    && json.skins[0].joints.every((j, i) => j === i), 'exact reconstructed26 rig required');
  check(json.animations.length === 1 && json.animations[0].name === PLANTED_CLIP,
    'only planted-standing clip permitted');
  const clip = json.animations[0], targets = new Set();
  check(clip.channels.length === 13 && clip.samplers.length === 13, 'standing track inventory changed');
  for (const channel of clip.channels) {
    const { node, path } = channel.target, key = `${node}:${path}`;
    check((node === 1 && path === 'translation') || (ROTATIONS.includes(node) && path === 'rotation'),
      'unapproved root/head/tail/hoof or walking channel');
    check(!targets.has(key) && json.nodes[node].name === NAMES[node], 'standing joint identity changed');
    targets.add(key);
    const sampler = clip.samplers[channel.sampler], input = json.accessors[sampler.input], output = json.accessors[sampler.output];
    check(sampler.interpolation === 'LINEAR' && input.componentType === 5126 && input.type === 'SCALAR'
      && input.count === 65 && input.min?.[0] === 0 && input.max?.[0] === 12
      && output.componentType === 5126 && output.count === 65 && output.type === (path === 'translation' ? 'VEC3' : 'VEC4'),
    'standing65 key/time/interpolation contract changed');
  }
  let triangles = 0;
  for (const mesh of json.meshes) for (const p of mesh.primitives) {
    check((p.mode ?? 4) === 4 && p.indices !== undefined, 'indexed standing triangles required');
    triangles += json.accessors[p.indices].count / 3;
  }
  check(json.meshes.length === 3 && triangles === PLANTED_TRIANGLES, 'standing mesh/triangle budget changed');
  return json;
}

export function createPlantedStandingHorseIdle({ T, root, clips, verifiedDerivedSha256, instanceId,
  sourceQualificationMode = 'anatomy_r3' }) {
  const master = Object.hasOwn(PLANTED_MASTERS, sourceQualificationMode) ? PLANTED_MASTERS[sourceQualificationMode] : null;
  check(master && verifiedDerivedSha256 === master.sha256 && typeof instanceId === 'string' && instanceId.length > 0,
    'source-bound standing identity required');
  check(!root.userData[OWNER], 'standing clone already has an animation owner');
  const meshes = []; root.traverse(n => { if (n.isMesh) meshes.push(n); });
  check(meshes.length === 3 && meshes.every(m => m.isSkinnedMesh && m.skeleton.bones.length === 26),
    'standing skin inventory changed');
  const bones = meshes[0].skeleton.bones;
  check(meshes.every(m => m.skeleton.bones.every((b, i) => b === bones[i])), 'standing joint order/identity changed');
  const clip = clips[0];
  check(clips.length === 1 && clip.name === PLANTED_CLIP && clip.duration === 12 && clip.tracks.length === 13,
    'single exported standing12s clip required');
  const targets = new Set();
  for (const track of clip.tracks) {
    const parsed = T.PropertyBinding.parseTrackName(track.name), node = T.PropertyBinding.findNode(root, parsed.nodeName);
    const joint = bones.indexOf(node), key = `${joint}:${parsed.propertyName}`;
    check((joint === 1 && parsed.propertyName === 'position')
      || (ROTATIONS.includes(joint) && parsed.propertyName === 'quaternion'), 'unexpected standing track target');
    check(node.name === NAMES[joint] && !targets.has(key), 'standing target duplicate or name mismatch'); targets.add(key);
    check(track.times.length === 65 && track.times[0] === 0 && track.times[64] === 12,
      'loaded standing sample times changed');
  }
  const mixer = new T.AnimationMixer(root), action = mixer.clipAction(clip);
  action.setLoop(T.LoopRepeat, Infinity); action.play(); mixer.setTime(0); root.userData[OWNER] = true;
  const delay = 2 * hash(instanceId) / 4294967295, rate = .96 + .08 * hash(instanceId + '|rate') / 4294967295;
  let disposed = false, elapsed = 0, age = 0;
  return {
    update(dt, { visible = true, reducedMotion = false, paused = false } = {}) {
      if (disposed) return; check(Number.isFinite(dt) && dt >= 0, 'invalid standing host delta');
      if (!visible || reducedMotion || paused) return;
      const before = age; age += dt;
      const advance = (Math.max(0, age - delay) - Math.max(0, before - delay)) * rate;
      elapsed += advance; mixer.update(advance);
    },
    get status() { return { elapsed_s: elapsed, disposed, clip: PLANTED_CLIP,
      source_qualification_mode: sourceQualificationMode, derived_sha256: verifiedDerivedSha256,
      initial_rest_delay_s: delay, deterministic_playback_rate: rate, mixer_count: disposed ? 0 : 1,
      weight_shift: true, head_tail_composed: false, independent_ear_motion: false, walk: false, trot: false }; },
    dispose() { if (disposed) return; disposed = true; mixer.stopAllAction(); mixer.uncacheRoot(root); delete root.userData[OWNER]; },
  };
}
