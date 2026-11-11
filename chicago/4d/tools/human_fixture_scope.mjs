// SPDX-License-Identifier: GPL-3.0-or-later
// Explicit native remeasurement scopes: rebuilt teamsters, Charles near coat,
// settler linen, and the five approved Prairie child/teen roles. Every other asset retains its
// SHA and passing native baseline.
export const TEAMSTER_IDS = Object.freeze(['bardwell_otis_1835', 'dufresne_joseph_1835', 'flynn_martin_1835']);
export const CHARLES_COAT_ID = 'nelson_charles_1904_coachman';
export const SETTLER_ID = 'settler_1812';
export const PRAIRIE_CHILD_IDS = Object.freeze(['child_boy_1904', 'child_girl_1904', 'child_toddler_1904', 'teen_boy_1904', 'teen_girl_1904']);
const SHA = /^[a-f0-9]{64}$/;
const need = (ok, message) => { if (!ok) throw Error(`human fixture scope: ${message}`); };
const sameSet = (a, b) => a.size === b.size && [...a].every(value => b.has(value));

export function parseFixtureArgs(args) {
  let mode = '', assetIds = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--write' || args[i] === '--check') {
      need(!mode, 'choose one mode'); mode = args[i];
    } else if (args[i] === '--asset-ids') {
      need(assetIds === null && typeof args[i + 1] === 'string', 'one --asset-ids value required');
      assetIds = args[++i].split(',');
      const charles = assetIds.length === 1 && assetIds[0] === CHARLES_COAT_ID;
      const settler = assetIds.length === 1 && assetIds[0] === SETTLER_ID;
      const children = assetIds.length === 5 && new Set(assetIds).size === 5
        && sameSet(new Set(assetIds), new Set(PRAIRIE_CHILD_IDS));
      need(charles || settler || children || assetIds.length === 3 && new Set(assetIds).size === 3
        && sameSet(new Set(assetIds), new Set(TEAMSTER_IDS)), 'scope must name exactly the three rebuilt teamsters, the one Charles near-coat ID, the one settler eight-file ID, or the five approved Prairie child/teen IDs');
      assetIds = charles ? [CHARLES_COAT_ID] : settler ? [SETTLER_ID] : children ? [...PRAIRIE_CHILD_IDS] : [...TEAMSTER_IDS];
    } else throw Error(`human fixture scope: unknown argument ${args[i]}`);
  }
  need(assetIds === null || mode === '--write', '--asset-ids requires --write; --check remains global');
  return { mode, assetIds };
}

export function teamsterFiles(assetIds) {
  need(Array.isArray(assetIds) && assetIds.length === 3 && new Set(assetIds).size === 3
    && sameSet(new Set(assetIds), new Set(TEAMSTER_IDS)), 'scope must name exactly the three rebuilt teamster IDs');
  return ['assets/humans', 'assets/humans/web'].flatMap(dir => TEAMSTER_IDS.flatMap(id =>
    [0, 1, 2, 3].map(lod => `${dir}/${id}.lod${lod}.glb`)));
}

export function scopedFiles(assetIds) {
  if (Array.isArray(assetIds) && assetIds.length === 1 && assetIds[0] === SETTLER_ID) {
    return ['assets/humans', 'assets/humans/web'].flatMap(dir => [0, 1, 2, 3].map(lod => `${dir}/${SETTLER_ID}.lod${lod}.glb`));
  }
  if (Array.isArray(assetIds) && assetIds.length === 1 && assetIds[0] === CHARLES_COAT_ID) {
    return ['assets/humans', 'assets/humans/web'].flatMap(dir => [0, 1].map(lod => `${dir}/${CHARLES_COAT_ID}.lod${lod}.glb`));
  }
  if (Array.isArray(assetIds) && assetIds.length === 5 && new Set(assetIds).size === 5
    && sameSet(new Set(assetIds), new Set(PRAIRIE_CHILD_IDS))) {
    return ['assets/humans', 'assets/humans/web'].flatMap(dir => PRAIRIE_CHILD_IDS.flatMap(id =>
      [0, 1, 2, 3].map(lod => `${dir}/${id}.lod${lod}.glb`)));
  }
  return teamsterFiles(assetIds);
}

