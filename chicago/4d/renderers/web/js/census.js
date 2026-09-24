/**
 * census.js — the Evidence → City summary of the town in numbers.
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
 * T-1365 kept that ladder and fixed what its second rung COUNTED. Both ends of the
 * people row were the wrong population:
 *
 *   the denominator was 3,265, the town census of NOVEMBER 1835, which
 *   `town_census.json`'s own `town_total_note` forbids reading as the scene's
 *   population and which the town model has since resolved to a point of 2,536 within
 *   2,353–3,265 — so the front screen filled toward a bound the reconstruction
 *   programme had already resolved, and the two quoted different towns;
 *
 *   the numerator was every card in the residents index, and most of those people are
 *   not established in Chicago on 1 July at all — a name waiting on a post-office
 *   letter list is a card, not a resident of that Tuesday. 829 of 2,144 are cards.
 *
 * So the row now reads the SAME population at both ends, out of `people.scene`: the
 * residents the layer records present on the scene date, graded as before, filling
 * toward the model's point for that date. The cards the project holds are still said —
 * as cards, on their own line, which is what they are. `people housed` is unmoved.
 *
 * T-1386 changed WHICH of two real figures the rung shows, and made the card say which
 * question its number answers. `people.scene.persons` counts the people a record
 * ESTABLISHES here on 1 July, and that is the strictest reading the layer supports — but
 * it is not the town's population, because it left 827 people the project has attested or
 * inferred evidence for outside the town on an unadjudicated `uncertain`. The owner's rule
 * is that an attested person is the ideal case, so those 827 are now RULED into the town
 * one at a time, each at the tier its own dated readings reach, and the rung shows
 * `people.scene.population` — 2,267 of a modelled 2,536. The established figure is not
 * overwritten: it keeps its own line under the bar, because they are two real measures and
 * the project needs both. Each figure carries its own `question` string from the census as
 * its tooltip, so a visitor can read what they are looking at without leaving City.
 *
 * FAIL SOFT, ALWAYS. Either source may be absent while a branch is being built. Show the
 * rows that can be read and never turn a census nicety into a page error in Evidence.
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

async function readJson(url, onError) {
  try {
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    onError?.(err);
    return null;
  }
}

/**
 * Fill Evidence → City from committed derived data. This function is called only after
 * the Evidence tab is opened, so neither JSON belongs to the boot payload.
 *
 * @param {{ dataBase: URL|string, root?: Element|null, buildStamp?: string }} opts
 * @returns {Promise<object|null>} the town census as loaded, or null if it could not be read
 */
