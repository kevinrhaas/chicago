/**
 * What `tools/publish.sh` prebuilt, before the page asks for any of it.
 *
 * `tools/prebuild_layers.mjs` builds the frontage, ground and distant-base layers only
 * for the scenes that draw a frontage (1835 today), and writes `data/prebuilt/index.json`
 * naming every year and layer it wrote, with the build that wrote them. The page used to
 * ask for `prebuilt/<year>/<layer>.json` for whatever year it was showing and read a 404
 * as "none"; on /1904/ and /1812/ that was two 404s on every boot, and a page error the
 * mobile smoke rightly counts. Now it reads this one small file first and asks only for
 * what it lists. A page with no build stamp (the source tree) never gets this far.
 */

const listings = new Map();

/** `{ build, layers: { year: [layer, …] } }` from `prebuilt/index.json`, or `{ why }`.
 * Fetched once per data base; never rejects. */
export function prebuiltListing(dataBase) {
  const key = String(dataBase);
  if (!listings.has(key)) {
    listings.set(key, (async () => {
      try {
        const res = await fetch(new URL('prebuilt/index.json', dataBase));
        if (!res.ok) return { why: `no list of what publish prebuilt (${res.status})` };
        const list = await res.json();
        return list && typeof list.layers === 'object' ? list : { why: 'the list of what publish prebuilt is malformed' };
      } catch (err) {
        return { why: `the list of what publish prebuilt did not load: ${err.message}` };
      }
    })());
  }
  return listings.get(key);
}

/** Null when publish prebuilt `layer` for `year` with this build, or why the page should
 * not ask for it at all. */
export async function prebuiltAbsent({ dataBase, year, build, layer }) {
  const list = await prebuiltListing(dataBase);
  if (list.why) return list.why;
  if (list.build !== build) return `prebuilt by build ${list.build}, this page is build ${build}`;
  if (!(list.layers[String(year)] ?? []).includes(layer)) return `publish prebuilt no ${layer} for ${year}`;
  return null;
}

/** For the unit tests: forget what was fetched. */
export function resetPrebuiltListing() { listings.clear(); }
