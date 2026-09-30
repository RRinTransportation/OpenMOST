# Full-text extraction

Walkthrough of the dataset curation: retrieve article DOIs and full-text XML
from the Elsevier API. The XML output is the input to
[`../feature-extraction`](../feature-extraction).

All notebooks are run from inside this `full-text-extraction/` folder.

## Environment (uv)

Dependencies are pinned in `pyproject.toml` / `uv.lock` (CPython 3.10.15, which uv
downloads automatically; versions match the original `feature-extraction`
environment). With [uv](https://docs.astral.sh/uv/) installed:

```bash
cd full-text-extraction
uv sync                                  # creates .venv with the locked versions
cp config.example.yaml config.yaml       # then put your Elsevier API key in it
mkdir -p journal-meta                    # TR-doi.ipynb does not create it
uv run jupyter notebook                  # open TR-doi.ipynb, then TR.ipynb
```

To execute a notebook non-interactively without overwriting the committed copy:

```bash
uv run jupyter nbconvert --to notebook --execute --output-dir executed TR-doi.ipynb
```

Note that `TR-doi.ipynb` as written queries volumes 0-199 of all seven TR
journals (thousands of API calls); run only the cells you need.

1. Use `TR-doi.ipynb` to retrieve all the articles with the corresponding DOI first. You need to prepare the journal ISSN (print) as input. It will automatically extract all the papers published in this journal since its inception. Results are written to `journal-meta/` (create the folder first).
2. With the DOI information, use `TR.ipynb` to extract the full-text data from the journal. XML files are written to `journal-full-text/<journal>/`.

The full-text XML is under Elsevier copyright and is not redistributed. Five
open-access sample XML files are provided in the Zenodo record
(`sample_xml_data.zip`); see [`../zenodo/README.md`](../zenodo/README.md).

## About the Elsevier API usage

### Get your API key

[Elsevier API](https://dev.elsevier.com/)

### Safely use your API key

Copy the template and fill in your key:

```bash
cp config.example.yaml config.yaml
```

```yaml
elsevier_api:
    api_key: your_api_key_here
```

`config.yaml` is gitignored so your key is never committed.

## License

Apache License 2.0; see the repository root [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
