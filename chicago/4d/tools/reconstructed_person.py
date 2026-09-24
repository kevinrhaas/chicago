#!/usr/bin/env python3
"""One question, asked in one place: did a stage of the reconstruction programme write
this person?

    from reconstructed_person import is_reconstructed

`grade: reconstructed` means a person the sources do not name, drawn from the population
model to fill a count the town demonstrably needs. T-1167's programme is the only writer of
one and `data/reconstruction/1835_resident_reconstruction_programme.json` is its contract;
T-1171 was the first stage to write a PERSON rather than an attribute block, and the moment
it did, a dozen research passes met a kind of record they had never seen.

WHY THE TEST IS THE CLAIM AND NOT THE GRADE. `reconstruction.stage` names the stage that
can RE-DERIVE this person from its own seeds, and `reconstruct_residents_1835.py --check`
holds every claimed person to exactly that, byte for byte. A bare `reconstructed` grade
that no stage claims is the leak `refuse_reconstructed_grade.py` exists to refuse — it
cannot be re-derived, so nothing can say where it came from.

WHAT A CALLER DOES WITH THE ANSWER, and it is the same answer every time: A RECONSTRUCTED
PERSON IS NOT EVIDENCE. They are not read for a sex, not counted in a rate the layer
measures on itself, not offered as the holder of a surname, not proposed as a duplicate of
a real card, and not used to date or corroborate anything. They are the town's own
invention, and a pass that read one back as a finding would be this dataset quoting itself.
"""


def is_reconstructed(person) -> bool:
    """True where a stage of the reconstruction programme wrote this person."""
    if not isinstance(person, dict):
        return False
    rc = person.get("reconstruction")
    return isinstance(rc, dict) and bool(rc.get("stage"))


def named_by_a_source(persons) -> list:
    """`persons`, cut to the people the sources name. The other half of the same rule."""
    return [p for p in (persons or []) if not is_reconstructed(p)]
