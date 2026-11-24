/** Make your case: the case table (T-3663, T-3678, T-3693). One row per jaunt whose own cited
 * evidence argues a question both ways. A row names the jaunt (its tellings match by
 * `version_of`), the scene year, and the readings to compare; each reading is a set of
 * the jaunt's compiled evidence ids, with the stop that cites it, the grade it must still
 * carry and the source ids it must still name. The words a visitor reads (questions per
 * audience band, reading titles, labels and review notes) are in strings/investigation.js
 * under `investigation.<case id>.…`. docs/RESEARCH/investigations-3678.md records why each
 * case's readings conflict. A row adds no fact: the model refuses the case unless every
 * named claim is still in the telling, on a visited stop, with its grade and sources.
 *
 * `locator` on a reading borrows one claim's locator for the whole reading (the Gossip
 * American item, whose Springfield reading has none of its own). `adults: true` lets an
 * adults (18+) telling offer the case; the later cases leave those tellings out. */
const claim = (id, stop, confidence, ...sources) => Object.freeze({ id, stop, confidence, sources: Object.freeze(sources) });
const reading = (id, claims, locator = '') => Object.freeze({ id, locator, claims: Object.freeze(claims) });

export const CASES = Object.freeze([
  Object.freeze({ id: 'gossip', jaunt: 'gossip-or-notice', year: '1835', adults: true, readings: Object.freeze([
    reading('democrat', [claim('land-sale', 'the-democrat', 'attested', 'chicago_democrat_1833_1835')], 'land-sale'),
    reading('american', [claim('bank-branch', 'the-american', 'attested', 'chicago_american_1835'),
      claim('bank-springfield', 'the-american', 'inferred', 'chicago_american_1835')], 'bank-branch'),
  ]) }),
  Object.freeze({ id: 'where-attack', jaunt: 'battle-of-fort-dearborn', year: '1812', readings: Object.freeze([
    reading('officers', [claim('heald-journal', 'the-bank', 'attested', 'quaife_1913'),
      claim('helm-hour', 'the-bank', 'attested', 'quaife_1913')]),
    reading('remembered', [claim('place-readings', 'cottonwoods', 'attested', 'andreas_1884_v1', 'kirkland_1893_chicago_massacre'),
      claim('stand-bank', 'the-bank', 'inferred', 'andreas_1884_v1', 'kirkland_1893_chicago_massacre', 'quaife_1913')]),
  ]) }),
  Object.freeze({ id: 'trading-post', jaunt: 'killing-of-jean-lalime', year: '1812', readings: Object.freeze([
    reading('family', [claim('family-version', 'du-sable-house', 'attested',
      'kinzie_waubun_1856', 'currey_1912_story_of_old_fort_dearborn', 'quaife_1913')]),
    reading('deed', [claim('deed', 'du-sable-house', 'attested', 'dailing_2018_chicago_reader_lalime')]),
  ]) }),
  Object.freeze({ id: 'chappel', jaunt: 'schoolday-errand', year: '1835', readings: Object.freeze([
    reading('andreas', [claim('chappel-school', 'the-log-house', 'attested', 'andreas_1884_v1')]),
    reading('online', [claim('chappel-moved', 'the-log-house', 'attested', 'drloih_chappell')]),
    reading('placed', [claim('chappel-place', 'the-log-house', 'inferred', 'andreas_1884_v1', 'drloih_chappell')]),
  ]) }),
  Object.freeze({ id: 'bronze-rescue', jaunt: 'bronze-at-eighteenth', year: '1904', readings: Object.freeze([
    reading('monument', [claim('battle-statue', 'bronze', 'attested',
      'wikipedia_fort_dearborn_massacre_monument', 'chicagoandcook_2017_1812_massacre_site')]),
    reading('historian', [claim('statue-doubt', 'bronze', 'attested', 'karamanski_2004_monuments_lost_nation_p6'),
      claim('statue-models', 'bronze', 'attested', 'karamanski_2004_monuments_lost_nation_p6')]),
  ]) }),
  // T-3693: Who Started the Fire? Four accounts of the barn: Catherine O'Leary's sworn
  // testimony, Sullivan's affidavit, the Board's finding, and Bales's modern theory.
  Object.freeze({ id: 'fire', jaunt: 'who-started-the-fire', year: '1871', readings: Object.freeze([
    reading('oleary', [claim('oleary-testimony', 'catherine', 'attested', 'greatchicagofire_oleary_legend_2011')]),
    reading('sullivan', [claim('sullivan-affidavit', 'the-barn', 'attested', 'andreas_1885_v2')]),
    reading('board', [claim('board-finding', 'the-inquiry', 'attested', 'greatchicagofire_oleary_legend_2011')]),
    reading('bales', [claim('peg-leg', 'other-suspects', 'attested', 'chicago_tribune_1998_03_03_odds_improve')]),
  ]) }),
]);
