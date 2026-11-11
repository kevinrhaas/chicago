// SPDX-License-Identifier: GPL-3.0-or-later
// Guard/parser controls over the real inventory; no browser, GLB writes or mocks.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { TEAMSTER_IDS, CHARLES_COAT_ID, SETTLER_ID, PRAIRIE_CHILD_IDS, parseFixtureArgs, teamsterFiles, scopedFiles, prepareFixtureScope, mergeFixtureScope } from './human_fixture_scope.mjs';

// The gate's explicit check mode runs this same complete assertion suite.
const cliArgs = process.argv.slice(2);
if (cliArgs.length > 1 || (cliArgs.length === 1 && cliArgs[0] !== '--check')) {
  console.error('usage: node tools/test_human_fixture_scope.mjs [--check]');
  process.exit(2);
}

const fullBaseline = JSON.parse(readFileSync(new URL('../data/humans/fixture.measure.json', import.meta.url)));
const childFiles = new Set(scopedFiles(PRAIRIE_CHILD_IDS));
// Keep the original 248-file admission scenario intact after the separate child
// admission adds its rows. The new scope below also checks the complete inventory.
const baseline = { ...fullBaseline, files: fullBaseline.files.filter(row => !childFiles.has(row.file)) };
const recipe = JSON.parse(readFileSync(new URL('../data/humans/recipes/worker_1835.json', import.meta.url)));
const sha = value => createHash('sha256').update(value).digest('hex');
const clone = value => JSON.parse(JSON.stringify(value));
const date = '2026-11-10';
function inputs() {
  const document = clone(baseline);
  const files = [...new Set([...document.files.map(row => row.file), ...teamsterFiles(TEAMSTER_IDS)])];
  const hashes = new Map(document.files.map(row => [row.file, row.sha256]));
  for (const file of teamsterFiles(TEAMSTER_IDS)) hashes.set(file, sha('guard-test-new-output:'+file));
  return { baseline: document, files, hashes, assetIds: [...TEAMSTER_IDS] };
}
function measured(scope) {
  const rows = new Map(scope.baseline.files.map(row => [row.file, row]));
  return scope.selectedFiles.map(file => {
    // New Joseph/Martin rows are synthetic guard inputs, never engine output.
    const old = rows.get(file) ?? rows.get(file.replace(/dufresne_joseph_1835|flynn_martin_1835/, 'bardwell_otis_1835'))
      ?? rows.get(file.replace(/(?:child_boy|child_girl|child_toddler|teen_boy|teen_girl)_1904/, 'child_boy_1812'));
    return { ...clone(old), file, sha256: scope.hashes.get(file), triangles: old.triangles + 1,
      derivative_of: file.includes('/web/') ? file.replace('/web/', '/') : null };
  });
}

test('default full modes remain available; scoped mode names the actual three recipe IDs', () => {
  assert.deepEqual([...TEAMSTER_IDS].sort(), recipe.proof_variants.map(v => v.id).sort());
  for (const mode of ['', '--write', '--check']) assert.deepEqual(parseFixtureArgs(mode ? [mode] : []), { mode, assetIds: null });
  assert.deepEqual(parseFixtureArgs(['--write', '--asset-ids', [...TEAMSTER_IDS].reverse().join(',')]),
    { mode: '--write', assetIds: [...TEAMSTER_IDS] });
});

test('partial sets, duplicates, wrong IDs, unknown arguments and scoped check are refused', () => {
  const ids = TEAMSTER_IDS.join(',');
  for (const args of [ ['--asset-ids', ids], ['--check', '--asset-ids', ids], ['--write', '--asset-ids'],
    ['--write', '--asset-ids', TEAMSTER_IDS.slice(0, 2).join(',')], ['--write', '--asset-ids', ids+',other'],
    ['--write', '--asset-ids', [TEAMSTER_IDS[0], TEAMSTER_IDS[0], TEAMSTER_IDS[2]].join(',')],
    ['--write', '--asset-ids', ids, '--asset-ids', ids], ['--write', '--check'], ['--unknown'] ]) {
    assert.throws(() => parseFixtureArgs(args), /human fixture scope/);
  }
});

test('248 baseline files plus 16 explicit additions select 24 source/web LODs and retain 240', () => {
  const state = inputs(), scope = prepareFixtureScope(state);
  assert.equal(state.baseline.files.length, 248); assert.equal(state.files.length, 264);
  assert.equal(scope.selectedFiles.length, 24); assert.equal(scope.unchangedCount, 240); assert.equal(scope.addedCount, 16);
  assert.equal(new Set(scope.selectedFiles).size, 24);
  for (const id of TEAMSTER_IDS) {
    assert.equal(scope.selectedFiles.filter(file => file.includes('/'+id+'.lod')).length, 8);
    for (const dir of ['assets/humans', 'assets/humans/web']) for (const lod of [0, 1, 2, 3]) {
      assert(scope.selectedFiles.includes(`${dir}/${id}.lod${lod}.glb`));
    }
  }
});

