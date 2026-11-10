# T-2797 strict recovery contract: outside-app source proposal

This reuses the archived BoardingController. There is no physical Board, motion,
live UI, renderer, existing person transfer, geometry or current-app binding here.
The intended future specimen remains the existing parked Brougham and Charles;
the separate Hans Johnson loop is not repurposed. Production acceptance stays false.

The archived source/default behavioral test is retained verbatim in baseline/.
The proposed copy changes strict-mode branches only. Its default tests remain
byte-identical. Strict recovery now requires an explicit adapter capability;
legacy/unsupported ports refuse before reservation rather than imply atomicity.

## Contract

The adapter owns a stop promise keyed by the actual seat token. Canceling a waiter
does not cancel or replace that operation. A result must explicitly report completed
and finalNeutral, and current finite speed and the independent stopped check must
agree. Only a later explicit recovery command may retry a settled rejected stop.

The strict recovery sequence is:

1. Capture visitor/camera/person/model lease identities once; verify they and the
   attachment are still held. Saved visitor/camera state stays in the controller.
2. Await verified stop. Preparation may await readiness but must not detach or
   release ownership. It must provide a compensation-ready plan for this token.
3. Commit, verify recovered state independently, release external leases, and verify
   that release in one synchronous turn. No camera frame can run halfway through.
4. Only then may the core release its own matching seat token and snapshots.

A mutate-then-throw is synchronously compensated and acknowledged, with independent
retained-state verification. It reports recovery-blocked; no idle/release is inferred.
An absent plan, unsupported async commit, failed verification or failed compensation
never counts as successful recovery. A real port must qualify these methods; merely
supplying callbacks is not evidence that a live renderer can compensate correctly.
Promise-returning/misbehaving ports are refused, and their transaction token is
revoked; no guarantee is made for arbitrary code that ignores revoked ownership.

Both strict rollback and strict normal leave use that same transaction, so a normal
leave's later camera-restoration error cannot bypass ownership retention. Cancellation
supersedes an uncommitted exit plan. Exact owner/snapshot checks and a generation guard
prevent a delayed recovery from clearing a newer reservation or state. While recovery
is blocked and an attachment is held, camera-follow ticks continue. A provider's
retirement request cannot be treated as successful disposal before recovery commits.

Default-mode semantics, successful old controls, shared Interact timeout behavior,
day/jaunt ownership, installed assets and current source are unchanged.

## Actual pure qualification

Run the exact archived default tests against baseline and proposed source. Run the
new stateful ownership/failure harness against original strict source, retaining its
real failures, then against the proposal. The fixture independently holds visitor,
camera, person and model lease tokens; it injects failures before/after mutation,
independent-verification refusal, partial release, rejected/non-neutral stops,
canceled waiters, concurrent cancellation, old generations, blocked exit and provider
retirement. These are synthetic contract controls, not body/door/camera-fit or scene
acceptance.

Original SUP120 guard-01 closed in0.616s with original resource floors accepted,
complete cleanup and zero remaining children. The exact archived default suite
passed12/12 against both baseline and proposal. The original strict core failed
18 of20 new controls; all original failures are retained. The proposal passed20/20.
Source-before/after hashes were unchanged during execution. No browser, model,
scene, physical Board, motion or UI ran. Full native check.sh/preflight is UNRUN.

Reproduce the pure controls with Node (no extra dependencies):

```
node --test baseline/passenger-regression.test.mjs
node --test proposed/passenger-regression.test.mjs
node strict-recovery.test.mjs baseline   # expected exit1: preserved negatives
node strict-recovery.test.mjs proposed   # expected exit0
```

The native current83c ports do not implement this transaction contract. They remain
unsupported; the source does not adapt or enable them. Current source/API evidence is
in the preceding t2797-boarding-reuse-map-20261110 packet.
