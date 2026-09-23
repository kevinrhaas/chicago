import json, os, re, csv, collections, datetime

DATE = '2026-09-05'
TICKET = 'T-0510'
ROOT = '.'
PKG = '../reference/resident-research/T-0510'

cohort = json.load(open('data/research/residents/pass_15_76_cohort.json'))
people = cohort['people']
verdict = json.load(open('/tmp/verdict2.json'))
xw = json.load(open('/tmp/xw.json'))
CONTEMP = {'civic', 'land_sales', 'census_1830', 'church', 'books'}

SEED = 'chicago_democrat_1833_1835'
FERGUS = 'fergus_historical_series_26_29'

# ---- source-id normalisation: keep only ids that resolve to a committed source record
def resolves(sid):
    return os.path.exists(f'data/sources/{sid}.json')

# a positive crosswalk record does not always carry its own source_id; the file it
# lives in always identifies the volume the reading came out of.
FILE_SOURCE = [
 ('fergus_1839', 'fergus_chicago_directory_1839'),
 ('fergus_1843', 'fergus_chicago_directory_1843'),
 ('norris_1844', 'norris_directory_1844'),
 ('death_notices', 'fergus_1843_old_settler_death_notices'),
 ('old_settlers/crosswalk', 'calumet_club_early_chicago_1879'),
 ('old_settlers/people', 'calumet_club_early_chicago_1879'),
 ('census_1830', 'census_1830_peoria_county_chicago_precinct'),
 ('census_1840', 'census_1840_chicago_name_crosswalk'),
 ('newberry_index', 'newberry_genealogical_index'),
 ('st_cyr', 'st_cyr_register_ichr_v4'),
 ('st_marys', 'st_marys_baptismal_register_1833_1835'),
 ('civic/', 'chicago_voter_lists_1833_1835_irad'),
 ('land_sales', 'isa_public_domain_land_tract_sales'),
 ('books/', 'fergus_historical_series_26_29'),
]

# The Newberry genealogical index is a FINDING AID published in 1960, and
# tools/read_newberry_index.py refuses to let it stand behind a person, a household or
# a building.  A lead off one of its cards is recorded in the person's notes and is
# never cited as a source here.
FINDING_AIDS = {'newberry_genealogical_index'}


def source_from_file(f):
    for frag, sid in FILE_SOURCE:
        if frag in f:
            return None if sid in FINDING_AIDS else sid
    return None