test('any changed unscoped byte binding or failed baseline verdict prevents native scope', () => {
  const state = inputs(), selected = new Set(teamsterFiles(TEAMSTER_IDS));
  const other = state.files.find(file => !selected.has(file));
  state.hashes.set(other, sha('changed-unrelated-asset'));
  assert.throws(() => prepareFixtureScope(state), /unscoped file changed/);
  const failed = inputs(); failed.baseline.files.find(row => row.file === other).verdicts[0].ok = false;
  assert.throws(() => prepareFixtureScope(failed), /failed\/empty verdicts/);
});

test('added, missing, duplicate and unbound files cannot disappear behind a scope', () => {
  const extra = inputs(); extra.files.push('assets/humans/unrelated.lod0.glb'); extra.hashes.set(extra.files.at(-1), sha('extra'));
  assert.throws(() => prepareFixtureScope(extra), /inventory differs/);
  const absent = inputs(), file = teamsterFiles(TEAMSTER_IDS)[0];
  absent.files = absent.files.filter(name => name !== file); absent.hashes.delete(file);
  assert.throws(() => prepareFixtureScope(absent), /all 24/);
  absent.baseline.files = absent.baseline.files.filter(row => row.file !== file);
  assert.throws(() => prepareFixtureScope(absent), /all 24/);
  const missingOld = inputs(), selected = new Set(teamsterFiles(TEAMSTER_IDS));
  const oldFile = missingOld.files.find(name => !selected.has(name));
  missingOld.files = missingOld.files.filter(name => name !== oldFile); missingOld.hashes.delete(oldFile);
  assert.throws(() => prepareFixtureScope(missingOld), /baseline removals forbidden/);
  const missingNew = inputs(), newFile = teamsterFiles(TEAMSTER_IDS).find(name => !baseline.files.some(row => row.file === name));
  missingNew.files = missingNew.files.filter(name => name !== newFile); missingNew.hashes.delete(newFile);
  assert.throws(() => prepareFixtureScope(missingNew), /all 24/);
  const duplicate = inputs(); duplicate.baseline.files.push(clone(duplicate.baseline.files[0]));
  assert.throws(() => prepareFixtureScope(duplicate), /duplicate/);
  const noHash = inputs(); noHash.hashes.delete(noHash.files[0]);
  assert.throws(() => prepareFixtureScope(noHash), /complete actual file inventory/);
});

test('merging updates only the measured rows, preserves old rows/date, and records the scope honestly', () => {
  const state = inputs(), before = JSON.stringify(state.baseline), scope = prepareFixtureScope(state);
  const rows = measured(scope), merged = mergeFixtureScope(scope, rows, state.files, state.hashes, date);
  assert.equal(JSON.stringify(state.baseline), before);
  assert.equal(merged.files.length, 264); assert.equal(merged.measured, state.baseline.measured);
  assert.equal(merged.scoped_remeasurement.measured, date);
  assert.equal(merged.scoped_remeasurement.measured_files, 24);
  assert.equal(merged.scoped_remeasurement.unchanged_files_sha256_verified, 240);
  assert.equal(merged.scoped_remeasurement.added_files, 16);
  assert.equal(merged.scoped_remeasurement.replaced_existing_files, 8);
  const updated = new Map(rows.map(row => [row.file, row]));
  for (let i = 0; i < merged.files.length; i++) assert.deepEqual(merged.files[i], updated.get(merged.files[i].file) ?? state.baseline.files[i]);
});

test('missing, duplicated, failed, stale or mispaired native rows cannot be merged', () => {
  const state = inputs(), scope = prepareFixtureScope(state), rows = measured(scope);
  for (const wrong of [rows.slice(1), [...rows, clone(rows[0])],
    rows.map((row, i) => i ? row : { ...row, verdicts: [{ check: 'native failure', ok: false }] }),
    rows.map((row, i) => i ? row : { ...row, sha256: sha('stale-output') }),
    rows.map((row, i) => i ? row : { ...row, lod: 3-row.lod }),
    rows.map((row, i) => i ? row : { ...row, derivative_of: 'wrong-master.glb' })]) {
    assert.throws(() => mergeFixtureScope(scope, wrong, state.files, state.hashes, date), /human fixture scope/);
  }
});

