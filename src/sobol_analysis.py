#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sobol_analysis.py  —  CineInfini v7.14
Sobol global sensitivity analysis using the parametric cost model.

Usage (standalone):
    python sobol_analysis.py

Usage (as module):
    from sobol_analysis import run_sobol_analysis
    results = run_sobol_analysis(N=1024)

Design notes
------------
- film_duration and shot_duration are NOT constants: they vary across
  productions.  shot_duration analytically cancels in the video-cost
  formula  (n_shots × L_shot × C_video = film_dur × C_video),  so
  only film_duration appears as a Sobol variable.
- The 5-variable problem matches the bounds stated in paper §7.2.
- N=1024 → 12,288 evaluations  (paper).  N=2048 → 20,480  (tighter CI).
"""

import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional

# ── locate the cost model ─────────────────────────────────────────────
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parent))   # works whether run from root or src/
from src.cineinfini_cost_model_param import compute_cost_ia

# ── SALib version-safe import ─────────────────────────────────────────
try:
    import importlib.metadata
    _salib_ver = importlib.metadata.version("SALib")
    _salib_major = int(_salib_ver.split(".")[0])
except Exception:
    _salib_major = 1

if _salib_major >= 2:
    from SALib.sample.sobol  import sample  as _sample
    from SALib.analyze.sobol import analyze as _analyze
else:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from SALib.sample import saltelli as _salt
        from SALib.analyze import sobol   as _sob
    _sample  = _salt.sample
    _analyze = _sob.analyze

# ─────────────────────────────────────────────────────────────────────
# Problem definition
# ─────────────────────────────────────────────────────────────────────

#: Default Sobol problem matching paper §7.2.
#: film_duration is a *variable* (different films have different lengths).
#: shot_duration cancels analytically in the cost formula and is omitted.
SOBOL_PROBLEM: Dict = {
    "num_vars": 5,
    "names": [
        "video_cost",       # C_video  — API unit cost (USD/s)   [21]
        "regen_video",      # V_regen  — attempts per shot        [7]
        "film_duration",    # V_dur    — total film length (s)
        "vfx_duration",     # V_vfx    — VFX-heavy portion (s)
        "regen_vfx",        # V_rvfx   — VFX regen factor
    ],
    "bounds": [
        [0.30, 0.50],       # USD/s  (paper §7.2)
        [20.0, 30.0],       # attempts/shot
        [3_600, 7_200],     # 60–120 min  (variable across productions)
        [600,   2_400],     # 10–40 min
        [0.2,   1.0],
    ],
}

#: Fixed defaults for parameters NOT included in the Sobol problem.
_FIXED = {
    "regen_tts":    0.2,
    "regen_music":  0.2,
    "regen_editing":0.2,
    "vfx_duration_sec": 1200,   # overridden when vfx_duration is sampled
}


# ─────────────────────────────────────────────────────────────────────
# Core function
# ─────────────────────────────────────────────────────────────────────

def run_sobol_analysis(
    N: int = 1024,
    seed: int = 42,
    scenario: str = "medium",
    problem: Optional[Dict] = None,
    verbose: bool = True,
) -> Dict:
    """
    Run a Sobol global sensitivity analysis on the CineInfini cost model.

    Parameters
    ----------
    N        : Saltelli base sample size.  Total evaluations = N*(2*k+2).
               N=1024 → 12,288 evals (paper §7.2).
               N=2048 → 20,480 evals (tighter confidence intervals).
    seed     : Random seed for reproducibility (paper uses seed=42).
    scenario : Cost scenario passed to compute_cost_ia ('low'|'medium'|'high').
    problem  : SALib problem dict.  Defaults to SOBOL_PROBLEM.
    verbose  : Print progress and results table.

    Returns
    -------
    dict with keys:
        S1, S1_conf, ST, ST_conf  — numpy arrays (length num_vars)
        names                     — parameter names
        cost_stats                — dict (mean, std, min, max)
        config                    — dict (N, seed, n_evaluations, scenario)
    """
    if problem is None:
        problem = SOBOL_PROBLEM

    n_evals = N * (2 * problem["num_vars"] + 2)
    if verbose:
        print(f"Generating {n_evals:,} Saltelli samples  "
              f"(N={N}, k={problem['num_vars']}, seed={seed}) …")

    np.random.seed(seed)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        pv = _sample(problem, N, calc_second_order=False)

    if verbose:
        print(f"Running {len(pv):,} model evaluations …", flush=True)

    costs = np.empty(len(pv))
    for i, v in enumerate(pv):
        user_p = {**_FIXED}
        for j, name in enumerate(problem["names"]):
            _KEY = {
                "video_cost":    "video_ia_par_sec",
                "regen_video":   "regen_video",
                "film_duration": "film_duration_sec",
                "vfx_duration":  "vfx_duration_sec",
                "regen_vfx":     "regen_vfx",
            }
            user_p[_KEY[name]] = float(v[j])
        costs[i] = compute_cost_ia(scenario=scenario, user_params=user_p)

    if verbose:
        print(f"Cost range: [{costs.min():,.0f}, {costs.max():,.0f}] USD  "
              f"(mean={costs.mean():,.0f}, std={costs.std():,.0f})")
        print("Computing Sobol indices …")

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        Si = _analyze(problem, costs, calc_second_order=False,
                      print_to_console=False)

    results = {
        "S1":       Si["S1"],
        "S1_conf":  Si["S1_conf"],
        "ST":       Si["ST"],
        "ST_conf":  Si["ST_conf"],
        "names":    problem["names"],
        "cost_stats": {
            "mean": float(costs.mean()),
            "std":  float(costs.std()),
            "min":  float(costs.min()),
            "max":  float(costs.max()),
        },
        "config": {
            "N":             N,
            "seed":          seed,
            "n_evaluations": n_evals,
            "scenario":      scenario,
        },
    }

    if verbose:
        _print_results(results)

    return results


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _print_results(r: Dict) -> None:
    """Pretty-print Sobol results."""
    print(f"\n{'═'*72}")
    print(f"Sobol Sensitivity Indices  —  scenario={r['config']['scenario']}, "
          f"N={r['config']['N']}, seed={r['config']['seed']}")
    print(f"{'═'*72}")
    print(f"{'Parameter':<22}  {'S1':>6}  {'±conf':>6}  {'ST':>6}  {'±conf':>6}")
    print(f"{'─'*56}")
    for i, name in enumerate(r["names"]):
        print(f"{name:<22}  {r['S1'][i]:6.3f}  "
              f"±{r['S1_conf'][i]:.3f}  "
              f"{r['ST'][i]:6.3f}  "
              f"±{r['ST_conf'][i]:.3f}")
    print(f"{'─'*56}")
    print(f"{'Sum S1':<22}  {sum(r['S1']):6.3f}")


def save_results(r: Dict, path: str = "sobol_results.json") -> None:
    """Save results to JSON (arrays serialised as lists)."""
    out = {k: (v.tolist() if hasattr(v, "tolist") else v)
           for k, v in r.items()}
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Results saved → {path}")


# ─────────────────────────────────────────────────────────────────────
# CLI entry-point
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_sobol_analysis(N=1024, seed=42, scenario="medium")
    save_results(results, path=str(_HERE / "sobol_results.json"))