# ---- hand readings taken off the Fergus Historical Series 26-29 volume (1843 Chicago
#      Directory + Wentworth's obituary/death lists), quoted as printed.
FERGUS_READ = {
 'harmon_elijah_d': ("Harmon, Eli[j]ah D[e]we[y], physician, bds C. L. Harmon [died January 3, 1869, aged 80]",
   "The 1843 directory prints the full given names Elijah Dewey behind this project's 'Dr Elijah Dewey Harmon', with the same trade the 1835 record carries, and a death date and age that put birth about 1788-89."),
 'heacock_russel_e': ("Heacock, Russel Easton (Old Shallow-Cut, Chicago's first attorney at law), res 129 Adams [died, Summit, Ill., June 20, 1849, aged 70]",
   "The 1843 directory gives the middle name Easton, the trade the 1835 record carries, and a death date and age that put birth about 1779."),
 'hogan_john_s_c': ("Hogan, John Stephen Coates, ex postmaster, bds Charles L. P. Hogan [died, Boonville, Mo., December 2, 1868, aged 63]",
   "The 1843 directory resolves the initials S. C. to Stephen Coates and prints the postmastership. THE SAME VOLUME'S OBITUARY LIST CONTRADICTS ITSELF: 'Hogan, John Stephen Coates, early postmaster, died, Memphis, Tenn., 1866' — a different place and a different year. Both readings are recorded; neither is asserted."),
 'pearsons_hiram': ("Pearsons, Hiram, speculator, bds Tremont House [died, Almeda, Cal., August 11, 1868, aged 57]",
   "The 1843 directory prints the exact name with a death date and age that put birth about 1811."),
 'peck_philip': ("Peck, Phili[p] F[e]rdinand W[h]eeler, ca[p]italist, res 248 Clark, n.-w. cor Jackson [died October 23, 1871, aged 62]",
   "The 1843 directory resolves the initials F. W. to Ferdinand Wheeler and gives a death date and age that put birth about 1809."),
 'snow_george_w': ("Snow, George W[a]shington, lumber merchant, S. Water, res 344-6 State, s.-w. cor Jackson [died, en route to Philadelphia, at Altoona Pa., July 20, 1870, aged 72-10-13]",
   "The 1843 directory resolves the initial W. to Washington and gives a death date and an age to the day that put birth about October 1797."),
 'spring_giles': ("Spring, Giles (S[pring] & Goodrich), res 62 Adams near State [died May 14, 1851]",
   "The 1843 directory prints the exact name, the firm Spring & Goodrich, attorneys, 124 Lake, and a death date of 14 May 1851."),
 'owen_thomas_jv': ("Owen, Thomas J. V. (Indian agent), died Oct. 15, 1835, aged 34-1/2",
   "The volume's obituary list gives a death INSIDE the scene year, 15 October 1835, three and a half months after the scene date, and an age that puts birth about April 1801."),
 'robinson_alexander': ("Robinson, Alex. (Indian chief), died, on his Reservation, April 22, 1872, aged 83",
   "The volume's obituary list gives a death date and age that put birth about 1789, and names the reservation."),
 'morris_b_s': ("Morris, Buckner Smith, attorney, 59 Clark, res Indiana, bet Cass and Rush [Chicago's 2d mayor, died December 16, 1879, aged 79]",
   "The 1843 directory resolves the initials B. S. to Buckner Smith, prints the trade the 1835 record carries, and gives a death date and age that put birth about 1800."),
 'jones_benjamin': ("Jones, Benj. (B. J. & Co.), res 109 Randolph, bet Clark and Dearborn [died, Manitowoc, Wis., August 11, 1881, aged 87]",
   "The 1843 directory prints the name in the firm B. Jones & Co. with a death date and age that put birth about 1794. The surname is one of the town's commonest and the agreement is on the forename initial only, so the reading enriches without settling."),
}

# outcome overrides decided by hand against the discriminator, not the count
HAND = {
 # exact full name in the 1843 directory, but the bracketed death age contradicts an
 # 1834 newspaper adult: born about 1821 would make him fourteen at the scene date.
 'hoit_thomas': ('candidate_identity',
   "Fergus's reprint of the 1843 Chicago Directory prints 'Hoit, Thomas, carpenter, bds Mrs. E. Holt [died 1881, aged 60]' — the exact name of this project's Thomas Hoit, in the same town, eight years after the scene. THE AGE REFUSES TO SETTLE IT: an 1881 death at 60 puts birth about 1821, which would make him fourteen when the Democrat printed the 1835 resident. The 1843 carpenter is retained as a candidate and not asserted.",
   ['cand_thomas_hoit_fergus_1843_carpenter']),
}

# hand evidence_against, appended where a documented refusal is the discriminator
AGAINST_EXTRA = {
 'wright_john': "The same volume's obituary list prints 'Wright, John, died September 20, 1810, aged 57' — a death 25 years before the scene date, so that entry is not this man; the 1840 census pair is refused in the repository because 'John Wright' is borne by two people of 1835.",
 'fell_j_w': "A raw text sweep over-reports this surname because 'fell' is also an English verb; every apparent hit in the book corpus was the verb. The Newberry index lead heading 'Fell' is refused in the repository as locality_absent — its card names Illinois and neither Chicago nor Cook County.",
 'temple_mrs_john_t': "'Mrs Temple' carries no forename at all, so every later volume that prints the surname Temple is refused by the project's standing rule that a surname-only agreement is a refusal.",
 'temple_children_four': "The four Temple children are a household inference from Dr John Taylor Temple's record and carry no forenames; no later volume prints a Temple child of this household.",
 'robinson_catherine': "The 1840 census heads 'James Robinson' and 'John Robinson' are both refused against her in the repository on a given-name conflict; she is the only Robinson woman the 1835 layer holds.",
}

