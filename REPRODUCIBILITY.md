# Reproducibility

This document records how the computational results in this repository were
validated, what reproduces, and what cannot yet be reproduced.

Last validated: 2026-09-30 on macOS (Apple silicon), uv 0.7.8, R 4.6.1,
Quarto 1.8, TeX Live 2025.

## How to validate

```bash
# 1. download the Zenodo data into zenodo/ (see zenodo/README.md)
make setup        # install every locked environment
make validate     # lock checks + the three checks below
```

| Target | What it does | Needs |
|---|---|---|
| `make check-locks` | `uv lock --check` in each Python folder, `renv::status()` for R | uv, R |
| `make validate-feature-extraction` | Runs `1_meta.py`, `2_xml2md.py` and `5_a_meta_csv.ipynb` on the 5 sample XMLs and compares 14 metadata fields with the published rows | `sample_xml_data`, `analysis_dataset` |
| `make validate-choice-models` | Re-estimates the 4 Biogeme models from scratch and compares them with `analysis/choice-models/Results/` | `analysis_dataset` |
| `make validate-descriptive` | Re-renders `rrmeasures-paper.qmd` and compares the `.tex` and figure sources with the committed copies | `analysis_dataset`, R, Quarto, LuaLaTeX |

All checks run in a temporary copy of the component, so they never modify
the repository.

## Environments

Every component has its own locked environment.

| Component | Tool | Runtime | Pinned to |
|---|---|---|---|
| `full-text-extraction/` | uv | CPython 3.10.15 | Versions shared with feature-extraction's original conda env |
| `feature-extraction/` | uv | CPython 3.10.15 | The original conda env (`RR-measure`); 135/135 overlapping packages identical |
| `analysis/choice-models/` | uv | CPython 3.11.12 | The former `Pipfile.lock`; 39/39 packages identical |
| `analysis/descriptive-statistics-and-bivariate-tests/` | renv | R 4.6.1 | Posit Package Manager CRAN snapshot 2026-07-01 |

Notes:

- `feature-extraction` overrides numpy to 1.26.4. spaCy 3.8.7's dependency
  thinc 8.3.6 declares `numpy>=2`, but gensim 4.3.3 needs `numpy<2`, and the
  original environment ran this combination. As a result, `uv pip check`
  reports that conflict. The pip fallback (`requirements.txt`) must be installed
  with `--no-deps`.
- Python 3.11.2 (the original choice-models version) is not available as a
  uv-managed build; 3.11.12 is used. Results are bitwise identical.
- The uv-managed CPython is used on purpose (`python-preference = "managed"`).
  The python.org macOS build ships without CA certificates, which makes
  `nltk.download()` fail silently.
- The Posit deployment lockfile of the Shiny app
  (`data_explorer/.posit/publish/deployments/renv.lock`, R 4.5.2) is kept for
  deployment only. It is not the reproduction environment.

## Results

### Reproduced

| Result | Outcome |
|---|---|
| Choice models: 4 Biogeme models (N = 10,480): estimates, standard errors, robust covariances, gradients, log-likelihoods, ρ² | Bitwise identical to the committed `Results/*.pickle` |
| Choice models: notebook LaTeX tables and ρ̄² values | 48 of 49 cell outputs identical. The exception, `papers.info()`, shows the committed outputs came from pandas 2.x; re-estimating with pandas 2.2.3 is also bitwise identical |
| Manuscript `rrmeasures-paper.tex`: all tables, inline numbers and test statistics | Byte-identical after `quarto render` |
| Manuscript figures `fig-citations-1/2` | Identical apart from the tikzDevice creation timestamp |
| Shiny app `data_explorer/` | Starts and serves HTTP 200. Headless `shiny::testServer` checks pass for numeric variables and for binary categorical variables. `paper_data.rds` has the same 10,480 × 85 shape and DOI set as the manuscript's `papers` object; two columns are character in the committed file and factor when regenerated |
| Feature extraction: metadata of the 5 sample papers (steps 1, 2, 5_a) | 70/70 fields identical to the published rows |
| Feature extraction: regions and continents (step 6) and LDA topic ids (step 8), 5 sample papers | Identical to the published rows (LDA label strings differ; see below) |
| Analysis sample size | Both analyses independently arrive at N = 10,480, with 528 papers with public code |

### Not yet validated (require API keys)

These steps call paid or keyed APIs. They are also not deterministic: LLM
outputs vary between runs, and citation counts drift over time.

| Step | Key | Where to put it |
|---|---|---|
| `feature-extraction/3_code-p1-gemini.py`, `4_a_data-p1-gemini.py` (both runs), then `5_b`, `5_c` on real outputs | Gemini | `feature-extraction/config.json`: `{"GOOGLE_API_KEY": "..."}` |
| `feature-extraction/7_get_citations.ipynb` | Elsevier (Scopus) | `feature-extraction/.env`: `ELSEVIER_API=...` |
| `full-text-extraction/TR-doi.ipynb`, `TR.ipynb` | Elsevier (full text, needs an institutional entitlement) | `full-text-extraction/config.yaml` |

