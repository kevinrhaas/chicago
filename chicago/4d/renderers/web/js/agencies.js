/**
 * agencies.js — the relation the card had no place for.
 *
 * A house on this street sold goods, and the card says so: a trade, the goods, the
 * proprietors, a street, a placement. Those are the fields a business record had when
 * the card was written, and a HOLDING is none of them. Hubbard & Co. of La Salle Street
 * was appointed agent for the Howard Fire Insurance Company of the city of New-York and
 * insured property against loss by fire for eleven months; three weeks before the day
 * you are standing in, the identical notice starts running in the singular over one man,
 * and the agency is E. K. Hubbard's. That is a relation between two records, and until
 * this module existed it reached no visitor at all — `identity.json` held it,
 * `gazetteer.json` compiled it, and nothing read either (T-0410, T-1041).
 *
 * WHAT THIS MODULE WILL NOT DO. It renders what `tools/compile_agencies.py` wrote and
 * nothing else. The standing caveat under every holding — that a holding is a relation
 * and says nothing about the holder's trade, roof or partners — is read out of the FILE
 * rather than typed here, because the acceptance clause it answers is about rendered
 * text and text that lives only in a renderer is text a later edit can drop. The dates
 * are printed as printings, never as a term: the register knows when the notice ran and
 * says nothing about when the appointment began.
 *
 * Degrades the way every other layer here degrades: a failure pushes a problem and
 * returns null, and null means "not loaded" — which the cards treat as a reason to say
 * nothing, never as a reason to say a house held nothing.
 */

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

/** `1834-07-02` → `2 July 1834`. An ISO date on a card is a machine talking. */
export function prettyDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso ?? ''));
  if (!m) return String(iso ?? '');
  return `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]} ${m[1]}`;
}

/**
 * Load the compiled relation.
 *
 * @param {object} o
 * @param {URL} o.dataBase        where data/ lives
 * @param {string[]} [o.problems] the shared collector
 * @returns {Promise<object|null>}
 */
export async function loadAgencies({ dataBase, problems = [] }) {
  try {
    const url = new URL('reconstruction/1835_agencies.json', dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const doc = await res.json();
    if (!Array.isArray(doc?.agencies)) throw new Error('no agencies array');
    return doc;
  } catch (err) {
    problems.push(`agencies: ${err.message}`);
    return null;
  }
}

/**
 * Every holding, held or refused, that belongs on one card.
 *
 * A card is addressed by exactly one of the two keys the compiler derives — a
 * `structure_id` for the roof a house is seated under, a `household_id` for a man's own
 * town card — so asking with the wrong one returns nothing rather than somebody else's
 * agency.
 *
 * @param {object|null} doc   `loadAgencies()`'s handle
 * @param {'structure_id'|'household_id'} key
 * @param {string} id
 */
export function agenciesFor(doc, key, id) {
  if (!doc || !id) return [];
  const out = [];
  for (const agency of doc.agencies) {
    const held = (agency.holdings || []).filter((h) => h[key] === id);
    const refused = (agency.refused_holdings || []).filter((h) => h[key] === id);
    for (const h of held) out.push({ agency, holding: h, refused: false });
    for (const h of refused) out.push({ agency, holding: h, refused: true });
  }
  return out;
}

/**
 * One holding, as a sentence a visitor can read and a list of the printings it rests on.
 *
 * `escape` is passed in rather than imported so this module stays free of the popup's
 * DOM helpers and can be rendered from the household browser too — two surfaces, one
 * rendering of a relation, which is the same rule `householdHtml` follows.
 */
export function holdingHtml({ agency, holding, refused }, escape) {
  const e = escape;
  const seat = agency.principal_seat ? ` of ${e(agency.principal_seat)}` : '';
  const window = holding.first_issue === holding.last_issue
    ? `printed ${e(prettyDate(holding.first_issue))}`
    : `printed from ${e(prettyDate(holding.first_issue))} to ${e(prettyDate(holding.last_issue))}`;
  const onTheDay = holding.printings_bracket_the_scene_date
    ? ' — the notice was running on the day you are standing in'
    : ' — the notice is not running on the day you are standing in';

  const lead = refused
    ? `<p class="agency-lead"><b>Refused:</b> this house was read as holding the agency for
         ${e(agency.principal)}${seat}, and the reading does not stand.</p>`
    : `<p class="agency-lead">${e(holding.holder)} held the agency for
         ${e(agency.principal)}${seat} — ${e(agency.trade || 'an agency')}, signed
         <q>${e(holding.signature || '')}</q>, ${window}${onTheDay}.</p>`;

  const why = refused ? holding.refused_because : holding.note;

  return `<article class="agency${refused ? ' agency-refused' : ''}">
    ${lead}
    ${why ? `<details class="agency-why"><summary>why</summary><p>${e(why)}</p></details>` : ''}
    <p class="agency-cites">${holding.witnesses.length} printing(s):
      ${holding.witnesses.map((w) => `<code>${e(w)}</code>`).join(' ')}</p>
  </article>`;
}

/**
 * The whole section for one card, caveat included, or '' when there is nothing to say.
 *
 * The caveat is printed once per section rather than once per holding — it qualifies
 * every line under it — and it is the FILE's sentence, never this module's.
 */
export function agencySectionHtml(doc, key, id, escape) {
  const mine = agenciesFor(doc, key, id);
  if (!mine.length) return '';
  const caveat = doc.the_caveat_the_card_prints || '';
  const window = doc.the_window_is_printings || '';
  return `<section class="pop-sec pop-agency">
    <h3>An agency held here <span class="pop-count">${mine.length}</span></h3>
    ${mine.map((row) => holdingHtml(row, escape)).join('')}
    <p class="agency-caveat">${escape(caveat)}</p>
    <p class="agency-caveat">${escape(window)}</p>
  </section>`;
}
