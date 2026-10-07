"""
Credential loading for MetaCentrum/e-INFRA notebooks.

Env file search order (lowest → highest priority, later overrides earlier):
  1. <repo>/env_*          — user-named uploads (e.g. env_omar, env_workshop)
  2. <repo>/env            — non-dotfile alternative to .env
  3. <repo>/.env           — standard dotenv (gitignored)
  4. ~/.config/mcnb/env   — persistent home-dir config (highest priority)

env.example is never auto-loaded — it is a template used only by setup_env().
"""
import os
from pathlib import Path
from typing import Optional

# ── optional python-dotenv ───────────────────────────────────────────────────
try:
    from dotenv import load_dotenv as _dotenv_load
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False


def _repo_root() -> Path:
    """Repo root is two levels above src/mcnb/env.py."""
    return Path(__file__).resolve().parent.parent.parent


def _env_files(root: Path) -> list:
    """
    Return env files to load, ascending priority (later entries override earlier).
    env.example and env_*.example are excluded — they are templates only.
    """
    found = []
    # 1. user-named: env_omar, env_workshop, ...
    for p in sorted(root.glob("env_*")):
        if p.is_file() and p.suffix != ".example":
            found.append(p)
    # 2. plain non-dotfile
    plain = root / "env"
    if plain.is_file():
        found.append(plain)
    # 3. standard dotfile
    dot = root / ".env"
    if dot.is_file():
        found.append(dot)
    # 4. persistent home-dir config (highest priority)
    home_cfg = Path.home() / ".config" / "mcnb" / "env"
    if home_cfg.is_file():
        found.append(home_cfg)
    return found


def _load_file(path: Path) -> None:
    """Load one env file into os.environ, overriding existing values."""
    if _HAS_DOTENV:
        _dotenv_load(str(path), override=True)
        return
    # Stdlib-only fallback — works without python-dotenv installed
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                os.environ[key] = val


# ── auto-load on import ──────────────────────────────────────────────────────
_ROOT = _repo_root()
for _f in _env_files(_ROOT):
    try:
        _load_file(_f)
    except OSError as _e:
        print(f"⚠  Could not load {_f}: {_e}")


# ── public API ────────────────────────────────────────────────────────────────

def reload() -> None:
    """Re-read all env files into os.environ. Call after editing .env mid-session."""
    for _f in _env_files(_ROOT):
        try:
            _load_file(_f)
        except OSError as _e:
            print(f"⚠  Could not load {_f}: {_e}")


def need(name: str) -> str:
    """Return a required env var or raise RuntimeError with a clear message.

    If the variable is not found, env files are reloaded once (picks up edits
    made after kernel start) before giving up.
    """
    v = os.getenv(name)
    if not v:
        reload()
        v = os.getenv(name)
    if not v:
        raise RuntimeError(
            f"Missing env var '{name}'. "
            f"Add it to ~/.config/mcnb/env, repo env/.env, or run setup_env()."
        )
    return v


def optional(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return an optional env var, or default if not set."""
    return os.getenv(name, default)


def mask(value: str, show_last: int = 4) -> str:
    """Return '****abcd' style masked string for safe printing."""
    if not value:
        return "****"
    if len(value) <= show_last:
        return "*" * len(value)
    return "*" * 4 + value[-show_last:]


def setup_env(template: str = "env.example", force: bool = False) -> bool:
    """
    Interactive credential setup for MetaCentrum OnDemand / workshop use.

    Reads <repo>/env.example (or the given template), prompts for every
    REPLACE_ME value, and writes credentials to ~/.config/mcnb/env which
    persists across kernel restarts and JupyterLab sessions.

    Names containing KEY, SECRET, TOKEN, PASSWORD, or CREDENTIAL use
    getpass (input hidden). All others use plain input.

    Args:
        template: Template filename in repo root. Default: "env.example".
        force:    Overwrite existing credentials file. Default: False.

    Returns:
        True if credentials were written or already existed, False on error.
    """
    import getpass as _gp

    _SECRETS = {"KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL"}

    config_dir = Path.home() / ".config" / "mcnb"
    target = config_dir / "env"

    if target.exists() and not force:
        print(f"✓ Credentials already at {target}")
        print("  To overwrite: setup_env(force=True)")
        return True

    template_path = _ROOT / template
    if not template_path.exists():
        print(f"✗ Template not found: {template_path}")
        print(f"  Upload '{template}' to the repo root, then retry.")
        return False

    print(f"Credential setup — template: {template}")
    print("─" * 50)
    print("Press Enter to keep default shown in [brackets].\n")

    lines = template_path.read_text().splitlines()
    output = []
    prompted = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output.append(line)
            continue

        key, _, val = stripped.partition("=")
        key, val = key.strip(), val.strip()
        is_secret = any(h in key.upper() for h in _SECRETS)

        if val == "REPLACE_ME":
            entered = (
                _gp.getpass(f"  {key}: ")
                if is_secret
                else input(f"  {key}: ").strip()
            )
            output.append(f"{key}={entered}")
            prompted += 1
        else:
            if is_secret:
                entered = _gp.getpass(f"  {key} [keep existing, hidden]: ")
                output.append(f"{key}={entered or val}")
            else:
                entered = input(f"  {key} [{val}]: ").strip()
                output.append(f"{key}={entered or val}")

    if prompted == 0:
        print("No REPLACE_ME values found — nothing to configure.")
        return False

    config_dir.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(output) + "\n")
    print(f"\n✓ Credentials saved to {target}")
    _load_file(target)
    return True
