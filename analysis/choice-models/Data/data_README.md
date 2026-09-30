# Data

## Analysis dataset

The processed dataset used to estimate the Biogeme models is published on
Zenodo as `analysis_dataset.zip` (see [`../../../zenodo/README.md`](../../../zenodo/README.md)).
Unzip it to `zenodo/analysis_dataset/` at the repository root; the notebook
reads `papers_cleaned_with_new_columns.csv` from there. The notebook can be
run without re-running the data extraction pipeline.

**Provenance**

- **Source pipeline:** [`feature-extraction/`](../../../feature-extraction)
- **Date extracted:** `2025-09-25`

If the pipeline is updated after this snapshot was taken, the Zenodo dataset
will **not** automatically reflect those changes. To regenerate the dataset
from raw sources, see the instructions in the pipeline folder linked above.

**Shared with the descriptive-statistics analysis**

The same Zenodo dataset is used by
[`../../descriptive-statistics-and-bivariate-tests`](../../descriptive-statistics-and-bivariate-tests),
so both analyses always read the same version.

## Data availability

The underlying papers were identified and their metadata/full text accessed
via the **Elsevier API** (Text and Data Mining access). The papers themselves
remain under Elsevier's copyright and are **not** redistributed.

The dataset consists of **derived, factual indicators**
extracted from those papers (e.g., binary/categorical variables such as
whether a paper reports code or data availability), not verbatim text from
the source articles. Bare facts of this kind are not generally subject to
copyright protection independent of the source text.

That said, **use of the Elsevier API is governed by Elsevier's Text and Data
Mining (TDM) terms of use**, which may impose separate contractual
restrictions on redistributing data derived through the API, independent of
copyright. Anyone reusing this dataset should independently confirm their
own compliance with Elsevier's current TDM/API terms
(https://dev.elsevier.com/) and any institution-specific TDM agreement, as
these terms can vary and change over time.

