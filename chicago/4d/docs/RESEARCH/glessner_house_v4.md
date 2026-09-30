# Glessner House v4 — fabric, roof junctions and opening audit

T-1730, owner-directed fourth version, 2026-09-29. This is an alternate of the
canonical default, not a promotion of v2 or v3. The building position, footprint,
street setbacks, principal east and north roofs, and historically dated 1904 phase
remain the default's measured reconstruction. The new record is
`data/structures/versions/glessner_house/v4.json`.

## What the owner asked to correct

The owner requested substantially more realistic material and facade detail, a
cross-gabled roof reading, the small alley-side roof projection, missing stable
courtyard/south windows and garden-level lights, the copper roof continuing around
the inner northeast corner, variable-height stone courses, and east-wing chimneys.
The request also specifically calls for accurate windows, doors and cutouts. It is
recorded as `owner_glessner_v4_reconstruction_brief_2026`: an inventory/production
brief, never testimony that a guessed detail is measured or existed in 1904.

Fourteen visual references were read: `Pasted Graphic 14.png` through `19.png` and
`image(4).png` through `image(10).png`, and `image(20260929-211747).png`. Graphics 14–18 are modern aerial/oblique views;
Graphic 19 and images 4–8 are modern street photographs. The aerials expose missing
forms, and image 5 is a useful qualitative comparison for depth and shadow around
the front entrance and second-floor colonnettes. None supplies a dated 1904 state.
Modern views inform reconstructed feature arrangement, counts and material boundaries
where named below. No modern image pixels, textures, photogrammetric mesh, modern
street furniture, vehicles, or replacement garage doors are incorporated.

## Coordinate and date discipline

All data below uses the HABS building frame: **W** is feet west from the Prairie
Avenue face; **S** is feet south from the 18th Street face. Conversion to the mesh is
`x=(161.25-W)*0.3048`, `y=(74-S)*0.3048`; x east, y north, z up. `ng` is the model's
north-grade datum. `door` is the Prairie front sill, 0.74 ft above grade. Never
silently compare a door-datum height with a grade-datum one.

HABS IL-1015 sheets 2–3 are 1963 plans, sheet 4 the 1963 section, sheet 5 masonry
and entrance details, and sheet 6 the 1965 photogrammetric east elevation. Their
geometry is carried back only for unchanged fabric. HABS photo 5 is a circa-1923
court photograph, 19 years later than the scene. Photos 1 and 13–15 are 1963/1965.
The 1946 courtyard paving, replacement carriage/underpass doors and closed loft,
and the circa-1955 wooden stairs behind the stable are excluded. The modern image
is a comparison of surviving fabric; it is not an instruction to depict 2026.

## What changed and why

