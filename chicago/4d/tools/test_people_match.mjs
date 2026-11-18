// T-3417: the people match's records hold together (data/people_match/README.md). No browser and
// no evidence clone: the rig (tools/people_match.mjs) verifies the pictures' bytes when it shoots;
// this holds what the tree says about them.
//
// - every reference set: an id, role, years and scenes; two or more pictures, near and far, each
//   with a sha256, a caption, the copy and crop it is, and a source_id that resolves in
//   data/sources/ (AGENTS.md rule 1);
// - every subject: a set that judges its scene, a transport row that drives that person in that
//   scene, the fixed rig (one still at 3 m, one at 10 m) and a clip of about 5 seconds;
// - every match record: each checklist item answered, a verdict its items allow, a still per band
//   and viewport, and no verdict given on a figure that has since changed;
// - a stage subject (T-3553, the catalogue's figures on tools/people_match_stage.html): the body
//   its instance record wears, a pose and a time for every still and the clip, pair pictures of
//   the right band, and differences each with a status.
// Then it breaks a copy of each record in memory, one way at a time, and expects the refusal.
import assert from 'node:assert/strict';
import { checkAll, checkSet, checkSubject, checkMatch, readJSON, boundValues, CHECKLIST } from './people_match_records.mjs';

const root = process.cwd();
const { errs, sets, subjects, counts } = checkAll(root);
if (errs.length) { for (const e of errs) console.error(`FAIL ${e}`); process.exit(1); }
assert.ok(counts.sets >= 1 && counts.subjects >= 1, 'the coachman set and Hans are on file');

// ---- refusals, on copies -----------------------------------------------------------------
const clone = o => JSON.parse(JSON.stringify(o));
let refusals = 0;
const refuses = (label, errsOf, pattern) => {
  refusals++;
  const got = errsOf();
  assert.ok(got.some(e => pattern.test(e)), `${label}: expected a refusal matching ${pattern}, got ${JSON.stringify(got)}`);
};
const set = clone(sets.get('coachman_1904'));
const subject = clone(subjects.get('hans_johnson_1904'));
const setsWith = s => new Map([[s.id, s]]);

refuses('an invented source', () => { const s = clone(set); s.pictures[0].source_id = 'no_such_source'; return checkSet(root, s); }, /does not resolve/);
refuses('one picture', () => { const s = clone(set); s.pictures = s.pictures.slice(0, 1); return checkSet(root, s); }, /at least two pictures/);
refuses('no far picture', () => { const s = clone(set); s.pictures = s.pictures.filter(p => p.band === 'near'); return checkSet(root, s); }, /no far picture/);
refuses('no sha256', () => { const s = clone(set); delete s.pictures[0].sha256; return checkSet(root, s); }, /sha256/);
refuses('no evidence folder', () => { const s = clone(set); s.evidence.repo = 'kevinrhaas/chicago'; return checkSet(root, s); }, /chicago-evidence/);
refuses('a 5 m still', () => { const s = clone(subject); s.stills[0].distance_m = 5; return checkSubject(root, s, setsWith(set)); }, /exactly one at each/);
refuses('the wrong person on the row', () => { const s = clone(subject); s.person_id = 'rc_bardwell_otis'; return checkSubject(root, s, setsWith(set)); }, /drives/);
refuses('a set for another scene', () => { const s = clone(set); s.scenes = ['1835']; return checkSubject(root, subject, setsWith(s)); }, /does not judge scene/);
refuses('a one-second clip', () => { const s = clone(subject); s.clip.interval_s = 0.25; return checkSubject(root, s, setsWith(set)); }, /about 5 seconds/);

