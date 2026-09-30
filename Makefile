# OpenMOST: environment setup and reproducibility checks.
# Requires uv (Python components) and R + Quarto + LuaLaTeX (descriptive analysis).
# Download the Zenodo data into zenodo/ first (see zenodo/README.md).

UV       ?= uv
PY_DIRS  := full-text-extraction feature-extraction analysis/choice-models
R_DIR    := analysis/descriptive-statistics-and-bivariate-tests

.PHONY: help data setup setup-python setup-r check-locks validate \
        validate-choice-models validate-descriptive validate-feature-extraction

help:
	@echo "make data         download, checksum and unzip the Zenodo data into zenodo/"
	@echo "make setup        install every locked environment (uv sync + renv::restore)"
	@echo "make check-locks  verify uv.lock / renv.lock are in sync with their manifests"
	@echo "make validate     re-run the analyses and compare with the committed/published results"
	@echo "  make validate-choice-models | validate-descriptive | validate-feature-extraction"

# Current version of the Zenodo record (all versions: doi:10.5281/zenodo.23045963)
ZENODO_URL := https://zenodo.org/records/23059196/files

data:
	@cd zenodo && for f in analysis_dataset:1b1bfbc6e2d127cada44b349b1a2bdcc \
	    sample_xml_data:67244bc81d500261ffa5a44cb501c57d \
	    manual_validation_dataset:68fb6ca78b460f9bceb237752e747e07; do \
	  name=$${f%%:*}; md5=$${f##*:}; \
	  [ -f $$name.zip ] || curl -fsSL -o $$name.zip "$(ZENODO_URL)/$$name.zip?download=1" || exit 1; \
	  got=$$(python3 -c "import hashlib,sys;print(hashlib.md5(open(sys.argv[1],'rb').read()).hexdigest())" $$name.zip); \
	  [ "$$got" = "$$md5" ] || { echo "$$name.zip: MD5 mismatch ($$got)"; exit 1; }; \
	  echo "$$name.zip: OK"; \
	done
	cd zenodo && unzip -oq analysis_dataset.zip && unzip -oq sample_xml_data.zip \
	  && unzip -oq manual_validation_dataset.zip

setup: setup-python setup-r

setup-python:
	@for d in $(PY_DIRS); do echo "== $$d"; (cd $$d && $(UV) sync --frozen) || exit 1; done

setup-r:
	cd $(R_DIR) && Rscript -e 'renv::restore(prompt = FALSE)'

check-locks:
	@for d in $(PY_DIRS); do echo "== $$d"; (cd $$d && $(UV) lock --check) || exit 1; done
	cd $(R_DIR) && Rscript -e 'if (!renv::status()$$synchronized) quit(status = 1)'

validate: check-locks validate-feature-extraction validate-choice-models validate-descriptive

validate-choice-models:
	cd validation && $(UV) run --frozen --project ../analysis/choice-models python check_choice_models.py

validate-feature-extraction:
	cd validation && $(UV) run --frozen --project ../feature-extraction python check_feature_extraction.py

validate-descriptive:
	./validation/check_descriptive.sh
