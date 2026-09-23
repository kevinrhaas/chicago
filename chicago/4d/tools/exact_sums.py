#!/usr/bin/env python3
"""T-1486. The min-max-mean refusal, in one place, so every site that publishes the
three can assert them against each other.

Rounding is MONOTONIC: if every sample lies between the smallest and the largest, so
does their mean, and so do the three figures after rounding. A record that prints a mean
outside its own min and max is therefore not a close call — it is arithmetically
impossible, and it means the summation drifted across a rounding boundary and the last
digit was decided by the order the samples happened to be added in.

`generate_plat_lots.ground_reading` committed exactly that reading (T-1477): 418
identical 0.885 m samples over the School Section's flat blocks, min and max rounding up
to 0.89, the left-to-right sum accumulating to 0.8849999999999949 and rounding down to
0.88. `math.fsum` is correctly rounded and order-independent, so the same samples give
the same digit on every machine; this refusal is what stops the impossible reading being
committed if anything ever puts the drift back.

`summer` exists so the gate can restore `sum()` and watch the refusal fire —
tools/check_exact_sums.py does that, because an assertion nobody has seen fail is a
comment rather than a check.
"""
from __future__ import annotations

import math


def consistent_reading(values, nd: int, *, summer=math.fsum,
                       label: str = "reading") -> tuple[float, float, float]:
    """(min, mean, max), each rounded to `nd`, refusing a mean outside its own bounds."""
    values = list(values)
    if not values:
        raise ValueError(f"{label}: no samples to read")
    lo = round(min(values), nd)
    hi = round(max(values), nd)
    mean = round(summer(values) / len(values), nd)
    if not lo <= mean <= hi:
        raise AssertionError(
            f"REFUSING a {label} whose mean {mean} falls outside its own min {lo} and "
            f"max {hi} over {len(values)} sample(s). Rounding is monotonic, so this "
            "cannot happen to an honestly summed mean — it means the arithmetic "
            "drifted across a rounding boundary.")
    return lo, mean, hi
