# `data/businesses/authored/`

Business records a human wrote, as opposed to the 196 in the directory above, which
`tools/compile_businesses.py --build` compiles out of the newspaper register and rewrites
whole on every build.

A record here is read, validated and carried into `index.json` untouched. It must:

- carry `provenance: "authored"` or `"reconstructed"` — never `"compiled_from_register"`,
  which `--check` refuses, because that word means *a rebuild produces this file* and a
  rebuild does not produce this one;
- validate against `../../businesses.schema.json` like any other record;
- satisfy the same semantic rules the compiled records do — a tier that cites nothing, a
  `person_id` the resident layer does not hold, a limit with no reason, or two primary
  locations are each refused here exactly as they are there.

T-1182 writes the inferred-by-audit firms into it; T-1184 and the reconstruction band write
the `rcb_…` records. `docs/RESEARCH/business-layer.md` is the page.

## The `rcb_…` records are DERIVED, not authored

Everything in here matching `rcb_*.json` is written by
`tools/reconstruct_businesses_1835.py --build` and re-derived, byte for byte, by its
`--check`, which `tools/check.sh` runs. They are hand-written in the sense that a human
wrote the rules; they are not hand-written in the sense that a human may edit one. Each
carries `provenance: "reconstructed"` and a `reconstruction` block naming the order-book
bucket that bought it, the group and ticket that wrote it, the seed a reader can retype to
redraw its style and its street face, and what retires it. `tools/compile_businesses.py`
refuses a reconstructed record with no such block, a record carrying one that is not a
reconstruction, and any reconstructed record that cites a source.

Change the rules, or the order book, and rebuild. `docs/RESEARCH/business-naming-1835.md`
is the style guide and `docs/LIBERTIES.md § L254` carries the invention.
