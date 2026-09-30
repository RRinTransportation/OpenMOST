#!/usr/bin/env bash
# Re-render the Quarto manuscript in a scratch copy and compare it with the
# committed rrmeasures-paper.tex and figure sources.
# Requires R + renv packages restored (make setup), Quarto and LuaLaTeX.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMP=analysis/descriptive-statistics-and-bivariate-tests
[ -f "$ROOT/zenodo/analysis_dataset/papers_cleaned_with_new_columns.csv" ] || {
  echo "Missing zenodo/analysis_dataset. See zenodo/README.md."; exit 1; }

TMP="$(mktemp -d -t openmost-validate-XXXX)"
mkdir -p "$TMP/analysis"
cp -R "$ROOT/$COMP" "$TMP/$COMP"
ln -s "$ROOT/zenodo" "$TMP/zenodo"
cd "$TMP/$COMP"
# remove committed render outputs so only freshly generated files are compared
rm -rf rrmeasures-paper.tex rrmeasures-paper.pdf rrmeasures-paper_files
quarto render rrmeasures-paper.qmd

status=0
if cmp -s rrmeasures-paper.tex "$ROOT/$COMP/rrmeasures-paper.tex"; then
  echo "rrmeasures-paper.tex: identical"
else
  echo "rrmeasures-paper.tex: DIFFERS"; diff "$ROOT/$COMP/rrmeasures-paper.tex" rrmeasures-paper.tex | head -40; status=1
fi
for f in rrmeasures-paper_files/figure-pdf/*.tex; do
  # line 1 is tikzDevice's creation timestamp
  if diff -q <(tail -n +2 "$f") <(tail -n +2 "$ROOT/$COMP/$f") >/dev/null; then
    echo "$f: identical (ignoring timestamp line)"
  else
    echo "$f: DIFFERS"; status=1
  fi
done
for f in "$ROOT/$COMP"/rrmeasures-paper_files/figure-pdf/*.tex; do
  rel="rrmeasures-paper_files/figure-pdf/$(basename "$f")"
  [ -f "$rel" ] || echo "$rel: committed but not produced by the current .qmd"
done
echo "Scratch run: $TMP/$COMP"
exit $status