def domains_of(pid, kinds=('pos',)):
    return set(verdict[pid].get('pos_domains') or [])

AGREE_RE = re.compile(r'folds to the same string|initial for initial|both agree|forenames? agree')
REFUSE_RE = re.compile(r'is a refusal|is refused|\bis NOT\b|^Refused', re.I)

def classify(rec):
    """One classifier, used for both the source list and the quoted rules."""
    o = (rec.get('outcome') or '').lower()
    m = (rec.get('match') or '').lower()
    b = json.dumps(rec, ensure_ascii=False)
    r = rec.get('rule') or rec.get('reason') or ''
    if o == 'refused': return 'neg'
    if o == 'candidate' or 'CONTESTED' in b: return 'cand'
    if o in ('matched', 'merged', 'earlier_evidence'): return 'pos'
    if m in ('forename_agrees', 'exact'): return 'pos'
    if 'into' in rec and 'from' in rec: return 'pos'
    if AGREE_RE.search(r): return 'pos'
    if REFUSE_RE.search(r): return 'neg'
    return 'other'

def rule_texts(pid, want, limit=3):
    out = []
    for f, rec in xw.get(pid, []):
        r = rec.get('rule') or rec.get('reason') or ''
        if not r: continue
        if classify(rec) != want: continue
        r = re.sub(r'\s+', ' ', r).strip()[:400]
        if r not in out: out.append(r)
        if len(out) >= limit: break
    return out

PRETTY = {'civic': "the town's 1833 tax and 1834/1835 poll lists",
          'land_sales': 'the Illinois public-domain land tract sales',
          'census_1830': 'the 1830 census of the Chicago precinct',
          'census_1840': 'the 1840 census heads',
          'church': 'the St Cyr / St Mary registers',
          'books': 'the held book corpus',
          'directories': 'the Fergus 1839/1843 and Norris 1844 directories',
          'old_settlers': "the old-settler rolls and Fergus's death notices",
          'genealogytrails': 'the Genealogy Trails transcriptions',
          'newberry_index': 'the Newberry genealogical index cards',
          'sources': 'the source register'}

def pretty(doms):
    return ', '.join(PRETTY.get(d, d) for d in sorted(doms)) or 'a later volume'

rows = []
overrides = {}
counts = collections.Counter()
candidates_sheet = []
sources_used = collections.Counter()
search_log = []