The Gemini model hard-coded in steps 3 and 4
(`gemini-2.5-flash-lite-preview-06-17`) is a dated preview and may no longer
be served. In that case the LLM features cannot be regenerated exactly.

### Cannot be reproduced from this repository

1. **The step that builds the analysis dataset is missing.** The pipeline ends
   at `feature-extraction/fla_csvs/lda.csv` (44 columns). No code in the
   repository produces:
   - 42 of the 77 columns of `papers_cleaned_with_new_columns.csv`, e.g.
     `open_science_score_0_5`, `region_normalized`, `uses_data`,
     `paper_age_years`, `n_code_links`, and the `journal_*` / `papers_*_share`
     columns;
   - the 3 extra columns of `papers_cleaned_p2.csv`;
   - `datasets_aggregated.csv` and `paper_dataset_mapping.csv`.

   Both analyses read the published CSV directly, so the analyses reproduce,
   but the dataset itself cannot be rebuilt from the pipeline.
2. **The manual validation has no code.** Nothing reads
   `manual-validation-dataset/h1_96.csv` or `h2_96.csv`, and the manuscript
   sources report no validation metrics to compare against. Recomputed for
   reference, on the 96 papers labelled by both annotators:

   | Field | Inter-annotator κ | LLM accuracy vs. consensus |
   |---|---|---|
   | is_quantitative_study | 0.476 | 0.977 |
   | is_data_used | 0.452 | 0.907 |
   | is_code_publicly_available | 0.753 | 1.000 |
   | is_simulation_study | 0.432 | 0.899 |
   | is_data_cited | 0.667 | 0.817 |
   | is_data_repository_available | 0.333 | 0.989 |

   `h1_96.csv` has 113 rows (112 papers plus one duplicate DOI written as
   `10.1016_j.tra.2018.10.032`); 96 papers overlap with `h2_96.csv`.

## Issues found

These do not change the reproduced results above, but they need a decision
from the authors because they touch scientific code, manuscript text or the
published data.

| Severity | Where | Issue |
|---|---|---|
| High | `feature-extraction/6_clean_regions.ipynb` | Fuzzy matching maps `UK` to `Ukraine` (score 90 ≥ 80). 232 published rows have `clean_primary_region = Ukraine`. The continent (Europe) is still correct |
| High | `feature-extraction/8_create_lda.ipynb` | The final cell writes short topic labels (`Mobility policy`, …), but the published data uses the longer labels (`Social & Policy Aspects of Mobility`, …); topic ids agree. Topics are also assigned by row position rather than by DOI |
| High | `rrmeasures-paper.qmd` ≈ line 146 | Data-availability percentages in the prose are attached to the wrong categories. Correct shares: no repository or citation 68.7%, repository only 2.5%, cited only 27.7%, both 1.0% (counts 7,202 / 264 / 2,906 / 108) |
| Medium | `rrmeasures-paper.qmd` ≈ line 144 | `round(n_code / nrow(papers), 0)` renders "a little more than 0 %"; the value is 5.04% |
| Medium | `zenodo/analysis_dataset/datasets_aggregated.csv` | 3 of 405 dataset URLs have the digit `1` replaced by `True` (not used by any analysis) |
| Medium | `zenodo/analysis_dataset/papers_cleaned_with_new_columns.csv` | `has_code_any` is `True` for all 10,724 rows (not used by any analysis) |
| Medium | `feature-extraction/7_get_citations.ipynb` | Without a key or on request errors it silently writes `NaN` citation counts and exits successfully |
| Medium | `feature-extraction/4_a_data-p1-gemini.py` | On a JSON decode error it writes into a non-existent `errors/` folder and aborts the batch |
| Medium | `feature-extraction/8_create_lda.ipynb` | A missing LLM column makes every file fail inside a broad `try/except`; the notebook then writes `NaN` topics and exits successfully |
| Medium | `full-text-extraction/TR.ipynb` | Any non-200 response raises `UnboundLocalError` and stops the whole journal |
| Medium | `full-text-extraction/TR-doi.ipynb` | No retry or rate limiting; one HTTP 429 silently truncates a volume's DOI list |
| Medium | `data_explorer/server.R` | With the outcome "data availability" (`data_multi`, 4 levels), every categorical comparison fails with `'x' must have 2 columns`: `pairwise_prop_test()` needs a 2-column table. It also fails for single-level variables such as `article_subtype` |
| Medium | `data_explorer/server.R` | All columns are offered as comparison variables, including high-cardinality ones (`doi`, `primary_institution`, dates, `code_link`, …). Selecting one runs a pairwise test over thousands of groups and the app stops responding |
| Low | `feature-extraction/5_a` … `8` | Index columns accumulate (`Unnamed: 0` … `0.4`); row order depends on the filesystem's `listdir` order |
| Low | `analysis/choice-models/Notebook/ChoiceModels.ipynb` | Markdown says the notebook reads `papers_cleaned.csv`; it reads `papers_cleaned_with_new_columns.csv` |
| Low | `analysis/descriptive-statistics-and-bivariate-tests/rrmeasures-paper_files/` | `fig-temporal-trends-*` are not produced by the current `.qmd` |
