# T-3744 site films

Plans for `tools/site_films.mjs` servers, fed by `run_plan.py PLAN CTL`:

- `plan-1812.json`: the column marching out on 15 August 1812 (battle jaunt, `river-mouth` stop),
  filmed as a dolly down its side and a rise over it (`column-track.js`).
- `plan-1904.json`: the Prairie Avenue walk (Glessner, Kimball, Coleman, back past Pullman, east on
  Eighteenth to the conservatory, ending on the Pullman and Kimball corner), the then-and-now stills
  for the Educators page, and a walk behind a person with name cards (`people-track.js`).

The trailer (`reel`) and the home background (`hero`) are cut from those films and the site's
older ones:

- `trailer_cards.cjs` draws the title cards in the site's own type (serve the repository root on
  127.0.0.1:8765 first) as transparent 1920x1080 PNGs.
- `trailer_cut.py FILMS CARDS THEME-FINAL.mp3 OUT.mp4` cuts the trailer to the complete main title
  theme (never a clipped jaunt cue, T-3745), then it is scaled to 1600x900 at CRF 25 for the site.
- `hero_montage.py FILMS OUT.mp4` dissolves shot to shot and back into its first shot, so the loop
  never jumps.
