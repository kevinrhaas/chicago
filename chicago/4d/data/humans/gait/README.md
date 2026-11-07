# Normative gait reference (`normative_gait.json`)

Reference numbers for the procedural gait layer (`renderers/web/js/human-gait.js`). They
replace the baked flat-foot clip (0.6 m/s, 0.36 m steps, straight knees, no heel strike).
Comfortable adult walking, measured in open datasets.

## What is in the JSON

- `cycle_tables.*`: 21 values each, at 0, 5, ... 100 % of the gait cycle. 0 % is heel
  strike of the reference foot. Every table has `values`, `sd`, `unit`, `source_id`,
  `basis` and `speed_m_s`, plus a `note` that gives the sign convention and the method.
  - hip / knee / ankle flexion, foot-floor angle, pelvis tilt / obliquity / rotation: WBDS
    young adults (n = 24, 1.24 m/s), Visual3D processed angles, left and right averaged.
  - thorax rotation (here the acromion line, against the lab), shoulder flexion of the
    same-side arm (against the sacrum-to-C7 trunk line), elbow flexion: Horst young adults
    (n = 57, about 1.45 m/s), computed from raw full-body markers.
  - COM vertical / lateral: a proxy, the centre of the four pelvis markers.
  - heel / toe height: the calcaneus and first-metatarsal markers, measured from their own
    foot-flat height. The toe value is the forefoot marker, not the toe tip.
- `alt.*`: the older-adult curves (WBDS, 50 to 84 y), thorax minus pelvis, trunk lean, arm
  against vertical, and arm swing split by sex.
- `events`: toe-off 61.7 %, opposite toe-off 11.7 %, opposite heel strike 50 %, foot flat
  about 15 %, heel-off 40 % (Perry gives 31 %), double support 0.23, knee swing peak 62 deg
  at 73.5 %, Perry phase boundaries, and the swing minimum of the forefoot marker
  (1.6 cm at 87 %).
- `spatiotemporal`: WBDS results by group (speed, cadence, stride, step, step width, toe-out
  angle), Oberg 1993 by decade (20s, 40s, 60s), Bohannon & Andrews 2011 speed by decade,
  and speed relations:
  - stride / height = 0.385 + 0.327 v
  - stride / leg = 2.31 (v / sqrt(g leg))^0.47, which is close to Alexander's
    λ/h = 2.3 (v²/gh)^0.3
  - cadence = 51.4 + 80.7 v / height

  Example: 1.70 m tall at 1.25 m/s gives a 1.35 m stride, about 111 steps/min.
- `modifiers`: long skirts and corsets, older adults, men in 1900s dress. Each one is split
  into `measured`, `period_advice` and `inference`. **Only `measured` is evidence.** The
  `inference` scales are reconstruction choices, and any use of them belongs in
  `docs/LIBERTIES.md`.

## Sources actually used for numbers

- **WBDS**: Fukuchi, Fukuchi & Duarte 2018, PeerJ 6:e4640; figshare 10.6084/m9.figshare.5722711.
- **Horst et al. 2019**: Mendeley Data 10.17632/svx74xcrjr.3 (`Gait_rawdata_tsv.zip`).
- **Oberg, Karsznia & Oberg 1993**, JRRD 30(2):210-223, tables (via scispace PDF).
- **Bohannon & Andrews 2011**, Physiotherapy 97:182-189 (via the U of Toronto PT handout).
- **Perry & Burnfield 2010** (phases, via the AAPM&R page); **Winter 1992** (toe clearance
  1.29 cm, via a citing paper); **Alexander 1976** (via Ruiz & Torices 2013).
- Events in the raw marker data come from Zeni et al. 2008. Toe-off comes from the force
  plates, because Zeni's toe-off reads about 4 % late (65.6 %).

## Caveats

- `source_id`s here are local to this file. They are **not** `data/sources/` records yet.
  Register them before anything cites them from scene data.
- Signs of pelvis obliquity and rotation are deduced from the phase (the peak falls during
  reference loading response / reference limb forward). The dataset does not state them.
  Pelvis tilt has a marker offset of about 10 deg; use only its oscillation (about 2.4 deg).
- "Thorax" rotation is the shoulder girdle (acromion markers), not a thorax segment. It runs
  in antiphase to the pelvis (about 6 deg peak-to-peak against the lab, 18 deg against the
  pelvis).
