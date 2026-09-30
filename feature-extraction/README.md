# Feature extraction

Metadata and reproducibility-feature extraction for the publications, using
the full-text XML files retrieved in [`../full-text-extraction`](../full-text-extraction).

All commands below are run from inside this `feature-extraction/` folder.

## Input data

The pipeline expects a folder of Elsevier full-text XML files. For
demonstration, 5 open-access XML files are available in the Zenodo record as
`sample_xml_data.zip`; see [`../zenodo/README.md`](../zenodo/README.md) to
download them into `../zenodo/sample_xml_data/`. To run on your own corpus,
replace `../zenodo/sample_xml_data` below with the folder of XML files produced
by [`../full-text-extraction`](../full-text-extraction).

## API keys

To get your Gemini API key, go to https://ai.google.dev/gemini-api/docs/api-key and follow the instructions.

Create `config.json` with your Gemini API key (steps 3 and 4), and `.env` with
your Elsevier API key (step 7, citations). Both files are gitignored.

```bash
echo '{"GOOGLE_API_KEY": "your-gemini-key"}' > config.json
echo 'ELSEVIER_API=your-elsevier-key' > .env
```

## Create environment

The environment is managed with [uv](https://docs.astral.sh/uv/). `pyproject.toml`
lists the direct dependencies pinned to the versions used for the paper, and
`uv.lock` pins the full environment. `.python-version` pins CPython 3.10.15, which
uv downloads automatically. The spaCy model `en_core_web_sm` 3.8.0 is part of the
lock, so no separate `spacy download` step is needed.

```bash
uv sync          # creates .venv/ with the locked packages (incl. Jupyter)
```

Prefix every command below with `uv run` so it uses this environment.

<details>
<summary>Without uv (pip or conda)</summary>

`requirements.txt` is generated from the lock with
`uv export --no-hashes --format requirements-txt > requirements.txt`. Install it
with `--no-deps`: spaCy 3.8.7's dependency thinc 8.3.6 declares `numpy>=2`, but
gensim 4.3.3 needs `numpy<2`. The original environment ran thinc 8.3.6 on
numpy 1.26.4, and the lock keeps that combination (see `override-dependencies`
in `pyproject.toml`), so pip's resolver rejects it without `--no-deps`.

```bash
conda create --name RR-measure python=3.10.15 pip   # or: python3.10 -m venv .venv
conda activate RR-measure
pip install --no-deps -r requirements.txt
```

If you use the python.org macOS installer, run its `Install Certificates.command`
first; otherwise `nltk.download()` in `8_create_lda.ipynb` fails on SSL.
`uv sync` is the canonical setup; `requirements.txt` is only a fallback.
</details>

## Usage of the metadata extraction script
```bash
uv run python 1_meta.py --input_dir '../zenodo/sample_xml_data' --output_dir 'meta'
```

## Usage of the XML to Markdown script
```bash
uv run python 2_xml2md.py '../zenodo/sample_xml_data' -o 'markdowns'
```

## Usage of the p1 feature on the code with gemini
```bash
uv run python 3_code-p1-gemini.py 'markdowns' 'code-p1-gemini'
```

## Usage of the p1 feature on the data with gemini
```bash
uv run python 4_a_data-p1-gemini.py 'markdowns' 'data-p1-gemini'
```

## Extract is_quantitative (this was added later as a feature):
```bash
uv run python 4_a_data-p1-gemini.py 'markdowns' 'is-quantitative-p1-gemini' --prompt-file '4_c_is-quantitative-paper.md'
```

Steps 3 and 4 call the Gemini model hard-coded in the scripts
(`gemini-2.5-flash-lite-preview-06-17`). LLM outputs are not deterministic, so
re-running them can give different feature values.

## Create the CSV file for LLM features

The notebooks write to `fla_csvs/`, which must exist first:

```bash
mkdir -p fla_csvs
```

Run in this order:
Use notebook `5_a_meta_csv.ipynb` to create csv of just metadata.
Use notebook `5_b_create_new_fla.ipynb` to add code and data features, and `5_c_10k_quant.ipynb` to add is_quantitative.

Open the notebooks interactively with `uv run jupyter notebook`, or execute one
non-interactively without overwriting the committed copy (and its reference
outputs), e.g.:

```bash
uv run jupyter nbconvert --to notebook --execute --output-dir executed 5_a_meta_csv.ipynb
```

## Clean regions into continents
Use notebook `6_clean_regions.ipynb`.

## Add citations
Use notebook `7_get_citations.ipynb` (needs the Elsevier key in `.env`).

## Add LDA topics
Use notebook `8_create_lda.ipynb`. The pre-trained LDA model is in `lda_data/`.
The notebook downloads the NLTK stopword list on first run.

## Output

The notebooks write intermediate and final CSVs to `fla_csvs/`. The final,
cleaned dataset used in the paper is published on Zenodo as
`analysis_dataset.zip` and is consumed by [`../analysis`](../analysis).

## License

Apache License 2.0; see the repository root [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
