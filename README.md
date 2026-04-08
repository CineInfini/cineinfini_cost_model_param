
# CineInfini Parametric Cost Model for AI‑Driven Film Production

**Version:** 7.15  
**Author:** Salah‑Eddine Benbrahim  
**License:** MIT  
**Repository:** [https://github.com/CineInfini/cineinfini_cost_model_param](https://github.com/CineInfi/cineinfini_cost_model_param)  
**Zenodo Archive:** [doi:10.5281/zenodo.xxxxxx] (to be assigned)

This repository contains the complete, reproducible implementation of the parametric cost model presented in the paper *“A Parametric Cost Model for AI‑Driven Film Production: Preliminary Lower‑Bound Estimates and Sensitivity Analysis”* (ACM AI Letters, 2026).

All Python code is located in the [`/src`](./src) directory. Running `python src/workflow.py` regenerates all paper results, figures, and validation reports.

---

## Repository Structure

```
cineinfini_cost_model_param/
├── .gitignore
├── LICENSE
├── README.md
└── src/                                    # All Python source code
    ├── cineinfini_cost_model_param.py      # Core cost model (constants, functions)
    ├── workflow.py                         # Main pipeline (reproduces paper)
    ├── sobol_analysis.py                   # Sobol sensitivity analysis
    ├── example_sobol_sensitivity.py        # Example: Sobol with custom parameters
    ├── example_hybrid_cost.py              # Example: AI + human supervision
    ├── example_elephants_dream.py          # Example: validation on open‑data film
    └── (any other utility modules)
```

---

## Constants, Variables, and Parameters

All constants are defined in the `INTERVALS` dictionary inside `src/cineinfini_cost_model_param.py`. They are given as **low / medium / high** triples. The user‑adjustable variables are listed in `DEFAULT_PARAMS` and can be overridden via `user_params` in `compute_cost_ia()`.

### Constants (key median values)

| Constant | Value (medium) | Unit | Source |
|----------|---------------|------|--------|
| `SHOT_DURATION_SEC` | 5.0 | seconds | [13] |
| `DIALOGUE_RATIO` | 0.4 | fraction of film | [1] |
| `SPEECH_RATE_CHAR_PER_SEC` | 10 | characters/second | [8] |
| `MUSIC_RATIO` | 0.7 | fraction of film | [9] |
| `VIDEO_AI_COST_PER_SEC` | 0.40 | USD/second | [21] |
| `TTS_COST_PER_CHAR` | 0.0003 | USD/character | [8,11] |
| `MUSIC_AI_COST_PER_SEC` | 0.03 | USD/second | [10] |
| `VFX_AI_COST_PER_SEC` | 0.01 | USD/second | [9] |
| `EDITING_AI_COST_PER_SEC` | 0.005 | USD/second | [12] |
| `GPU_PRICE_PER_HOUR` | 3.0 | USD/hour (H100 spot) | [19] |

> **Note:** The full low/medium/high ranges are defined in the code (`INTERVALS`). For the low (optimistic) and high (pessimistic) scenarios, the code automatically selects the first or third value from each triple.

### User‑Adjustable Variables (default values)

| Variable | Default | Range | Unit | Source |
|----------|---------|-------|------|--------|
| `film_duration_sec` | 5400 | 3600–7200 | seconds | creative decision |
| `vfx_duration_sec` | 1200 | 600–2400 | seconds | creative decision |
| `regen_video` | 25 | 20–30 | attempts/shot | [7] |
| `regen_tts` | 0.2 | 0–1 | factor | [8,11] |
| `regen_music` | 0.2 | 0–1 | factor | [10] |
| `regen_vfx` | 0.5 | 0–2 | factor | [9] |
| `regen_editing` | 0.2 | 0–1 | factor | [12] |

All variables can be overridden by passing a dictionary to `compute_cost_ia(scenario, user_params=...)`.

---

## Code Files – Descriptions and Links

All scripts are inside the [`/src`](./src) folder.

### 1. [`src/cineinfini_cost_model_param.py`](./src/cineinfini_cost_model_param.py)

**Core cost model.** Contains:
- `INTERVALS` dictionary – all constants (low/medium/high)
- `DEFAULT_PARAMS` – default user variables
- `compute_cost_ia(scenario, user_params)` – returns technical rendering cost
- `cost_breakdown(scenario, user_params)` – returns component costs
- Self‑test that runs on import (validates canonical costs)

**Usage example:**
```python
from src.cineinfini_cost_model_param import compute_cost_ia
cost = compute_cost_ia("medium", {"regen_video": 25})
```

### 2. [`src/workflow.py`](./src/workflow.py)

**Complete paper reproduction pipeline.**  
Executes all steps:
1. Validates cost model against paper claims (validation_report.json)
2. Runs Sobol analysis (sobol_results.json)
3. Generates SVG figures (figure2_sensitivity.svg, figure3_sobol.svg)
4. Produces the final Markdown paper (paper_v7.14.md)
5. Writes a workflow report (workflow_report.md)

**Run:** `python src/workflow.py`  
**Partial steps:** `python src/workflow.py --step validate` (or `sobol`, `figures`, `paper`)

### 3. [`src/sobol_analysis.py`](./src/sobol_analysis.py)

**Sobol global sensitivity analysis (production version).**  
Performs the variance decomposition reported in Section 7.2. Uses `SALib` to sample over five parameters (video cost, regen_video, film duration, VFX duration, regen_vfx) and evaluates the cost model 12,288 times (N=1024). Outputs first‑order (S1) and total‑order (ST) indices with confidence intervals.

**Run standalone:** `python src/sobol_analysis.py`  
**Output:** `sobol_results.json` (also generated by `workflow.py`)

### 4. [`src/example_sobol_sensitivity.py`](./src/example_sobol_sensitivity.py)

**Example script for Sobol sensitivity analysis.**  
Similar to `sobol_analysis.py` but with additional comments and customizable parameters. Useful for learning how to run sensitivity analysis on the cost model.

**Run:** `python src/example_sobol_sensitivity.py`

### 5. [`src/example_hybrid_cost.py`](./src/example_hybrid_cost.py)

**AI + human supervision trade‑off (example).**  
Extends the model by adding a human labour cost (default $100/hour) to the AI rendering cost. Quantifies total production cost as a function of `regen_video` (0–100 attempts) and human hours (0–160). Exports results to `hybrid_cost_results.csv`.

**Run:** `python src/example_hybrid_cost.py`

### 6. [`src/example_elephants_dream.py`](./src/example_elephants_dream.py)

**External validation using an open‑source film (example).**  
Compares the model’s technical rendering cost for the 11‑minute CGI short *Elephants Dream* (2006) with its publicly reported budget of $142,000. Demonstrates that the AI compute cost is orders of magnitude lower than human‑artist production.

**Run:** `python src/example_elephants_dream.py`

---

## Reproducing the Paper Results

After cloning the repository, install dependencies:

```bash
pip install numpy SALib
```

Then run the full pipeline:

```bash
python src/workflow.py
```

All outputs appear in the `outputs/` folder (created automatically). The generated `paper_v7.14.md` is a complete version of the manuscript with all numerical values automatically cross‑checked against the code.

---

## References (as numbered in the paper)

[1] Vogel, H. L. *Entertainment Industry Economics*, 10th ed. Cambridge Univ. Press, 2020.  
[7] AdMonsters. The truth about AI video yield. 2025.  
[8] ElevenLabs. Pricing. 2026.  
[9] BBC. Netflix cuts VFX costs by 90% using AI. 2025.  
[10] CometAPI. Suno AI pricing. 2025.  
[11] bigvu.tv. ElevenLabs Pricing 2026.  
[12] Runway Research. Gen-4 Turbo. 2025.  
[13] Follows, S. How many shots are in the average movie? 2017.  
[19] Spheron. GPU Cloud Pricing Comparison 2026.  
[21] ModelsLab. Veo 3.1 vs Kling 3.0 vs Sora 2: AI Video API Pricing 2026.  
[22] Wu, X. et al. CineTrans. arXiv:2508.11484, 2025.  
[23] ShotDirector. ICLR, 2025. arXiv:2512.10286.

Full reference list is included in the generated paper.

---

## License and Citation

This code is released under the MIT License. If you use this model in your own research, please cite the accompanying paper:

> Salah‑Eddine Benbrahim. *A Parametric Cost Model for AI‑Driven Film Production: Preliminary Lower‑Bound Estimates and Sensitivity Analysis.* ACM AI Letters, 2026.

---

**Contact:** benbrahim.salah.eddine.777@gmail.com  
**Last updated:** April 8, 2026
