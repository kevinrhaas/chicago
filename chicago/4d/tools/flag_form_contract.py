"""The three form values the actual flag app layer consumes, not master geometry.

The declaration belongs beside its JS sidecar reads. Both validator and compiler
check it; an omitted runtime module/read must not turn an anchor into a silent
record-only note. This is deliberately bounded to the existing flag layer.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

FLAG_FORM_FIELDS = frozenset(("flag", "flag_flying", "flag_anchor"))
FLAG_READER = Path("renderers/web/js/flag-anchors.js")


def flag_form_fields(root: Path) -> frozenset[str]:
    path = root / FLAG_READER
    text = path.read_text() if path.is_file() else ""
    declaration = re.search(
        r"export\s+const\s+CONSUMED_FORM\s*=\s*Object\.freeze\((\[[^;]*?\])\);", text)
    try:
        names = json.loads(declaration.group(1)) if declaration else None
    except (ValueError, TypeError):
        names = None
    if not isinstance(names, list) or any(not isinstance(n, str) for n in names) or set(names) != FLAG_FORM_FIELDS:
        raise ValueError(f"{FLAG_READER}: CONSUMED_FORM must name exactly flag, flag_flying, flag_anchor")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    for name in names:
        if not re.search(r"\bat\." + re.escape(name) + r"\b", code):
            raise ValueError(f"{FLAG_READER}: declares {name} without reading at.{name}")
    return FLAG_FORM_FIELDS


def compiled_form_attributes(form: dict, root: Path) -> dict:
    """Keep existing sidecar/card shape and reject false runtime omissions.

    Legacy fort record_only declarations still describe their masters and are
    preserved byte-for-byte in content. New runtime anchor claims need no such
    label: the flag layer really builds them, with their own grade and reasoning.
    """
    if FLAG_FORM_FIELDS.intersection(form):
        consumed = flag_form_fields(root)
        for key in consumed.intersection(form):
            if form[key].get("geometry") not in (None, "record_only"):
                raise ValueError(f"form.{key}: the flag renderer consumes this value; geometry omission is false")
    return {key: {k: v for k, v in claim.items() if k in
            ("value", "confidence", "sources", "note", "geometry")}
            for key, claim in form.items()}
