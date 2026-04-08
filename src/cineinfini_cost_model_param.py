#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineInfini Parametric Cost Model
Author:     Salah-Eddine Benbrahim
License:    MIT
Version:    7.14  (aligned with paper v7.14 – Final for ACM AI Letters)
Repository: https://github.com/CineInfini/master-reference/tree/main/cineinfini_cost_model_param

This module provides a parametric cost model for AI-generated films.

Fixes vs v7.12
--------------
[Fix 1] regen_video removed from DEFAULT_PARAMS so that each scenario
        correctly uses INTERVALS values (low=20, medium=25, high=30).
        User can still override via user_params={"regen_video": N}.
[Fix 2] VFX_AI_COST_PER_SEC medium corrected from 0.05 → 0.01 USD/s
        to match paper Section 4.2 and Reference [9].
[Fix 3] Added "video_ia_par_sec" support in user_params to allow
        external overriding of VIDEO_AI_COST_PER_SEC (required for
        Sobol sensitivity analysis to vary video unit cost).
[Fix 4] Version string updated to 7.14.

Expected output (default parameters, all scenarios):
    {'low': 34084.92, 'medium': 56354.26, 'high': 84223.44}

Note: the paper reports slightly rounded values (34,220 / 56,360 / 83,900)
due to minor parameter adjustments between v7.12 and v7.14. All values
are within ±0.4% of the paper figures.
"""

from typing import Dict, Optional, Union

# ─────────────────────────────────────────────────────────────────────
# 1. Configuration defaults
# ─────────────────────────────────────────────────────────────────────

CONFIG = {
    "default_scenario": "medium",   # 'low' | 'medium' | 'high' | 'all'
    "default_params":   None,
}

# ─────────────────────────────────────────────────────────────────────
# 2. Intervals for all constants  (low, medium, high)
# ─────────────────────────────────────────────────────────────────────

INTERVALS: Dict[str, tuple] = {
    # ── Film structure
    "SHOT_DURATION_SEC":        (4.0,   5.0,   8.0),    # s/shot            [13]
    "DIALOGUE_RATIO":           (0.3,   0.4,   0.5),    # fraction          [1]
    "SPEECH_RATE_CHAR_PER_SEC": (8,     10,    12),      # char/s            [8]
    "MUSIC_RATIO":              (0.6,   0.7,   0.8),    # fraction          [9]

    # ── AI API costs  (USD per unit, 2026 pricing)
    "VIDEO_AI_COST_PER_SEC":    (0.30,  0.40,  0.50),   # USD/s             [21]
    "TTS_COST_PER_CHAR":        (0.0001,0.0003,0.0005), # USD/char          [8,11]
    "MUSIC_AI_COST_PER_SEC":    (0.01,  0.03,  0.05),   # USD/s             [10]
    # [Fix 2] medium was 0.05 → corrected to 0.01 (paper §4.2, Ref [9])
    "VFX_AI_COST_PER_SEC":      (0.01,  0.01,  0.10),   # USD/s             [9]
    "EDITING_AI_COST_PER_SEC":  (0.001, 0.005, 0.01),   # USD/s             [12]

    # ── Infrastructure
    "GPU_SEC_PER_VIDEO_SEC":    (60,    120,   600),     # GPU-s/s (reference)
    "GPU_PRICE_PER_HOUR":       (1.5,   3.0,   5.0),    # USD/h             [19]
    "TRADITIONAL_VFX_COST_PER_SEC": (10_000, 50_000, 100_000),  # USD/s

    # ── Human costs (traditional – kept for hybrid-cost comparisons)
    "ALIST_ACTOR_DAY":          (500_000,   1_000_000, 2_000_000),
    "EXTRA_NON_UNION_DAY":      (300,       500,       1_000),
    "EXTRA_UNION_DAY":          (2_500,     2_500,     2_500),
    "SCREENWRITER_FLAT":        (100_000,   250_000,   500_000),
    "DIRECTOR_FLAT":            (500_000, 2_000_000, 10_000_000),
    "CREW_DAY":                 (500,       800,       1_500),

    # ── Regeneration: video attempts per shot
    # [Fix 1] This value is now used as default when regen_video is NOT
    #         in user_params. Previous code always used 25 regardless of scenario.
    "REGENERATION_RATE_VIDEO":  (20.0, 25.0, 30.0),     # dimensionless     [7]
}

# ─────────────────────────────────────────────────────────────────────
# 3. Default film parameters  (user-adjustable via user_params)
# ─────────────────────────────────────────────────────────────────────

DEFAULT_PARAMS: Dict[str, object] = {
    "film_duration_sec": 5400,      # 90 minutes
    "vfx_duration_sec":  1200,      # 20 minutes
    "currency":          "USD",
    # [Fix 1] regen_video intentionally omitted here so that
    #         INTERVALS["REGENERATION_RATE_VIDEO"] is used per scenario.
    #         Override: user_params={"regen_video": 25}
    "regen_tts":    0.2,            # TTS regeneration factor   [8,11]
    "regen_music":  0.2,            # music regeneration factor [10]
    "regen_vfx":    0.5,            # VFX regeneration factor   [9]
    "regen_editing":0.2,            # editing regeneration factor [12]
}

# ─────────────────────────────────────────────────────────────────────
# 4. Internal helpers
# ─────────────────────────────────────────────────────────────────────

SCENARIO_TO_INDEX = {"low": 0, "medium": 1, "high": 2}


def _constants_for_scenario(scenario: str) -> Dict[str, float]:
    """Return a flat dict of constants for the given scenario."""
    idx = SCENARIO_TO_INDEX[scenario]
    return {key: values[idx] for key, values in INTERVALS.items()}


def _merge_params(user_params: Optional[Dict]) -> Dict:
    """Merge user overrides onto DEFAULT_PARAMS."""
    params = DEFAULT_PARAMS.copy()
    if user_params:
        params.update(user_params)
    return params

# ─────────────────────────────────────────────────────────────────────
# 5. Main cost function – mode AI
# ─────────────────────────────────────────────────────────────────────

def compute_cost_ia(
    scenario: str = CONFIG["default_scenario"],
    user_params: Optional[Dict] = CONFIG["default_params"],
) -> Union[float, Dict[str, float]]:
    """
    Compute the technical production cost for a fully AI-generated film.

    Parameters
    ----------
    scenario : {'low', 'medium', 'high', 'all'}
        Cost scenario.
        - 'low'    : optimistic (lowest constant values, regen_video=20)
        - 'medium' : median values (regen_video=25)
        - 'high'   : pessimistic (highest constant values, regen_video=30)
        - 'all'    : returns dict with all three scenarios

    user_params : dict, optional
        Override any default parameter. Recognised keys:
          film_duration_sec  – total film duration (seconds)
          vfx_duration_sec   – VFX-heavy portion (seconds)
          regen_video        – video regeneration attempts per shot
          regen_tts          – TTS regeneration factor (0–1)
          regen_music        – music regeneration factor (0–1)
          regen_vfx          – VFX regeneration factor (0–2)
          regen_editing      – editing regeneration factor (0–1)
          video_ia_par_sec   – override VIDEO_AI_COST_PER_SEC (USD/s)
                               [Fix 3: required for Sobol sensitivity analysis]

    Returns
    -------
    float or dict
        Total technical rendering cost in USD.
        If scenario == 'all', returns {'low': float, 'medium': float, 'high': float}.

    Notes
    -----
    Cost formula:
        C_IA = N_shots * L_shot * C_video * (1 + V_regen_video)
             + T_dial  * R_char * C_TTS   * (1 + V_regen_tts)
             + T_music * C_music           * (1 + V_regen_music)
             + T_vfx   * C_vfx             * (1 + V_regen_vfx)
             + T_film  * C_edit            * (1 + V_regen_editing)

    where N_shots = film_duration_sec / SHOT_DURATION_SEC.

    Excludes: marketing, distribution, music licensing, human supervision.
    """
    if scenario == "all":
        return {s: compute_cost_ia(s, user_params) for s in ("low", "medium", "high")}

    if scenario not in SCENARIO_TO_INDEX:
        raise ValueError(f"scenario must be 'low', 'medium', 'high', or 'all'; got {scenario!r}")

    const  = _constants_for_scenario(scenario)
    params = _merge_params(user_params)

    film_duration = float(params["film_duration_sec"])
    vfx_duration  = float(params["vfx_duration_sec"])

    # ── Regeneration rates ────────────────────────────────────────────
    # [Fix 1] Use scenario constant when user has not explicitly set regen_video.
    regen_video   = float(params.get("regen_video",   const["REGENERATION_RATE_VIDEO"]))
    regen_tts     = float(params.get("regen_tts",     0.2))
    regen_music   = float(params.get("regen_music",   0.2))
    regen_vfx     = float(params.get("regen_vfx",     0.5))
    regen_editing = float(params.get("regen_editing", 0.2))

    # ── Video unit cost override ──────────────────────────────────────
    # [Fix 3] Allow Sobol analysis to vary VIDEO_AI_COST_PER_SEC via
    #         user_params["video_ia_par_sec"].
    video_unit_cost = float(
        params.get("video_ia_par_sec", const["VIDEO_AI_COST_PER_SEC"])
    )

    # ── Derived quantities ────────────────────────────────────────────
    shot_duration = const["SHOT_DURATION_SEC"]
    n_shots       = film_duration / shot_duration

    # ── Cost components ───────────────────────────────────────────────
    # Video generation  (dominant: ~99.7% at default params)
    video_cost = n_shots * shot_duration * video_unit_cost * (1.0 + regen_video)

    # Text-to-speech (dialogues)
    dialogue_sec = film_duration * const["DIALOGUE_RATIO"]
    tts_cost = (
        dialogue_sec
        * const["SPEECH_RATE_CHAR_PER_SEC"]
        * const["TTS_COST_PER_CHAR"]
        * (1.0 + regen_tts)
    )

    # Music & SFX
    music_sec  = film_duration * const["MUSIC_RATIO"]
    music_cost = music_sec * const["MUSIC_AI_COST_PER_SEC"] * (1.0 + regen_music)

    # VFX
    vfx_cost = vfx_duration * const["VFX_AI_COST_PER_SEC"] * (1.0 + regen_vfx)

    # AI editing
    editing_cost = film_duration * const["EDITING_AI_COST_PER_SEC"] * (1.0 + regen_editing)

    return video_cost + tts_cost + music_cost + vfx_cost + editing_cost


# ─────────────────────────────────────────────────────────────────────
# 6. Convenience: cost breakdown (for reporting / paper tables)
# ─────────────────────────────────────────────────────────────────────

def cost_breakdown(
    scenario: str = "medium",
    user_params: Optional[Dict] = None,
) -> Dict[str, float]:
    """
    Return individual cost components and totals.

    Returns
    -------
    dict with keys: video, tts, music, vfx, editing, total, n_shots
    """
    const  = _constants_for_scenario(scenario)
    params = _merge_params(user_params)

    film_duration = float(params["film_duration_sec"])
    vfx_duration  = float(params["vfx_duration_sec"])

    regen_video   = float(params.get("regen_video",   const["REGENERATION_RATE_VIDEO"]))
    regen_tts     = float(params.get("regen_tts",     0.2))
    regen_music   = float(params.get("regen_music",   0.2))
    regen_vfx     = float(params.get("regen_vfx",     0.5))
    regen_editing = float(params.get("regen_editing", 0.2))
    video_unit    = float(params.get("video_ia_par_sec", const["VIDEO_AI_COST_PER_SEC"]))

    shot_duration = const["SHOT_DURATION_SEC"]
    n_shots       = film_duration / shot_duration

    video   = n_shots * shot_duration * video_unit * (1.0 + regen_video)
    tts     = film_duration * const["DIALOGUE_RATIO"] * const["SPEECH_RATE_CHAR_PER_SEC"] * const["TTS_COST_PER_CHAR"] * (1.0 + regen_tts)
    music   = film_duration * const["MUSIC_RATIO"] * const["MUSIC_AI_COST_PER_SEC"] * (1.0 + regen_music)
    vfx     = vfx_duration  * const["VFX_AI_COST_PER_SEC"] * (1.0 + regen_vfx)
    editing = film_duration * const["EDITING_AI_COST_PER_SEC"] * (1.0 + regen_editing)
    total   = video + tts + music + vfx + editing

    return {
        "video":   round(video,   2),
        "tts":     round(tts,     2),
        "music":   round(music,   2),
        "vfx":     round(vfx,     2),
        "editing": round(editing, 2),
        "total":   round(total,   2),
        "n_shots": n_shots,
    }


# ─────────────────────────────────────────────────────────────────────
# 7. Self-test  (run once at import to catch regressions)
# ─────────────────────────────────────────────────────────────────────

def _run_self_test() -> None:
    """Assert expected outputs for the three canonical scenarios."""
    expected = {"low": 34084.92, "medium": 56354.26, "high": 84223.44}
    results  = compute_cost_ia("all")
    for sc, exp in expected.items():
        got = results[sc]
        assert abs(got - exp) < 1.0, (
            f"Self-test FAILED for scenario '{sc}': got {got:.2f}, expected {exp:.2f}. "
            "Check INTERVALS and DEFAULT_PARAMS for accidental edits."
        )


_run_self_test()


# ─────────────────────────────────────────────────────────────────────
# 8. CLI entry point
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("CineInfini Parametric Cost Model  –  Version 7.14")
    print("=" * 52)
    print("\nTechnical rendering cost for a 90-min AI film:\n")

    results = compute_cost_ia(scenario="all")
    for sc, cost in results.items():
        print(f"  {sc.capitalize():6s}: {cost:>10,.2f} {DEFAULT_PARAMS['currency']}")

    print("\nCost breakdown (median scenario):\n")
    bd = cost_breakdown("medium")
    for key in ("video", "tts", "music", "vfx", "editing"):
        pct = bd[key] / bd["total"] * 100
        print(f"  {key:8s}: {bd[key]:>10,.2f} USD  ({pct:.2f}%)")
    print(f"  {'n_shots':8s}: {bd['n_shots']:.0f}")
    print(f"  {'TOTAL':8s}: {bd['total']:>10,.2f} USD")

    print("\nSensitivity – video regeneration rate (medium scenario):\n")
    for regen in [20, 25, 30]:
        cost = compute_cost_ia("medium", {"regen_video": regen})
        print(f"  regen_video = {regen:2d}  →  {cost:>10,.2f} USD")
