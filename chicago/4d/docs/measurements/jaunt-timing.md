# Jaunt timing — every primary path ridden on the published mirror

Written by `node tools/time_jaunts.mjs` (T-2041 and its children). Viewport 390x780, seed 1279, default pace settings.
Each leg is ridden by the travel controller itself (`travel.simulate`, 30 steps a simulated second) until it arrives;
**measured** = opening read + every visited stop's read and action time + the simulated seconds of every ride.
**estimate** is `jaunts.state.estimate` at the first stop — the figure the menu rounds to the half minute.
The band is 3–6 minutes at the recommended mode; Fly and Instantly must each be faster.

| Jaunt | Recommended | Stops | Content s | Travel s | Measured min | Estimate min | Menu says | Fly min | Instantly min | 1280x800 min | Verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| from-prairie-to-town | horse | 4 | 114 | 447 | 9.35 | 10.20 | about 10 | 3.85 | 1.90 | 9.33 | **over by 201 s** |
| outfit-for-the-west | wagon | 5 | 156 | 383 | 8.98 | 8.92 | about 9 | 3.63 | 2.60 | — | **over by 179 s** |
| boots-and-leather | horse | 4 | 171 | 293 | 7.73 | 7.63 | about 7.5 | 3.88 | 2.85 | — | **over by 104 s** |
| soap-and-candles | horse | 4 | 168 | 260 | 7.13 | 7.08 | about 7 | 3.62 | 2.80 | — | **over by 68 s** |
| inspect-a-lot | walk | 4 | 137 | 270 | 6.78 | 6.97 | about 7 | 2.77 | 2.28 | — | **over by 47 s** |
| shopping-south-water | walk | 4 | 124 | 272 | 6.60 | 6.67 | about 6.5 | 2.55 | 2.07 | — | **over by 36 s** |
| sunday-circuit | horse | 4 | 120 | 273 | 6.55 | 6.58 | about 6.5 | 3.13 | 2.00 | — | **over by 33 s** |
| fort-dearborn-errand | walk | 5 | 112 | 270 | 6.37 | 6.50 | about 6.5 | 2.30 | 1.87 | 6.23 | **over by 22 s** |
| schoolday-errand | horse | 4 | 179 | 202 | 6.35 | 6.37 | about 6.5 | 4.05 | 2.98 | — | **over by 21 s** |
| work-on-waterfront | horse | 4 | 198 | 176 | 6.23 | 6.18 | about 6 | 4.22 | 3.30 | 6.05 | **over by 14 s** |
| freight-for-the-store | wagon | 4 | 182 | 185 | 6.12 | 6.10 | about 6 | 3.77 | 3.03 | 5.83 | **over by 7 s** |
| materials-for-a-roof | horse | 4 | 166 | 198 | 6.07 | 6.02 | about 6 | 3.77 | 2.77 | 6.10 | **over by 4 s** |
| along-the-harbor | horse | 4 | 160 | 197 | 5.95 | 5.87 | about 6 | 3.68 | 2.67 | 5.38 | in band |
| across-wolf-point | walk | 4 | 116 | 230 | 5.77 | 5.52 | about 5.5 | 2.35 | 1.93 | 5.42 | in band |
| news-before-breakfast | horse | 4 | 204 | 138 | 5.70 | 5.63 | about 5.5 | 4.25 | 3.40 | — | in band |
| gossip-or-notice | horse | 4 | 172 | 168 | 5.67 | 5.55 | about 5.5 | 3.78 | 2.87 | — | in band |
| bed-for-the-night | horse | 4 | 162 | 168 | 5.50 | 5.58 | about 5.5 | 3.68 | 2.70 | — | in band |
| taverns-of-chicago | horse | 4 | 202 | 94 | 4.93 | 4.95 | about 5 | 3.95 | 3.37 | — | in band |
| household-provisions | walk | 4 | 136 | 153 | 4.82 | 4.97 | about 5 | 2.57 | 2.27 | — | in band |
| over-the-draw | horse | 4 | 135 | 149 | 4.73 | 4.75 | about 5 | 3.02 | 2.25 | — | in band |
| mend-the-harness | wagon | 4 | 180 | 101 | 4.68 | 4.83 | about 5 | 3.47 | 3.00 | — | in band |
| letter-home | horse | 4 | 166 | 111 | 4.62 | 4.62 | about 4.5 | 3.48 | 2.77 | — | in band |
| an-evening-stroll | horse | 4 | 121 | 147 | 4.47 | 4.42 | about 4.5 | 2.88 | 2.02 | 4.30 | in band |
| calling-on-neighbors | horse | 4 | 159 | 85 | 4.07 | 4.05 | about 4 | 3.22 | 2.65 | 3.95 | in band |
| a-decent-coat | horse | 4 | 127 | 115 | 4.03 | 4.02 | about 4 | 2.85 | 2.12 | 4.03 | in band |
| new-in-chicago | horse | 5 | 126 | 116 | 4.03 | 3.97 | about 4 | 2.90 | 2.10 | — | in band |

26 jaunts measured: 14 in band, 12 over, 0 under.

## Findings

- boots-and-leather: recommended horse measures 7.73 min, outside 3-6
- fort-dearborn-errand: recommended walk measures 6.37 min, outside 3-6
- freight-for-the-store: recommended wagon measures 6.12 min, outside 3-6
- from-prairie-to-town: recommended horse measures 9.35 min, outside 3-6
- inspect-a-lot: recommended walk measures 6.78 min, outside 3-6
- materials-for-a-roof: recommended horse measures 6.07 min, outside 3-6
- outfit-for-the-west: recommended wagon measures 8.98 min, outside 3-6
- schoolday-errand: recommended horse measures 6.35 min, outside 3-6
- shopping-south-water: recommended walk measures 6.60 min, outside 3-6
- soap-and-candles: recommended horse measures 7.13 min, outside 3-6
- sunday-circuit: recommended horse measures 6.55 min, outside 3-6
- work-on-waterfront: recommended horse measures 6.23 min, outside 3-6