| Feature | Reading and implementation | Grade / limit |
|---|---|---|
| Western roof intersection | The north range's east–west roof continues to the measured alley plane **W 161.25**, through the stable's north–south roof. The default stopped it at W 139, suppressing the west-facing cross gable. Keep BOTH roof directions and the north-facing stable gable. Add the west triangular closure on S 0–26.83, ridge S 14.6 and z 34.1 ng, eaves 23.1/26.5. | Inferred from HABS photo 1's intersecting roof reading and measured range envelope; owner overview is qualitative cross-check. Not a new guessed building mass. |
| Small alley projection | One west-facing roof dormer centered S 47, width 8 ft, projected front W 161.5, back W 153, base 25/eave 29/apex 35 ft ng. | Reconstructed within the stable roof and upper alley opening at S 43–50.3 on sheet 3. Its outline is not traced from Google imagery. |
| Copper corner roof | The hall bow keeps its low curved copper sector. A contiguous shallow return covers W 38–55.5, S 20.5–28, lower edge z 26.5 ng, rise 3.5 ft. It meets the bow at its W 38 termination and continues toward the dining bay. | Copper on the bow is HABS data p.21. The precise return width, pitch and seams are reconstructed from the measured wing envelope and owner-noted missing continuation. |
| Dining roof | Retain the tall faceted metal cap with band top z 20.5 and apex W 70.6/S 20/z 34 ng. This meets the north range; render its intersection, not an isolated cone. | HABS photo 5 plainly shows a tall sheet-metal cap reaching near the main ridge. A flatter modern roof reading does not replace that closer historical witness. Copper identity of this bay roof remains reconstructed. |
| East-wing chimneys | Preserve sheet 6's N–S positions and heights, including printed north top **48.62 ft door**. Use distinct transverse widths rather than identical cubes: north 5.1, middle 4.0, south 7.5 ft; great chimney 4.4 ft. Add coursed faces, cap geometry, flue mouths and roof flashings. | Tops/S spans measured or attested; W widths and flue arrangements are reconstructed. Do not claim HABS prints those widths. |
| Curved walls | 64 segments for the stair and north towers, with the same measured radius/height. | Tessellation refinement, no changed historical dimension. |
| Courtyard windows | Add the explicit stable east/courtyard schedule from sheets 2–3 and the three stable south upper gaps from sheet 3. North-range upper windows follow their own plan instead of duplicating the lower row. | Horizontal plan bounds are measured; unprinted heights reconstructed. Exact schedule below. |
| Garden lights | Add the east-court low light and bowed basement pair visible on sheet 4, dining-bay garden lights visible in photo 5, plus bounded lower north/stable rows. | Existence strongest on east/bow/dining faces. Stable count and portions of north row remain reconstructed; neither plan is a basement plan. |
| Service doors | The north-court opening at W 100–104 is a door (sheet 2 swinging leaf), sill z 6 ng. The 18th Street opening immediately east of the stable at W 122.8–125.2 is a full-height street door, not a floating slit; HABS photo 15 confirms it. | Door identity inferred from plan/photo; courtyard height from section floor and street head 10.4 ng reconstructed within about 1 ft. |
| High north gable | Add the missing arched attic slit centered W 13.25, W 12.5–14, z 29–35.2 ng, spring 34.45, broad radiating-stone surround; read HABS photo 14. | Position/form inferred; photographic scale about ±1 ft, not printed dimensions. |
| Stable gable vents | Nine small round-headed openings in a **5–3–1** triangle, with a projecting ledge. HABS photo 15 and the owner image 7 show the same arrangement. | Count/form visible; positions and heights reconstructed from the gable proportions. |

## Masonry is a measured rhythm, not uniform bricks

The bottom-to-top course-height string on **HABS sheet 5** is transcribed, in
inches, as:

`18,18,15.5,9.5,13.5,14.5,7.5,14.5,7.5,11.5,7.5,11.5,7.5,9.5,7.5,20,8.5,11.5,17.5,7.5,9.5,9.5,9.5,4`.

It totals **271 in / 22 ft 7 in**, below the north eave/cornice at 23.1 ft. Do not
normalize every course to the complete wall height. This is a reading of one
measured strip at the 18th Street entrance. Carrying its rhythm around the granite
faces and choosing further upper/gable courses is reconstructed. Individual block
lengths are irregular and joints stagger; corner return courses must line up.
Joint width 0.025 ft and rock-face relief 0.025–0.15 ft are explicitly artistic
bounds, not survey dimensions. Preserve the stone's broad horizontal courses,
rock-pitched centres, flatter margin near joints, and dressed coping/lintel faces.

Courtyard walls are common brick with limestone lintels and sills, not a granite
copy. HABS photo 5 shows deeply recessed sash, substantial pale lintels, thin pale
sills, and some complete stone surrounds and continuous window-group bands. Use
brick-sized texture/relief and separately model the stone blocks. The lower rows
need their own sills and iron bars; they must not read as dark rectangles painted
onto a flat wall.

## Opening construction and honest limits

- **Actual depth:** v4 declares a reconstructed 0.55-ft recess, 0.15-ft sash frames
  and 0.12-ft meeting rails. These dimensions produce reveal shadow; HABS does not
  give a universal setback. Recess behind the wall, never place glazing proud of it.
- **Prairie main sash:** sheet 6 gives the complete arrangement. Main windows have
  one horizontal meeting rail; second-floor groups contain **1 / 3 / 4 / 3** lights.
  The grouped lights have slender stone colonnettes and individually carved capitals.
  A generic thick square mullion is not equivalent. The middle four-light group has
  its carved lower string course. Interpret the foliate detail in geometry without
  claiming a precise moulding survey.
- **Prairie basement:** exactly **four groups of 3 by 3 openings through stone**,
  with 0.35-ft stone bars in the default measurement. These are not 36 ordinary sash
  windows with little timber frames. Glazing/darkness lies behind the stone grille.
- **Prairie front door:** single heavy panelled oak door, upper square glazing with
  iron grille, lower raised panel, straps and fittings. Sheet 5 and the c.1888
  evidence control it. A 7-by-7 iron grille is an explicitly simplified rendering,
  not a transcription of every original bar.
