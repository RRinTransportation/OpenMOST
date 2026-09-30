# Choice Models for Data and Code Availability

Discrete choice models predicting data and code availability in
published Transportation Research papers, developed as part of:

> *Measuring the State of Open Science in Transportation Using Large Language Models*
> [arXiv:2601.14429](https://arxiv.org/abs/2601.14429)

**Author:** Silvia Varotto, EMob-Lab, ENTPE (UMR Université Gustave Eiffel – ENTPE)

This folder is part of the OpenMOST repository. It complements the other
components that together support the paper:

- **Full-text extraction**: [`../../full-text-extraction`](../../full-text-extraction)
- **Feature extraction** (data pipeline): [`../../feature-extraction`](../../feature-extraction)
- **Descriptive statistics and bivariate tests (R)**: [`../descriptive-statistics-and-bivariate-tests`](../descriptive-statistics-and-bivariate-tests)
  (originally [`gregmacfarlane/rr-measures-paper`](https://github.com/gregmacfarlane/rr-measures-paper))

Each component is maintained and owned by its respective author(s). See
[`Data/data_README.md`](Data/data_README.md) for details on how the processed dataset
used here relates to the data pipeline.

---

## Repository structure

```
analysis/choice-models/
├── Data/
│   └── data_README.md     # provenance of the data (dataset itself is on Zenodo)
├── Notebook/       # Notebook with Biogeme model specification, estimation results, and Latex tables
├── Results/        # Biogeme estimation output files (.html, .pickle/.yaml, etc.)
├── pyproject.toml  # dependencies, pinned to the versions used for the paper
├── uv.lock         # fully locked environment (managed by uv)
├── .python-version # Python 3.11
├── LICENSE
├── CITATION.cff
└── README.md
```

---

## Instructions for Running the Notebook

This project uses [uv](https://docs.astral.sh/uv/) to manage a locked,
reproducible Python environment (`pyproject.toml` / `uv.lock`). The locked
versions reproduce the results in `Results/` bit for bit
(Python 3.11, biogeme 3.2.13, numpy 1.26.0, pandas 3.0.5, scipy 1.16.3).

1. **Install uv**, if not already installed (see the
   [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository, download the data, and move into this folder:**
   ```bash
   git clone https://github.com/RRinTransportation/OpenMOST.git
   cd OpenMOST
   # download analysis_dataset.zip from Zenodo into zenodo/ (see zenodo/README.md), then
   unzip zenodo/analysis_dataset.zip -d zenodo
   cd analysis/choice-models
   ```

3. **Install the locked dependencies.** This downloads Python 3.11 if needed
   (the version is pinned in `.python-version`), creates `.venv/`, and installs
   exactly the package versions pinned in `uv.lock`, including Jupyter:
   ```bash
   uv sync --locked
   ```

4. **Launch Jupyter** inside the locked environment:
   ```bash
   uv run jupyter notebook
   ```
   Open the notebook in `Notebook/` and use the default **Python 3** kernel
   (it is the one from `.venv/`).

   Alternatively, run the whole notebook non-interactively:
   ```bash
   uv run jupyter nbconvert --to notebook --execute --output ChoiceModels.executed.ipynb Notebook/ChoiceModels.ipynb
   ```

5. **Run the notebook top to bottom.** The notebook reads
   `zenodo/analysis_dataset/papers_cleaned_with_new_columns.csv` from the
   repository root — no pipeline run is required. Biogeme writes its output
   (`.html`, `.pickle`, `__*.iter`, `biogeme.toml`) to the current working
   directory, i.e. `Notebook/`; the reference output is in `Results/`. If
   `__*.iter` files already exist there, Biogeme uses them as starting values;
   delete them for an estimation from scratch.

---

## Reproducing the models

The models are estimated directly from the processed dataset published on
Zenodo (`analysis_dataset.zip`, unzipped to `zenodo/analysis_dataset/` at the
repository root), so the notebook can be run end to end without re-running the
data pipeline. See [`Data/data_README.md`](Data/data_README.md) for how that
dataset was produced, if you want to trace it back to raw sources.

---

## License

This project is licensed under the MIT License — see [`LICENSE`](LICENSE).

## Citation

See [`CITATION.cff`](CITATION.cff).