const stills = Object.fromEntries(['near', 'far'].flatMap(b => ['desktop', 'phone'].map(v => [`${b}-${v}`, { file: `x/${b}-${v}.jpg`, sha256: 'a'.repeat(64) }])));
const answered = status => Object.fromEntries(Object.keys(CHECKLIST).map(k => [k, { what: CHECKLIST[k], status, note: 'read' }]));
const bound = (() => { const row = readJSON(root, subject.bound.file).rows.find(r => r.id === subject.bound.row); return Object.fromEntries(subject.bound.keys.map(k => [k, row[k] ?? null])); })();
const match = { subject: subject.id, reference_set: set.id, shot: { date: '2026-11-06', target: 'dev' }, bound, stills, verdict: 'matches', checklist: answered('reads') };
assert.deepEqual(checkMatch(root, match, subject), [], 'a complete approval on the current figure is accepted');
refuses('matches with an open item', () => { const m = clone(match); m.checklist.hands.status = 'open'; return checkMatch(root, m, subject); }, /open items: hands/);
refuses('differs with nothing open', () => { const m = clone(match); m.verdict = 'differs'; return checkMatch(root, m, subject); }, /names no open item/);
refuses('an unanswered item', () => { const m = clone(match); delete m.checklist.skin; return checkMatch(root, m, subject); }, /checklist.skin is missing/);
refuses('a missing phone still', () => { const m = clone(match); delete m.stills['far-phone']; return checkMatch(root, m, subject); }, /far-phone/);
refuses('an approval of an earlier livery', () => { const m = clone(match); m.bound.driver_livery_sha256 = '0'.repeat(64); return checkMatch(root, m, subject); }, /different figure \(driver_livery_sha256/);
{ const m = clone(match); m.bound.driver_livery_sha256 = '0'.repeat(64); m.verdict = 'unreviewed'; assert.deepEqual(checkMatch(root, m, subject), [], 'an unreviewed record of an earlier figure waits for its reshoot'); }

// ---- a stage subject (T-3553: the catalogue's figures, stood or walked on the stage page) ----
const stageSubject = [...subjects.values()].find(s => s.find?.kind === 'stage');
if (stageSubject) {
  const sset = clone(sets.get(stageSubject.reference_set));
  const ss = clone(stageSubject);
  assert.deepEqual(checkSubject(root, ss, setsWith(sset)), [], `${ss.id}: the stage subject on file is accepted`);
  refuses('a stage body the record does not wear', () => { const s = clone(ss); s.find.asset = 'hans_johnson_1904'; return checkSubject(root, s, setsWith(sset)); }, /wears/);
  refuses('a stage still with no pose', () => { const s = clone(ss); delete s.stills[0].pose; return checkSubject(root, s, setsWith(sset)); }, /pose must be one of/);
  refuses('a stage still at no time', () => { const s = clone(ss); s.stills[1].at_s = -1; return checkSubject(root, s, setsWith(sset)); }, /at_s/);
  refuses('a stage clip with no pose', () => { const s = clone(ss); delete s.clip.pose; return checkSubject(root, s, setsWith(sset)); }, /clip.pose/);
  refuses('a stage bound without the body', () => { const s = clone(ss); s.bound.keys = ['animation']; return checkSubject(root, s, setsWith(sset)); }, /appearance among the keys/);
  refuses('a pair picture of the wrong band', () => { const s = clone(ss); const far = sset.pictures.find(p => p.band === 'far'); s.pair = { near: far.name }; return checkSubject(root, s, setsWith(sset)); }, /is a far picture/);
  refuses('a pair picture not in the set', () => { const s = clone(ss); s.pair = { near: 'no_such_picture' }; return checkSubject(root, s, setsWith(sset)); }, /is not a picture of/);
  const sbound = (() => { const rec = readJSON(root, ss.bound.file); return Object.fromEntries(ss.bound.keys.map(k => [k, rec[k] ?? null])); })();
  const smatch = { subject: ss.id, reference_set: sset.id, shot: { date: '2026-11-17', target: 'stage' }, bound: { ...sbound, asset_lod0_sha256: 'f'.repeat(64) }, stills, verdict: 'differs',
    checklist: { ...answered('reads'), silhouette: { what: CHECKLIST.silhouette, status: 'open', note: 'read' } },
    differences: [{ what: 'collar', picture: 'high', ours: 'low', status: 'open' }] };
  refuses('a verdict on a rebuilt body', () => checkMatch(root, smatch, ss), /asset_lod0_sha256/);
  { const m = clone(smatch); m.verdict = 'unreviewed'; assert.deepEqual(checkMatch(root, m, ss), [], 'an unreviewed stage record of an earlier body waits for its reshoot'); }
  refuses('a difference with no status', () => { const m = clone(smatch); m.verdict = 'unreviewed'; delete m.differences[0].status; return checkMatch(root, m, ss); }, /differences\[0\]\.status/);
  refuses('matches with an open difference', () => { const m = clone(smatch); m.verdict = 'matches'; m.checklist = answered('reads'); m.bound = boundValues(root, ss); return checkMatch(root, m, ss); }, /open difference/);
}

console.log(`OK people match: ${counts.sets} reference set(s), ${counts.subjects} subject(s), ${counts.matches} match record(s); ${refusals} refusals hold`);
