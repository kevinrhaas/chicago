#!/usr/bin/env python3
"""
Chicago 1835 — structure dataset validator.

Runs three passes:
  1. JSON Schema  — shape.
  2. Referential  — every source_id resolves in sources.json.
  3. Semantic     — the provenance and date rules that the schema cannot express.

Exit 0 clean, 1 on any error. Warnings do not fail the build but are always printed.

Usage:
    python tools/validate_structures.py
    python tools/validate_structures.py --data data/structures.json --sources data/sources.json
    python tools/validate_structures.py --strict     # warnings become errors
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("missing dependency: pip install jsonschema")


ROOT = Path(__file__).resolve().parent.parent

# Attribute-level confidence rules. See BRIEF.md §4.
NEEDS_SOURCES = "documented"
NEEDS_NOTE = "inferred"

# form attributes that must be present on every structure regardless of confidence,
# because the generators cannot produce a mesh without them.
REQUIRED_FORM = ("stories", "wall_height_m", "roof_type", "construction")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats: dict[str, int] = {"documented": 0, "inferred": 0, "conjectural": 0}

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"  ERROR  {where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"  WARN   {where}: {msg}")

    def count(self, confidence: str) -> None:
        if confidence in self.stats:
            self.stats[confidence] += 1


def load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"{path}: invalid JSON at line {e.lineno}: {e.msg}")


def parse_date(value: str, where: str, rpt: Report) -> date | None:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        rpt.error(where, f"not an ISO date: {value!r}")
        return None


def check_attested(
    node: dict,
    where: str,
    source_ids: set[str],
    rpt: Report,
) -> None:
    """Enforce the confidence rules on a single attested attribute."""
    confidence = node.get("confidence")
    rpt.count(confidence)

    sources = node.get("sources") or []
    note = (node.get("note") or "").strip()

    if confidence == NEEDS_SOURCES:
        if not sources:
            rpt.error(where, "documented but cites no sources")
        for sid in sources:
            if sid not in source_ids:
                rpt.error(where, f"source_id {sid!r} does not resolve in sources.json")

    elif confidence == NEEDS_NOTE:
        if not note:
            rpt.error(where, "inferred but has no note explaining the inference")
        for sid in sources:
            if sid not in source_ids:
                rpt.error(where, f"source_id {sid!r} does not resolve in sources.json")

    elif confidence == "conjectural":
        if sources:
            rpt.warn(where, "conjectural but cites sources — should this be inferred?")


def validate(data: dict, sources: dict, rpt: Report) -> None:
    source_ids = {s["id"] for s in sources.get("sources", [])}

    target = parse_date(data.get("target_date", ""), "target_date", rpt)

    datum = data.get("datum", {})
    if not datum.get("verified"):
        rpt.error(
            "datum",
            "origin is unverified. Check against georeferenced Hathaway (1834) and "
            "Wright (1834) before generating geometry — fixing this later means "
            "regenerating everything.",
        )

    seen_ids: set[str] = set()

    for i, s in enumerate(data.get("structures", [])):
        sid = s.get("id", f"<index {i}>")
        where = f"structures[{sid}]"

        if sid in seen_ids:
            rpt.error(where, "duplicate structure id")
        seen_ids.add(sid)

        # --- date gate: the most important check in the suite ---
        rng = s.get("documented_range", {})
        frm = parse_date(rng.get("from", ""), f"{where}.documented_range.from", rpt)
        to = parse_date(rng.get("to", ""), f"{where}.documented_range.to", rpt)

        if frm and to:
            if frm > to:
                rpt.error(f"{where}.documented_range", "from is after to")
            elif target and not (frm <= target <= to):
                rpt.error(
                    f"{where}.documented_range",
                    f"target date {target} falls outside attested range "
                    f"{frm}..{to} — this structure does not belong in the scene",
                )
            span_years = (to - frm).days / 365.25
            if span_years > 12:
                rpt.warn(
                    f"{where}.documented_range",
                    f"span is {span_years:.0f} years. Chicago changed fast between 1833 "
                    "and 1837 — a range this wide usually means the evidence is weaker "
                    "than the confidence claims.",
                )

        for node, label in ((s.get("position"), "position"), (s.get("footprint"), "footprint")):
            if node:
                check_attested(node, f"{where}.{label}", source_ids, rpt)

        if rng:
            check_attested(rng, f"{where}.documented_range", source_ids, rpt)

        # --- form ---
        form = s.get("form", {})
        for key in REQUIRED_FORM:
            if key not in form:
                rpt.error(f"{where}.form", f"missing required generator parameter {key!r}")
        for key, node in form.items():
            if isinstance(node, dict):
                check_attested(node, f"{where}.form.{key}", source_ids, rpt)

        for label in ("function", "occupants"):
            if isinstance(s.get(label), dict):
                check_attested(s[label], f"{where}.{label}", source_ids, rpt)

        # --- conjectural density ---
        conf_values = [
            n.get("confidence")
            for n in list(form.values()) + [s.get("position"), s.get("footprint")]
            if isinstance(n, dict)
        ]
        if conf_values:
            conjectural = sum(1 for c in conf_values if c == "conjectural")
            if conjectural / len(conf_values) > 0.6:
                rpt.warn(
                    where,
                    f"{conjectural}/{len(conf_values)} attributes are conjectural. "
                    "This structure is mostly invention — confirm that is intended and "
                    "that the renderer will show it as such.",
                )

        if s.get("review_required"):
            rpt.warn(where, "flagged review_required — blocked from release until reviewed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=ROOT / "data" / "structures.json", type=Path)
    ap.add_argument("--sources", default=ROOT / "data" / "sources.json", type=Path)
    ap.add_argument("--schema", default=ROOT / "data" / "structures.schema.json", type=Path)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    data = load(args.data)
    sources = load(args.sources)
    schema = load(args.schema)

    rpt = Report()

    # Pass 1 — schema
    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    for e in schema_errors:
        path = "/".join(str(p) for p in e.path) or "<root>"
        rpt.error(f"schema {path}", e.message)

    # Passes 2 and 3 — only meaningful if the shape is right
    if not schema_errors:
        validate(data, sources, rpt)

    total = sum(rpt.stats.values())
    print(f"\nchicago1835 :: {len(data.get('structures', []))} structures, {total} attested attributes")
    if total:
        for level in ("documented", "inferred", "conjectural"):
            n = rpt.stats[level]
            print(f"  {level:<12} {n:>4}  {n / total * 100:5.1f}%")

    if rpt.warnings:
        print(f"\n{len(rpt.warnings)} warning(s):")
        print("\n".join(rpt.warnings))

    if rpt.errors:
        print(f"\n{len(rpt.errors)} error(s):")
        print("\n".join(rpt.errors))
        print("\nFAIL\n")
        return 1

    if args.strict and rpt.warnings:
        print("\nFAIL (strict: warnings are errors)\n")
        return 1

    print("\nPASS\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
