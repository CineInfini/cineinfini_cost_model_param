#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sobol sensitivity analysis for the CineInfini parametric cost model.

Purpose
-------
Compute first-order (S1) and total-order (ST) Sobol sensitivity indices
to identify which input parameters dominate the variance of C_IA.
Results reproduce Figure 3 and Section 7.2 of the paper.

Expected results (paper §7.2, 12,288 evaluations):
    S1(video_cost)   ≈ 0.65
    S1(regen_video)  ≈ 0.25
    S1(film_dur)     ≈ 0.05
    S1(vfx_dur)      ≈ 0.04
    S1(regen_vfx)    ≈ 0.01

Requirements
------------
    pip install SALib>=1.4  numpy

SALib version notes
-------------------
SALib 1.x : from SALib.sample import saltelli; saltelli.sample(problem, N)
SALib 2.x : from SALib.sample import sobol;    sobol.sample(problem, N)
This script auto-detects the installed version.

Critical fix vs original script
--------------------------------
The original script passed "video_ia_par_sec" as a user_params key that
was silently ignored by compute_cost_ia (video cost was always 0.40 USD/s).
This caused S1(video_cost) ≈ 0 instead of ≈ 0.65 – the Sobol results in
the paper could not be reproduced.

Fix: compute_cost_ia v7.14 now reads user_params["video_ia_par_sec"] and
uses it to override VIDEO_AI_COST_PER_SEC.  (See [Fix 3] in module header.)
"""

import sys
import numpy as np

sys.path.append('..')
from src.cineinfini_cost_model_param import compute_cost_ia

# ─── SALib version-safe import ────────────────────────────────────────
try:
    import SALib
    _salib_major = int(SALib.__version__.split(".")[0])
except Exception:
    _salib_major = 1

if _salib_major >= 2:
    from SALib.sample.sobol import sample as saltelli_sample
    from SALib.analyze.sobol import analyze as sobol_analyze
else:
    from SALib.sample import saltelli as _salt_mod
    from SALib.analyze import sobol as _sobol_mod
    saltelli_sample = _salt_mod.sample
    sobol_analyze   = _sobol_mod.analyze

# ─── 1. Problem definition ────────────────────────────────────────────

problem = {
    "num_vars": 5,
    "names": [
        "video_cost",       # C_video   – video unit cost (USD/s)       [21]
        "regen_video",      # V_regen   – attempts per shot              [7]
        "film_duration",    # V_dur     – total film duration (s)
        "vfx_duration",     # V_vfx_dur – VFX-heavy portion (s)
        "regen_vfx",        # V_regen_vfx – VFX regeneration factor
    ],
    "bounds": [
        [0.30, 0.50],       # video cost range (paper §4.2, low–high)   [21]
        [20.0, 30.0],       # video regen range (paper §4.3)            [7]
        [3_600, 7_200],     # 60–120 min in seconds
        [600,   2_400],     # 10–40 min of VFX
        [0.2,   1.0],       # VFX regen range (paper §4.3)
    ],
}

N_SAMPLES = 1024   # → 1024 × (2 × 5 + 2) = 12,288 model evaluations (paper §7.2)

# ─── 2. Saltelli sampling ─────────────────────────────────────────────

print(f"Generating Saltelli samples  (N={N_SAMPLES}, "
      f"evaluations={N_SAMPLES * (2 * problem['num_vars'] + 2)}) …")

param_values = saltelli_sample(problem, N_SAMPLES, calc_second_order=False)
print(f"Sample matrix shape: {param_values.shape}")

# ─── 3. Model evaluations ─────────────────────────────────────────────

BASE_PARAMS = {
    "film_duration_sec": 5400,
    "vfx_duration_sec":  1200,
    "regen_tts":    0.2,
    "regen_music":  0.2,
    "regen_editing":0.2,
}

costs = np.empty(len(param_values))

for i, vals in enumerate(param_values):
    user_params = {
        # [Fix] video_ia_par_sec is now handled by compute_cost_ia v7.14
        "video_ia_par_sec":  float(vals[0]),   # overrides VIDEO_AI_COST_PER_SEC
        "regen_video":       float(vals[1]),
        "film_duration_sec": float(vals[2]),
        "vfx_duration_sec":  float(vals[3]),
        "regen_vfx":         float(vals[4]),
        # Keep TTS, music, editing at default
        "regen_tts":    BASE_PARAMS["regen_tts"],
        "regen_music":  BASE_PARAMS["regen_music"],
        "regen_editing":BASE_PARAMS["regen_editing"],
    }
    costs[i] = compute_cost_ia(scenario="medium", user_params=user_params)

print(f"Model evaluations complete.  "
      f"Cost range: [{costs.min():,.0f}, {costs.max():,.0f}] USD")

# ─── 4. Sobol analysis ────────────────────────────────────────────────

Si = sobol_analyze(
    problem,
    costs,
    calc_second_order=False,
    print_to_console=False,   # suppress verbose SALib output
)

# ─── 5. Results table ─────────────────────────────────────────────────

print("\n" + "=" * 68)
print("Sobol Sensitivity Indices  –  First-order (S1) and Total-order (ST)")
print("=" * 68)
header = f"{'Parameter':<22} | {'S1':>6} | {'S1_conf':>7} | {'ST':>6} | {'ST_conf':>7}"
print(header)
print("-" * 68)

for i, name in enumerate(problem["names"]):
    print(
        f"{name:<22} | {Si['S1'][i]:>6.4f} | {Si['S1_conf'][i]:>7.4f} | "
        f"{Si['ST'][i]:>6.4f} | {Si['ST_conf'][i]:>7.4f}"
    )

s1_sum = sum(Si["S1"])
print("-" * 68)
print(f"{'Sum S1 (top 2)':<22} | {sum(Si['S1'][:2]):>6.4f} |         |        |")

print("\nExpected values from paper (§7.2):")
paper_s1 = [0.65, 0.25, 0.05, 0.04, 0.01]
for name, exp in zip(problem["names"], paper_s1):
    print(f"  S1({name:<18}) ≈ {exp:.2f}")

print(f"\nNote: small deviations from paper values are expected due to")
print(f"Monte Carlo variance at N={N_SAMPLES}.  Increase N for tighter confidence.")
