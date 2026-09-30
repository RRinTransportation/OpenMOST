# Zenodo data

The datasets for this repository are published on Zenodo (not in git):

**Zenodo record:** TODO: add DOI / URL (https://doi.org/10.5281/zenodo.XXXXXXX)

Download the three zip files from the record into this `zenodo/` folder and
unzip them here. Everything in this folder except this README is gitignored.

| File | Contents | Used by |
|---|---|---|
| `analysis_dataset.zip` | `analysis_dataset/`: `papers_cleaned_with_new_columns.csv` (paper-level features used in the paper), `papers_cleaned.csv`, `papers_cleaned_p2.csv`, `datasets_aggregated.csv`, `paper_dataset_mapping.csv` | [`../analysis`](../analysis) |
| `sample_xml_data.zip` | `sample_xml_data/`: 5 open-access Elsevier full-text XML files for demonstration | [`../feature-extraction`](../feature-extraction) |
| `manual-validation-dataset.zip` | `h1_96.csv`, `h2_96.csv`: two independent human annotations of 96 papers, used to validate the LLM-extracted features | manual validation (reference data) |

## Download and unzip

From the repository root:

```bash
cd zenodo
# replace RECORD with the Zenodo record id
curl -L -O https://zenodo.org/records/RECORD/files/analysis_dataset.zip
curl -L -O https://zenodo.org/records/RECORD/files/sample_xml_data.zip
curl -L -O https://zenodo.org/records/RECORD/files/manual-validation-dataset.zip

unzip analysis_dataset.zip
unzip sample_xml_data.zip
unzip manual-validation-dataset.zip -d manual-validation-dataset   # this zip has no top-level folder
cd ..
```

## Expected layout

```
zenodo/
├── analysis_dataset/
│   ├── datasets_aggregated.csv
│   ├── paper_dataset_mapping.csv
│   ├── papers_cleaned.csv
│   ├── papers_cleaned_p2.csv
│   └── papers_cleaned_with_new_columns.csv
├── manual-validation-dataset/
│   ├── h1_96.csv
│   └── h2_96.csv
└── sample_xml_data/
    └── 10.1016_j.tra.*.xml   (5 files)
```

## Data availability

The underlying papers were accessed via the Elsevier API (Text and Data
Mining). The papers themselves remain under Elsevier's copyright and are not
redistributed; the analysis dataset consists of derived, factual indicators.
See the Zenodo record for the data license.
