
# CineInfini Parametric Cost Model for AI‑Driven Film Production

**Version:** 7.15  
**Author:** Salah‑Eddine Benbrahim  
**License:** MIT  
**Repository:** [https://github.com/CineInfini/cineinfini_cost_model_param](https://github.com/CineInfini/cineinfini_cost_model_param)  
**Zenodo Archive:** [doi:10.5281/zenodo.xxxxxx] (to be assigned)

This repository contains the complete, reproducible implementation of the parametric cost model presented in the paper *“A Parametric Cost Model for AI‑Driven Film Production: Preliminary Lower‑Bound Estimates and Sensitivity Analysis”* (submitted to ACM AI Letters, 2026).

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
    ├── sobol_analysis.py                   # Sobol sensitivity analysis (production)
    ├── example_elephants_dream.py          # Example: validation on open‑data film
    ├── example_hybrid_cost.py              # Example: AI + human supervision
    ├── example_sobol_sensitivity.py        # Example: Sobol with custom parameters
    └── (any other utility modules)
```

---

## Constants, Variables, and Parameters

All constants are defined in the `INTERVALS` dictionary inside `src/cineinfini_cost_model_param.py`. They are given as **low / medium / high** triples. The user‑adjustable variables are listed in `DEFAULT_PARAMS` and can be overridden via `user_params` in `compute_cost_ia()`.

### Constants (key median values)

| Constant | Value (medium) | Unit | Source |
|----------|---------------|------|--------|
| `SHOT_DURATION_SEC` | 5.0 | seconds | [Follows, 2017](https://stephenfollows.com/p/many-shots-average-movie); [Dark Skies, 2025](https://darkskiesfilm.com/what-influneces-the-length-of-a-shot-in-film/) (accessed 2026-04-09) |
| `DIALOGUE_RATIO` | 0.4 | fraction of film | [Vogel, 2020](https://www.cambridge.org/9781108493086) |
| `SPEECH_RATE_CHAR_PER_SEC` | 10 | characters/second | Industry standard: comfortable reading range for subtitles is 10–15 CPS [Graffiti Studio, 2026](https://graffitistudio.bg/subtitle-reading-speed-psychology/#/) (accessed 2026-04-09) |
| `MUSIC_RATIO` | 0.7 | fraction of film | [Cutting et al., 2012](https://link.springer.com/article/10.3758/s13423-016-1051-4/figures/4) (accessed 2026-04-09) |
| `VIDEO_AI_COST_PER_SEC` | 0.20 | USD/second | 2026 market average for cinema-quality models [ModelsLab, 2026](https://modelslab.com/blog/api/veo-3-1-vs-kling-3-sora-2-ai-video-api-cost-2026) (accessed 2026-04-09); [TeamDay.ai, 2026](https://www.teamday.ai/blog/ai-image-video-api-providers-comparison-2026) (accessed 2026-04-09) |
| `TTS_COST_PER_CHAR` | 0.0003 | USD/character | [ElevenLabs, 2026](https://elevenlabs.io/pricing) / [Magic Hour, 2026a](https://magichour.ai/blog/elevenlabs-pricing) (accessed 2026-04-09) |
| `MUSIC_AI_COST_PER_SEC` | 0.03 | USD/second | [Suno, 2025](https://suno.com/pricing) (accessed 2026-04-09) |
| `VFX_AI_COST_PER_SEC` | 0.20 | USD/second | See `VIDEO_AI_COST_PER_SEC` above; VFX cost assumed equal to video generation cost [ModelsLab, 2026](https://modelslab.com/blog/api/veo-3-1-vs-kling-3-sora-2-ai-video-api-cost-2026) (accessed 2026-04-09) |
| `EDITING_AI_COST_PER_SEC` | 0.065 | USD/second | AI video editing API pricing [WaveSpeedAI, 2026](https://www.wavespeedai.com/models/x-ai/grok-imagine-video/edit-video) (accessed 2026-04-09) |
| `GPU_PRICE_PER_HOUR` | 3.0 | USD/hour (H100 spot) | [Spheron, 2026](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026) (accessed 2026-04-09) |

> **Note:** The full low/medium/high ranges are defined in the code (`INTERVALS`). For the low (optimistic) and high (pessimistic) scenarios, the code automatically selects the first or third value from each triple.

### User‑Adjustable Variables (default values)

| Variable | Default | Range | Unit | Source |
|----------|---------|-------|------|--------|
| `film_duration_sec` | 6840 | 3600–7200 | seconds | Average runtime for major theatrical releases is 114 minutes (6,840 seconds) [IndexBox, 2026](https://www.indexbox.io/blog/film-runtimes-increase-major-releases-now-average-114-minutes/) (accessed 2026-04-09) |
| `vfx_duration_sec` | 1200 | 600–2400 | seconds | Industry VFX shot‑count data (assumed) |
| `regen_video` | 25 | 20–30 | attempts/shot | [AdMonsters, 2025](https://www.admonsters.com/the-truth-about-ai-video-yield) (accessed 2026-04-09) |
| `regen_tts` | 0.2 | 0–1 | factor | [ElevenLabs, 2026](https://elevenlabs.io/pricing) / [Magic Hour, 2026a](https://magichour.ai/blog/elevenlabs-pricing) (accessed 2026-04-09) |
| `regen_music` | 0.2 | 0–1 | factor | [Suno, 2025](https://suno.com/pricing) (accessed 2026-04-09) |
| `regen_vfx` | 0.5 | 0–2 | factor | Assumed |
| `regen_editing` | 0.2 | 0–1 | factor | Assumed |

All variables can be overridden by passing a dictionary to `compute_cost_ia(scenario, user_params=...)`.

---

## Code Files – Descriptions and Links (in execution order)

All scripts are inside the [`/src`](./src) folder. They are listed in the typical order of use: from the core model to the main pipeline, then the production analysis, and finally the example scripts.

### 1. [`src/cineinfini_cost_model_param.py`](./src/cineinfini_cost_model_param.py)

**Core cost model.**  
Contains the constant intervals, default parameters, and the main functions `compute_cost_ia()` and `cost_breakdown()`. This module is imported by all other scripts. It includes a self‑test that runs on import to validate the canonical costs.

**Usage example:**
```python
from src.cineinfini_cost_model_param import compute_cost_ia
cost = compute_cost_ia("medium", {"regen_video": 25})
```

### 2. [`src/workflow.py`](./src/workflow.py)

**Complete paper reproduction pipeline.**  
Executes all steps in order:
1. Validates cost model against paper claims → `validation_report.json`
2. Runs Sobol sensitivity analysis → `sobol_results.json`
3. Generates SVG figures (Figure 2: sensitivity curve, Figure 3: Sobol bar chart)
4. Produces the final Markdown paper → `paper_v7.14.md`
5. Writes a workflow report → `workflow_report.md`

**Run:** `python src/workflow.py`  
**Partial steps:** `python src/workflow.py --step validate` (or `sobol`, `figures`, `paper`)

### 3. [`src/sobol_analysis.py`](./src/sobol_analysis.py)

**Sobol global sensitivity analysis (production version).**  
Performs the variance decomposition reported in Section 7.2 of the paper. Uses `SALib` to sample over five parameters (video cost, regen_video, film duration, VFX duration, regen_vfx) and evaluates the cost model 12,288 times (N=1024). Outputs first‑order (S1) and total‑order (ST) indices with confidence intervals. This script is also called by `workflow.py`.

**Run standalone:** `python src/sobol_analysis.py`  
**Output:** `sobol_results.json`

### 4. [`src/example_elephants_dream.py`](./src/example_elephants_dream.py)

**External validation using an open‑source film (example).**  
Compares the model’s technical rendering cost for the 11‑minute CGI short *Elephants Dream* (2006) with its publicly reported budget of $142,000. Demonstrates that the AI compute cost is orders of magnitude lower than human‑artist production. Good starting point for new users.

**Run:** `python src/example_elephants_dream.py`

### 5. [`src/example_hybrid_cost.py`](./src/example_hybrid_cost.py)

**AI + human supervision trade‑off (example).**  
Extends the model by adding a human labour cost (default $100/hour) to the AI rendering cost. Quantifies total production cost as a function of `regen_video` (0–100 attempts) and human hours (0–160). Exports results to `hybrid_cost_results.csv`. Useful for budget planning.

**Run:** `python src/example_hybrid_cost.py`

### 6. [`src/example_sobol_sensitivity.py`](./src/example_sobol_sensitivity.py)

**Example script for Sobol sensitivity analysis.**  
Similar to `sobol_analysis.py` but with additional comments and customizable parameters. Ideal for learning how to modify the analysis (e.g., change the number of samples, add new parameters). Not used in the paper’s production pipeline.

**Run:** `python src/example_sobol_sensitivity.py`

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

## References (with hyperlinks, author‑year format)

- **AdMonsters, 2025** – AdMonsters. “The truth about AI video yield.” (accessed 2026-04-09) [🔗](https://www.admonsters.com/the-truth-about-ai-video-yield)
- **Cutting et al., 2012** – Cutting, J. E., Brunick, K. L., & Candan, A. “Narrative theory and the dynamics of popular movies.” *Psychonomic Bulletin & Review*. [🔗](https://link.springer.com/article/10.3758/s13423-016-1051-4/figures/4) (accessed 2026-04-09)
- **Dark Skies, 2025** – Dark Skies. “The Art of the Shot: Decoding the Duration of Cinematic Moments.” (accessed 2026-04-09) [🔗](https://darkskiesfilm.com/what-influneces-the-length-of-a-shot-in-film/)
- **ElevenLabs, 2026** – ElevenLabs. Pricing. (accessed 2026-04-09) [🔗](https://elevenlabs.io/pricing)
- **Follows, 2017** – Follows, S. “How many shots are in the average movie?” (accessed 2026-04-09) [🔗](https://stephenfollows.com/p/many-shots-average-movie)
- **Graffiti Studio, 2026** – Graffiti Studio. “Psychology of Subtitle Reading Speed: What Cognitive Load Research Tells Us.” (accessed 2026-04-09) [🔗](https://graffitistudio.bg/subtitle-reading-speed-psychology/#/)
- **IndexBox, 2026** – IndexBox. “Film Runtimes Increase: Major Releases Now Average 114 Minutes.” (accessed 2026-04-09) [🔗](https://www.indexbox.io/blog/film-runtimes-increase-major-releases-now-average-114-minutes/)
- **Magic Hour, 2026a** – Magic Hour. “ElevenLabs Pricing 2026: Plans, Credits and Commercial Rights.” (accessed 2026-04-09) [🔗](https://magichour.ai/blog/elevenlabs-pricing)
- **Magic Hour, 2026b** – Magic Hour. “Kling 3.0 vs Veo 3.1 vs Runway Gen-3: AI Video API Comparison (2026).” (accessed 2026-04-09) [🔗](https://magichour.ai/blog/kling-30-vs-veo-31)
- **ModelsLab, 2026** – ModelsLab. “Veo 3.1 vs Kling 3.0 vs Sora 2: AI Video API Pricing 2026.” (accessed 2026-04-09) [🔗](https://modelslab.com/blog/api/veo-3-1-vs-kling-3-sora-2-ai-video-api-cost-2026)
- **Runway Research, 2025** – Runway Research. Introducing Runway Gen-4. (accessed 2026-04-09) [🔗](https://runwayml.com/research/introducing-runway-gen-4)
- **ShotDirector, 2025** – ShotDirector. “Directorial control in multi‑shot video generation.” ICLR 2025. arXiv:2512.10286. [🔗](https://arxiv.org/abs/2512.10286)
- **Spheron, 2026** – Spheron. GPU Cloud Pricing Comparison 2026. (accessed 2026-04-09) [🔗](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026)
- **Suno, 2025** – Suno AI. Pricing & Music API. (accessed 2026-04-09) [🔗](https://suno.com/pricing)
- **TeamDay.ai, 2026** – TeamDay.ai. “AI API Comparison 2026: FAL.AI vs Replicate vs ...” (accessed 2026-04-09) [🔗](https://www.teamday.ai/blog/ai-image-video-api-providers-comparison-2026)
- **Vogel, 2020** – Vogel, H. L. *Entertainment Industry Economics*, 10th ed. Cambridge University Press, 2020. [🔗](https://www.cambridge.org/9781108493086)
- **WaveSpeedAI, 2026** – WaveSpeedAI. “X-AI Grok Imagine Video Edit | AI Video Editing With Text Prompts.” (accessed 2026-04-09) [🔗](https://www.wavespeedai.com/models/x-ai/grok-imagine-video/edit-video)
- **Wu et al., 2025** – Wu, X., Gao, B., Qiao, Y., Wang, Y., & Chen, X. “CineTrans: Learning to Generate Videos with Cinematic Transitions via Masked Diffusion Models.” arXiv:2508.11484. [🔗](https://arxiv.org/abs/2508.11484)

Full reference list is also included in the generated paper.

---

## License and Citation

This code is released under the MIT License. If you use this model in your research, please cite the accompanying paper (submitted, preprint available upon request).

---

**Contact:** benbrahim.salah.eddine.777@gmail.com  
**Last updated:** April 9, 2026
