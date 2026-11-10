# Audio hosting options — 2026-11-10

The app can stream ordinary audio files from its own site or a separate asset
host. It does not need a streaming subscription, a second application, or HLS
for these short music cues. The current player streams one music cue at a time;
short nearby effects are downloaded and decoded only when requested. Streaming
reduces visitor downloads, not the space occupied on the host.

## Two different limits

`tools/validate.py` sets a project budget of **432 MiB per app tree**. This is
editable project policy. GitHub's documented **1 GB published Pages site limit**
is a provider limit, not a setting we can raise in that file. The present workflow
assembles production and `/4d/dev/` into one Pages deployment. Other site content
also consumes that allowance. An additional folder or hostname pointing to the
same deployment does not create another allowance.

Before this library expansion, the local app mirror measured 465.988 MiB, of
which 34.011 MiB was audio. Two copies of that app alone would occupy about
931.977 MiB, before the other site content. The local full tree also has 187.845
MiB of other files, giving a conservative two-copy local projection of 1119.821
MiB. These are local measurements, **not the size of the current deployed
artifact**; deployment transforms and the current production revision differ.
A temporary budget increase needs a fresh complete-artifact measurement and a
promotion scenario, not just today's dev directory size.

## Choices

| Option | What changes | Benefit and limit |
|---|---|---|
| Raise the local 432 MiB budget | Validator and documented storage allowance | Smallest change if the complete deployment has headroom; cannot increase GitHub's 1 GB limit. |
| Separate dev and production Pages deployments | Separate publishing repositories/projects, workflows, hostnames, origin/offline checks | Each actual Pages site has its own allowance. Merely serving branches under two folders does not do this. Shared audio would still be duplicated unless separately hosted. |
| Shared audio object storage and CDN — recommended | One media bucket, production hostname, CORS, versioned catalogue URLs | Both app versions use the same immutable files; audio leaves the Pages artifact. No app split and no duplicate library. |
| Separate audio-only Pages site | Separate deployment and media hostname | A free bridge for a small library, but still subject to Pages storage/bandwidth limits and Git-oriented binary publishing. |
| Move the complete app to another host | Main and preview hosting/deployments, domains, cache and offline verification | Can address geometry and media growth together; a larger migration. Check file-size, file-count, storage and bandwidth limits for the actual provider/plan. |

Splitting dev is useful if the app itself keeps growing. Moving audio first is
the narrower change and avoids paying to ship the same recordings twice. Later,
the same asset-hosting approach can serve large model/texture files if needed.

## Cost candidates

Cloudflare R2 Standard currently includes **10 GB-month storage, 1 million
Class A operations and 10 million Class B operations per month**, with no R2
Internet-egress charge. Beyond the included tier the documented Standard rates
are $0.015/GB-month storage, $4.50/million Class A and $0.36/million Class B.
A modest audio library can fit the free allowance; traffic, operations and any
additional paid services still determine the bill. The owner subsequently
activated R2, as recorded below. Use a **custom domain** for production: Cloudflare explicitly
describes `r2.dev` as a rate-limited development endpoint.

The owner activated R2 during this work and created `chicago-4d-media` with
Standard storage. A public NS lookup on 2026-11-10 returned GoDaddy's
`ns43.domaincontrol.com` and `ns44.domaincontrol.com` for `polecat.live`.
Consequently, a production R2 custom domain may require onboarding DNS to
Cloudflare or using another domain already managed there. An ordinary CNAME
at the existing DNS provider is not, by itself, the R2 custom-domain setup.
Use the bucket's public `r2.dev` URL for initial verification; do not treat it as
the production endpoint or change existing domain delegation as part of an upload.

The owner supplied `https://pub-f67d07c4cd6144e9b478b7f268f5495d` and reported
the CORS policy saved. Its inferred complete public-development address is
`https://pub-f67d07c4cd6144e9b478b7f268f5495d.r2.dev/`; a browser-style request
to the empty root returned 404, which does not verify any object or CORS policy.
The subsequent upload verification passed for all 40 objects / 41,173,377 bytes:
full SHA-256 matches, CORS for https://chicago.polecat.live, MIME types and HTTP
206 byte ranges. R2's dashboard uses the supported audio/x-m4a alias for AAC
files. A Chromium fixture at the app origin played Opus, AAC/M4A and an MP3
effect through Web Audio with nonzero decoded samples and no page errors.
The generated development app now uses these verified remote URLs; Chromium
checks of its published modules pass at phone and desktop widths, including era
changes, decoded wind, mute cleanup and no candidate autoplay. This is local
published-build integration, not a live deployment. Cache-Control
headers were absent; production cache policy and the custom domain remain work.
For repeat verification use
`tools/verify_audio_host.py --manifest <upload-manifest.json> --report <report.json>`
after uploading, then exercise browser playback from an allowed origin. The
verifier reads only; it never uploads or changes access policies.

Bunny is another simple storage/CDN option. Its current pricing page advertises
a $1 monthly CDN minimum and North America/Europe delivery at $0.01/GB;
storage and delivery-region charges must be included in a final estimate.

Sources checked 2026-11-10:

- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://developers.cloudflare.com/r2/pricing/
- https://developers.cloudflare.com/r2/buckets/public-buckets/
- https://developers.cloudflare.com/r2/buckets/cors/
- https://bunny.net/pricing/

## Prepared migration path

`python tools/package_audio.py --output /tmp/chicago-audio-release` builds a
local upload bundle. It never uploads or changes the app. Each media filename
contains its full SHA-256, so dev cannot overwrite bytes production uses. The
bundle has MIME/cache metadata, a CORS template and a small app-side catalogue;
original recordings and evidence files stay outside it. Review candidates are
excluded by default; `--include-candidates` includes the audition library too.

`tools/audio-hosting.json` selects the development host and
`tools/audio-host-verification.json` retains the successful full-object receipt.
Publication checks source hashes against that receipt, writes absolute hashed
URLs into the generated catalogue and omits the corresponding local binaries.
`check_published.mjs` checks this transformation and rejects duplicate media.
The source/archive copies remain available for authoring and rollback. Published
`data/liberties.json` is also minified with full parsed-value equality checked;
the generated app now measures 431.363 MiB within its unchanged 432 MiB budget.

For a production hostname, repackage with `--public-base https://HOST/`, upload
or reuse the same hashed objects, repeat host verification and browser playback,
then update the policy and receipt together. The helper refuses a development
endpoint when explicitly run with `C4D_PUBLISH_TIER=production`; the existing
deployment workflow does not yet set that flag. This is not an automatic
production-promotion gate. Production domain/cache setup must precede promotion.

Full-scene localhost smoke replays verified local delivery bytes because the
bucket allows the app origin, not localhost. `test_hosted_audio_browser.mjs`
separately tests real R2 networking/CORS using the published modules at that
allowed origin. Neither test substitutes for Safari or human listening review.
`test_audio_arrival_browser.mjs` additionally drives the actual published
loading screen at 390px and 1280px, including trusted opt-in, real R2 samples
through the master gain, zero muted requests and a second-click mute. It is a
focused arrival test, not full-town smoke coverage.

Each app revision keeps its own catalogue; old hashed objects remain until no
supported revision uses them. Apply long immutable caching to media, not to a
mutable catalogue URL. Both current app tiers use the same origin; a future dev
subdomain must be added to the media CORS policy. Keep credentials in deployment
secrets, never in browser code or the catalogue.

This prepares a choice; it does not claim a live bucket, working media hostname,
raised budget, production promotion or completed release gate.
