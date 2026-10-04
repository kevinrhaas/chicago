# Jaunt timing — every primary path ridden on the published mirror

Written by `node tools/time_jaunts.mjs` (T-2041 and its children). Viewport 390x780, seed 1279, default pace settings.
Each leg is ridden by the travel controller itself (`travel.simulate`, 30 steps a simulated second) until it arrives;
**measured** = opening read + every visited stop's read and action time + the simulated seconds of every ride.
**estimate** is `jaunts.state.estimate` at the first stop — the figure the menu rounds to the half minute.
The band is 3–6 minutes at the recommended mode; Fly and Instantly must each be faster.

| Jaunt | Recommended | Stops | Content s | Travel s | Measured min | Estimate min | Menu says | Fly min | Instantly min | 1280x800 min | Verdict |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|
| along-the-harbor | horse | 4 | 160 | 197 | 5.95 | 5.87 | about 6 | 3.68 | 2.67 | 5.38 | in band |
| boots-and-leather | horse | 4 | 155 | 197 | 5.87 | 5.87 | about 6 | 3.55 | 2.58 | 3.93 | in band |
| freight-for-the-store | wagon | 4 | 163 | 185 | 5.80 | 5.78 | about 6 | 3.45 | 2.72 | 5.52 | in band |
| sunday-circuit | horse | 4 | 74 | 273 | 5.78 | 5.82 | about 6 | 2.37 | 1.23 | 5.73 | in band |
| across-wolf-point | walk | 4 | 116 | 230 | 5.77 | 5.52 | about 5.5 | 2.35 | 1.93 | 5.42 | in band |
| soap-and-candles | horse | 4 | 171 | 172 | 5.72 | 5.73 | about 5.5 | 3.68 | 2.85 | 5.65 | in band |
| news-before-breakfast | horse | 4 | 204 | 138 | 5.70 | 5.63 | about 5.5 | 4.25 | 3.40 | — | in band |
| work-on-waterfront | horse | 4 | 166 | 176 | 5.70 | 5.65 | about 5.5 | 3.68 | 2.77 | 5.52 | in band |
| gossip-or-notice | horse | 4 | 172 | 168 | 5.67 | 5.55 | about 5.5 | 3.78 | 2.87 | — | in band |
| materials-for-a-roof | horse | 4 | 141 | 198 | 5.65 | 5.60 | about 5.5 | 3.35 | 2.35 | 5.68 | in band |
| schoolday-errand | horse | 4 | 137 | 202 | 5.65 | 5.67 | about 5.5 | 3.35 | 2.28 | 5.60 | in band |
| bed-for-the-night | horse | 4 | 162 | 168 | 5.50 | 5.58 | about 5.5 | 3.68 | 2.70 | — | in band |
| fort-dearborn-errand | walk | 4 | 100 | 229 | 5.48 | 5.73 | about 5.5 | 2.00 | 1.67 | — | in band |
| from-prairie-to-town | horse | 4 | 111 | 216 | 5.45 | 5.30 | about 5.5 | 2.92 | 1.85 | 5.40 | in band |
| taverns-of-chicago | horse | 4 | 202 | 94 | 4.93 | 4.95 | about 5 | 3.95 | 3.37 | — | in band |
| outfit-for-the-west | horse | 5 | 156 | 138 | 4.90 | 4.93 | about 5 | 3.38 | 2.60 | 4.87 | in band |
| household-provisions | walk | 4 | 136 | 153 | 4.82 | 4.97 | about 5 | 2.57 | 2.27 | — | in band |
| over-the-draw | horse | 4 | 135 | 149 | 4.73 | 4.75 | about 5 | 3.02 | 2.25 | — | in band |
| mend-the-harness | wagon | 4 | 180 | 101 | 4.68 | 4.83 | about 5 | 3.47 | 3.00 | — | in band |
| letter-home | horse | 4 | 166 | 111 | 4.62 | 4.62 | about 4.5 | 3.48 | 2.77 | — | in band |
| an-evening-stroll | horse | 4 | 121 | 147 | 4.47 | 4.42 | about 4.5 | 2.88 | 2.02 | 4.30 | in band |
| calling-on-neighbors | horse | 4 | 159 | 85 | 4.07 | 4.05 | about 4 | 3.22 | 2.65 | 3.95 | in band |
| a-decent-coat | horse | 4 | 127 | 115 | 4.03 | 4.02 | about 4 | 2.85 | 2.12 | 4.03 | in band |
| new-in-chicago | horse | 5 | 126 | 116 | 4.03 | 3.97 | about 4 | 2.90 | 2.10 | — | in band |
| shopping-south-water | wagon | 4 | 124 | 112 | 3.93 | 3.93 | about 4 | 2.55 | 2.07 | — | in band |
| inspect-a-lot | horse | 4 | 137 | 62 | 3.32 | 3.35 | about 3.5 | 2.77 | 2.28 | — | in band |

26 jaunts measured: 26 in band, 0 over, 0 under.
