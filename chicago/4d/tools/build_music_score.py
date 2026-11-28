#!/usr/bin/env python3
"""T-3710 — writes data/music/score.json, the Chicago 4D score's cues as ElevenLabs Music
composition plans (the owner picked ElevenLabs on 2026-11-20).

    python3 tools/build_music_score.py            rewrite data/music/score.json

Themes, era instruments, the respect rules and the under-narration rules are in the
"Chicago 4D Score" doc; this file turns them into sections and styles. Make the clips with
tools/fal_music.mjs --cues data/music/score.json.
"""
import json, sys, os
HOOK = "the Portage hook: a quick rising D major arpeggio D, F-sharp, A to a long held A; then F-sharp, D, down to a long C-sharp; then A, G, F-sharp down to a long D, and up to a long E; then home to D"
G = ["cinematic orchestral film score", "grand Hollywood adventure style", "French horns", "lush strings", "harp", "timpani", "consonant and tonal", "instrumental"]
N = ["vocals", "choir", "singing", "humming", "spoken word", "electronic", "synthesizer", "drum kit", "electric guitar", "atonal", "dissonant chromatic wandering"]
BEDG = ["soft underscore bed for a narrator speaking over it", "sparse and even", "slow steady tempo", "no lead melody in the middle register", "low strings, harp and high soft violins"]
BEDN = ["loud", "sudden hits", "big crescendo", "busy percussion", "prominent melody"]
ERA = {
 "1812": ["year 1812 frontier fort on Lake Michigan", "Woodlands cedar flute", "soft hand drum like a heartbeat", "Metis fiddle", "fife and rope snare"],
 "1835": ["year 1835 boom town on the Chicago River", "fiddle", "fife and drum", "keyed bugle", "hammered dulcimer", "reed organ"],
 "1871": ["year 1871 wooden city before the Great Fire", "saxhorn brass band", "cornet", "parlor piano", "church bells"],
 "1904": ["year 1904 gilded Prairie Avenue", "romantic orchestra", "ragtime piano touches", "salon strings"],
}
ERAN = {"1812": ["stereotyped tom-tom beat", "war whoops"], "1835": [], "1871": [], "1904": []}
def sec(name, s, *styles, neg=()):
    return {"section_name": name, "duration_ms": int(s * 1000), "positive_local_styles": list(styles), "negative_local_styles": list(neg)}
def plan(sections, era=None, bed=False):
    g = G + (ERA[era] if era else []) + (BEDG if bed else [])
    n = N + (ERAN[era] if era else []) + (BEDN if bed else [])
    return {"positive_global_styles": g, "negative_global_styles": n, "sections": sections}
def bed(name, era, text, extra=()):
    # a 60 s bed in three even sections, so it never builds
    return plan([sec(name + " A", 20, text, *extra), sec(name + " B", 20, text, "same texture continues, no new ideas"), sec(name + " C", 20, text, "eases to a quiet sustained close that can loop")], era, bed=True)
C = []
def cue(id, group, kind, themes, use, p, jaunts=None, era=None):
    c = dict(id=id, group=group, kind=kind, themes=themes, use=use, era=era or "all", plan=p)
    if jaunts: c["jaunts"] = jaunts
    C.append(c)
B12 = ["battle-of-fort-dearborn", "battle-of-fort-dearborn-grades-3-5", "battle-of-fort-dearborn-grades-9-10"]
cue("theme-first-people", "core", "statement", ["first-people"], "Theme suite; source for 1812 cues", plan([
  sec("Flute alone", 20, "a solo Woodlands cedar flute, free and unhurried, an original melody that opens with the rising fifth D to A, dignified and still"),
  sec("Strings join", 25, "soft strings and harp beneath the flute, a hand drum like a slow heartbeat"),
  sec("Close", 15, "the flute alone again, a long final note")], "1812"))
cue("theme-waters", "core", "statement", ["waters", "portage"], "Theme suite; the river and lake", plan([
  sec("Current", 20, "a rolling six-eight ostinato in harp and low strings, like a river current"),
  sec("Melody", 25, "a warm clarinet and horn line over the current that hints at the Portage hook"),
  sec("Lake", 15, "the current widens into shimmering strings, the river meeting the lake")]))
cue("theme-fort", "core", "statement", ["fort"], "Theme suite; Fort Dearborn", plan([
  sec("Call", 12, "a crisp fife and rope-tension snare play a dotted garrison duty call"),
  sec("March", 30, "horns and strings take the call up as a proud small march, about 112 beats per minute"),
  sec("Retreat", 18, "the fife plays the call once more, softer, as at day's end")], "1812"))
cue("theme-remembrance", "core", "statement", ["remembrance", "portage"], "Theme suite; loss and memory", plan([
  sec("Cello", 25, "a solo cello plays the Portage hook slowly in D minor, noble and sorrowful"),
  sec("Strings", 25, "full strings take it, grief without blame"),
  sec("Horn", 10, "a quiet French horn and an open fifth to end")], None))