test('any asset mutation or inventory change during native measurement is refused', () => {
  const state = inputs(), scope = prepareFixtureScope(state), rows = measured(scope);
  const selected = new Set(scope.selectedFiles);
  for (const file of [scope.selectedFiles[0], state.files.find(name => !selected.has(name))]) {
    const after = new Map(state.hashes); after.set(file, sha('changed-during-render:'+file));
    assert.throws(() => mergeFixtureScope(scope, rows, state.files, after, date), /asset changed during native measurement/);
  }
  const files = [...state.files, 'assets/humans/late.lod0.glb'], hashes = new Map(state.hashes);
  hashes.set(files.at(-1), sha('late'));
  assert.throws(() => mergeFixtureScope(scope, rows, files, hashes, date), /inventory changed/);
});

test('the one reviewed Charles scope replaces only four near rows and holds FAR/all other SHAs', () => {
  assert.deepEqual(parseFixtureArgs(['--write','--asset-ids',CHARLES_COAT_ID]), {mode:'--write',assetIds:[CHARLES_COAT_ID]});
  const document=clone(baseline),files=document.files.map(r=>r.file),hashes=new Map(document.files.map(r=>[r.file,r.sha256]));
  const wanted=scopedFiles([CHARLES_COAT_ID]);assert.equal(wanted.length,4);
  for(const file of wanted)hashes.set(file,sha('Charles-native-scope-guard:'+file));
  const scope=prepareFixtureScope({baseline:document,files,hashes,assetIds:[CHARLES_COAT_ID]});
  assert.equal(scope.selectedFiles.length,4);assert.equal(scope.addedCount,0);assert.equal(scope.unchangedCount,files.length-4);
  assert.deepEqual(scope.assetIds,[CHARLES_COAT_ID]);
  const rows=measured(scope),merged=mergeFixtureScope(scope,rows,files,hashes,date);
  assert.equal(merged.files.length,baseline.files.length);assert.equal(merged.measured,baseline.measured);
  assert.equal(merged.scoped_remeasurement.measured_files,4);assert.equal(merged.scoped_remeasurement.replaced_existing_files,4);
  for(const old of baseline.files.filter(r=>!wanted.includes(r.file)))assert.deepEqual(merged.files.find(r=>r.file===old.file),old);
  const far=files.find(f=>f.includes('/'+CHARLES_COAT_ID+'.lod2.'));assert(far);
  const bad=new Map(hashes);bad.set(far,sha('FAR-must-not-change'));
  assert.throws(()=>prepareFixtureScope({baseline:document,files,hashes:bad,assetIds:[CHARLES_COAT_ID]}),/unscoped file changed/);
  assert.throws(()=>mergeFixtureScope(scope,rows,files,bad,date),/asset changed during native measurement/);
  for(const args of [['--write','--asset-ids',CHARLES_COAT_ID+','+TEAMSTER_IDS[0]],['--check','--asset-ids',CHARLES_COAT_ID],['--write','--asset-ids',CHARLES_COAT_ID+','+CHARLES_COAT_ID]])assert.throws(()=>parseFixtureArgs(args));
});

test('settler scope replaces all eight rows and retains the other 240 actual SHA bindings', () => {
  assert.deepEqual(parseFixtureArgs(['--write','--asset-ids',SETTLER_ID]), {mode:'--write',assetIds:[SETTLER_ID]});
  const document=clone(baseline),files=document.files.map(r=>r.file),hashes=new Map(document.files.map(r=>[r.file,r.sha256]));
  const wanted=scopedFiles([SETTLER_ID]);assert.equal(wanted.length,8);
  for(const file of wanted)hashes.set(file,sha('settler-scope-synthetic-guard:'+file));
  const scope=prepareFixtureScope({baseline:document,files,hashes,assetIds:[SETTLER_ID]});
  assert.equal(scope.selectedFiles.length,8);assert.equal(scope.unchangedCount,240);assert.equal(scope.addedCount,0);
  assert.deepEqual(scope.assetIds,[SETTLER_ID]);
  const rows=measured(scope),merged=mergeFixtureScope(scope,rows,files,hashes,date);
  assert.equal(merged.files.length,248);assert.equal(merged.scoped_remeasurement.measured_files,8);
  assert.deepEqual(merged.scoped_remeasurement.asset_ids,[SETTLER_ID]);assert.equal(merged.scoped_remeasurement.unchanged_files_sha256_verified,240);
  for(const old of document.files.filter(r=>!wanted.includes(r.file)))assert.deepEqual(merged.files.find(r=>r.file===old.file),old);
  for(const args of [['--check','--asset-ids',SETTLER_ID],['--write','--asset-ids',SETTLER_ID+','+SETTLER_ID],
    ['--write','--asset-ids',SETTLER_ID+','+CHARLES_COAT_ID],['--write','--asset-ids',SETTLER_ID+','+TEAMSTER_IDS[0]]])assert.throws(()=>parseFixtureArgs(args));
});

