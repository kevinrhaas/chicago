# T-2172 — courtyard tower proportions

Owner follow-up to T-2157, 8 October 2026. The supplied courtyard photo shows
the upper tower glazing related to the north-wing upper windows, with a shallower
copper cap than the current application. The model had placed the 3.1-ft glazed
band at 17.4–20.5 ft ng, below the wing upper windows at 19.5–24 ft ng.

Raise the band intact by 3.5 ft to 20.9–24 ft; extend the masonry to its sill.
Keep the copper apex at the established 34.1-ft north-wing ridge, its forward
plan position, flared apron, tiled connector and ridge crests. The cap rise
changes from 13.6 to 10.1 ft (25.7% shorter). This is an owner-directed proportional
reconstruction, approximately +/-1 ft, not a measured historical elevation.
The photograph has perspective and is not used as a survey or photographic texture.

HABS IL-1015 photograph 5 (courtyard view, circa 1923) shows a continuous band
with two pane rows and several vertical lights per facet. Retain those period
divisions rather than adopting the modern photograph's replacement broad panes.
The first-floor and basement openings, plan footprint and main roof remain fixed.

## Recovery and validation

Branch: steward/glessner-tower-proportions. Canonical parameters live in
data/structures/glessner_house.json. Source change complete; bake, full/light
derivatives, published desktop/mobile review and repository gate pending.
Build with the existing pinned Blender using generators/build.py --only
glessner_house, then tools/web_derivatives.sh --only glessner_house__as_built_1887.glb.
The derivative producer repacks the canonical recovery archive. Run
python3 tools/compile_scene.py --all and tools/publish.sh, then the roof envelope
check and tools/preflight.sh. Review using the fixed dining-roof cameras.
