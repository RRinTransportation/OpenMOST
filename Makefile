# OpenMOST: environment setup and reproducibility checks.
# Requires uv (Python components) and R + Quarto + LuaLaTeX (descriptive analysis).
# Download the Zenodo data into zenodo/ first (see zenodo/README.md).

UV       ?= uv
PY_DIRS  := full-text-extraction feature-extraction analysis/choice-models
R_DIR    := analysis/descriptive-statistics-and-bivariate-tests

.PHONY: help setup setup-python setup-r check-locks validate \
        validate-choice-models validate-descriptive validate-feature-extraction

help:
	@echo "make setup        install every locked environment (uv sync + renv::restore)"
	@echo "make check-locks  verify uv.lock / renv.lock are in sync with their manifests"
	@echo "make validate     re-run the analyses and compare with the committed/published results"
	@echo "  make validate-choice-models | validate-descriptive | validate-feature-extraction"

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
