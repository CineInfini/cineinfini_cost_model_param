#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrid cost model: AI rendering + human supervision trade-off.

Purpose
-------
Quantify how total production cost scales with (a) the number of video
regeneration attempts per shot and (b) the hours of human supervision.
This extends the parametric model of the paper (§8) by adding a human-
labour component.

Methodology
-----------
Previous version used:
    ai_cost = base_ai_cost * (1 + rejection_rate)          ← INCORRECT

That formula multiplied the TOTAL cost (including TTS, music, etc.) by the
rejection rate, conflating regeneration of all components.  The correct
approach is to use compute_cost_ia() directly with the desired regen_video
value, which internally applies the regeneration factor only to the video
component (the dominant cost).

Corrected formula:
    total = compute_cost_ia(regen_video=V) + human_hours * human_rate_per_hour
"""

import csv
import sys
sys.path.append('..')
from src.cineinfini_cost_model_param import compute_cost_ia

# ─── Parameters ──────────────────────────────────────────────────────

HUMAN_RATE_USD_PER_HOUR = 100.0   # USD/h – film supervisor (industry estimate)
                                   # Range: 75–150 USD/h (below-the-line, 2026)

REGEN_RATES   = [0, 5, 10, 15, 20, 25, 30, 50, 100]  # video attempts per shot
HUMAN_HOURS   = [0, 5, 10, 20, 40, 80, 160]           # supervision hours

BASE_PARAMS = {
    "film_duration_sec": 5400,
    "vfx_duration_sec":  1200,
    "regen_tts":    0.2,
    "regen_music":  0.2,
    "regen_vfx":    0.5,
    "regen_editing":0.2,
}

# ─── Core function ────────────────────────────────────────────────────

def compute_hybrid_cost(
    regen_video: float,
    human_hours: float,
    human_rate: float = HUMAN_RATE_USD_PER_HOUR,
    scenario: str = "medium",
) -> float:
    """
    Return total cost = AI rendering cost + human supervision cost.

    Parameters
    ----------
    regen_video  : video regeneration attempts per shot (integer or float)
    human_hours  : hours of human supervision/QA
    human_rate   : hourly rate for supervision (USD/h)
    scenario     : 'low' | 'medium' | 'high'

    Notes
    -----
    The AI cost is computed via compute_cost_ia, which applies the
    regeneration factor correctly to the video component only.
    At regen_video=25 (paper default), ai_cost ≈ $56,354.
    """
    ai_params = BASE_PARAMS.copy()
    ai_params["regen_video"] = float(regen_video)
    ai_cost    = compute_cost_ia(scenario=scenario, user_params=ai_params)
    human_cost = human_hours * human_rate
    return ai_cost + human_cost

# ─── Reference values ─────────────────────────────────────────────────

ai_zero_regen = compute_cost_ia("medium", {**BASE_PARAMS, "regen_video": 0.0})
ai_default    = compute_cost_ia("medium", {**BASE_PARAMS, "regen_video": 25.0})

print("=" * 65)
print("Hybrid cost model: AI rendering + human supervision")
print("=" * 65)
print(f"\n  AI cost (regen_video = 0,  no retries): {ai_zero_regen:>10,.2f} USD")
print(f"  AI cost (regen_video = 25, default):    {ai_default:>10,.2f} USD")
print(f"  Human rate:                             {HUMAN_RATE_USD_PER_HOUR:>10.2f} USD/h")

# ─── Summary table ────────────────────────────────────────────────────

print(f"\n{'regen_video':>12} | {'human_h':>7} | {'AI cost':>10} | "
      f"{'Human cost':>10} | {'Total':>10}")
print("-" * 65)

rows = []
for r in REGEN_RATES:
    for h in HUMAN_HOURS:
        ai   = compute_cost_ia("medium", {**BASE_PARAMS, "regen_video": r})
        hc   = h * HUMAN_RATE_USD_PER_HOUR
        tot  = ai + hc
        rows.append((r, h, ai, hc, tot))
        print(f"{r:>12} | {h:>7} | {ai:>10,.2f} | {hc:>10,.2f} | {tot:>10,.2f}")

# ─── Export to CSV ────────────────────────────────────────────────────

CSV_PATH = "hybrid_cost_results.csv"
with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["regen_video", "human_hours", "ai_cost_usd",
                     "human_cost_usd", "total_cost_usd"])
    writer.writerows(rows)

print(f"\nResults saved to: {CSV_PATH}")
print(f"Human rate used:  {HUMAN_RATE_USD_PER_HOUR} USD/h  "
      f"(adjust HUMAN_RATE_USD_PER_HOUR for different assumptions)")
