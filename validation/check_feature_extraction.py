"""Run the offline feature-extraction steps on the 5 sample XMLs and compare the
metadata with the published rows in zenodo/analysis_dataset.

Steps covered: 1_meta.py, 2_xml2md.py, 5_a_meta_csv.ipynb. Steps 3, 4 (Gemini)
and 7 (Elsevier citations) need API keys and are not run here.

Run with the feature-extraction environment:
    uv run --project feature-extraction python validation/check_feature_extraction.py
"""
import math
import sys

import pandas as pd

from _common import ZENODO, execute_notebook, require_zenodo, run, scratch_copy

FIELDS = ["year", "journal", "article_subtype", "num_authors", "primary_institution",
          "number_of_keywords", "open_access", "figure_number", "table_number",
          "reference_count", "page_count", "submission_date", "acceptance_date",
          "review_time_days"]


def norm(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    s = str(v).strip()
    if s.lower() in ("true", "false"):
        return s.lower()
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else str(f)
    except ValueError:
        return s


require_zenodo("sample_xml_data", "analysis_dataset")
work = scratch_copy("feature-extraction", ignore=(".venv", "executed", "meta", "markdowns", "fla_csvs"))
xml = "../zenodo/sample_xml_data"
run([sys.executable, "1_meta.py", "--input_dir", xml, "--output_dir", "meta"], cwd=work)
run([sys.executable, "2_xml2md.py", xml, "-o", "markdowns"], cwd=work)
(work / "fla_csvs").mkdir()
execute_notebook(work / "5_a_meta_csv.ipynb")

n_md = len(list((work / "markdowns").glob("*.md")))
new = pd.read_csv(work / "fla_csvs/meta.csv", dtype=str).set_index("doi")
pub = pd.read_csv(ZENODO / "analysis_dataset/papers_cleaned_with_new_columns.csv",
                  dtype=str).set_index("doi")

mismatches = []
for doi in new.index:
    for f in FIELDS:
        a, b = norm(new.at[doi, f]), norm(pub.at[doi, f])
        if a != b:
            mismatches.append((doi, f, b, a))

print(f"\nmarkdowns: {n_md}/5, metadata rows: {len(new)}/5, "
      f"fields compared: {len(new) * len(FIELDS)}, mismatches: {len(mismatches)}")
for doi, f, b, a in mismatches:
    print(f"  {doi} {f}: published={b!r} regenerated={a!r}")
print(f"Scratch run: {work}")
sys.exit(1 if mismatches or n_md != 5 or len(new) != 5 else 0)