- **Prairie porte-cochere:** two oak leaves, **each three panels across by six high**
  (36 panels total), recessed panels with rounded mouldings, strap iron and pulls.
  Do not substitute the later garage door visible in a modern reference.
- **Stable carriage entrance:** opening and flat stone lintel are measured. The
  pre-1946 leaves are not recorded; paired timber leaves remain reconstructed.
- **Stable loft:** the north loft opening was closed in 1946. In 1904 depict the
  opening/dark interior, not the sealed panel in the 1965 photograph.
- **North arch:** 12-ft clear span, spring 4.6 ng, crown about 10.8, outer
  voussoir radius 9.5 ft. The return masonry, recessed porch and steps need depth.
- **Garden and stable openings:** each carries its own dimensions below. Some
  stable garden and south lower openings remain reconstructions. Their uncertainty
  is material: a photoreal surface must not be described as a measured 1904 survey.

The version's descriptive `porte_cochere_doors`, `front_door` and `ironwork_finish`
attributes retain their historical meaning; rendering implementation must update
any inherited `geometry: simplified/record_only` note only when the corresponding
part has actually been built. Decorative relief is a visual reconstruction,
not a newly attested carving inventory.

## Full planar opening schedule

Each listed span is separate unless the subdivision column says a grouped number
of lights. Position runs in **S** on east/west faces and **W** on north/south faces.
Sill/head heights retain the table's explicit datum. Garden, porch and arch
openings are included; decorative bands are identified rather than counted as
windows. Curved-wall lights are listed after the planar schedule.