export async function mountCityCensus({ dataBase, root, buildStamp = '', onError }) {
  const host = root ?? document.getElementById('city');
  if (!host) return null;

  const [census, residents] = await Promise.all([
    readJson(new URL('town_census.json', dataBase), onError),
    readJson(new URL('residents/index.json', dataBase), onError),
  ]);

  const rows = [];
  const aria = [];

  const standing = Number(census?.buildings?.standing);
  const target = Number(census?.buildings?.target);
  const housed = Number(census?.people?.housed);

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
      + '<p class="gc-definition">Physical roofs standing in the scene; bridges, piers and grounds are not counted.</p>'
      + '</section>',
    );
    aria.push(`${group(standing)} buildings standing${of ? ` ${of}` : ''}`);
  }

  // The scene block is the T-1365 population: both ends of the row, counted the same
  // way, out of the derived census. The residents manifest stays the fallback for the
  // grades when the census cannot be read at all — fail soft, always — but a fallback
  // row carries NO denominator, because the only total in reach there is the November
  // count and quoting it is the defect this ticket exists to fix.
  const scene = census?.people?.scene;
  const counts = residents?.counts || {};
  // THE POPULATION (T-1386) is the figure the rung shows when the census carries it; the
  // established count stays in `scene.persons` and gets its own line below. Fail soft:
  // a census written before T-1386 has no `population` block and the row falls back to
  // the established figure, then to the manifest's cards, exactly as it did before.
  const population = scene?.population;
  const sceneGrades = population?.by_grade || scene?.by_grade;
  const named = Number(population ? population.persons : (scene ? scene.persons : counts.persons));
  const established = Number(population?.established);
  const ruledIn = Number(population?.ruled_in);
  const grades = sceneGrades || counts.by_grade || {};
  const attested = Number(grades.attested);
  const inferred = Number(grades.inferred);
  const reconstructed = Number(grades.reconstructed);
  const modelled = Number(scene?.target);
  const cardsHeld = Number(scene?.cards_total);
  const cardsUnestablished = Number(scene?.cards_not_established);
  // The tooltip on the "of roughly N" line carries the model's own note and method, so a
  // visitor who wants to know where 2,536 came from can read it without leaving the gate.
  const ofTitle = [scene?.target_note, scene?.target_method].filter(Boolean).join(' — ')
    || census?.people?.town_total_note;

  // Row two: the people, the same shape. The bar's three segments are the grades in
  // the order they are earned, so the visitor sees the named count as a portion of the
  // town filling from the best-evidenced end. Reconstructed is listed in the key even
  // at zero: it is the work still to do, and a key that hid it would hide that.
  if (Number.isFinite(named)) {
    const rowLabel = population ? 'people in the town'
      : (scene ? 'residents in the town' : 'named on a card');
    // WHICH QUESTION THIS NUMBER ANSWERS, in the census's own words.
    const namedTitle = population?.question || residents?._doc;
    const of = Number.isFinite(modelled)
      ? `of roughly ${group(modelled)} here on 1 July 1835`
      : '';
    const key = [
      ['att', attested, 'attested'],
      ['inf', inferred, 'inferred'],
      ['rec', reconstructed, 'reconstructed'],
    ].filter(([, n]) => Number.isFinite(n));
    rows.push(
      `<section class="gc-row"${titleAttr(namedTitle)}>`
      + '<p class="gc-head">'
      + `<b class="gc-n">${group(named)}</b>`
      + `<span class="gc-l">${rowLabel}</span></p>`
      + (Number.isFinite(modelled)
        ? '<div class="gc-bar">'
          + key.map(([k, n]) => `<i class="gc-seg gc-seg-${k}" style="width:${pct(n, modelled)}"></i>`).join('')
          + '</div>'
        : '')
      + (of ? `<p class="gc-of"${titleAttr(ofTitle)}>${of}</p>` : '')
      + '<p class="gc-definition">People the project’s evidence puts in Chicago on the target date.</p>'
      + (key.length
        ? `<ul class="gc-key">${key.map(([k, n, label]) =>
          `<li><i class="gc-sw gc-sw-${k}"></i>${group(n)} ${label}</li>`).join('')}</ul>`
        : '')
      + (Number.isFinite(housed)
        ? `<p class="gc-note"${titleAttr(census?.people?.basis)}>`
          + `${group(housed)} of them are placed in a building that stands</p>`
        : '')
      // THE OTHER REAL MEASURE, kept rather than overwritten (T-1386): how many of these
      // people a record establishes here on the day itself, and how many are carried into
      // the town by their own evidence under the ruling. The tooltip is the census's own
      // question string for the stricter figure.
      + (Number.isFinite(established) && Number.isFinite(ruledIn)
        ? `<p class="gc-note"${titleAttr(scene?.question)}>`
          + `${group(established)} of them are established here by a record dated across `
          + `that day; ${group(ruledIn)} are ruled into the town on their own evidence</p>`
        : '')
      // The cards the layer holds without establishing the person in the town that day.
      // They were the numerator until T-1365 and they are still worth saying — as what
      // they are, one line down, never as residents.
      + (!population && Number.isFinite(cardsHeld) && Number.isFinite(cardsUnestablished) && cardsUnestablished > 0
        ? `<p class="gc-note"${titleAttr(scene?.basis)}>`
          + `${group(cardsHeld)} cards are held in all; ${group(cardsUnestablished)} name `
          + 'someone not yet established here on that day</p>'
        : '')
      // Under the ruling the residue is not a heap of unadjudicated cards but the people
      // the sources place OUTSIDE the town, and two is the whole of it.
      + (population && Number.isFinite(cardsHeld) && Number(population.absent_on_evidence) > 0
        ? `<p class="gc-note"${titleAttr(population?.basis)}>`
          + `${group(cardsHeld)} cards are held in all; `
          + `${group(Number(population.absent_on_evidence))} name someone a source places `
          + 'outside the town that day</p>'
        : '')
      + '</section>',
    );
    aria.push(`${group(named)} ${rowLabel}${of ? ` ${of}` : ''}`
      + (key.length ? `: ${key.map(([, n, name]) => `${group(n)} ${name}`).join(', ')}` : ''));
    if (Number.isFinite(housed)) {
      aria.push(`${group(housed)} of them are placed in a building that stands`);
    }
    if (Number.isFinite(established) && Number.isFinite(ruledIn)) {
      aria.push(`${group(established)} of them are established here by a record dated `
        + `across that day; ${group(ruledIn)} are ruled into the town on their own evidence`);
    }
    if (!population && Number.isFinite(cardsHeld) && Number.isFinite(cardsUnestablished) && cardsUnestablished > 0) {
      aria.push(`${group(cardsHeld)} cards are held in all; ${group(cardsUnestablished)} name `
        + 'someone not yet established here on that day');
    }
    if (population && Number.isFinite(cardsHeld) && Number(population.absent_on_evidence) > 0) {
      aria.push(`${group(cardsHeld)} cards are held in all; `
        + `${group(Number(population.absent_on_evidence))} name someone a source places `
        + 'outside the town that day');
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

  const targetDate = attr(census?.target_date || '');
  const meta = census ? '<dl class="city-meta">'
    + `<div><dt>Target date</dt><dd><time datetime="${targetDate}">`
    + `${targetDate || 'not recorded'}</time></dd></div>`
    + '<div><dt>Derived by</dt><dd><code>'
    + `${attr(census.derived_by || 'not recorded')}</code></dd></div>`
    + `<div><dt>Build</dt><dd>${attr(buildStamp || 'development build')}</dd></div>`
    + '</dl>' : '';
  host.innerHTML = meta + rows.join('');
  host.setAttribute('aria-label', aria.join('. '));
  host.removeAttribute('aria-busy');
  host.removeAttribute('hidden');
  return census;
}
