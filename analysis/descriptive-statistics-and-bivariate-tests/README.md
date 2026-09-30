# Descriptive statistics and bivariate tests

Analysis by Gregory S. Macfarlane, originally developed in
[`gregmacfarlane/rr-measures-paper`](https://github.com/gregmacfarlane/rr-measures-paper).

This repository contains the manuscript, data, and supporting analysis for
*Towards Accelerating Transportation Research: Measuring the Practice of Open
Science*. The study examines the availability of research code and data in
transportation publications.

In addition to the reproducible Quarto manuscript, the repository includes a
Shiny app for interactively exploring how paper characteristics relate to code
and data availability.

## Repository contents

- `rrmeasures-paper.qmd`: manuscript and analysis source
- `main.bib`: bibliography
- `data_explorer/`: Shiny app and its prepared data snapshot
- `_extensions/quarto-journals/elsevier/`: local Quarto journal extension
- `rrmeasures-paper.pdf`: rendered manuscript

## Data

The analysis data and paper-to-dataset mappings are published on Zenodo as
`analysis_dataset.zip`. Download it and unzip it into `zenodo/` at the
repository root (see [`../../zenodo/README.md`](../../zenodo/README.md)) so that
`zenodo/analysis_dataset/papers_cleaned_with_new_columns.csv` exists.

## Requirements

To reproduce the manuscript and run the app, install:

- [R](https://cran.r-project.org/) (the lockfile was recorded with R 4.6.1)
- [Quarto](https://quarto.org/docs/get-started/) (validated with 1.8)
- a LaTeX distribution with LuaLaTeX, such as [TinyTeX](https://yihui.org/tinytex/)
  (validated with TeX Live 2025)

R packages are managed with [renv](https://rstudio.github.io/renv/). `renv.lock`
pins every package, and `.Rprofile` points CRAN at a dated Posit Package Manager
snapshot (2026-07-01) so the same versions are installed. From this folder:

```sh
Rscript -e 'renv::restore(prompt = FALSE)'
```

R bootstraps renv automatically the first time it starts in this folder
(`renv/activate.R`). `_dependencies.R` is never run; it only records packages
that are used indirectly (e.g. `tikzDevice` for the `dev: tikz` figure) so that
`renv::snapshot()` keeps them.

`data_explorer/.posit/publish/deployments/renv.lock` is the separate lockfile
Posit Connect uses to deploy the live Shiny app (R 4.5.2). It is not used for
local reproduction.

## Render the manuscript

From this folder (`analysis/descriptive-statistics-and-bivariate-tests/`), run:

```sh
quarto render rrmeasures-paper.qmd
```

The rendered manuscript is written to `rrmeasures-paper.pdf`. The Quarto file
reads the source data from `../../zenodo/analysis_dataset/` and performs the data preparation,
descriptive analysis, statistical tests, and table generation used in the
paper.

## Explore the data with Shiny

The Shiny app provides an interactive view of the paper-level analysis data.
It lets users choose one of two outcomes—code availability or data
availability—and compare that outcome with another variable in the dataset.

The display adapts to the selected comparison variable:

- For numeric variables, it shows distributions by availability group and
  t-tests comparing group means.
- For categorical variables, it shows a cross-tabulation and pairwise tests of
  proportions with adjusted p-values.

These are exploratory, unadjusted bivariate comparisons; they should not be
interpreted as causal estimates or as substitutes for the analyses reported in
the manuscript.

Launch the app from this folder with:

```sh
Rscript -e 'shiny::runApp("data_explorer")'

```


The app uses `data_explorer/paper_data.rds`, a prepared snapshot created from
the manuscript's `papers` analysis object. To refresh that snapshot after
changing the source data or preparation steps, uncomment the corresponding
`write_rds()` line in `rrmeasures-paper.qmd`, render the manuscript, and then
restart the app.

The shiny app is live at <https://019b33f2-34f4-9d17-cc65-86ffbaaa9028.share.connect.posit.cloud/>.

## Notes on reproducibility

Run commands from this folder so that relative data paths resolve
correctly. With the renv environment, R 4.6.1, Quarto 1.8 and TeX Live 2025,
`quarto render` reproduces the committed `rrmeasures-paper.tex` byte for byte,
and the regenerated figures differ from the committed ones only in their
creation-timestamp line. The committed `rrmeasures-paper_files/figure-pdf/fig-temporal-trends-*`
files are not produced by the current `rrmeasures-paper.qmd`.