| Face / plane | Opening | Position spans (ft) | Sill–head (ft) / datum | Subdivision / head |
|---|---|---|---|---|
| east, W 0.0 | porte-cochere, closed by its two oak leaves | 62.38–70.16 | -1.9–7 door | doors; 1 opening per span |
| east, W 0.0 | pair of small first-floor windows | 67–69.3; 63.5–66.2 | 11.8–16.2 door | window; 1 opening per span |
| east, W 0.0 | first-floor windows | 54.4–58.3; 45.1–49; 16.9–20.8; 8.1–12 | 9.2–14.5 door | window; 1 opening per span |
| east, W 0.0 | front door | 30.4–35.4 | 0–7.75 door | door; 1 opening per span |
| east, W 0.0 | stone lintel over the door | 30.1–35.7 | 7.75–9.3 door | band; 1 opening per span |
| east, W 0.0 | carved tympanum in a fan of radiating voussoirs | 30.4–35.4 | 9.3–15.7 door | fan; 1 opening per span; spring 9.3; outer radius 6.4 |
| east, W 0.0 | basement lights, 3 x 3 | 54.4–58.3; 45.1–49; 16.9–20.8; 8.1–12 | 0.8–4.7 door | window; 3×3 stone grille |
| east, W 0.0 | second-floor single window | 64.6–68 | 19.8–24.3 door | window; 1 opening per span |
| east, W 0.0 | second-floor group of three, colonnettes between | 46.7–56.8 | 19.8–24.3 door | window; 3 lights |
| east, W 0.0 | second-floor group of four | 26.2–40 | 19.8–24.3 door | window; 4 lights |
| east, W 0.0 | carved string course under the group of four | 26.2–40 | 19.2–19.6 door | band; 1 opening per span |
| east, W 0.0 | second-floor group of three | 9.3–19.4 | 19.8–24.3 door | window; 3 lights |
| north, S 0.0 | narrow corridor windows, first floor | 4–5.6; 28.7–30.3; 50.2–51.5; 59.5–60.8; 71.7–73; 84.1–85.3 | 9.3–15.2 ng | window; 1 opening per span |
| north, S 0.0 | wider first-floor window, 4 ft | 116.1–120.1 | 9.3–15.2 ng | window; 1 opening per span |
| north, S 0.0 | the great arch, over a recessed porch | 96.5–108.5 | 0–10.8 ng | arch; 1 opening per span; spring 4.6; outer radius 9.5 |
| north, S 0.0 | wide window over the great arch | 97.7–110.1 | 20–23.7 ng | window; 3 lights |
| north, S 0.0 | paired second-floor windows, east wing gable | 7.2–10.1; 12–14.7 | 20.5–23.8 ng | window; 1 opening per span |
| north, S 0.0 | second-floor windows | 25.8–28.1; 30–32.9; 47.7–48.5; 59.5–60.8; 71.7–73.1; 83.8–85.1; 116.1–120.2; 122.8–125.2 | 20.5–23.8 ng | window; 1 opening per span |
| north, S 0.0 | service door immediately east of the stable carriage block | 122.8–125.2 | 0–10.4 ng | door; 1 opening per span |
| north, S 0.0 | first-floor window in the east wing's north face | 17.6–19 | 9.3–15.2 ng | window; 1 opening per span |
| north, S 0.0 | loft opening over the carriage doorway, open in 1904 | 137.5–144.7 | 17.4–24.4 ng | dark; 1 opening per span |
| north, S 0.0 | small windows flanking the loft opening | 132.4–133.6; 149.1–150.3 | 17.8–22.9 ng | window; 1 opening per span |
| north, S 0.0 | the stable's carriage doorway, closed by two leaves | 134.9–147 | 0–12.6 ng | doors; 1 opening per span |
| west, W 161.25 | ground-floor lights | 6.2–11; 19.9–24.5; 34.4–36.9; 41.3–43.9; 48.2–49.8; 53.8–55.7 | 7–10.5 ng | window; 1 opening per span |
| west, W 161.25 | loft windows | 7.5–8.9; 15.9–16.7 | 17.8–22.9 ng | window; 1 opening per span |
| west, W 161.25 | wide upper opening, a second candidate for a loft door | 43–50.3 | 17.8–22.9 ng | dark; 1 opening per span |
| west, W 26.5 | underpass exit into the courtyard | 63.3–72.9 | 0–8.1 ng | dark; 1 opening per span |
| west, W 26.5 | first-floor window | 43–47.5 | 9.5–14.6 ng | window; 1 opening per span |
| west, W 26.5 | tall narrow second-floor light | 44.9–46.7 | 19.5–25.6 ng | window; 1 opening per span |
| west, W 26.5 | windows over the underpass | 62–64.5; 67.5–70 | 12.3–16.9 ng | window; 1 opening per span |
| west, W 26.5 | windows under the eave over the underpass | 62–64.5; 67.5–70 | 21–24.8 ng | window; 1 opening per span |
| south, S 26.83 | north range courtyard windows, first floor | 40–44.5; 46–50; 52–56; 82–86; 92–96; 112–118 | 9.3–14.5 ng | window; 1 opening per span |
| south, S 26.83 | north range courtyard windows, second floor | 40–42; 44–48; 50–54; 82–86; 92–96; 101–105; 108–109.5; 114–119 | 19.5–24 ng | window; 1 opening per span |
| south, S 26.83 | service entrance into the courtyard, with stone threshold | 100–104 | 6–14.5 ng | door; 1 opening per span |
| south, S 26.83 | garden-level north-court lights below the principal rooms | 40–44.5; 46–50; 52–56; 82–86; 92–96; 112–118 | 0.8–5.4 ng | window; 1 opening per span |
| east, W 125.75 | stable courtyard narrow first-floor windows, HABS sheet 2 plan gaps | 30.5–32; 41.7–43.2; 51.8–53.4 | 7.5–13.5 ng | window |
| east, W 125.75 | stable courtyard upper windows, HABS sheet 3 plan gaps | 29.3–34.3; 41–45.3; 51–55 | 18–22.5 ng | window |
| east, W 125.75 | stable courtyard garden lights, reconstructed beneath the stable window bays | 29.5–33; 41–44.5; 50.8–54.3 | 0.8–4.2 ng | window |
| east, W 125.75 | stable courtyard door beside the north-range junction | 26.9–29.4 | 5.8–14 ng | door |
| south, S 59.75 | stable south upper windows, HABS sheet 3 plan gaps; excludes the c.1955 stair door | 138.8–141.4; 143.5–146; 148–150.4 | 20–23 ng | window |
| south, S 59.75 | stable south lower windows, reconstructed from the stable window rhythm | 130.5–134; 152–155.5 | 7–11 ng | window |
| west, W 26.5 | east-wing courtyard garden light beside the stair tower, HABS sheet 4 | 43–48.5 | 1–4.5 ng | window |
| north, S 0 | east-wing north-gable arched attic slit, HABS photo 14 | 12.5–14 | 29–35.2 ng | arch; spring 34.45; outer radius 4.7 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 136.75–137.25 | 31–31.85 ng | arch; spring 31.6; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 138.75–139.25 | 31–31.85 ng | arch; spring 31.6; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 140.75–141.25 | 31–31.85 ng | arch; spring 31.6; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 142.75–143.25 | 31–31.85 ng | arch; spring 31.6; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 144.75–145.25 | 31–31.85 ng | arch; spring 31.6; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 138.75–139.25 | 33–34.2 ng | arch; spring 33.95; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 140.75–141.25 | 33–34.2 ng | arch; spring 33.95; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 142.75–143.25 | 33–34.2 ng | arch; spring 33.95; outer radius 0.25 |
| north, S 0 | stable north-gable pigeon opening, 5-3-1 arrangement visible in HABS photo 15 | 140.75–141.25 | 35.2–36.4 ng | arch; spring 36.15; outer radius 0.25 |

