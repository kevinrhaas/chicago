"""Explicit scene membership, independent of a structure's date bounds.

A broad phase range is not evidence that a reconstruction belongs in every
scene inside that range. An optional scene ``structure_ids`` list selects the
records whose phases may be resolved there. Omission preserves the established
date-only rule; an empty list deliberately selects no named structures.
"""

from __future__ import annotations

import re


def structure_is_selected(scene: dict, structure_id: str) -> bool:
    """Whether this scene may resolve the record; malformed selections fail closed."""
    if "structure_ids" not in scene:
        return True
    selected = scene["structure_ids"]
    return isinstance(selected, list) and structure_id in selected


def selection_errors(scene: dict, available_ids) -> list[str]:
    """Refuse misspellings and malformed lists before compiling or baking anything."""
    if "structure_ids" not in scene:
        return []
    selected = scene["structure_ids"]
    if not isinstance(selected, list):
        return ["structure_ids must be an array (an empty array selects no structures)"]
    errors, seen = [], set()
    available = set(available_ids)
    for sid in selected:
        if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9_]+", sid):
            errors.append(f"structure_ids contains an invalid structure id: {sid!r}")
            continue
        if sid in seen:
            errors.append(f"structure_ids repeats '{sid}'")
        seen.add(sid)
        if sid not in available:
            errors.append(f"structure_ids names '{sid}', which does not resolve in data/structures/")
    return errors
