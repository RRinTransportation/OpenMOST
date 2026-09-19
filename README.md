# rr-meta-data
Meta data extraction for the publications

Assuming original xml files are stored in a folder called `data`.

For the sake of demonstration, 5 open-access xml files are put into an example data folder.

To get your Gemini API key, go to https://ai.google.dev/gemini-api/docs/api-key and follow the instructions.

Create config.json and add your gemini API key, create .env and add Elsevier API key.

## Create environment
Use requirements.txt
```bash
conda create --name RR-measure --file requirements.txt
```

## Usage of the metadata extraction script
```bash
python 1_meta.py --input_dir 'data' --output_dir 'meta'
```

## Usage of the XML to Markdown script
```bash
python 2_xml2md.py 'data' -o 'markdowns'
```

## Usage of the p1 feature on the code with gemini
```bash
python 3_code-p1-gemini.py 'markdowns' 'code-p1-gemini'
```

## Usage of the p1 feature on the data with gemini
```bash
python 4_a_data-p1-gemini.py 'markdowns' 'data-p1-gemini'
```

## Extract is_quantitative (this was added later as a feature):
```bash
python 4_a_data-p1-gemini.py 'markdowns' 'is-quantitative-p1-gemini' --prompt-file '4_c_is-quantitative-paper.md'
```

## Create the CSV file for LLM features

Run in this order:
Use notebook `5_a_meta_csv.ipynb` to create csv of just metadata.
Use notebook `5_b_create_new_fla.ipynb` to add code and data features, and `5_c_10k_quant.ipynb` to add is_quantitative.



## Clean regions into continents
Use notebook `6_clean_regoins.ipynb`.

## Add citations
Use notebook `7_get_citations.ipynb`.

## Add LDA topics
Run `python -m spacy download en_core_web_sm` to download necessary files.
Use notebook `8_create_lda.ipynb`.

## License

**Code:** [Apache License 2.0](LICENSE). Free to use, modify, and redistribute,
including commercially. If you redistribute this code or a derivative, you must
retain the copyright notice, include a copy of the license, carry forward the
[NOTICE](NOTICE) file, and state any significant changes you made.

**Data:** licensed separately -- see [DATA-LICENSE.md](DATA-LICENSE.md). The
license on this code does not extend to third-party data redistributed here.

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

Preprint: [arXiv:2601.14429](https://arxiv.org/abs/2601.14429)
