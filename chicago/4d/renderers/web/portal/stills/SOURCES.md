# Launch page stills (T-3798)

The year tiles and the full-screen backdrop on the launch page (`/4d/`). Each still is a WebP
derivative (1600 px wide and an 800 px copy) of a poster frame of the public site's films,
`site/media/films/`: renders of this project's own published scenes, so they carry no outside
rights and are not shown as evidence about the scene.

| still | poster it was cut from | what it shows |
|---|---|---|
| `1835.webp`, `1835-800.webp` | `site/media/films/1835-forks-fly.jpg` | the 1835 scene, flying over the forks of the river |
| `1904.webp`, `1904-800.webp` | `site/media/films/1904-dusk.jpg` | the 1904 scene on Prairie Avenue at dusk |
| `1812.webp`, `1812-800.webp` | `site/media/films/1812-dawn.jpg` | the 1812 scene at dawn |
| `1871.webp`, `1871-800.webp` | `site/media/films/1871-fire-night.jpg` | the 1871 scene, the fire at night |

`tools/test_launch_page.mjs` holds each still under 90 KB and fails on a still no tile uses.
