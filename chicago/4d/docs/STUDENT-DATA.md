# Student data (T-3776)

The owner, 2026-11-26, approving Stage 1 of the server plan ("Server, cloud GPU and engine
plan"): class codes, cloud save, shared routes and follow-the-teacher put student work on a
server for the first time. This page comes first. It says, field by field, what 4D Chicago
keeps, where, who can read it, how long, and how it is deleted. It is written for a teacher
and a parent; the visitor's own page is `renderers/web/privacy.html` (published at
`/4d/walk/privacy.html`), and the school agreement is `docs/STUDENT-DATA-AGREEMENT.md`.

## The switch

`cloudFeatures` in `renderers/web/js/sign-in-config.js` is **on**: the owner switched it on on
27 November 2026 ("Turn on the cloud features"). Every Stage 1 feature that writes student work
(T-3777 cloud save, T-3778 classes, T-3779 shared routes and hand-ins, T-3780 follow the teacher
and classmates) checks `cloudFeaturesOn()` in `js/student-data.js` first and writes nothing while
it is off, so setting it back to `false` stops them all at once. Each feature adds its rows to
the table below before it ships. A school gets the agreement before its classes use them.

## What is kept today

Everything below lives in Google Cloud Firestore, project `chicago-61643`, location `nam5`
(United States). Each record is written over HTTPS with the visitor's own Firebase sign-in, and
the rules in `docs/SIGN-IN.md` decide who reads it.

| Record | Fields | Why | Who can read it |
| --- | --- | --- | --- |
| `visitors/<uid>` | email, name (from Google or Microsoft, else blank), sign-in method, first and last seen, first and last year, last device class, years entered, entry count | The owner's list of who has visited | The visitor, the owner |
| `visits/<id>` | uid, email, sign-in method, year, device class (computer, tablet, phone), time | Usage by year, device and day | The visitor, the owner |
| `readers/<uid>` | reading ages, time | The same reading level on every device | The visitor |
| `people/<uid>` | the visitor's own person (look and dress), time | The same person on every device | The visitor |
| `bugs/<id>` | uid, email, the report, build, device, graphics chip, place in the town, recent errors, an optional screenshot | Fixing what broke | The visitor (to delete), the owner |

Not kept on a server: the field notebook, people met and places found, teacher routes, settings,
the field log. They stay in the browser until a later ticket moves them, with this page updated
in the same change.

Firebase's own sign-in service holds the account itself (email, and the Google or Microsoft
link). Firebase Analytics counts page views and the `login` and `enter_year` events with no
email. Neither is sold, shared or used for advertising, and no third party reads any of it.

## How long

Until the visitor deletes it, or until the owner removes a record on request. A school's class
records (T-3778) are kept for the school year the class names and deleted when the teacher
closes the class; the agreement states the same.

## Deleting it

Settings › About › **Delete my saved data** (`js/student-data.js` `deleteMyData`): the visitor's
`visitors`, `readers` and `people` documents and every `visits` and `bugs` row carrying their uid,
at once, then a sign-out (so the next entry does not write the visitor row straight back).
Signing in again starts a new record. The account itself in Firebase sign-in is removed by the
owner on request (the contact page), because deleting it from the page needs a fresh sign-in.

A collection that holds a visitor's data is added to `ACCOUNT_DOCS` or `ACCOUNT_ROWS` in
`js/student-data.js` and to the rules in the same change; `tools/test_sign_in.mjs` holds the
code, the rules, this table and the visitor's page to the same list.

## What later Stage 1 tickets add

Each adds its rows to the table above before it ships, and only behind the switch:

- T-3777: the notebook, people met and places found and settings, under the visitor's uid.
- T-3778: classes (teacher uid, name, join code) and membership; hand-ins the student chooses.
- T-3779: the teacher's routes and route answers handed in to a class.
- T-3780: the teacher's current stop; a classmate's position in the town, kept only while the
  class is in session.

Never kept: grades, scores, rankings, chat between students, location from the device (On-site
mode reads the position in the browser and sends it nowhere), or anything for advertising.