cue("theme-mystery", "core", "statement", ["mystery"], "Theme suite; mysteries and ghosts", plan([
  sec("Question", 20, "celesta and low clarinet, a curious motif that bends through a tritone before settling, pizzicato basses"),
  sec("Search", 25, "muted strings creep, a little eerie, never horror"),
  sec("Unanswered", 15, "the motif once more, ending on an unresolved chord")]))
# Jaunt openings and closings: only the bed is generated. The fixed Portage recording's first
# phrase is spliced on the front of an opening and its cadence on the end of a closing.
for era in ("1812", "1835", "1871", "1904"):
    cue(f"jaunt-opening-{era}", "jaunt", "bed", ["portage"], f"Every {era} jaunt opening, after the fixed fanfare phrase", bed("Opening", era, "a quiet bed that follows a heroic D major brass fanfare and sits under a narrator, settled and expectant"), None, era)
    cue(f"jaunt-closing-{era}", "jaunt", "bed", ["portage"], f"Every {era} jaunt closing scene, before the fixed fanfare cadence", bed("Closing", era, "a quiet, warm bed under a narrator's closing words, gently rising at the very end toward a D major cadence"), None, era)
cue("bed-1812-fort", "jaunt", "bed", ["fort", "waters"], "Fort Dearborn, Building by Building", bed("Fort day", "1812", "a guided walk around the fort by day: a soft distant fife figure now and then, a rolling harp current beneath, warm low strings"), ["first-fort-dearborn-tour"], "1812")
cue("bed-1812-mystery", "jaunt", "bed", ["mystery", "first-people"], "Chicago's First Murder", bed("Dusk", "1812", "a frontier murder mystery at dusk by the river: pizzicato low strings, soft celesta, a single flute phrase in pauses, tension kept low"), ["killing-of-jean-lalime"], "1812")
cue("battle-1-buildup", "battle", "bed", ["fort", "first-people"], "Battle of Fort Dearborn: the order to leave, the warnings", bed("Dread", "1812", "August 1812, the order to leave the fort: the garrison call slowed and uneasy, a low string pedal, a heartbeat hand drum, a worried horn answers the flute"), B12, "1812")
cue("battle-2-march", "battle", "bed", ["fort", "portage"], "Battle of Fort Dearborn: the march out along the lake", bed("March out", "1812", "the garrison and families march out along the lake shore: a slow funereal fife and muffled drum, the hook in a minor key in low horns, waves in the harp"), B12, "1812")
cue("battle-3-fight", "battle", "bed", ["fort", "first-people", "remembrance"], "Battle of Fort Dearborn: the fight in the dunes", bed("Dunes", "1812", "the fight among the sand dunes: driving low string ostinato, low timpani and frame drums kept beneath the voice, fragments of the fife call and flute colliding, tragic, no side cheered"), B12, "1812")
cue("battle-4-aftermath", "battle", "bed", ["remembrance", "first-people"], "Battle of Fort Dearborn: the aftermath and the fort burning", bed("Aftermath", "1812", "the aftermath: a slow solo cello, the cedar flute mourning everyone who died, low string tremolo like a distant fire"), B12, "1812")
for id, use, jaunts, txt in [
  ("bed-1904-places", "Meet the Glessner House", ["prairie-avenue-orientation"], "a walking tour of great houses on a fine morning: gentle salon strings in three-four, soft harp, a piano chord now and then"),
  ("bed-1904-household", "The Glessner Household (all grades)", ["glessner-household-tour", "glessner-household-tour-grades-3-5"], "a tour of one family's home and its servants: an intimate piano trio, warm cello, soft violin, a celesta touch of the hook in pauses"),
  ("bed-1904-people", "Famous names; Women of Prairie Avenue", ["prairie-famous-names", "prairie-notable-women"], "stories of famous people: a dignified string orchestra, a soft horn hint of the hook in pauses"),
  ("bed-1904-stories", "The seven other 1904 story jaunts", ["field-and-mrs-caton", "frances-glessner-lee", "monday-reading-class", "one-year-and-a-day", "pullmans-other-son", "the-pullman-twins", "the-walk-to-the-lake"], "true personal stories: harp and clarinet, gentle strings, a soft piano, like turning the pages of a family album"),
  ("bed-1904-architecture", "Architects; Italianate, Romanesque and Second Empire walks", ["prairie-architects", "prairie-style-italianate", "prairie-style-romanesque", "prairie-style-second-empire"], "walks about architecture and craftsmanship: a slow stately brass and string chorale, soft, like light moving across carved stone"),
  ("bed-1904-ghosts", "Ghosts of Prairie Avenue", ["prairie-ghosts-at-night"], "a ghost-story walk at night: celesta, muted strings, a distant music box waltz slightly out of tune, spooky fun, never horror"),
  ("bed-1904-bronze", "The Bronze at Eighteenth Street (the Fort Dearborn monument)", ["bronze-at-eighteenth"], "a bronze monument to the Battle of Fort Dearborn: slow soft strings in D minor, once a single distant cedar flute rising a fifth"),
  ("bed-1904-scandal", "The Scandal at 1612 Prairie; The Sisters of the Levee", ["scandal-at-1612", "sisters-of-the-levee"], "scandalous true stories: a sly slow ragtime piano, soft, pizzicato strings, a muted trumpet sigh in pauses")]:
    themes = {"bed-1904-ghosts": ["mystery"], "bed-1904-bronze": ["remembrance", "first-people"], "bed-1904-scandal": ["mystery", "gilded-age"]}.get(id, ["gilded-age", "portage"])
    cue(id, "jaunt", "bed", themes, use, bed(id.split("-")[-1].title(), "1904", txt), jaunts, "1904")
