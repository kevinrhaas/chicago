/**
 * census.js — live town/population statistics on the gate screen.
 *
 * T-0036 established the rule: the front screen never carries hand-typed population
 * numbers. Buildings standing comes from `data/town_census.json`. T-0490 extends the
 * same rule to the evidence population: named/attested/inferred/reconstructed counts
 * come directly from `data/residents/index.json`.
 *
 * T-0782 rebuilt what those numbers SAY. The card had three stacked figures, and read
 * top-down they told three unrelated stories — worst of all `29 people housed · of
 * roughly 3,265`, which set a placement figure against the town's whole population and
 * so announced the town as 0.9 % peopled. It is one ladder, twice:
 *
 *   buildings — 359 of the 662 roofs the town held;
 *   people    — 1,404 named of the roughly 3,265 who lived here, and the named count is
 *               itself graded attested → inferred → reconstructed, three portions of the
 *               same bar filling toward the census total.
 *
 * `people housed` survives as what it actually is — a PLACEMENT note under the people
 * row, the named residents standing inside a building that stands — and is never again
 * quoted against 3,265. `projected_residents` stays in the residents manifest for
 * T-0490's readers; it no longer reaches the card, because a parenthesis inside the
 * inferred count read as a fourth grade.
 *
 * FAIL SOFT, ALWAYS. Either source may be absent while a branch is being built. Show the
 * rows that can be read and never turn a census nicety into a page error on the first
 * screen a visitor sees.
 */

/** `3265` → `3,265`, in the locale-independent form the rest of the UI uses. */
function group(n) {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** A bar segment's width, as a percentage string, clamped into the bar. */
function pct(part, whole) {
  if (!Number.isFinite(part) || !Number.isFinite(whole) || whole <= 0) return '0%';
  return `${Math.max(0, Math.min(100, (part / whole) * 100)).toFixed(2)}%`;
}

function attr(s) {
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
}

/** `title="…"`, or nothing at all when there is no title to carry. */
function titleAttr(s) {
  return s ? ` title="${attr(s)}"` : '';
}

async function readJson(url) {
  try {
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Fill the gate census/evidence rows from committed derived data.
 *
 * @param {{ dataBase: URL|string, root?: Element|null }} opts
 * @returns {Promise<object|null>} the town census as loaded, or null if it could not be read
 */
export async function mountGateCensus({ dataBase, root }) {
  const host = root ?? document.getElementById('gate-census');
  if (!host) return null;

  const [census, residents] = await Promise.all([
    readJson(new URL('town_census.json', dataBase)),
    readJson(new URL('residents/index.json', dataBase)),
  ]);

  const rows = [];
  const aria = [];

  const standing = Number(census?.buildings?.standing);
  const target = Number(census?.buildings?.target);
  const housed = Number(census?.people?.housed);
  const town = Number(census?.people?.town_total);

  // Row one: the roofs. One segment, because a building either stands or it does not.
  if (Number.isFinite(standing)) {
    const of = Number.isFinite(target) ? `of the ${group(target)} the town held` : '';
    rows.push(
      `<section class="gc-row"${titleAttr(census?.buildings?.basis)}>`
      + '<p class="gc-head">'
      + `<b class="gc-n">${group(standing)}</b>`
      + '<span class="gc-l">buildings standing</span></p>'
      + (Number.isFinite(target)
        ? '<div class="gc-bar">'
          + `<i class="gc-seg gc-seg-built" style="width:${pct(standing, target)}"></i></div>`
        : '')
      + (of ? `<p class="gc-of">${of}</p>` : '')
      + '</section>',
    );
    aria.push(`${group(standing)} buildings standing${of ? ` ${of}` : ''}`);
  }

  const counts = residents?.counts || {};
  const named = Number(counts.persons);
  const grades = counts.by_grade || {};
  const attested = Number(grades.attested);
  const inferred = Number(grades.inferred);
  const reconstructed = Number(grades.reconstructed);

  // Row two: the people, the same shape. The bar's three segments are the grades in
  // the order they are earned, so the visitor sees the named count as a portion of the
  // town filling from the best-evidenced end. Reconstructed is listed in the key even
  // at zero: it is the work still to do, and a key that hid it would hide that.
  if (Number.isFinite(named)) {
    const of = Number.isFinite(town) ? `of roughly ${group(town)} who lived here` : '';
    const key = [
      ['att', attested, 'attested'],
      ['inf', inferred, 'inferred'],
      ['rec', reconstructed, 'reconstructed'],
    ].filter(([, n]) => Number.isFinite(n));
    rows.push(
      `<section class="gc-row"${titleAttr(residents?._doc)}>`
      + '<p class="gc-head">'
      + `<b class="gc-n">${group(named)}</b>`
      + '<span class="gc-l">named residents</span></p>'
      + (Number.isFinite(town)
        ? '<div class="gc-bar">'
          + key.map(([k, n]) => `<i class="gc-seg gc-seg-${k}" style="width:${pct(n, town)}"></i>`).join('')
          + '</div>'
        : '')
      + (of ? `<p class="gc-of"${titleAttr(census?.people?.town_total_note)}>${of}</p>` : '')
      + (key.length
        ? `<ul class="gc-key">${key.map(([k, n, label]) =>
          `<li><i class="gc-sw gc-sw-${k}"></i>${group(n)} ${label}</li>`).join('')}</ul>`
        : '')
      + (Number.isFinite(housed)
        ? `<p class="gc-note"${titleAttr(census?.people?.basis)}>`
          + `${group(housed)} of them are placed in a building that stands</p>`
        : '')
      + '</section>',
    );
    aria.push(`${group(named)} named residents${of ? ` ${of}` : ''}`
      + (key.length ? `: ${key.map(([, n, label]) => `${group(n)} ${label}`).join(', ')}` : ''));
    if (Number.isFinite(housed)) {
      aria.push(`${group(housed)} of them are placed in a building that stands`);
    }
  } else if (Number.isFinite(housed)) {
    // The residents manifest could not be read, so there is no named count to hang the
    // placement figure under. It still belongs on the card — but as its own statement of
    // what is placed, never as a share of the town.
    rows.push(
      `<section class="gc-row"${titleAttr(census?.people?.basis)}>`
      + '<p class="gc-head">'
      + `<b class="gc-n">${group(housed)}</b>`
      + '<span class="gc-l">residents placed in a building that stands</span></p>'
      + '</section>',
    );
    aria.push(`${group(housed)} residents placed in a building that stands`);
  }

  if (!rows.length) return null;

  host.innerHTML = rows.join('');
  host.setAttribute('aria-label', aria.join('. '));
  host.removeAttribute('hidden');
  return census;
}
