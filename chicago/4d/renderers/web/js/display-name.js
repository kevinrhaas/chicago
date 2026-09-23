/**
 * display-name.js — what a building is CALLED, as against what a generator numbered it.
 *
 * The owner, 2026-08-18, looking at a card in the walkthrough: *"this name is not great
 * Reconstructed D3 one-room frame cottage #03 … give the locations useful names not
 * technical D3 #03 names, you can have that somewhere on the card for reference identity
 * purposes but dont make it the title."*
 *
 * He is describing 222 buildings. The anonymous reconstruction programme names its roofs
 * `Reconstructed <family> <description> #<seq>` because that string is what the recipe
 * DERIVES — the family is the archetype the roof was dealt, the sequence is its place in
 * the parcel — and the record has to carry it or the parcel stops being re-derivable. It
 * is a production identity. A town does not use production identities: a house is known
 * by whoever lives in it, and an empty one is known by what it is.
 *
 * So this composes the title a visitor reads, and it composes it FROM THE DATA the record
 * and the residents layer already carry — never from a table somebody typed. Three cases,
 * and the third is the one that needs watching:
 *
 * 1. **Somebody lives there.** 104 of the 222 anonymous roofs were adopted by an inferred
 *    household (`data/residents/`, ROADMAP K1 phase two), so the card can say "The Pratt
 *    house" the way the town would have. A household that only WORKS there gets the
 *    workplace form — "Newell's stable" — because the building is their shop, not their home.
 * 2. **It is an outbuilding.** A privy is a privy. Titling one "vacant" would be a claim
 *    about occupancy for a building nothing occupies.
 * 3. **Nothing is recorded there.** The title says "A vacant one-room frame cottage", or
 *    for premises that would have been offered, the 1830s phrasing the owner asked for:
 *    "…, to let". **That is a liberty and it is recorded as one (L157).** The residents
 *    layer places households on the roofs its trade argument needs and stops; the other
 *    118 roofs are unmodelled, not attested empty, and the card says so in as many words
 *    under the title. The distinction costs one sentence and is exactly the sort of thing
 *    this project would otherwise lose.
 *
 * The production identity is not deleted. `sidecar.name` is untouched — it is what the
 * generators re-derive, what the GLB is named after, and what `smoke_renderer.mjs`'s
 * naming gate reads — and the card prints it under the title as the reference line the
 * owner asked for. Search takes both, so "D3 #017" and "Pratt" both find the same roof.
 *
 * Named and attested buildings do not come through here at all: they have real names from
 * real sources, and their titles are their records' own.
 */

/** `Reconstructed D3 one-room frame cottage #017` — the generators' own composition. */
const SPEC = /^Reconstructed\s+(\S+)\s+(.+?)\s+#(\d+)$/;

/**
 * The OTHER production name in the anonymous layer, and it arrived there rather than
 * being built there. `Reconstructed bakery (baker)` — a function and the trade the roof
 * was raised for, with no family band and no part number, because these 31 were authored
 * one at a time by the inferred-household programme instead of being dealt out of a
 * parcel. They read `inferred_household` until 2026-09-02, when the owner retired the
 * reconstructed resident population and ruled the roofs kept as anonymous stock (T-0516),
 * and they came into this layer still wearing the production vocabulary the owner's naming
 * ruling is about: "give the locations useful names not technical D3 #03 names, you can
 * have that somewhere on the card for reference identity purposes but dont make it the
 * title." A part number is not what makes a name technical — leading with `Reconstructed`
 * is — so these compose a title the same way their 249 neighbours do, off the same
 * description, and keep the production name on the reference line underneath.
 */
const RAISED = /^Reconstructed\s+(.+?)\s+\(([^)]+)\)$/;

/**
 * The building noun a title can end in, matched against the record's own description.
 * Ordered, because the descriptions are deliberately hedged ("small shop or office",
 * "small inn or tavern") and the FIRST reading is the one the archetype is named for.
 */
const NOUNS = [
  [/\b(?:tavern|inn)\b/, 'tavern'],
  [/\bboarding house\b/, 'boarding house'],
  [/\bstore\b/, 'store'],
  [/\bwarehouse\b/, 'warehouse'],
  [/\b(?:workshop|shop)\b/, 'shop'],
  [/\boffice\b/, 'shop'],
  [/\bstable\b/, 'stable'],
  [/\bbarn\b/, 'barn'],
  [/\bshed\b/, 'shed'],
  [/\bprivy\b/, 'privy'],
  [/\b(?:schoolhouse|meeting hall)\b/, 'schoolhouse'],
  [/\b(?:cottage|dwelling|house|shanty|residence)\b/, 'house'],
];

/** Premises a town would have advertised. The others are not "to let", they are just empty. */
const LETTABLE = new Set(['tavern', 'boarding house', 'store', 'warehouse', 'shop']);
/** Nothing lives in these, so nothing about them is vacant. */
const OUTBUILDING = new Set(['stable', 'barn', 'shed', 'privy', 'schoolhouse']);

function nounFor(description) {
  for (const [pattern, noun] of NOUNS) if (pattern.test(description)) return noun;
  return null;
}

function article(phrase) {
  return /^[aeiou]/i.test(String(phrase)) ? 'An' : 'A';
}

