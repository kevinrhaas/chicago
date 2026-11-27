# Cloud play (Stage 2: T-3793, T-3794, T-3795)

A player with cloud play (the launch page's rights by email, T-3797) presses **Play from the
cloud**; a Google Cloud machine with an NVIDIA L4 opens the town at their year in Chromium and
streams it to their browser, so a weak computer or a phone plays at full detail.

```
launch page ──POST /start (Firebase ID token, year)──▶ chicago-stream-starter (Cloud Run)
     ▲                                                   │ rights: Firestore rules, read AS the player
     │ link https://<ip>.sslip.io/?k=<token>             │ caps: 1 machine, the month's hours, the budget
     └──────────── GET /status until ready ◀─────────────┤ starts a Spot g2-standard-4 from family chicago-stream
                                                         ▼
                         machine: Caddy (HTTPS + per-session cookie) → Selkies Chromium (GPU)
                         ends itself after 10 idle minutes; Google ends it after 2 hours
```

| File | What it is |
| --- | --- |
| `setup.sh` | One-time (and repeatable) project setup: accounts, ledger bucket, firewall, the starter on Cloud Run, the budget's Pub/Sub stop. Prints the starter's address. |
| `build-image.sh` | Builds the machine image (family `chicago-stream`) with `machine/provision.sh`. |
| `machine/provision.sh` | Docker, the NVIDIA container toolkit, Caddy, the Selkies Chromium image, the session service. |
| `machine/session.sh` | One session at boot: the gate, the town at the year, ready flag, idle end. |
| `starter/` | The Cloud Run service (`server.mjs`, logic in `lib.mjs`, tested by `tools/test_stream_starter.mjs`). |

## What a player gets (measured 2026-11-27, Spot L4, us-central1, from a home connection)

* The town at Full detail (its own device check scores the L4 79, Good), drawn on the GPU and the
  stream encoded on it (NVENC H.264, about 4 ms from capture to sent).
* Walking a jaunt: 23 to 48 frames a second; standing still the town draws fewer, as on any
  computer. About 40 ms from the machine to the screen.
* 2 to 7 Mbit/s while moving, peaks of 13: roughly 1 to 2 GB an hour, which Google bills as
  internet traffic (about 12 cents a GB).
* The driver Google ships is compute-only; `machine/provision.sh` adds its OpenGL and video-encoder
  parts. Without them the town drew in software and the CPU encoded the stream.

## Money

* A Spot L4 hour with its streamed bytes is about **$0.71**; on demand about $1.00.
* The starter keeps its own count of the month's machine-hours and their cost ($0.75 an hour on Spot,
  $1.05 on demand, rounded up) and starts no machine that could take it past **$90** (90 % of the $100
  budget). Budget alerts lag by hours, so this count is the hard cap.
* L4s are often all taken (2026-11-27: none free in any US zone, Spot or on demand, nor any T4). The
  starter tries a Spot L4 in every US zone; if none is free a player hears so plainly, and an admin
  falls back to on demand. The older T4 (n1-standard-4) can stand in when no L4 is free, but only
  with `GPUS=l4,t4` at setup: it is off until it is measured, so nobody is handed a weaker machine
  untested. The launch page names the machine before the stream opens.
* The image build runs on demand and needs no GPU: with none free it builds on a plain machine and
  the GPU is first checked by the first session.
* For a week from setup, Cloud Scheduler calls the starter's `/probe` hourly: it asks for a Spot
  machine as the starter would (and on demand only if none), in the US and Canada, deletes it at
  once, and logs what was free. At most one machine-minute an hour, about $1 for the week. The
  tally is at `<starter>/probe`.
* The $100 budget's 100 % alert reaches `/budget`, which deletes every machine and stops the starter
  until next month or until an admin calls `/resume`.
* Nothing here touches the Firebase project (chicago-61643): the starter reads rights with the
  player's own token, as the launch page does.

## Running it

From Cloud Shell in chicago-stream, signed in as the owner:

```
git clone https://github.com/kevinrhaas/chicago && cd chicago
bash chicago/4d/tools/stream/build-image.sh     # ~15 minutes, under $1
bash chicago/4d/tools/stream/setup.sh           # prints the starter's address
```
