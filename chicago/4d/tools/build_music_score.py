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
cue("main-title", "core", "statement", ["portage", "first-people"], "Home page, main title, credits", plan([
  sec("Opening fanfare", 16, "trumpets and horns play " + HOOK, "bold and bright, light timpani"),
  sec("Variation", 24, "a variation on the same hook: the same notes in violins and horns with a new rhythm and fresh harmony, light and clear, harp arpeggios"),
  sec("Flute", 20, "a solo cedar flute plays the hook simply over soft strings, open prairie and lake"),
  sec("Exploring", 30, "the music explores and develops fragments of the hook, adventurous and curious, transparent and uncluttered"),
  sec("Opening returns", 30, "the opening fanfare returns exactly as at the start, trumpets and horns with the full orchestra, ending on a big D major chord")]))
cue("main-title-short", "core", "statement", ["portage"], "App start, time travel, loading", plan([
  sec("Call", 8, "trumpets and horns state " + HOOK), sec("Answer", 14, "full orchestra repeats the hook, strings swell"), sec("End", 8, "bright held D major chord")]))
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
cue("stings-discovery", "core", "sting", ["discovery"], "Stop arrivals, right answers, photo found (cut into stings)", plan([
  sec("Sting 1", 5, "a bright short horn flourish leaping up a fifth, harp glissando, triangle, then silence"),
  sec("Gap 1", 3, "silence"),
  sec("Sting 2", 5, "a short trumpet and glockenspiel flourish on the hook's first notes, then silence"),
  sec("Gap 2", 3, "silence"),
  sec("Sting 3", 5, "a warm string and harp flourish rising to a D major chord, then silence"),
  sec("Gap 3", 3, "silence"),
  sec("Sting 4", 6, "a cedar flute and horn rising fifth, a soft cymbal, then silence")]))
cue("overture-1812", "era", "statement", ["first-people", "fort", "portage"], "1812 arrival, era theme", plan([
  sec("Dawn", 25, "a cedar flute over a heartbeat hand drum, wide prairie and lake"),
  sec("Traders", 25, "a Metis fiddle tune answers, lively but gentle"),
  sec("The fort", 25, "the fife and drum garrison call, horns join"),
  sec("Portage", 45, "the orchestra plays " + HOOK + " with flute and fiddle colours, broad and hopeful")], "1812"))
cue("overture-1835", "era", "statement", ["portage", "fort"], "1835 arrival, era theme", plan([
  sec("Reel", 30, "a lively fiddle reel version of the Portage hook, fife and drum, hammered dulcimer"),
  sec("Hymn", 30, "a hymn-like passage on reed organ and strings"),
  sec("Farewell", 15, "a brief distant cedar flute phrase"),
  sec("Boom town", 45, "keyed bugle and the orchestra in full with the hook, optimism and hustle")], "1835"))
cue("overture-1871", "era", "statement", ["portage", "fire"], "1871 arrival, era theme", plan([
  sec("Parlor", 30, "a parlor piano and cornet play the Portage hook as a parlor ballad"),
  sec("Band", 30, "a saxhorn brass band march on the hook"),
  sec("Omen", 30, "a darker passage, a falling bass line and a high bell striking in threes, the fire foreshadowed"),
  sec("Resolve", 30, "the orchestra returns to the hook, resolute and strong")], "1871"))
cue("overture-1904", "era", "statement", ["gilded-age", "portage"], "1904 arrival, era theme", plan([
  sec("Rag", 30, "ragtime piano plays a syncopated Portage hook"),
  sec("Waltz", 30, "salon strings turn the hook into a graceful three-four waltz"),
  sec("Trio", 30, "a concert band trio gives the hook a proud march"),
  sec("Grand", 30, "the full romantic orchestra closes on the hook, grand and warm")], "1904"))
for era, open_txt, close_txt in [("1812", "a cedar flute plays the hook's opening, a soft horn answers", "a gentle horn and string statement of the hook's end with a final flute note"),
                                 ("1904", "warm strings and a touch of piano play the hook", "a warm string and horn statement of the hook's end, a glowing chord")]:
    cue(f"jaunt-opening-{era}", "jaunt", "statement-then-bed", ["portage"], f"Every {era} jaunt opening (narration starts after about 6 s)", plan([
      sec("Hook", 6, open_txt), sec("Bed", 54, "settles into a quiet bed for a narrator, sparse and even", neg=BEDN)], era))
    cue(f"jaunt-closing-{era}", "jaunt", "bed-then-statement", ["portage"], f"Every {era} jaunt closing scene", plan([
      sec("Bed", 48, "a quiet bed for a narrator, sparse and even", neg=BEDN), sec("Hook", 12, close_txt)], era))
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
out = {"version": 1,
 "about": "T-3710 (owner, 2026-11-20): the Chicago 4D score's first baseline set, as ElevenLabs Music composition plans through fal (the owner picked ElevenLabs over MiniMax v2.5 and Stable Audio). Themes and rules: the Chicago 4D Score doc (https://claude.ai/artifact/ACXQqZ3pvHqLpofx2ZuqUP). Nothing here is played by the app yet. Built by a script; re-run it rather than hand-editing.",
 "models": {"elevenlabs": {"endpoint": "fal-ai/elevenlabs/music", "price": {"usd": 0.6, "per": "minute", "rounded_up": True}, "duration_param": "music_length_ms", "duration_scale": 1000, "duration_range": [3, 600], "output": "audio", "plans": True, "extra": {"force_instrumental": True}}},
 "trial_models": ["elevenlabs"], "cues": C}
for c in C: assert all(len(x) <= 300 for x in c["plan"]["positive_global_styles"])
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "music", "score.json")
text = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
open(path, "w").write(text); print(f"wrote {len(C)} cues")