### Curved and faceted faces

- Hall bow: canonical three lights per principal row, z 9.3–14.5 and 19.5–24 ng.
  The new basement row is **two** broad lights z 1–5.5, matching sheet 4's pair,
  not a copied three-light row. Sheet 4/photo 5 also show a central main-level door
  and a curved low terrace/areaway parapet; these should be distinguished from sash
  wherever the detailed mesh supports that distinction.
- Dining bay: five canted principal glazed faces z 9.3–14.5 ng, upper continuous
  glazed band 17.4–23; photo 5 shows multi-pane joinery in that band. Garden openings
  below the exposed canted faces z 1–6 are newly included, with limestone heads and
  sills and iron bars. Heights remain an inference from the adjoining floor levels.
- Stair tower: alternating narrow slit lights are at different heights, following
  the stair rise, not repeated level rings of identical windows. HABS sheet 4 is the
  controlling evidence for these and for the upper three-window lantern band.
- North round tower: opening form comes from HABS photos 1 and 13/14; the visible
  curvature and rock-faced masonry must continue between apertures.

## Source register and uncertainties to preserve

Read directly in this pass: HABS sheets 1–6, photographs 1, 3, 4, 5, 13, 14 and 15,
Richardson sketch GLE B9 (design intent only), the existing measured spec and all
three existing structure records. The source IDs are unchanged HABS records plus
`owner_glessner_v4_reconstruction_brief_2026`. HABS government drawings permit
geometry use. Photo 5 has `rights_status: check_required`; its facts are cited and
forms compared, but no image-derived asset is created from it. Modern references
remain private evidence of surviving fabric; their feature arrangements inform
reconstruction where named, but the images are not re-published or used as textures.

The v4 artistic bounds needing a liberty entry are: surface roughness/joint depth,
individual block lengths and course continuation beyond the measured strip,
window recess and joinery profiles, exact stone/carving/wood colours, copper patina
and seam layout, the small western dormer dimensions, corner copper return,
chimney W depths/caps/flues, unmeasured basement and south lower openings, high
gable opening/vent scale, iron-grid simplification and weathering. These bounds
must remain reconstructed even if the resulting image is convincing.

No photographic-quality claim is made by this dossier. The rendered image must be
inspected against these references, at whole-building and facade-detail distances.

## Later courtyard views, received during the same pass

Owner images 9 and 10 show the same east-court arrangement already visible in
HABS sheet 4/photo 5: the main hall bow has three upper lights and a central door
between two lower sash. Its basement pair is in a **projecting low terrace wall**,
with a rounded stone coping and stairs down to the south. The stair drum has four
slits on alternating northwest/southwest angles, not two uniform rings. Those
slits have brick jambs and individual stone lintels/sills; the upper lantern has
a continuous pale sill belt and a continuous stone head beneath the conical roof.
The underpass beside it must be an actual open tunnel with substantial stone
lintel and masonry side returns; a black plane cannot stand in for it.

The westward courtyard view `image(20260929-211747).png` resolves the stable
upper windows as three nearly square sash beneath the eave, above three much
narrower lower windows. The earlier oblique aerial compressed their apparent
height. V4 therefore uses z18–22.5 ng for the sheet-3 upper spans and z7.5–13.5
for the sheet-2 lower spans. The source of those heights is still reconstructed
proportion, not a newly found dimension. The same view shows lower stable garden
lights near grade, partly obscured by planting and stairs. The exact three-light
basement repetition is still reconstructed.

