/**
 * Reading a household record, wherever the published tree keeps it — T-0438.
 *
 * Every household is committed as its own file under `data/residents/households/`,
 * and in the dev tree that is where it is read from. The published mirror ships the
 * letter-list cohort differently: `tools/pack_letter_list.py` packs those records
 * into `residents/letter_list/` — a roster holding every string the cohort repeats,
 * once, and one shard per initial — and takes the per-record files out. The
 * cohort's paragraphs are the same paragraph on most of its 773 records, and as one
 * file each they had grown to 9.3 MiB of the tree.
 *
 * So a cohort row asks the roster first and its own file second, and every other
 * row asks the other way round. Either order ends at the same record: the dev tree
 * has no roster and reads the file; the mirror has no file and reads the roster.
 * The roster is fetched once per data base and each shard once, so opening a second
 * name with the same initial costs nothing.
 *
 * `tools/check_published_residents.mjs` unpacks the shipped shards with
 * `unpackRecord` below — this function, not a copy of it — and asserts each record
 * is deep-equal to its source.
 */

const MARK = '$s';
const ROSTER = 'residents/letter_list/roster.json';

/** A packed record back to its source value: each `{"$s": i}` is `strings[i]`. */
export function unpackRecord(packed, strings) {
  if (Array.isArray(packed)) return packed.map((v) => unpackRecord(v, strings));
  if (packed && typeof packed === 'object') {
    const keys = Object.keys(packed);
    if (keys.length === 1 && keys[0] === MARK) {
      const s = strings[packed[MARK]];
      if (typeof s !== 'string') throw new Error(`the letter-list roster has no string ${packed[MARK]}`);
      return s;
    }
    return Object.fromEntries(keys.map((k) => [k, unpackRecord(packed[k], strings)]));
  }
  return packed;
}

const fetchJson = async (rel, dataBase) => {
  const res = await fetch(new URL(rel, dataBase), { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${rel}: ${res.status} ${res.statusText}`);
  return res.json();
};

// One promise per data base. A roster that is not there (the dev tree) resolves to
// null and stays null; a network failure is forgotten so the next open retries.
const rosters = new Map();
const shards = new Map();

function roster(dataBase) {
  const key = String(dataBase);
  if (!rosters.has(key)) {
    rosters.set(key, fetch(new URL(ROSTER, dataBase), { cache: 'no-cache' })
      .then((res) => (res.ok ? res.json() : null))
      .catch((err) => { rosters.delete(key); throw err; }));
  }
  return rosters.get(key);
}

async function fromRoster(dataBase, file) {
  const r = await roster(dataBase);
  const shard = r?.shards?.[file];
  if (!shard) return null;
  const key = `${String(dataBase)}|${shard}`;
  if (!shards.has(key)) {
    shards.set(key, fetchJson(`residents/letter_list/${shard}.json`, dataBase)
      .catch((err) => { shards.delete(key); throw err; }));
  }
  const packed = (await shards.get(key)).records?.[file];
  return packed === undefined ? null : unpackRecord(packed, r.strings || []);
}

/**
 * The household record at `residents/<file>`.
 * @param {URL} dataBase   where data/ lives
 * @param {string} file    the index's `file`, e.g. `households/hh_abbot_8_g.json`
 * @param {{cohort?: boolean}} [o] true for a letter-list row — the roster is asked first
 */
export async function readHouseholdRecord(dataBase, file, { cohort = false } = {}) {
  const direct = () => fetchJson(`residents/${file}`, dataBase);
  const viaRoster = () => fromRoster(dataBase, file).catch(() => null);
  if (cohort) return (await viaRoster()) ?? direct();
  try {
    return await direct();
  } catch (err) {
    const hh = await viaRoster();
    if (hh) return hh;
    throw err;
  }
}
