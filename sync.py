"""
Refresh this repo's snapshot of the thesis repo (metacentrum-notebooks).

Only committed files are copied (git archive), so the thesis repo's .env and
any work in progress can never end up here.

    python sync.py                 # snapshot HEAD
    python sync.py <commit-or-tag> # snapshot a specific commit
    python sync.py --allow-dirty   # snapshot HEAD although uncommitted changes exist

The thesis repo is expected next to this folder; set MCNB_REPO to point elsewhere.
"""
import io
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THESIS_REPO = Path(
    os.environ.get("MCNB_REPO", ROOT.parent / "metacentrum-notebooks")
).resolve()

# What a Binder session needs: the notebooks, the mcnb package they import,
# its dependency list, and the template the credential wizard reads.
PATHS = ["notebooks", "src", "env.example", "pyproject.toml"]


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(THESIS_REPO), *args], check=True, capture_output=True
    ).stdout


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--allow-dirty"]
    ref = args[0] if args else "HEAD"
    sha = git("rev-parse", f"{ref}^{{commit}}").decode().strip()

    dirty = git("status", "--porcelain", "--", *PATHS).decode().strip()
    if dirty and "--allow-dirty" not in sys.argv:
        print("✗ Thesis repo has uncommitted changes that would NOT be in the snapshot:")
        print("   " + dirty.replace("\n", "\n   "))
        print("Commit them first, or pass --allow-dirty to snapshot the committed state anyway.")
        return 1

    archive = git("archive", "--format=tar", sha, "--", *PATHS)

    for path in PATHS:
        target = ROOT / path
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(ROOT, filter="data")

    # The paired jupytext .py files are for editing in the thesis repo; a
    # reviewer should only see the notebooks.
    for script in (ROOT / "notebooks").glob("*.py"):
        script.unlink()

    subject = git("log", "-1", "--format=%s", sha).decode().strip()
    date = git("log", "-1", "--format=%cI", sha).decode().strip()
    (ROOT / "SOURCE_COMMIT").write_text(f"{sha}\n{date}\n{subject}\n")
    print(f"✓ snapshot = {THESIS_REPO.name} @ {sha[:7]} ({subject})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