Added data: `tower_stair_windows`, `bow_terrace`,
`bow_first_floor_central_door`, and `underpass` inside `v4_detail.value`.
All window angles use degrees from mesh +x (east) toward +y (north). Slit pairs
at 145 degrees have z7.6–12.5 and17.8–22; those at215 degrees z4.5–9.2 and
15.7–19.8. Three lantern lights at135/180/225 degrees have z27–31; the stone
belt is25.8–27 and the upper band31–32.5. Heights are section readings, about
±1ft; angle/width choices are reconstructed on the measured drum.

The paired historical oak porte-cochere leaves are posed **82 degrees open inward**
in v4, so the tunnel can be read through from the court. This is a reconstructed
momentary operating position, not a claim that a period photograph shows the
doors held open. The c.1888 image controls their construction and shows them shut.
Modern views influence reconstructed feature arrangement and material boundaries
where named above; their use is not concealed under a claim that HABS measured
every detail. No photographic pixels or photogrammetric surface is copied.

The garden openings were checked again against supplied image(9): the bowed
terrace grille is reconstructed at z 1–3.8 ft ng below a 6.1-ft platform, and the
dining-bay garden lights at z 1–5 ft ng. Both are photographic proportion estimates,
not printed HABS dimensions; the lower lights receive iron grilles.

The bowed terrace includes a parapet 2.2 ft (0.67 m) above its walking platform,
within a reconstructed 0.55–0.8 m bound from image(10), where the coping obscures
the bottom of the door. Its coping curves downward beside the stairs. Nine risers
are reconstructed from the approximately 1.68-m total climb, not counted from
the partially visible photograph; the door threshold meets the platform.

The dining-bay glazed band is re-read from full-resolution HABS photograph 5:
about 78 px high against 129 px for the 5.2-ft main sash, giving about 3.1 ft.
Its top is inferred at 20.5 ft ng above the retained 17.4-ft masonry, with about
1-ft uncertainty. It receives two pane rows and three columns per front facet.
The 34-ft roof apex is retained. This replaces the default’s inferred 23-ft band
top; neither band height is a printed HABS dimension.

The dining-bay garden grilles alternate beneath the principal sash, as seen in
HABS photo 5 and supplied image(9): three openings on principal facets 0, 2 and 4,
with solid brick below facets 1 and 3. They are not repeated under every light.


The north-court service door receives the landing and stair drawn on HABS sheet 2.
Scaled against the four-foot doorway, the landing spans W98.7–112.9 / S26.83–32.2
ft, and a flight descends south at its west end through W108.2–112.1 /
S32.2–41.1 ft (approximately ±0.5 ft). The landing meets the 6-ft-ng threshold.
Ten risers and a 3-ft-high rail are reconstructed. The owner's tunnel-facing
courtyard photograph bounds the stone slab/treads, two slender brick landing
supports, brick stair cheek and iron rail; it does not certify those exact
materials and thicknesses for 1904. This is distinct from the later wooden stair
outside the stable south wall, which remains excluded.


Final surface review keeps the measured planes and course heights but varies
reconstructed rock-face relief within the declared 0.025–0.15-ft block depth
range, with bounded local fracture peaks. Individual mineral color and firing
variation are artistic material studies, not samples from reference pixels.
Window interiors use varied top-down pale linen shades and occasional simple
side curtains behind physical glass, with dark interior backing further inside.
These are reconstructed period-compatible treatments, not a claim that the
exact photographed shade positions or room furnishings existed on the scene date.


The Prairie entrance ornament is revised after close comparison with supplied
image(5) and the HABS entry views: four principal foliate scrolls around a central
stem, nested archivolts, carved leaf and dentil bands, three distinct capitals,
and egg-and-dart / bead-and-reel sill carving. The leaf lobes, drilled pockets,
small stems and tool-scale surfaces are reconstructed geometry, not a scan.
The semicircular carving is seated in a masonry recess with a continuous stone
backing; ashlar does not continue through its surface. Reconstructed sill ends
extend 0.435 m beyond the central band's bounds, with the recess following their
full envelope. These microdimensions remain artistic, not HABS measurements.

Granite color now uses a separately preserved original generated material image
at a reconstructed 0.22-m repeat, with restrained normal-map strength and the
existing physical block relief. Its exact prompt, method, original-image hash
and provenance are in `assets/textures/glessner-v4/granite_photographic_provenance.json`.
It contains no sampled historical or owner-reference pixels and is not a
photograph of the building. The numeric granite albedo remains preserved but
is not the rendered color map. Prairie upper shades are partly raised, with
reconstructed varied heights exposing the lower panes as in the reference.