# T-3811 (owner, 2026-11-27: "every jaunt should have music ... let me know if you need anything
# to fill in"): 1835 and 1871 get beds of their own (they borrowed the 1812 and 1904 cues).
J35 = {"town": ["a-decent-coat", "bed-for-the-night", "calling-on-neighbors", "gossip-or-notice", "household-provisions",
         "inspect-a-lot", "letter-home", "new-in-chicago", "news-before-breakfast", "notable-women-1835", "outfit-for-the-west",
         "schoolday-errand", "shopping-south-water", "soap-and-candles", "sunday-circuit", "an-evening-stroll", "from-prairie-to-town",
         "fort-dearborn-errand"],
       "river": ["a-parcel-across-the-river", "across-wolf-point", "along-the-harbor", "freight-for-the-store", "over-the-draw",
         "work-on-waterfront"],
       "trades": ["apprentice-at-the-democrat", "boots-and-leather", "materials-for-a-roof", "mend-the-harness", "taverns-of-chicago"]}
for key, use, txt in [
  ("town", "1835 errands, people and town walks", "a boom town of new frame stores and muddy streets on a bright day: a light fiddle and hammered dulcimer figure, soft reed organ chords, hopeful and busy but quiet"),
  ("river", "1835 river, harbor and bridge jaunts", "the working river and harbor: a rolling six-eight harp and low string current, a distant keyed bugle call now and then, schooners and the open lake"),
  ("trades", "1835 trades and workshops", "honest work in small shops: a steady plucked fiddle and dulcimer pattern like a tool in rhythm, warm low strings, homely and unhurried")]:
    cue(f"bed-1835-{key}", "jaunt", "bed", ["waters", "portage"] if key == "river" else ["portage"], use, bed(key.title(), "1835", txt), J35[key], "1835")
for id, use, jaunts, txt in [
  ("bed-1871-city", "The Last Sunday; A Message for the Opera House", ["the-last-sunday", "a-message-for-the-opera-house"],
   "the proud wooden city on a warm, dry Sunday afternoon in October: a gentle saxhorn band chorale far off, parlor piano, soft strings, a church bell now and then, a faint unease in the low strings"),
  ("bed-1871-inquiry", "Who Started the Fire?", ["who-started-the-fire"],
   "weighing the evidence of who started the fire: pizzicato low strings, a curious clarinet, soft muted brass, the mystery left open"),
  ("fire-1-rising", "The Great Fire: the barn to the river", ["the-great-fire"],
   "night, a fire spreading on a gale through a wooden city: a low string pedal with a slowly quickening pulse, a distant fire bell, tension that grows but stays under the voice"),
  ("fire-2-inferno", "The Great Fire: the business district and the North Side burning", ["the-great-fire"],
   "the whole city on fire: driving low string ostinato, low timpani kept beneath the voice, a minor saxhorn chorale, grief and awe, tragic, never exciting"),
  ("fire-3-ruins", "The Great Fire: the last refuges and the rain", ["the-great-fire"],
   "exhausted people in the ruins and then rain: a slow solo cello, soft strings, distant church bell, the first hope at the very end")]:
    kind = "fire" if id.startswith("fire-") else "jaunt"
    themes = ["mystery"] if id.endswith("inquiry") else ["remembrance", "portage"] if id.startswith("fire-") else ["portage"]
    cue(id, kind, "bed", themes, use, bed(id.split("-")[-1].title(), "1871", txt), jaunts, "1871")
out = {"version": 1,
 "about": "T-3710 (owner, 2026-11-20): the generated part of the Chicago 4D score, as ElevenLabs Music composition plans through fal (the owner picked ElevenLabs over MiniMax v2.5 and Stable Audio). The main theme is a FIXED recording the owner chose (THEME-FINAL-portage-main-title.mp3); the title, ident, stings and overtures are cut from or built around it, never regenerated. Themes and rules: the Chicago 4D Score doc (https://claude.ai/artifact/ACXQqZ3pvHqLpofx2ZuqUP). Nothing here is played by the app yet. Built by a script; re-run it rather than hand-editing.",
 "models": {"elevenlabs": {"endpoint": "fal-ai/elevenlabs/music", "price": {"usd": 0.6, "per": "minute", "rounded_up": True}, "duration_param": "music_length_ms", "duration_scale": 1000, "duration_range": [3, 600], "output": "audio", "plans": True, "extra": {"force_instrumental": True}}},
 "trial_models": ["elevenlabs"], "cues": C}
for c in C: assert all(len(x) <= 300 for x in c["plan"]["positive_global_styles"])
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "music", "score.json")
text = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
open(path, "w").write(text); print(f"wrote {len(C)} cues")
