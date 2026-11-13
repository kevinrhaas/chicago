# Recorded audio pilot — T-3532

For the owner's hosting questions, see [AUDIO-HOSTING.md](AUDIO-HOSTING.md):
streaming behavior, the project versus provider limits, separate dev/main sites,
shared audio storage, current published provider pricing and the upload bundle.

## Scope and delivery status

Current checkpoint (2026-11-11): PR #1912 is merged and live on DEV after all 18
published smoke jobs and a public speaker/playback check at both viewport sizes.
The older pilot measurements below describe pre-integration checkpoints. This
increment, T-3544, adds continuous music, a quieter environmental mix and moving transport; production promotion remains separate.
Eighteen candidates now remain audition-only, with two additional dated mechanical
textures using the existing verified R2 files. The owner-selected calmer river adds one verified 352,940-byte MP3; the existing deliveries are retained.

Moving transport uses the Effects bus: actual mesh anchors and accepted travelled
metres drive direction, distance and intensity. Harness jingles serve four loaded
moving teams; rolling wood serves the three 1812/1835 wagons, not the 1904 brougham.
The catalogue names each actor and scene date. Stop, dwell, pause, reduced motion,
hidden/cull, off-hours and disposal silence those sources. Two nearest teams share
two mono 48 kHz buffers (6,737,316 decoded bytes, 8 MiB ceiling) across four finite
voices. Four-to-six-second recorded excerpts have unchanged pitch, edge fades and
short gaps; they are mechanical textures, not individual hoof strikes. Pending
decode work cannot restart a retired source. The shared listener updates even with
Ambience and Music both off. Human listening and Safari/device qualification remain.

### Owner listening adjustment — 2026-11-11

The owner liked the insects and found wind too strong in town, especially 1904, and the river proxy too busy for the visibly slow, nearly still water. Habitat recordings, scheduling and gains remain unchanged. Wind now uses subdued town gains of 0.030 / 0.022 / 0.012 in 1812 / 1835 / 1904, versus the former constant 0.13. Classified lake proximity raises that mix gradually to at most 0.055; fall halves leaf rustle and winter stops it. These are listening presets and shoreline proximity, not simulated weather or calculated building shelter. Lake waves keep their separate gain and geography.

The owner selected **Light water on rocks** (TRP575244) from three actual loop auditions. Its exact 22-second mono loop now supplies classified river edges; it is a modern Manitoulin rocky-lake recording used as an explicitly reconstructed river proxy. It does not replace lake surf or supply slough audio. Source crop 121–145 seconds, a two-second end-to-start overlap and unity gain are preserved; both source and accepted delivery hashes are pinned. Generation verifies a temporary encoding before replacing the accepted file. The previous busy TRP577323 take remains `river-held`, disabled and excluded from scene requests, with its original rights and review history.

The owner uploaded the selected MP3, and full public verification passed for its exact hash, CORS, MIME and byte ranges. It adds 352,940 transferred bytes. Three eligible 22-second environmental buffers use 12,672,000 decoded bytes within the 14 MiB environmental cache. Habitat and transport have their separate existing bounds; insects remain unchanged.

