# Zenodo data

The datasets for this repository are published on Zenodo (not in git):

> *Supporting data for Measuring the State of Open Science in Transportation Using Large Language Models*
> DOI (all versions, use this to cite): [10.5281/zenodo.23045963](https://doi.org/10.5281/zenodo.23045963)
> Current version: record [23059196](https://zenodo.org/records/23059196)
> (DOI [10.5281/zenodo.23059196](https://doi.org/10.5281/zenodo.23059196)).
> License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The all-versions DOI always resolves to the latest version. The download
commands and checksums below are for the current version (record 23059196).

Download the three zip files into this `zenodo/` folder and unzip them here.
Everything in this folder except this README is gitignored.

| File | MD5 | Contents | Used by |
|---|---|---|---|
| `analysis_dataset.zip` | `1b1bfbc6e2d127cada44b349b1a2bdcc` | `analysis_dataset/`: `papers_cleaned_with_new_columns.csv` (the paper-level analysis input, 10,724 papers × 77 columns); `papers_cleaned.csv` (the same without `is_quantitative_study`); `papers_cleaned_p2.csv` (adds code-link liveness columns); `datasets_aggregated.csv` and `paper_dataset_mapping.csv` (dataset-level records) | [`../analysis`](../analysis) |
| `sample_xml_data.zip` | `67244bc81d500261ffa5a44cb501c57d` | `sample_xml_data/`: 5 open-access Elsevier full-text XML files for demonstration | [`../feature-extraction`](../feature-extraction) |
| `manual_validation_dataset.zip` | `68fb6ca78b460f9bceb237752e747e07` | `manual_validation_dataset/`: `h1_96.csv` (annotator 1: 113 rows, 112 papers incl. one duplicate DOI) and `h2_96.csv` (annotator 2: 96 papers); the 96 papers in both are the human-labelled validation sample for the LLM-extracted features | manual validation (reference data) |

## Download and unzip

From the repository root, either run

```bash
make data
```

or do it by hand:

```bash
cd zenodo
for f in analysis_dataset sample_xml_data manual_validation_dataset; do
  curl -L -o "$f.zip" "https://zenodo.org/records/23059196/files/$f.zip?download=1"
done
md5sum *.zip          # macOS: md5 *.zip — compare with the table above

unzip analysis_dataset.zip
unzip sample_xml_data.zip
unzip manual_validation_dataset.zip
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
├── manual_validation_dataset/
│   ├── h1_96.csv
│   └── h2_96.csv
└── sample_xml_data/
    └── 10.1016_j.tra.*.xml   (5 files)
```

## Citation

```bibtex
@dataset{ji_2026_openmost_data,
  author    = {Ji, Junyi and Lu, Ruth and Belkessa, Linda and Wang, Liming and
               Varotto, Silvia and Dong, Yongqi and Saunier, Nicolas and
               Ameli, Mostafa and Macfarlane, Gregory S. and Madadi, Bahman and
               Wu, Cathy},
  title     = {Supporting data for Measuring the State of Open Science in
               Transportation Using Large Language Models},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.23045963},
  url       = {https://doi.org/10.5281/zenodo.23045963}
}
```

To cite the exact version used, replace the DOI with the version DOI
(currently `10.5281/zenodo.23059196`).

## Data availability

The underlying papers were accessed via the Elsevier API (Text and Data
Mining). The papers themselves remain under Elsevier's copyright and are not
redistributed; the analysis dataset consists of derived, factual indicators.
The data are licensed under CC BY 4.0; reuse is also subject to Elsevier's
TDM terms (https://dev.elsevier.com/).
