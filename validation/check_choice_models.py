"""Re-estimate the Biogeme models and compare them with analysis/choice-models/Results/.

Run with the choice-models environment:
    uv run --project analysis/choice-models python validation/check_choice_models.py
"""
import sys

import numpy as np
from biogeme.results import bioResults

from _common import ROOT, execute_notebook, require_zenodo, scratch_copy

MODELS = ["logit_const_code", "logit_code_av", "logit_data_repo_cit_const", "logit_data_repo_cit"]
ARRAYS = ["betaValues", "varCovar", "robust_varCovar", "g"]

require_zenodo("analysis_dataset")
committed = ROOT / "analysis/choice-models/Results"
work = scratch_copy("analysis/choice-models", ignore=(".venv", "Results"))
execute_notebook(work / "Notebook/ChoiceModels.ipynb")

failures = 0
for m in MODELS:
    ref = bioResults(pickleFile=str(committed / f"{m}.pickle")).data
    new = bioResults(pickleFile=str(work / f"Notebook/{m}.pickle")).data
    checks = {"N": (ref.sampleSize, new.sampleSize), "K": (ref.nparam, new.nparam)}
    ok = all(a == b for a, b in checks.values())
    ok &= np.isclose(ref.logLike, new.logLike, rtol=1e-10, atol=0)
    bitwise = True
    for k in ARRAYS:
        a, b = np.asarray(getattr(ref, k)), np.asarray(getattr(new, k))
        bitwise &= np.array_equal(a, b)
        ok &= np.allclose(a, b, rtol=1e-8, atol=1e-12)
    status = "bitwise identical" if (ok and bitwise) else ("within tolerance" if ok else "MISMATCH")
    print(f"{m:28s} N={new.sampleSize} K={new.nparam} LL={new.logLike:.6f}  {status}")
    failures += not ok

print(f"\nScratch run: {work}")
sys.exit(1 if failures else 0)