for p in people:
    pid, name, stratum = p['person_id'], p['name'], p['stratum']
    v = verdict[pid]
    outcome = v['outcome']
    cand_ids = []
    if pid in HAND:
        outcome, hand_summary, cand_ids = HAND[pid]
    else:
        hand_summary = None

    pos_rules = rule_texts(pid, 'pos')
    neg_rules = rule_texts(pid, 'neg')
    cand_rules = rule_texts(pid, 'cand')

    srcs = [s for s in v['sources'] if resolves(s) and s not in FINDING_AIDS]
    for f, rec in xw.get(pid, []):
        k = classify(rec)
        keep = k == 'pos' or (outcome == 'candidate_identity' and k == 'cand')
        if keep:
            sid = source_from_file(f)
            if sid and resolves(sid) and sid not in srcs: srcs.append(sid)
    if pid == 'hoit_thomas' and resolves(FERGUS) and FERGUS not in srcs: srcs.append(FERGUS)
    fergus = FERGUS_READ.get(pid)
    if fergus and resolves(FERGUS) and FERGUS not in srcs:
        srcs.append(FERGUS)
        if outcome == 'no_corroboration': outcome = 'corroborated_enrichment'

    # evidence_for carries CONTEMPORARY evidence only (see the package README):
    # the synthesizer promotes canonical facts out of this field, and a trade or an
    # age read out of an 1843 volume is a back-projection this pass will not make.
    ev_for = ' '.join(pos_rules) if pos_rules else ''
    ev_against = ' '.join(neg_rules)
    if pid in AGAINST_EXTRA:
        ev_against = (ev_against + ' ' + AGAINST_EXTRA[pid]).strip()

    notes_bits = []
    if fergus:
        notes_bits.append(f'FERGUS 26-29, AS PRINTED: "{fergus[0]}". {fergus[1]}')
    if cand_rules and outcome == 'candidate_identity':
        notes_bits.append('Repository lead retained as a candidate: ' + cand_rules[0])
    notes_bits.append('Research only. Later-volume readings are recorded here and NOT promoted: T-0513 consolidates and T-0514/T-0515 apply.')
    notes = ' '.join(notes_bits)

    if hand_summary:
        summary = hand_summary
    elif outcome == 'corroborated':
        summary = (f"Independently corroborated. {name} agrees, forename for forename or initial for initial, "
                   f"with a record outside the post-office lists in " + pretty(domains_of(pid)) + ". " + (pos_rules[0] if pos_rules else ''))
    elif outcome == 'corroborated_enrichment':
        summary = (f"Corroborated in a volume printed after the scene date. {name} agrees with an entry in "
                   + pretty(domains_of(pid)) +
                   ". The reading enriches the biography and adds no 1835 attestation.")
    elif outcome == 'candidate_identity':
        summary = (f"A plausible external identity for {name} was found and is retained unasserted: no date, place, "
                   f"occupation or kinship discriminator bridges it to the 1835 person.")
    else:
        summary = (f"No reliable record outside the Chicago post-office lists could be tied to {name} with a "
                   f"date, place, occupation or kinship discriminator. "
                   + ("The repository's own crosswalks record the refusal: " + neg_rules[0] if neg_rules else
                      "No later volume, civic list, land-sale, census or church register reached prints the name at all.")
                   + " This is a documented no-corroboration result, not evidence that the person did not exist.")

    counts[outcome] += 1
    for s in srcs: sources_used[s] += 1

    item = {'outcome': outcome, 'summary': summary}
    if srcs: item['sources'] = sorted(set(srcs + [SEED]))
    if ev_for: item['evidence_for'] = ev_for
    if ev_against: item['evidence_against'] = ev_against
    if notes: item['notes'] = notes
    if cand_ids: item['candidate_ids'] = cand_ids
    overrides[pid] = item

    rows.append({'person_id': pid, 'name_transcribed': name, 'name_normalized': name,
                 'stratum': stratum, 'outcome': outcome, 'candidate_ids': ';'.join(cand_ids),
                 'proposed_facts': '', 'evidence_for': ev_for, 'evidence_against': ev_against,
                 'source_ids': ';'.join(sorted(set(srcs + [SEED]))),
                 'source_urls_tiers': '', 'queries': 'exact name; justified initial and OCR variants; surname with forename initial',
                 'access_date': DATE, 'notes': notes})

    search_log.append({'person_id': pid, 'name': name, 'date': DATE,
        'corpora': 'repository newspapers + identity ledger; civic tax/poll lists 1833-1835; ISA land tract sales; 1830 census; 1840 census heads; St Cyr / St Mary church registers; Fergus 1839, Fergus 1843 and Norris 1844 directories; Fergus Historical Series 26-29; Calumet Club old-settler rolls; Newberry index cards; genealogytrails transcriptions',
        'result': f"{v['pos']} agreement record(s), {v['cand']} candidate record(s), {v['neg']} documented refusal(s)",
        'limitation': 'FamilySearch and Ancestry are login-walled and were recorded as inaccessible, not absent; HathiTrust page views return 403.'})

json.dump({'counts': dict(counts), 'sources': dict(sources_used)}, open('/tmp/counts.json','w'), indent=1)
json.dump({'overrides': overrides, 'rows': rows, 'search_log': search_log,
           'counts': dict(counts)}, open('/tmp/built.json','w'), indent=1)
print(counts)
print(json.dumps(dict(sources_used), indent=1))