function checkedRows(rows) {
  need(Array.isArray(rows) && rows.length > 0, 'nonempty baseline rows required');
  const byFile = new Map();
  for (const row of rows) {
    need(row && typeof row.file === 'string' && !byFile.has(row.file), 'duplicate or missing measurement file');
    need(SHA.test(row.sha256 ?? '') && Array.isArray(row.verdicts) && row.verdicts.length > 0
      && row.verdicts.every(v => v?.ok === true), `missing hash or failed/empty verdicts for ${row.file}`);
    byFile.set(row.file, row);
  }
  return byFile;
}

function checkedHashes(files, hashes) {
  need(Array.isArray(files) && files.length === new Set(files).size, 'duplicate input files');
  need(hashes instanceof Map && sameSet(new Set(files), new Set(hashes.keys())), 'hashes must cover the complete actual file inventory');
  need([...hashes.values()].every(value => SHA.test(value ?? '')), 'invalid actual SHA256');
}

export function prepareFixtureScope({ baseline, files, hashes, assetIds }) {
  const wanted = new Set(scopedFiles(assetIds));
  const byFile = checkedRows(baseline?.files);
  checkedHashes(files, hashes);
  need([...wanted].every(file => hashes.has(file)), `all ${wanted.size} rebuilt source/web LOD files are required`);
  const expected = new Set([...byFile.keys(), ...wanted]);
  need(sameSet(new Set(files), expected), 'complete inventory differs from baseline plus the explicit scope; unrelated additions or baseline removals forbidden');
  for (const file of files) if (!wanted.has(file)) {
    need(hashes.get(file) === byFile.get(file).sha256, `unscoped file changed: ${file}`);
  }
  return { baseline, files: [...files], hashes: new Map(hashes), selectedFiles: files.filter(file => wanted.has(file)),
    unchangedCount: files.length - wanted.size,
    addedCount: [...wanted].filter(file => !byFile.has(file)).length,
    assetIds: assetIds.length === 1 ? [...assetIds] : assetIds.length === 5 ? [...PRAIRIE_CHILD_IDS] : [...TEAMSTER_IDS] };
}

export function mergeFixtureScope(scope, measured, files, hashes, date) {
  checkedHashes(files, hashes);
  need(sameSet(new Set(files), new Set(scope.files)), 'file inventory changed during native measurement');
  for (const file of files) need(hashes.get(file) === scope.hashes.get(file), `asset changed during native measurement: ${file}`);
  const replacements = checkedRows(measured);
  need(sameSet(new Set(replacements.keys()), new Set(scope.selectedFiles)), `native results must cover exactly the ${scope.selectedFiles.length} selected files`);
  for (const [file, row] of replacements) {
    need(row.sha256 === hashes.get(file), `stale native result: ${file}`);
    const lod = Number(/\.lod([0-3])\.glb$/.exec(file)[1]);
    const master = file.includes('/web/') ? file.replace('/web/', '/') : null;
    need(row.lod === lod && row.derivative_of === master, `wrong LOD/source pairing: ${file}`);
  }
  need(/^\d{4}-\d{2}-\d{2}$/.test(date), 'measurement date required');
  return { ...scope.baseline,
    // Old rows and the old full-corpus date retain their original provenance.
    files: [...scope.baseline.files.map(row => replacements.get(row.file) ?? row),
      ...measured.filter(row => !scope.baseline.files.some(old => old.file === row.file))],
    scoped_remeasurement: { measured: date, asset_ids: scope.assetIds,
      measured_files: measured.length, added_files: scope.addedCount,
      replaced_existing_files: measured.length - scope.addedCount,
      unchanged_files_sha256_verified: scope.unchangedCount,
      scope: 'Same native checks, both viewports and 30 timing frames; all other baseline file hashes unchanged before and after.' } };
}