test('settler cannot hide missing or extra files, other-family changes, or partial native results', () => {
  const document=clone(baseline),files=document.files.map(r=>r.file),hashes=new Map(document.files.map(r=>[r.file,r.sha256]));
  const state={baseline:document,files,hashes,assetIds:[SETTLER_ID]},wanted=scopedFiles([SETTLER_ID]);
  for(const file of wanted)hashes.set(file,sha('settler-native-synthetic:'+file));
  const scope=prepareFixtureScope(state),rows=measured(scope),other=files.find(f=>!wanted.includes(f));
  const changed=new Map(hashes);changed.set(other,sha('foreign-change'));
  assert.throws(()=>prepareFixtureScope({...state,hashes:changed}),/unscoped file changed/);
  assert.throws(()=>mergeFixtureScope(scope,rows,files,changed,date),/asset changed/);
  const missing=wanted.find(f=>f.includes('.lod3.')),shortFiles=files.filter(f=>f!==missing),shortHashes=new Map(hashes);shortHashes.delete(missing);
  assert.throws(()=>prepareFixtureScope({...state,files:shortFiles,hashes:shortHashes}),/all 8/);
  const extraFiles=[...files,'assets/humans/unreviewed.lod0.glb'],extraHashes=new Map(hashes);extraHashes.set(extraFiles.at(-1),sha('extra'));
  assert.throws(()=>prepareFixtureScope({...state,files:extraFiles,hashes:extraHashes}),/inventory differs/);
  for(const invalid of [rows.slice(1),rows.slice(0,4),[...rows,clone(rows[0])],rows.map((r,i)=>i?r:{...r,verdicts:[{ok:false}]}),rows.map((r,i)=>i?r:{...r,sha256:sha('stale')})])assert.throws(()=>mergeFixtureScope(scope,invalid,files,hashes,date));
});

// Keep the source-only seat observer controls in the existing fixture-owner gate.
await import('./test_human_settler_seat_review.mjs');

test('the five approved Prairie roles add exactly 40 rows and preserve every previous asset', () => {
  assert.deepEqual(parseFixtureArgs(['--write', '--asset-ids', [...PRAIRIE_CHILD_IDS].reverse().join(',')]),
    { mode: '--write', assetIds: [...PRAIRIE_CHILD_IDS] });
  const review = JSON.parse(readFileSync(new URL('../data/humans/role_reviews/prairie_children_1904.json', import.meta.url)));
  assert.deepEqual(review.roles.map(row => row.asset_id).sort(), [...PRAIRIE_CHILD_IDS].sort());
  const document = clone(baseline), files = [...document.files.map(row => row.file), ...childFiles];
  const hashes = new Map(document.files.map(row => [row.file, row.sha256]));
  for (const role of review.roles) for (const row of role.files) {
    assert(childFiles.has(row.file));
    const actual = sha(readFileSync(new URL('../' + row.file, import.meta.url)));
    assert.equal(actual, row.sha256, 'admission must bind the approved exported bytes');
    hashes.set(row.file, actual);
  }
  const state = { baseline: document, files, hashes, assetIds: [...PRAIRIE_CHILD_IDS] };
  const scope = prepareFixtureScope(state);
  assert.equal(scope.selectedFiles.length, 40); assert.equal(scope.addedCount, 40);
  assert.equal(scope.unchangedCount, document.files.length);
  const rows = measured(scope), merged = mergeFixtureScope(scope, rows, files, hashes, date);
  for (const old of document.files) assert.deepEqual(merged.files.find(row => row.file === old.file), old);
  assert.equal(merged.files.length, document.files.length + 40);
  const changed = new Map(hashes); changed.set(document.files[0].file, sha('unrelated-byte-change'));
  assert.throws(() => prepareFixtureScope({ ...state, hashes: changed }), /unscoped file changed/);
  assert.throws(() => mergeFixtureScope(scope, rows.slice(1), files, hashes, date), /native results must cover exactly/);
  for (const ids of [PRAIRIE_CHILD_IDS.slice(0, 4), [...PRAIRIE_CHILD_IDS, CHARLES_COAT_ID],
    [PRAIRIE_CHILD_IDS[0], ...PRAIRIE_CHILD_IDS.slice(0, 4)]]) {
    assert.throws(() => parseFixtureArgs(['--write', '--asset-ids', ids.join(',')]));
  }
  assert.throws(() => parseFixtureArgs(['--check', '--asset-ids', PRAIRIE_CHILD_IDS.join(',')]));
});