Other audition candidates remain inactive: [McClintock Bay](https://freesound.org/people/SoundsLikeYukon/sounds/758708/) includes a possible faint dock cleat/flagpole clang; [Pier Lap](https://freesound.org/people/craigsmith/sounds/438839/) has wooden-dock character. The selected [Manitoulin recording](https://freesound.org/people/TRP/sounds/575244/) retains its rocky-lake provenance rather than being relabelled a historical Chicago recording.

### 1904 nature sounds — T-3585 (2026-11-13)

The owner heard few birds in 1904 summer daytime: 1904 had no habitat sound at all, only the 0.012 leaf rustle. It now has its own `town_placements` (catalogue and intake), read by `renderers/web/js/habitat-town.js` through the existing habitat scheduler, on four recordings already licensed and verified on R2, so no new bytes are uploaded or shipped:

| Recording | 1904 seasons and hours | Where |
|---|---|---|
| robin-calls | spring and summer dawn/day/dusk (gaps 25–55 s, 20–45 s), fall dawn/day (90–180 s) | one mature parkway elm's crown, 9 m up, 24–110 m away, behind the listener when the phrase begins |
| summer-cicada-proxy | summer, after noon, day/dusk | listener within 45 m of a parkway elm |
| summer-crickets | summer dusk/night | listener within 45 m of a parkway elm |
| late-summer-katydid | summer nights from 20 July only (silent on the scene's 1 July) | listener within 45 m of a parkway elm |

The habitat is the scene's own `data/street_trees/1904.json` (main.js passes `streetTrees` into the audio environment); a date whose own season disagrees with the visitor's season stays quiet; winter is silent and no insect plays outside summer. The robin's season rests on Woodruff 1907 (`woodruff_1907_birds_chicago_area`: abundant summer resident, early April to October) and the Illinois DNR account. Unlike the 1835 red-wing, a robin phrase that has begun is not cut when the visitor turns toward its tree, since it sings inside a drawn crown. One habitat voice and the 12–25 s global gap are unchanged. The house sparrow, 1904's commonest street bird, has no licensed recording yet and is left silent rather than faked; the European starling is excluded (not in Woodruff's 1907 list). Liberty: L-1904-nature-sounds-3585. Test: `tools/test_habitat_audio_1904.mjs`.

### Pre-integration pilot checkpoints

This is a local, reviewable foundation, not a completed town soundscape or a
production release. It implements the owner's music, recorded wind/river/lake,
opt-in controls and the catalogue. Three dated 1835 habitat recordings now have a
first scheduler; actor events, additional wildlife, weather, speech,
interior filtering and scheduled activity below are implementation requirements.

The generated development build now points to verified, content-addressed R2
media. Its 40 delivery files (39.266 MiB) are omitted from the Pages artifact;
authoring files remain local. The pre-integration pilot measured 431.363 MiB within
its then-unchanged 432 MiB budget, including a lossless whitespace reduction in the
published liberties data. Incoming dev work now sets a 433 MiB allowance; the
combined build requires fresh validation. These are local builds, not a deployed release. The
bucket's r2.dev endpoint is for development; production hostname/cache setup and
the complete repository release gate remain outstanding. See AUDIO-HOSTING.md.

The actual published arrival page passes in Chromium at 390px and 1280px:
no audio requests before opt-in, a trusted speaker click starts real R2 samples
through the master gain, and a second click mutes. Published-module checks also
cover era changes, wind decoding and hidden/mute cleanup. The full-scene smoke
now targets the evidenced workplace action explicitly, since the People card's
first button is Find/Follow and can legitimately be disabled. A focused regression
test covers both a person present and a person away. The complete release gate
still requires both viewports and every smoke stage.

## Narration (T-3578)

The owner, 2026-11-13, asked for the jaunt scripts (first *The Glessner Household*) to be read
aloud in his ElevenLabs voices, made automatically rather than by copying text out of the app.

**What is spoken.** `renderers/web/js/narration.js` § `narrationScripts` lists a jaunt's opening
(its title, then the welcome's paragraphs), each stop (its `since` lead and text, read by the
stop's first host, else the narrator) and each ending (the narrator). The app and the voicer
both use that one function on the compiled jaunt the app loads, so what is voiced is exactly
what the panel shows. Each script is keyed by the SHA-256 of its words.

**Voices.** `data/narration/voices.json` lists the voiced jaunts and a voice per speaker: an
ElevenLabs voice id, or the exact name of one of the owner's voices; `null` is not yet chosen
and that speaker is skipped. Model, output format (`mp3_44100_64`, mono speech at 64 kbit/s,
about 0.5 MB a minute), voice settings and a per-run character cap live there too.

**Voicing.** `.github/workflows/chicago-4d-narration.yml` runs on a push to dev that touches a
compiled jaunt, the voice file or the script function, and by hand (plan / voice / list-voices).
`tools/narrate_jaunts.mjs` reads the media host's `narration/index.json` and sends ElevenLabs
only the scripts with no clip for their words, or a clip made with another voice or settings:
an unchanged jaunt costs nothing. Clips are uploaded to the R2 bucket as
`narration/<sha256 of the bytes>.mp3` (immutable), then the index (no-cache), and the run
fetches both back from the public host to verify them. The index only gains entries, so a
build still showing older words (production before a promote) keeps finding its clips. The run
keeps the clips as an artifact for 30 days. Secrets: `ELEVENLABS_API_KEY`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT` (an R2 API token with Object Read & Write on the
bucket); without them a push run says so and stops green.

**Playback.** The app finds the index beside the hosted media (`hosting.public_base` in the
published catalogue; a local build looks beside its own audio). A part with a clip for its
current words shows **Listen**; one without shows nothing, so changed words are silent until
voiced again. One media element, primed with a moment of silence inside a tap (WebKit, so
iPhone Chrome, then lets later stops start unprompted), streams through Settings › Sound's
**Narration** bus under Master, and music, ambience and effects duck to 0.3 while it speaks.
With sound on and Narration up, arriving at a stop starts its voice, or queues it behind the one
still speaking; travelling on does not cut a voice off; muting Narration or all sound, hiding
the page or leaving the jaunt ends it. A Listen tap with sound off turns it on. The
Navigator's **Mute narration** key flips the Narration level as Mute music flips Music.

**Liberty.** The voices are synthetic and chosen by ear, not the people's voices
(L-jaunt-voices-3578). A stop's `narrative` and the road notes are not voiced yet.

## Implemented foundation

The expanded catalogue now contains 34 source assets: seven era-specific music
cues, four environmental recordings (three active and the held earlier river take), and 23 additional recorded candidates.
Those candidates include wildlife/insects, horse vocalizations/hooves/harness,
woodworking, a musket, wagon, steam whistle, fire, dock/door/bell and performed
tavern chatter. Candidate previews add 5,605,876 bytes; all 41 delivery alternatives
together are 41,526,317 bytes (39.603 MiB). Eighteen candidates remain audition-only; two have dated moving-transport bindings.
Three have explicit 1835-07-01 habitat placements: the owner-approved Italian
cicada, Ontario field crickets and a distant red-wing call. Their source identity
and acoustic-proxy limitations remain visible; they are not enabled in all eras.
The library distinguishes habitat sounds, moving-team recordings and recordings still for review.

`assets/audio/intake.json` carries source evidence, proposed seasons/eras,
species uncertainties and pointers to existing 1835 fauna records. The same
fauna records may not be silently applied to 1812 or 1904. In particular, the
recorded true katydid is a late-summer candidate; the existing July record says
it is silent/not perceptible. The steam traction whistle is proposed for 1904,
not rail service in the two earlier scenes. The frog is not identified as a
bullfrog, and the tavern walla is one human performer, not Native dialogue.

The shared library is `assets/audio/catalog.json`; runtime deliveries and the
searchable Audio library are under `renderers/web/audio/`. Rebuild with
`python tools/prepare_audio.py` (ffmpeg/ffprobe). Originals remain under
`assets/audio/originals/`, outside the published tree. Keep source-specific rights:
the owner-supplied score is not licensed as an open sample collection.

Music collections are deliberately disjoint: 1812 Frontier (3), 1835 Border (2),
1904 Ragtime (10; T-3569, the owner's own set, which replaced the two waltzes on
2026-11-12). The waltzes stay catalogued with `runtime_enabled: false`. Eras listed in
the catalogue's `music_shuffle_eras` (only 1904) open at a random track and play a
shuffled order: every track once before any repeats, and a re-shuffle never reopens
with the track that just ended. The ragtime deliveries are matched to -17.5 LUFS
integrated by one static gain per track, with trailing silence cut to 0.4 s; Opus
64 kbps VBR (1.0-2.1 MB a track) with AAC-LC 112 kbps fallback. `prepare_audio.py
--ragtime-only` rebuilds just these, leaving every other verified delivery untouched. Browser selection uses Ogg/Opus first and AAC when unsupported.
Only the active cue streams. Music cycles continuously through the selected era’s
collection, wrapping to the first cue with no scheduled silence between tracks.
Period music is permitted only while exploring, inspecting, on a jaunt or touring; time travel, landing, the arrival choices and recall keep it off without changing the ambience/effects sliders. The compact loading-screen speaker retains a 44 px touch target and accessible on/off labels. Settings keep only the requested Ambience and Effects examples, grouped close to their own sliders; the additional Music/general notes were removed on owner review.
The same streaming element is retained across track endings; loading the next
file can still take a moment. There is no full-playlist preload. Music gain includes 6 dB headroom before its slider;
original decoded true peaks were -0.43 to +0.49 dBTP. Master defaults off; the
loading-screen speaker button enables it, with detailed levels in Settings.

Wind, the selected river and the lake use 22-second mono loops with a two-second edited seam. The previous river take remains held and auditionable in the library. A 48 kHz offline decoder keeps each loop at 4,224,000 bytes even when the output device runs at 96 or 192 kHz. The three eligible environmental buffers total 12,672,000 bytes within the existing 14 MiB environmental cache. River and lake play only in their own classified areas; sloughs do not borrow either recording. Music streams without full decoding into an AudioBuffer. The environmental cache is cleared on mute, hiding, context replacement, disposal and scene changes. Aborted/stale requests cannot restart playback. No network access to Freesound occurs at runtime.
The habitat scheduler shares the fixed 48 kHz decoder and adds at most one 24-second mono clip (4,608,000 bytes) in its separate bounded cache. Environment plus habitat therefore totals at most 17,280,000 decoded bytes; the environmental cache itself still remains below 14 MiB. Transport has its separate two-buffer limit described above.
Town offline downloads exclude audio media, so they do not prefetch every era or
both codecs. An explicit offline-audio option is not yet implemented; downloaded
towns therefore do not guarantee offline sound. The catalogue remains available.

The first habitat scheduler reads the existing fauna records and the actual
flora zone finder, solar hour/elevation and displayed date. It adds no habitat
geometry or second fauna fetch. Summer 1835-07-01 only: afternoon/day-dusk
cicadas in wet/mesic prairie and north timber; sparse dusk/night crickets in wet
prairie; occasional red-wing calls in sedge meadow or marsh. Other eras, viewing
seasons, alternate jaunt dates, missing habitat, and a provided freezing
temperature remain quiet. The town currently supplies no live temperature, so
weather-driven cold suppression is not active. No robin record exists here; katydids remain silent
under the actual July record.

One finite phrase plays at unchanged pitch. Each species has long cooldowns,
and a global 12–25-second gap prevents different calls filling one another's
silence. Insects attenuate with height above actual ground and stop by 32 m.
The scheduler reads surfaceHeight/groundHeight, never the 4 m walking barrier
returned by the compatibility height method over water. Bird anchors stay
1.5 m above the higher of actual ground or the Y=0 water plane. A
red-wing call originates at a fixed live-habitat point 44–84 m behind the listener,
with 3D distance attenuation; it fades out when approached within 36 m, beyond 96 m,
or brought toward view. No identifiable close bird call is emitted without an
animal body. The one pending decode stays reserved across resets until settled,
so mute/unmute cannot launch overlapping decodes or resurrect stale audio.
Master/Ambience, hidden state, disposal and speech ducking use the existing mixer.

Water type is separate from wet terrain: slough → quiet, lake → lake waves,
known river polygon → river lapping, unknown → quiet. The existing epoch vectors
and datum generate the classification catalogue. The renderer's derived lake
edge is an acoustic approximation at the mouth, recorded in LIBERTIES.md.
Water attenuation includes listener altitude above the water plane; flying above
the river does not retain the bank-level volume.

This pilot removes the old synthesized sound entirely. The Effects slider is
reserved for the next activity/transport batch; there are no replacement clicks
or hums. Music is independent of Ambience. The engine exposes setSpeechActive
for later narration ducking, without requiring any voice-service API at runtime.

Next reviewed batches: native seasonal birds and insects; slough reeds and
wetland wildlife; horse gait/hoof variants by surface; wheel/axle/harness sounds;
hand-tool activity; distant conversations; period-correct military effects;
reviewed narration and character lines. Each needs source/license and historical
placement metadata. Loading them is separate from scheduling them: visible work
and transport must drive their own events rather than an independent random loop.

Verification: unit tests cover era isolation, location classification, mute,
visibility, memory bounds and stale requests. Browser tests must decode the actual
files and exercise the loading-screen control on mobile and desktop. Technical
playback checks do not establish historical fidelity or listening quality; those
remain an audition/sign-off step before production promotion.

Activity contract (owner, 2026-11-10): identifiable sounds belong to actual scene
actors and actions. A camp conversation has two participating people, their
positions, speaking turns and reviewed language/lines. A hammer strike is emitted
by the worker's animation event. Moving hoof/wheel sounds follow the visible
assembly and its travelled distance. An offscreen or indoor source remains
attached to its real activity/location and is attenuated/occluded accordingly.
There are no free-floating conversation or hammer loops used to fake population.
Proxy recordings may supply the sound, but never invent a visible action that the
scene does not contain. This is the acceptance bar for the next activity batch.

Buildings also own sources: a tavern's indoor conversation or music follows its
era, use, occupancy and daily schedule. Doors/windows act as acoustic openings;
outside, level and high-frequency content fall with distance and obstruction.
The interior source may be hidden behind a wall without inventing visible outdoor
people. Horses need occasional snorts, breath and whinnies as well as hoofbeats;
vocalization belongs at the head, coordinated with the supported head/jaw/neck
animation, with cooldowns and variants. The architecture is entity-owned sound,
not a universal busy loop: every identifiable sound is attributable to a current
activity, animal, building or environmental process.

Wildlife contract (owner, 2026-11-10): occasional birds in spring, summer and
fall, with species-specific winter residents where supported. Use short calls
and meaningful silence, never a permanent chorus. Select candidates by Chicago
region, era, habitat, season and hour; recording location alone does not prove
historical suitability. Distant coyote calls are candidates for quieter prairie
or wetland edges at dusk/night, subject to historical review, not a default
sound in every era or built-up 1904 street. Frogs, insects and waterfowl need the
same habitat and seasonal checks. Near, identifiable calls attach to visible
animals; distant calls can originate from plausible offscreen habitat. No fauna
recordings or historical placements are approved by this design note alone.

Insects (owner, 2026-11-10): use seasonal, habitat-specific recorded layers for
grass, wooded edges and wetlands. Candidate crickets/katydids favor warm evenings;
candidate cicadas favor suitable summer daytime conditions. Species ranges,
seasonal phenology and daily activity must be checked before placement. Spring
begins sparsely, fall activity diminishes with cooling, and freezing conditions
suppress the layer. Season alone is only a fallback until actual temperature and
weather inputs exist. Periodical cicada choruses require a brood/emergence-year
check; never reuse them as a generic summer bed. Vary density gently and retain
quiet intervals; no synthetic hum or insects pasted into every habitat.

## Next implementation batches

1. **Habitat and wildlife:** author era-specific river, lakefront, slough, grass
   and tree zones; choose reviewed species; schedule short bird/fauna calls with
   randomized gaps and per-species cooldowns. Quiet hours, cold and habitat rules
   can suppress calls. A broad insect bed represents habitat, not a point animal.
2. **Visible activity:** add emitter IDs to people, horses, wagons and workplaces.
   Animation contact events trigger hoofbeats and strikes. Velocity controls
   wheel/rattle intensity; vocalization events coordinate animal animation.
   Route distance and obstruction control levels. Stop sources when their entity
   disappears, its activity ends or its layer is hidden.
3. **Occupied buildings:** link interior groups to building use and schedules.
   Door/window portals control audibility and low-pass filtering outside. Do not
   infer loud activity from a building label alone. Tavern music is a spatial
   indoor source, distinct from the visitor's non-spatial score.
4. **Speech and scoring:** separate narration and dialogue buses; recorded lines
   and captions keyed to approved scripts. Generate paid voices offline only
   after script/voice review; no visitor-side API calls or keys. Duck ambience and
   score during speech, then restore smoothly. Support interrupt/resume rules
   and avoid two intelligible conversations competing at full level.

Use one shared AudioContext. Start with a measured ceiling of eight concurrent
activity voices on mobile, reserving priority for nearby action and speech;
virtualize inaudible distant emitters instead of starting muted playback for
every object. Apply gain smoothing, per-emitter cooldowns, variant rotation and
bounded decode caches. Revisit that provisional ceiling with real scene profiling.
Spatial effects should normally be mono; music and broad ambience can be stereo.
Natural variation should primarily come from different real takes, not aggressive
pitch processing. Avoid turning every emitter up to compensate for a crowded mix.

## Library intake and quality

Keep a shared physical pool of reusable recordings with separate era eligibility
and scene placements; sharing a file does not authorize it in all three eras.
For each new item store source URL, creator, exact licence, acquisition date,
original hash, species/object/action, recording location, era eligibility,
habitat/season/hour restrictions, edit recipe, delivery hashes and audition status.
Record proxy use explicitly. Retain original licence evidence with acquisitions.

Prefer lossless real field recordings and isolated close recordings. CC0 is the
simplest reuse route; CC BY requires credits. Review each asset individually:
a site's being free does not make its whole library usable commercially, and NC,
ND or unclear terms are not automatic acceptance. Freesound is the initial source;
other field-recording and public-domain collections are candidates, not blanket
licence approvals. Purchase a small specialist pack only when free candidates
cannot meet quality or period requirements. Do not substitute synthesized effects.

Keep 44.1/48 kHz lossless masters when available. Typical audition targets are
64–96 kbps mono Opus for isolated effects and 128–160 kbps stereo Opus/AAC for
music or broad ambience; choose rates by listening, not file-size targets alone.
These are perceptual-quality goals, not a claim that lossy delivery is bit-exact
CD audio. The current environmental MP3 previews are explicitly interim sources.
Audition for modern traffic, speech, hum, wind overload, clipping, wrong surfaces,
wrong firearms, implausible fauna and audible loop seams. Check on headphones,
phone speakers and a stereo system; technical decoding is insufficient.

Deploy content-addressed/versioned media with long immutable cache headers, a
small versioned catalogue, correct MIME types, CORS and byte-range support.
Stream longer music and narration, decode only nearby short effects, prefetch at
most the next likely cue, and cancel obsolete work on scene changes. Avoid
hotlinking the free library's preview servers at runtime. Explicit optional audio
downloads should be sized per era and codec; they must not silently cache both
music formats or every era. Safari/iOS gesture and background/resume behavior
still require device verification before release.