### Courtyard close-up material refinement

The active granite albedo repeat is 0.22 m, revised from the earlier 0.6-m
trial after its crystals read too large. Normal strength is 1.0 on ashlar and
0.8 on courtyard rock-faced trim, with reduced numeric fracture warp. Common
brick uses a gray-tan clay body and occasional warmer/buff/smoky firing; this
represents the surviving material, not a claim to reproduce modern weathering.
Oak midtones and restrained varnish roughness make existing joinery readable.

A separate original generated turf albedo repeats at 0.4 m. It supplements the
existing lawn polygon, together with 20,000 seeded one-triangle blades, 10–40 mm
high and 1–3 mm wide. Every vertex lies inside the lawn and outside the drive
with a boundary margin. Blade positions, density, colours and heights are
reconstructed and carry conjectural `_CONFIDENCE=1.0`; no plant inventory or
new garden extent is claimed. Three added plain green material slots bring
the model library to 28 slots. Both original generated images are preserved
unchanged with prompts and provenance; the numeric recipes never overwrite them.


The exposed stair-tower foundation carries six rough stones around only its
courtyard arc, stepping from about 0.30 to 0.12 m toward the passage. Owner
image10 and the west-facing tunnel photograph establish this material transition;
HABS photo5 is obscured by ivy and shadow, so the precise height, block joints
and relief are reconstructed rather than measured. The tower's datum and
openings stay fixed.


### Court glazing and bow terrace door

HABS photo5 shows most roller hems around35–55% down the complete opening.
The earlier mostly closed profile hid the lower glass. The revised seeded
profile is18–64%, mostly32–55%, with a subset of narrow gathered side drapes.
These cloth positions are conjectural; existing Prairie colonnade shades keep
their6–34% profile. Physical glass and darker backing remain separate surfaces.

The c1923 photograph shows four upper door panes and a raised rectangular lower
wood panel at the terrace. The geometry now removes the full-height oak backing
from that upper aperture, builds real rails/stiles and2×2 muntins, and adds a
rounded lower-panel moulding and small latch. The construction is inferred
back to1904; microscopic moulding/hardware are reconstructed. The fine iron
protective grid in the modern photo is not substituted for the older door.


The controlled material study compares only test panels, not building renders.
It selected5×3 angular subdivisions for large rock-faced blocks and normal
strength1.0 (rough trim0.8): the earlier3×2/0.4 treatment read too smooth,
while6×3 produced distracting isolated pits. Split-face offsets are explicitly
bounded4–70mm, with nominal extrusion still8–46mm. Surface clipping preserves
these complete physical stones around openings, without artificial internal
joints. The labeled studies are retained in `images/glessner-v4/material-study/`.

### Stair-tower lantern bands

The former smooth, bright belts contradicted the rough stone reading in HABS
courtyard photo 5 and the owner's modern close views. Both bands now have
angular stone faces and narrow dressed upper seats using the same granite
fabric. A deterministic 16-block course is reconstructed around each ring.
The measured band heights and former outer radius remain unchanged; geometry
checks find no degenerate faces and retain the original circular edge points.


**Roof ridge crests (2026-09-29):** The v4 roof retains the ridge axes, pitches and endpoints already resolved from the structure record. HABS courtyard photograph05 (circa1923, `habs_glessner_photo_05_court_c1923`) clearly shows repeating raised ridge crests on both the foreground roofs and the long courtyard roof; photograph14 (`habs_glessner_photo_14_north_inclined_1965`) and the supplied modern roof views agree. Carrying this roof detail to1904 is inferred from the same surviving roof-form continuity used elsewhere in v4; the circa1923 image does not directly attest a1904 state. One raised terracotta collar is added inside each existing0.36m cap interval. Its55mm crown rise above the existing cap and35mm axial thickness are reconstructed visual proportions, not survey dimensions. The collar tapers to the existing cap width at its shoulders. The new collar vertices are tagged reconstructed (`_CONFIDENCE = 1.0`). It reuses the existing clay material and does not change roof pitch, ridge datum or endpoints. No historical or modern image pixels are reused.


