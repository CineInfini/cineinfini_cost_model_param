#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation case: Elephants Dream (2006, ~11 min)
Blender Foundation open-source short film.

Purpose
-------
Validate the CineInfini cost model against a known production with a
publicly documented budget.  Elephants Dream is a fully CGI short film,
making it an appropriate (though imperfect) analogue for an AI-generated
film.

Assumptions
-----------
- film_duration_sec = 660   (10 min 54 s → rounded to 660 s)
- vfx_duration_sec  = 600   (≈91% of film is VFX-intensive CGI rendering;
                              justified because Elephants Dream has no live
                              action – every frame involves 3D rendering
                              comparable to AI VFX generation)
- regen_video = 25           (median assumption, consistent with paper §7.1)
- scenario    = 'medium'     (median cost estimate)

Comparison
----------
Actual budget ≈ $142,000 USD (Blender Foundation, 2006; human artists,
professional 3D pipeline, ~12 months).
Source: Roosendaal, T. (2006). Elephants Dream: Making Of. Blender Foundation.

Interpretation
--------------
The CineInfini model estimates the *technical rendering cost* only.
It excludes: creative direction, scenario writing, sound design supervision,
and quality assurance labour – costs that are implicitly included in the
$142,000 human production budget.  The comparison therefore illustrates
the reduction in *compute cost*, not total production cost.
"""

import sys
sys.path.append('..')
from src.cineinfini_cost_model_param import compute_cost_ia, cost_breakdown

# ─── Parameters ──────────────────────────────────────────────────────

ACTUAL_BUDGET_USD = 142_000   # Blender Foundation 2006 (human artists)

params = {
    "film_duration_sec": 660,    # 10 min 54 s
    "vfx_duration_sec":  600,    # 91% of film – see module docstring
    "regen_video":       25,     # median; user-provided → overrides scenario
    "regen_tts":         0.2,
    "regen_music":       0.2,
    "regen_vfx":         0.5,
    "regen_editing":     0.2,
}

# ─── Compute ──────────────────────────────────────────────────────────

cost_medium = compute_cost_ia(scenario="medium", user_params=params)
bd          = cost_breakdown("medium", params)
reduction   = (1.0 - cost_medium / ACTUAL_BUDGET_USD) * 100

# ─── Report ───────────────────────────────────────────────────────────

print("=" * 60)
print("Validation case: Elephants Dream (2006)")
print("=" * 60)

print(f"\n  Film duration:   {params['film_duration_sec']} s  (~{params['film_duration_sec']//60} min)")
print(f"  VFX duration:    {params['vfx_duration_sec']} s  ({params['vfx_duration_sec']/params['film_duration_sec']*100:.0f}% of film)")
print(f"  Scenario:        medium")
print(f"  regen_video:     {params['regen_video']} attempts/shot")

print(f"\nCost breakdown (technical rendering only):")
for key in ("video", "tts", "music", "vfx", "editing"):
    pct = bd[key] / bd["total"] * 100
    print(f"  {key:8s}: {bd[key]:>8,.2f} USD  ({pct:.1f}%)")
print(f"  {'TOTAL':8s}: {bd['total']:>8,.2f} USD")

print(f"\nComparison with actual production:")
print(f"  CineInfini estimate: {cost_medium:>8,.2f} USD  (technical cost)")
print(f"  Actual budget:       {ACTUAL_BUDGET_USD:>8,} USD  (human artists)")
print(f"  Reduction (compute): {reduction:.1f}%")

print(f"\nNote: The $142,000 budget includes creative, supervision and QA")
print(f"labour not modelled here.  The CineInfini cost model estimates")
print(f"the compute/API cost only (Section 8 of paper).")
