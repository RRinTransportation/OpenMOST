"""Shared helpers for the reproducibility checks (stdlib only)."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZENODO = ROOT / "zenodo"


def scratch_copy(component: str, ignore=(".venv", "executed")) -> Path:
    """Copy ROOT/<component> into a temp dir at the same relative depth, with
    zenodo/ symlinked, so relative data paths resolve exactly as in the repo."""
    tmp = Path(tempfile.mkdtemp(prefix="openmost-validate-"))
    dst = tmp / component
    shutil.copytree(ROOT / component, dst, symlinks=True,
                    ignore=shutil.ignore_patterns(*ignore))
    (tmp / "zenodo").symlink_to(ZENODO)
    return dst


def require_zenodo(*names: str) -> None:
    missing = [n for n in names if not (ZENODO / n).exists()]
    if missing:
        sys.exit(f"Missing Zenodo data: {missing}. See zenodo/README.md.")


def run(cmd, cwd) -> None:
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def execute_notebook(nb: Path) -> None:
    """Execute a notebook in place (inside a scratch copy) with this interpreter."""
    run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
         "--execute", "--inplace", "--ExecutePreprocessor.timeout=-1",
         "--ExecutePreprocessor.kernel_name=python3", nb.name], cwd=nb.parent)
