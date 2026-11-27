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

## Money

* A Spot L4 hour with its streamed bytes is about **$0.71**; on demand about $1.00 (only an admin, only
  when Spot is refused in every zone).
* The starter refuses to start a machine once the month's ledger reaches **120 machine-hours** (90 % of
  $100 at $0.75 an hour). Budget alerts lag by hours, so this count is the hard cap.
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
