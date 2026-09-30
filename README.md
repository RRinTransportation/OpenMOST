# OpenMOST: Measuring the State of Open Science in Transportation

Code accompanying *Measuring the State of Open Science in Transportation Using
Large Language Models* (Transportation Research Part C, 2026;
[doi:10.1016/j.trc.2026.106024](https://doi.org/10.1016/j.trc.2026.106024);
preprint [arXiv:2601.14429](https://arxiv.org/abs/2601.14429)).

The repository is organized as a pipeline of three components. The data are
published separately on Zenodo and are placed in [`zenodo/`](zenodo).

| Folder | What it does | Input | Output |
|---|---|---|---|
| [`full-text-extraction/`](full-text-extraction) | Retrieve article DOIs and full-text XML from the Elsevier API | Journal ISSNs, Elsevier API key | Full-text XML |
| [`feature-extraction/`](feature-extraction) | Extract metadata and LLM-based open-science features (code/data availability, etc.), citations, regions, LDA topics | Full-text XML (demo: `zenodo/sample_xml_data/`) | Paper-level feature CSVs |
| [`analysis/`](analysis) | [Choice models](analysis/choice-models) and [descriptive statistics and bivariate tests](analysis/descriptive-statistics-and-bivariate-tests) | `zenodo/analysis_dataset/` | Tables, figures, model estimates |
| [`zenodo/`](zenodo) | Location for the downloaded Zenodo data (gitignored) | | |

## Quickstart

1. Clone the repository:
   ```bash
   git clone https://github.com/RRinTransportation/OpenMOST.git
   cd OpenMOST
   ```
2. Download the data from Zenodo
   ([10.5281/zenodo.23045963](https://doi.org/10.5281/zenodo.23045963)) into
   `zenodo/` and unzip it: `make data` downloads, checksums and unzips all three
   files. See [`zenodo/README.md`](zenodo/README.md) for the exact commands
   and expected layout.
3. Install the locked environments. Each component has its own:
   [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock` + `.python-version`)
   for the Python folders and [renv](https://rstudio.github.io/renv/) (`renv.lock`)
   for the R analysis. The R analysis also needs R, Quarto and a LuaLaTeX distribution.
   ```bash
   make setup        # uv sync --frozen in each Python folder + renv::restore()
   make validate     # re-run the analyses and compare with the published results
   ```
   See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for what is validated and the results.
4. Follow the README in the folder you want to run. Each folder is
   self-contained and is run from inside that folder:
   - To reproduce the paper's analyses, you only need `analysis_dataset`:
     see [`analysis/`](analysis).
   - To try the feature-extraction pipeline on the sample papers, see
     [`feature-extraction/`](feature-extraction) (requires Gemini and Elsevier API keys).
   - To build a new corpus from scratch, start with
     [`full-text-extraction/`](full-text-extraction) (requires an Elsevier API key).

```
OpenMOST/
├── full-text-extraction/
├── feature-extraction/
├── analysis/
│   ├── choice-models/
│   └── descriptive-statistics-and-bivariate-tests/
├── validation/      # reproducibility checks run by `make validate`
├── zenodo/          # downloaded data goes here
├── Makefile
└── REPRODUCIBILITY.md
```

## License

**Code:** licensed under the [Apache License 2.0](LICENSE). If you
redistribute this code or a derivative, you must retain the copyright notice,
include a copy of the license, carry forward the [NOTICE](NOTICE) file, and
state any significant changes you made.

Exceptions, pending the authors' agreement to relicense under Apache-2.0:

- [`analysis/choice-models/`](analysis/choice-models) is © Silvia F. Varotto and
  currently licensed under the [MIT License](analysis/choice-models/LICENSE).
- [`analysis/descriptive-statistics-and-bivariate-tests/`](analysis/descriptive-statistics-and-bivariate-tests)
  is © Gregory S. Macfarlane and does not yet carry a license.

<!-- TODO: once Varotto and Macfarlane agree, remove analysis/choice-models/LICENSE,
update analysis/choice-models/CITATION.cff (license: Apache-2.0), and drop this exception list. -->

**Data:** not distributed in this repository. The data are published on
Zenodo ([10.5281/zenodo.23045963](https://doi.org/10.5281/zenodo.23045963)) under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see
[`zenodo/README.md`](zenodo/README.md). The underlying
papers remain under Elsevier's copyright and are not redistributed.

## Citation

If you use this software or its outputs in published work, please cite the
accompanying paper. Machine-readable metadata is in
[CITATION.cff](CITATION.cff).

```bibtex
@article{ji2026most,
  title   = {Measuring the State of Open Science in Transportation Using Large Language Models},
  author  = {Ji, Junyi and Lu, Ruth and Belkessa, Linda and Wang, Liming and
             Varotto, Silvia and Dong, Yongqi and Saunier, Nicolas and
             Ameli, Mostafa and Macfarlane, Gregory S. and Madadi, Bahman and
             Wu, Cathy},
  journal = {Transportation Research Part C: Emerging Technologies},
  year    = {2026},
  doi     = {10.1016/j.trc.2026.106024},
  url     = {https://doi.org/10.1016/j.trc.2026.106024}
}
```