/** `Stebbins` → `Stebbins'`, `Pratt` → `Pratt's` — the ordinary rule, not a period one. */
function possessive(name) {
  return /s$/i.test(name) ? `${name}'` : `${name}'s`;
}

/**
 * The name a household would have been known by. The households the residents layer
 * writes are titled "The Pratt household — a reconstructed carpenter (south division)",
 * so the surname is in hand; where it is not, the head's own surname is, and where
 * neither is there this returns null and the caller falls back rather than inventing.
 */
function surnameOf(household) {
  const stated = /^The\s+(.+?)\s+household\b/.exec(String(household?.name ?? ''));
  if (stated) return stated[1];
  const persons = Array.isArray(household?.persons) ? household.persons : [];
  const head = persons.find((person) => person.relationship === 'head') ?? persons[0];
  const words = String(head?.name ?? '').trim().split(/\s+/).filter(Boolean);
  return words.length ? words[words.length - 1] : null;
}

/**
 * What to call this building, and the production identity it is called that INSTEAD of.
 *
 * @param {object} sidecar   the compiled record
 * @param {string} id        the record id, for the last-resort title
 * @returns {{title: string, spec: string|null, vacant: boolean}}
 *   `spec` is null whenever the title IS the record's own name, so a caller can print the
 *   reference line only where there is something to reference. `vacant` marks the titles
 *   that are asserting an absence, which is the half of this a card has to qualify.
 */
export function displayName(sidecar, id = '') {
  const spec = String(sidecar?.name ?? '');
  const parts = SPEC.exec(spec);
  const raised = parts ? null : RAISED.exec(spec);
  // Anything with a real name keeps it: this layer is the anonymous programme's alone.
  if (sidecar?.reconstruction?.status !== 'inferred_anonymous' || !(parts || raised)) {
    return { title: spec || id, spec: null, vacant: false };
  }

  // The description is the part of the production name that describes the BUILDING: the
  // family band's phrase where a parcel dealt it, the function where the household layer
  // raised it. The trade in the raised name's brackets is deliberately not folded in —
  // the roof was raised for a blacksmith the town's arithmetic argued for and the owner
  // retired, so titling it a blacksmith's anything would put back the occupant T-0516
  // took out. It stays on the card in `function` and on the reference line.
  const description = parts ? parts[2] : raised[1];
  const noun = nounFor(description);
  const households = Array.isArray(sidecar.residents) ? sidecar.residents : [];
  const lives = households.find((h) => /lived/.test(String(h.relation)));
  const works = households.find((h) => /worked/.test(String(h.relation)));

  const resident = lives && surnameOf(lives);
  if (resident) {
    // "The Dufresne boarding house", not "The Dufresne house", where they keep one:
    // the building the household lives in is also the building the town knew it by.
    const kind = noun && noun !== 'house' ? noun : 'house';
    return { title: `The ${resident} ${kind}`, spec, vacant: false };
  }
  const worker = works && surnameOf(works);
  if (worker) {
    return { title: `${possessive(worker)} ${noun ?? 'premises'}`, spec, vacant: false };
  }

  // A DOCUMENTED ADDRESS OUTRANKS A COMPOSED VACANCY, and it has to, because the
  // alternative is what this project spent a year avoiding: the one building in the whole
  // newspaper corpus placed by a lot AND a block — "LOT No. 7, in block No. 16 … on Lake
  // street", six printings of it — was titled "A vacant one-room frame cottage", which is
  // a claim about absence made over the top of a source that says a house was there.
  // It ranks BELOW a household, because a house the town knew by the family in it is known
  // by the family in it, and above everything else, because the address is read and the
  // rest of this function is composition. `attributes.lot_address` is the compiler's row
  // (tools/lot_addresses.py seats it, docs/LOT-ADDRESS.md is the policy); the address is
  // graded at the bottom tier there and the card's chip says so beside this title.
  const address = sidecar?.attributes?.lot_address?.value;
  if (address) return { title: String(address), spec, vacant: false };

  if (!noun || OUTBUILDING.has(noun)) {
    return { title: `${article(description)} ${description}`, spec, vacant: false };
  }
  if (LETTABLE.has(noun)) {
    return { title: `${article(description)} ${description}, to let`, spec, vacant: true };
  }
  return { title: `A vacant ${description}`, spec, vacant: true };
}

/**
 * Everything the Go-to search should match this building on, in one string.
 *
 * The reason it is here and not in the menu that uses it: the menu's list and the card's
 * title have to agree about what a building is called, and the search has to keep finding
 * the production identity after the title stops showing it. A visitor who read "D3 #017"
 * in a spreadsheet and a visitor who remembers the Pratts are looking for the same roof.
 *
 * @param {object} sidecar   the compiled record
 * @param {string} id        the record id
 */
export function searchTerms(sidecar, id = '') {
  const { title, spec } = displayName(sidecar, id);
  const households = Array.isArray(sidecar?.residents) ? sidecar.residents : [];
  return [
    id, title, spec,
    ...(Array.isArray(sidecar?.aka) ? sidecar.aka : []),
    sidecar?.placement?.symbolic_location,
    ...households.map((h) => h.name),
  ].filter(Boolean).join(' ');
}
