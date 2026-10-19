# Glessner's Prairie lights moved to HABS sheet 6 (T-2858)

T-2857 read the Prairie front against HABS sheet 6 and three street photographs
(`docs/RESEARCH/glessner-prairie-front-T-2857/`). It found the north-end openings 0.30-0.63 ft
south of the sheet's positions and the first-floor lights 3.9 ft wide where the sheet draws
4.3-4.45 ft. It left three things to rule. This piece rules them and builds the answer.
`tools/glessner_prairie_front.py` re-derives every number below from T-2857's picks. Nothing is
re-picked. Its report is `data/comparisons/glessner/prairie-front.json`, and `check.sh` holds it.

## 1. The widths: the sheet is right, and the oblique photographs see the sash

The two NE photographs fitted the old 3.9 ft better than the sheet's outer lines. Both are
oblique, 25-42 degrees off the front's normal. From there each light's south reveal faces the
camera, so the edge of the dark glass on that side is the sash, set back behind the arris. The
model sets it 0.49-0.98 ft back. Seen from the north-east it lands displaced toward the camera,
which makes the light look narrower. T-2857's one-dimensional fit had treated every jamb as an
arris.

Each such jamb is now projected from the camera's eye at the sash depth, with no free
parameter. Jamb rms, old schedule → sheet 6, by reveal depth:

| photograph | 0 ft | 0.49 ft | 0.6 ft | 0.95 ft |
|---|---|---|---|---|
| taylor-2135-ne | 1.50 → 2.87 | 1.93 → 1.23 | 2.24 → 0.98 | 3.40 → 1.22 |
| habs-17-habs-ne | 1.62 → 1.88 | 2.16 → 1.46 | 2.35 → 1.49 | 3.03 → 1.83 |
| habs-16-prairie-front | 3.30 → 2.69 | 3.19 → 2.03 | 3.22 → 1.94 | 3.42 → 1.85 |

With any real reveal, sheet 6 fits all three photographs better. The frontal HABS 16 prefers
it even at zero. If one free inset is fitted instead, it comes out at 0.40-0.55 ft on both NE
photographs. So the lights are built at the sheet's outer lines: A 7.19-11.65, B 16.28-20.67,
C 44.87-49.21 and D 53.98-58.40 ft from the north end. The second-floor north group is built at
8.98-19.12.

The basement grilles stay 3.9 ft wide and are centred under the moved lights. Read at full
resolution, sheet 6 draws them centred under each light and about 4.0 ft across.

## 2. The door stays

Sheet 6 gives the door only at its fan's centre (32.53 ft against the built 32.9), because the
reveal is hatched. The photographs split on it: Taylor 2135 fits the built place better (0.93
against 1.62 px), HABS 16 the sheet's (1.09 against 1.98), and HABS 17 neither. The door moves
the fan, the lintel and the stoop with it, so it stays at 30.4-35.4. Sheet 5 and its own image
gate (T-2853) are the place to read it.

## 3. The corners stand

Fitted on sheet 6's openings, with a 0.6 ft reveal:

- taylor-2135-ne: the N corner pick reads 1.34 ft from the north end
- habs-17-habs-ne: the N corner pick reads 0.70 ft from the north end
- habs-16-prairie-front: the S corner pick reads 73.13 ft from the north end

The corner picks stand on the downspouts, which sheet 6 draws 0.90 ft (north) and 0.82 ft
(south) in from the corners. Each pick reads within about 0.45 ft of its downspout. The
2.0-2.6 ft T-2857 found was the old schedule's error carried 8 ft past the last jamb, so the
piers stand as built.

## 4. Taylor 2135 refitted

The camera used to stand on five controls, two of them the downspouts taken as corners, and
put every first-floor jamb 20.5 px left of the photograph. It is now refitted on the ten
first-floor jambs (x only, with the far jamb at the sash), the corners' heights and the north
gable's foot. The corners' x picks are left out, because no source gives the downspouts'
standoff from the wall. It is a level camera with a small fitted roll, the height held to
1.0-2.5 m and the principal point held. The solve has more than one minimum, so it starts from
21 seeds and keeps the best.

- fit: 1.36 px rms; jambs +1.8, -0.3, -0.2, -0.3, -1.1, -3.6, +2.0, +0.9, +1.0, -0.0 px
- stacks, withheld (render minus photograph): before {"south": {"right_x": -22, "top_y": 2}, "middle": {"left_x": -21, "right_x": -19, "top_y": -1}, "north": {"left_x": -13, "right_x": -15, "top_y": 1}};
  after {"south": {"right_x": -14.6, "top_y": -0.5}, "middle": {"left_x": -7.8, "right_x": -6.6, "top_y": -2.1}, "north": {"left_x": 3.6, "right_x": 0.7, "top_y": 1.6}} (6.5 px rms, from 14.5)

The stack tops stay within 2 px. The south stack's north face still reads 14.6 px left, the
middle stack's 7-8 px and the north stack's within 4 px. That is a gradient along the roof which
the jambs below do not show. It is left open on the match record, because this piece does not
read the stacks' plan places.

## The three views

Rebaked, and all three side-by-sides re-rendered. In Taylor 2135, lights A and B, the door and
the grilles now sit on the photograph's within a few pixels. In HABS 17 the moved lights and the
north group sit on the photograph's horizontally. That frozen camera's vertical offset is its
own, from T-2200's 33.7 px withheld checks. Each front item is closed on its match record, and
all three still read `differs` on the stone relief and, for Taylor, the south stack.
