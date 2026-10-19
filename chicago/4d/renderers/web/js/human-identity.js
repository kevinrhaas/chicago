// SPDX-License-Identifier: GPL-3.0-or-later
/** Anonymous roles are reconstructions, never entries in the resident directory. */
const ROLES = new Set(['standing', 'walking', 'driver', 'rider']);
const inPeriod = (period, year) => Number.isInteger(period?.earliest_year)
  && Number.isInteger(period?.latest_year) && period.earliest_year <= year && year <= period.latest_year;
const fail = (why) => { throw new Error(`human identity: ${why}`); };
export function resolveHumanIdentity(instance, { sceneId = instance.scene, people = [], profiles = [] } = {}) {
  const named = Object.hasOwn(instance, 'person_id'), anonymous = Object.hasOwn(instance, 'anonymous_profile_id');
  if (named === anonymous) fail('exactly one of person_id or anonymous_profile_id is required');
  if (String(instance.scene) !== String(sceneId) || !/^\d{4}$/.test(String(sceneId))) fail('wrong scene/date');
  if (named) {
    if (Object.hasOwn(instance, 'role')) fail('named residents do not use anonymous role identity');
    if (instance.interaction?.opens === 'role_card') fail('named resident cannot open anonymous role card');
    const person = people.find(p => p.id === instance.person_id);
    if (!person) fail(`person ${instance.person_id} is not in sidecars/${sceneId}/people.json; anonymous roles must not mint a person`);
    return { kind: 'person', personId: person.id, person, profile: null, role: null };
  }
  if (instance.interaction?.opens === 'resident_card') fail('anonymous role cannot open a resident card');
  const profile = profiles.find(p => p.id === instance.anonymous_profile_id);
  if (!profile || profile.identity_kind !== 'anonymous' || profile.age_group !== 'adult' || profile.fallback_only !== true) fail('unknown anonymous adult profile');
  if (!ROLES.has(instance.role) || !profile.roles?.includes(instance.role)) fail('role is not eligible for this profile');
  if (typeof instance.fallback_basis !== 'string' || instance.fallback_basis.trim().length < 40 || !Array.isArray(instance.considered_person_ids)) fail('anonymous fallback requires an explicit no-suitable-person basis and considered person IDs');
  if (instance.considered_person_ids.some(id => !people.some(p => p.id === id))) fail('considered person does not resolve in this scene');
  const year = Number(sceneId);
  if (!inPeriod(profile.period, year)) fail('profile is not eligible for scene date');
  const asset = profile.eligible_assets?.find(a => a.asset_id === instance.appearance?.asset_id && inPeriod(a.period, year));
  if (!asset || typeof asset.wardrobe_basis !== 'string' || asset.wardrobe_basis.trim().length < 20) fail('asset/wardrobe is not accepted for this profile and date');
  if (profile.provenance?.grade !== 'reconstructed' || instance.provenance?.grade !== 'reconstructed') fail('anonymous role identity must remain reconstructed');
  return { kind: 'anonymous', personId: null, person: null, profile, role: instance.role, wardrobeBasis: asset.wardrobe_basis };
}
export function humanRoleCard(identity, instance) {
  if (identity.kind !== 'anonymous') return null;
  return { title: `Anonymous adult ${identity.role}`, profileId: identity.profile.id, instanceId: instance.id,
    scene: instance.scene, grade: 'reconstructed', basis: instance.provenance.basis,
    wardrobeBasis: identity.wardrobeBasis, fallbackBasis: instance.fallback_basis,
    description: 'An anonymous reconstructed adult role, not an identified historical resident or an attested likeness.' };
}