- Horst subjects were young sport students who walked fast (1.45 m/s). At 1.25 m/s, expect
  a little less arm swing than their mean shoulder ROM of 27 deg (women 31, men 22).
- Elbow absolute angles (20 to 52 deg) use the acromion as the shoulder point, so treat
  them as approximate. The swing of about 30 deg in phase with the shoulder is the reliable
  part.
- The WBDS older group was screened and active, and walked as fast as the young group.
  Population norms (Oberg, Bohannon) show a 6 to 11 % lower speed in the 60s, more so for
  women.
- WBDS cadence (105 to 116 steps/min) is lower than Oberg's (117 to 130) at similar speed,
  because its steps are longer. That is a real difference between the samples. Use the
  speed relation instead of a single cadence.
- The WBDS lab speed column is about 5 % above stride length / stride time. For
  self-consistent animation, use the stride-based speed.

## Could not source

- No motion-capture study of gait in a period steel-boned corset with a floor-length
  skirt. The nearest measured evidence is a modern lumbar corset and a rigid trunk
  orthosis: pelvic transverse ROM about 29 % lower, cadence 5 % higher, speed unchanged.
- No study of men walking in 1900s street dress.
- No numeric arm-swing values for older adults. Mirelman 2015 reports a decline, but its
  values are in a table image.
- No values from Murray 1964/1967/1970, Kadaba 1990, Dean 1965, Grieve & Gear 1966, Meyns
  2013 or Bruijn 2008. Some are cited for orientation and none is used for a number.
  Volume and page numbers marked "not verified" in `sources` were not checked.

## Period advice (real books on archive.org, an ideal of behaviour, not a measurement)

- Hill's *Manual of Social and Business Forms* (Chicago, 1887 ed.),
  https://archive.org/details/hillsmanualofsoc00hill. It says: "Ladies should avoid walking
  rapidly upon the street"; "Swinging the arms when walking" is among "evidences of
  ill-breeding in ladies"; trailing a dress on the street is "in exceedingly bad taste".
- F. H. Hall, *The Correct Thing in Good Society* (1902),
  https://archive.org/details/correctthingingo00hall. On tight corsets and high heels:
  "as gracefully as a swan on a turnpike-road".
- B. Macfadden, *The Power and Beauty of Superb Womanhood* (1901), pp. 106-110,
  https://archive.org/details/powerbeautyofsup00macf. It quotes Dr Anna M. Galbraith:
  skirts cause an "artificial shortening of the step".

## Period films for judging the result (c. 1896-1906)

Judge step length, arm swing, posture and skirt behaviour. Do not judge tempo: these were
hand-cranked cameras, and web copies are often replayed at the wrong frame rate.

- *Corner Madison and State Streets, Chicago*. Edison, 1897, camera William Heise. The LoC
  record says "Hundreds of shoppers".
  https://www.loc.gov/item/00694183/ (copy on Commons:
  https://commons.wikimedia.org/wiki/File:Chicago_-_State_St_at_Madison_Ave,_1897.ogv)
- *Armour's Electric Trolley*. Edison, 1897, Chicago stockyards. https://www.loc.gov/item/00694146/
- *What happened on Twenty-third Street, New York City*. Edison, 1901. Staged, but the
  passers-by are walking in long skirts. https://www.loc.gov/item/00694379
- *Lower Broadway*. AM&B, 1902. https://www.loc.gov/item/00694372
- *Flatiron Building and street scene, 8 Oct 1902*. LoC paper print, handle
  http://hdl.loc.gov/loc.mbrsmi/lcmp002.m2b03516 (the title is from its Commons copy).
- *Move on*. Edison, 1903, Lower East Side. https://www.loc.gov/item/00694375
- *Bargain day, 14th Street, New York*. AM&B, 1905. https://lcweb2.loc.gov/item/00694373/
- *A trip down Market Street before the fire*. Miles Brothers, San Francisco, 1906. Many
  pedestrians crossing in front of the cable car. https://www.loc.gov/item/00694408
- Lumière, *La Sortie de l'usine Lumière à Lyon* (1895), workers walking out. Wikimedia
  Commons file "La Sortie de l'Usine Lumière à Lyon I 1895.webm".
