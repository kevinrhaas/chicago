"""Read a committed terrain heightfield the way the walker reads it.

`generators/terrain_gen.py` writes `heightfield.json` + `heightfield.bin`, and
`renderers/web/js/terrain.js` samples them bilinearly to decide what the visitor
is standing on. This is the third reader, and it exists so `tools/validate.py`
can ask a question neither of the other two can: **does a structure actually
meet the ground it is placed on?**

It deliberately reports the RAW surface — the channel bed included — and not the
renderer's walkable surface. `terrain.js` substitutes a wading barrier at +4 m
over water so a walker cannot stroll into the river; that is a navigation rule,
and a check that inherited it would measure a bridge against an invented wall
instead of against the river it crosses.

The layout is `heightfield.json`'s own: row-major samples, row 0 at the SOUTH
edge, column 0 at the WEST edge, `cell_m` apart, sample [0][0] sitting exactly on
(`origin_e`, `origin_n`) in local ENU metres, elevation = raw * scale + offset.
Kept in `tools/` rather than beside the generator on purpose: the writer's bytes
are hashed into every asset's freshness (see `generators/mesh_inputs.py`), so a
reader living there would re-stale the whole town every time it changed, for a
change that cannot move a vertex.
"""

from __future__ import annotations

import array
import json
from pathlib import Path

ENCODINGS = {"int16": "h", "float32": "f"}


class Heightfield:
    """Bilinear elevation sampler over one epoch's committed field."""

    def __init__(self, meta: dict, samples) -> None:
        self.cols = int(meta["cols"])
        self.rows = int(meta["rows"])
        self.cell_m = float(meta["cell_m"])
        self.origin_e = float(meta["origin_e"])
        self.origin_n = float(meta["origin_n"])
        self.scale = float(meta.get("scale", 1.0))
        self.offset = float(meta.get("offset", 0.0))
        self.meta = meta
        self.samples = samples

    @classmethod
    def load(cls, epoch_dir: Path) -> "Heightfield | None":
        meta_path = epoch_dir / "heightfield.json"
        if not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        bin_path = epoch_dir / meta.get("bin", "heightfield.bin")
        typecode = ENCODINGS.get(meta.get("encoding", "int16"))
        if typecode is None or not bin_path.exists():
            return None
        samples = array.array(typecode)
        samples.frombytes(bin_path.read_bytes())
        if len(samples) != int(meta["cols"]) * int(meta["rows"]):
            raise ValueError(f"{bin_path.name} holds {len(samples)} samples, but "
                             f"{meta_path.name} declares {meta['cols']}x{meta['rows']}")
        return cls(meta, samples)

    def _at(self, i: int, j: int) -> float:
        return self.samples[j * self.cols + i] * self.scale + self.offset

    def height(self, e: float, n: float) -> float:
        """Ground elevation in metres above the datum water surface.

        Clamped at the edges rather than extrapolated: outside the modelled box
        there is no evidence, and inventing a slope there would be a claim.
        """
        x = (e - self.origin_e) / self.cell_m
        y = (n - self.origin_n) / self.cell_m
        x = max(0.0, min(self.cols - 1.001, x))
        y = max(0.0, min(self.rows - 1.001, y))
        i, j = int(x), int(y)
        fx, fy = x - i, y - j
        south = self._at(i, j) * (1 - fx) + self._at(i + 1, j) * fx
        north = self._at(i, j + 1) * (1 - fx) + self._at(i + 1, j + 1) * fx
        return south * (1 - fy) + north * fy

    def covers(self, e: float, n: float) -> bool:
        """Is (e, n) actually inside the modelled field?

        `height()` clamps at the edges, which is the right behaviour for a walker
        who cannot get there and the WRONG behaviour for a gate: a structure
        placed beyond the modelled ground gets the edge sample, its base gets the
        same edge sample, the two agree to the millimetre, and the ground-contact
        check reports that it lands. Fort Dearborn stands 832 m east of this
        field's edge and passed that check silently on 2026-08-11, which is what
        this method exists to stop. Asking whether the ground EXISTS is a
        different question from how high it is, so it gets its own method rather
        than a sentinel return from that one.
        """
        return (self.origin_e <= e <= self.origin_e + (self.cols - 1) * self.cell_m
                and self.origin_n <= n <= self.origin_n + (self.rows - 1) * self.cell_m)
