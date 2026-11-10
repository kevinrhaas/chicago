# Recorded audio pilot — T-3532

For the owner's hosting questions, see [AUDIO-HOSTING.md](AUDIO-HOSTING.md):
streaming behavior, the project versus provider limits, separate dev/main sites,
shared audio storage, current published provider pricing and the upload bundle.

## Scope and delivery status

This is a local, reviewable foundation, not a completed town soundscape or a
production release. It implements the owner's music, recorded wind/river/lake,
opt-in controls and the catalogue. Actor events, wildlife, weather, speech,
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

## Implemented foundation

The expanded catalogue now contains 33 source assets: seven era-specific music
cues, the three pilot environmental loops and 23 additional recorded candidates.
Those candidates include wildlife/insects, horse vocalizations/hooves/harness,
woodworking, a musket, wagon, steam whistle, fire, dock/door/bell and performed
tavern chatter. Candidate previews add 5,605,876 bytes; all 40 delivery alternatives
together are 41,173,377 bytes (39.266 MiB). The preview browser labels candidates
and does not automatically enable them in the scene. The Italian cicada proxy
is explicitly owner-authorized; that is separate from wiring its scene emitter.

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
1904 Waltzes (2). Browser selection uses Ogg/Opus first and AAC when unsupported.
Only the active cue streams; cues have 15 seconds of quiet between them. There is
no full-playlist preload. Music gain includes 6 dB headroom before its slider;
original decoded true peaks were -0.43 to +0.49 dBTP. Master defaults off; the
loading-screen speaker button enables it, with detailed levels in Settings.

Wind, river and lake use 22-second mono loops with a 2-second edited seam. A
48 kHz offline decoder keeps all three at 12,672,000 bytes even when the output
device runs at 96 or 192 kHz; the cache also enforces a 14 MiB ceiling. Real R2
playback at both output rates passes the memory and mute checks. Typically two play. Music is not
fully decoded into an AudioBuffer. The environmental cache is cleared on mute,
hiding, context replacement, disposal and scene changes. Aborted/stale requests
cannot restart playback. No network access to Freesound occurs at runtime.
Town offline downloads exclude audio media, so they do not prefetch every era or
both codecs. An explicit offline-audio option is not yet implemented; downloaded
towns therefore do not guarantee offline sound. The catalogue remains available.

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