**Courtyard dormer refinement (2026-09-29):** HABS courtyard photograph5
shows projecting flared cap edges and simple undivided timber lights. The
owner's recent courtyard image10 confirms clay cap/finial material and helps
bound the edge profile; the monochrome HABS image alone does not establish
red colour. The existing body, opening bounds, 32.9-ft eave and37-ft apex are
retained. A0.30m front/0.26m side projection,0.18m kick run/0.13m rise,
75mm timber fascia/soffit and47mm-radius hip covers are reconstructed, not
measured drawing labels. New stock, glazing recesses and edge details carry
reconstructed confidence1.0. The generic stone sill/reveals and extra sash
rail are replaced locally by timber and a single light. No other windows or
main roof mass are changed.


**Courtyard rainwater fittings (2026-09-29):** The courtyard rainwater fittings are inferred for 1904 from HABS courtyard photograph05 (circa1923, `habs_glessner_photo_05_court_c1923`). That view shows the north and east courtyard eave gutters, a curved gutter around the northeast bow, the dining-bay cap gutter, a conspicuous pipe at the photograph-left/west dining-bay junction, and a second slender pipe immediately west of the bow. The later photograph supports surviving form, not a directly photographed1904 condition. The new helper follows the existing generated roof edges, interrupts hidden runs at the projecting bay/bow and stair drum, and places pipes only at those two clearly visible junctions. Its120mm half-round section,3mm sheet thickness,6mm rolled lips,88mm pipes, small flared collectors and plain retaining collars are reconstructed within the photographed silhouette. The gutter outer lip projects98mm past the existing eave; its top is16mm below that eave. Dark oxidised-metal appearance reuses existing metallic slot10 and does not identify a particular alloy or repaint all copper roofs. All added vertices carry reconstructed confidence1.0. Roof pitches, ridge axes, openings and masonry remain unchanged. No source pixels or modern proprietary fittings are reproduced.


**Fine rock-face geometry (2026-09-29):** Stone faces now use a7.5cm
fracture grid with two correlated relief scales and small irregular edge chips,
superseding the5×3 trial. The6–70mm field is reconstructed within unchanged
course/block/opening envelopes. Finished facets are clipped at apertures; no
extra seams are introduced. The outer radial entry stones use the same rough
finish visible in the owner's close-up image5; carved inner mouldings remain
dressed. Shading normals blend across shallow fractures below35degrees inside
each stone, preserving hard sides, reveals and steep chips. This changes no
vertex positions, UVs or confidence. Export/reimport tests confirm the corner
normals survive the canonical GLB path. All fracture detail remains invented
within these bounds, not a surveyed map of individual stone faces.


### Glazing volume and stable turret detail

The v4 clear panes keep the existing front planes and opening outlines, but now form closed dielectric volumes. Their 4 mm stock thickness is reconstructed, not a HABS measurement: the front retains its source confidence and the added rear/edge faces carry reconstructed confidence (1.0). No glass colour, transmission, roughness or IOR was changed. A controlled export/import comparison at identical 48/128 samples reproduced the dark stipple with the previous open slab and single-quad panes; the closed pane reduced its 48-sample local pixel residual by about 86% in this fixture. That is diagnostic evidence about this rendering defect, not a photorealism score for the building.

The Prairie entrance leaf now has a real cutout within its already-defined upper glazing outline; its lower panel, stiles, rails, grille and outer dimensions remain unchanged. Previously a full-height wooden backing lay 1 mm behind the glass.

The existing turret_stable record, citing the 1888 exterior photograph and HABS photograph 1, describes the stable ridge turret band as louvred. V4 therefore replaces four false transmitting panes with actual timber slats and dark recessed backing, retaining the recorded turret/body/roof/finial envelope and band outlines. Approximately 145 mm slat spacing, 140 mm depth, 16 mm stock and the downward outward slope are bounded reconstructed joinery (1.0), not a photographed slat count or measured detail.


The courtyard material refinement retains the same geometry and 28 material slots.
All common-brick variants now share one clay fabric, with restrained kiln colour
variation and coherent roughness. The lime mortar receives a dedicated sandy
surface. The lawn uses a new original generated 4 m albedo with broad natural
variation; the earlier 0.4 m input is retained unchanged. These appearances are
reconstructed material studies, not extracted source-photo pixels or measured
historical reflectance. Exact prompts, hashes and channel conventions remain in
assets/textures/glessner-v4/. The first controlled material trial over-compressed
the brick palette; the accepted source restores a modest midpoint variation,
which still awaits review in the combined canonical bake.
