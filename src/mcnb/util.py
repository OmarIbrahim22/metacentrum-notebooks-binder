"""
Utility functions for MetaCentrum/e-INFRA notebooks.
"""
import importlib.util
import os
import platform
import subprocess
from typing import Dict, List, Optional


def check_deps(deps: Dict[str, str]) -> List[str]:
    """
    Check which of the given dependencies are importable, without installing
    anything.

    Args:
        deps: mapping of {pip_package_name: importable_module_name}

    Returns:
        List of pip package names that are NOT importable (empty if all present).
    """
    return [
        pip_name
        for pip_name, import_name in deps.items()
        if importlib.util.find_spec(import_name) is None
    ]


def require_deps(deps: Dict[str, str], extra: Optional[str] = None) -> None:
    """
    Raise ImportError with a copy-pasteable install command if any of `deps`
    is missing. Never installs anything itself — notebooks must never run
    pip on the user's behalf.

    Args:
        deps: mapping of {pip_package_name: importable_module_name}
        extra: name of the pyproject.toml optional-dependency group that
            provides these packages (e.g. "s3"), or None for the base install.
    """
    missing = check_deps(deps)
    if not missing:
        return
    cmd = f'pip install -e ".[{extra}]"' if extra else "pip install -e ."
    raise ImportError(
        "Missing dependencies: " + ", ".join(missing) + "\n\n"
        "Install them by running this in a terminal (repo root):\n"
        f"  {cmd}\n\n"
        "Then re-run this cell (no kernel restart needed)."
    )


def fmt_error(e: Exception, label: str = None) -> str:
    """
    Format any exception into a consistent, never-empty error string.

    Args:
        e: The exception to format
        label: Optional context label (e.g. "upload", "list buckets")

    Returns:
        A string like "✗ label: ExceptionType: message"
    """
    exc_type = type(e).__name__
    msg = str(e) if str(e) else repr(e)
    if label:
        return f"✗ {label}: {exc_type}: {msg}"
    return f"✗ {exc_type}: {msg}"


def safe_get(d: dict, *keys, default="<missing>"):
    """
    Safely walk a nested dict, returning default if any key is absent.

    Args:
        d: The dict to walk
        *keys: Sequence of keys to traverse
        default: Value to return when a key is missing

    Example:
        safe_get(e.response, "Error", "Code", default="UNKNOWN")
    """
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        if key not in current:
            return default
        current = current[key]
    return current


def run(cmd: str, timeout: int = 30, check: bool = True) -> str:
    """
    Run a shell command safely and return its output.

    Args:
        cmd: Command to execute
        timeout: Timeout in seconds (default: 30)
        check: Whether to raise on non-zero exit (default: True)

    Returns:
        Command output as string

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        return result.stdout.strip() or result.stderr.strip()
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.stdout.strip() or e.stderr.strip()
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"


def print_section(title: str, char: str = "=", width: int = 60) -> None:
    """
    Print a formatted section header for notebook output.

    Args:
        title: Section title
        char: Character to use for the line (default: "=")
        width: Total width of the header (default: 60)

    Example:
        >>> print_section("Setup")
        ============================================================
        Setup
        ============================================================
    """
    line = char * width
    print(f"\n{line}")
    print(title)
    print(f"{line}\n")


def detect_environment() -> dict:
    """
    Best-effort detection of the runtime environment.

    Returns:
        Dictionary with environment information:
        - platform: OS platform
        - python_version: Python version
        - is_jupyter: Whether running in Jupyter
        - is_metacentrum: Best guess if on MetaCentrum
        - is_e_infra: Best guess if on e-INFRA
        - hostname: System hostname
        - home: Home directory
        - cwd: Current working directory
    """
    _sentinel = "<detection failed>"
    try:
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "is_jupyter": _is_jupyter(),
            "is_metacentrum": _is_metacentrum(),
            "is_e_infra": _is_e_infra(),
            "hostname": platform.node(),
            "home": os.path.expanduser("~"),
            "cwd": os.getcwd(),
        }
    except Exception as e:
        info = {
            "platform": _sentinel,
            "python_version": _sentinel,
            "is_jupyter": False,
            "is_metacentrum": False,
            "is_e_infra": False,
            "hostname": _sentinel,
            "home": _sentinel,
            "cwd": _sentinel,
            "_error": fmt_error(e, label="detect_environment"),
        }
    return info


def _is_jupyter() -> bool:
    """Check if running in a Jupyter environment."""
    try:
        from IPython import get_ipython

        return get_ipython() is not None
    except ImportError:
        return False


def _is_metacentrum() -> bool:
    """Best-effort check if running on MetaCentrum."""
    # Check for common MetaCentrum environment indicators
    hostname = platform.node().lower()
    home = os.path.expanduser("~")

    # MetaCentrum hostnames often contain "metacentrum" or specific patterns
    if "metacentrum" in hostname or "ondemand" in hostname:
        return True

    # Check for MetaCentrum-specific paths
    if "/storage/" in home or home.startswith("/auto/"):
        return True

    # Check environment variables
    if os.getenv("METACENTRUM_ENV") or os.getenv("PBS_JOBID"):
        return True

    return False


def _is_e_infra() -> bool:
    """Best-effort check if running on e-INFRA CZ infrastructure."""
    hostname = platform.node().lower()

    # Check for e-INFRA hostnames
    if "e-infra" in hostname or "cerit" in hostname or "jupyter" in hostname:
        return True

    # Check for JupyterHub environment variables
    if os.getenv("JUPYTERHUB_USER") or os.getenv("JUPYTERHUB_API_TOKEN"):
        return True

    return False


def check_gpu_available() -> dict:
    """
    Check if GPU is available and get basic info.

    Returns:
        Dictionary with GPU information:
        - available: Whether nvidia-smi is available
        - output: nvidia-smi output or error message
        - devices: List of /dev/nvidia* devices
    """
    gpu_info = {
        "available": False,
        "output": "",
        "devices": [],
    }

    # Try nvidia-smi
    try:
        output = run("nvidia-smi", timeout=5, check=False)
        if output and "NVIDIA-SMI" in output:
            gpu_info["available"] = True
            gpu_info["output"] = output
    except Exception as e:
        gpu_info["output"] = f"nvidia-smi not available: {e}"

    # Check for /dev/nvidia* devices
    try:
        import glob

        gpu_info["devices"] = glob.glob("/dev/nvidia*")
    except Exception:
        pass

    return gpu_info


def format_env_report(env_info: dict) -> str:
    """
    Format environment detection info as a readable report.

    Args:
        env_info: Dictionary from detect_environment()

    Returns:
        Formatted string report
    """
    report = []
    report.append("Environment Report")
    report.append("=" * 60)
    report.append(f"Platform: {env_info.get('platform', '<unknown>')}")
    report.append(f"Python Version: {env_info.get('python_version', '<unknown>')}")
    report.append(f"Hostname: {env_info.get('hostname', '<unknown>')}")
    report.append(f"Home Directory: {env_info.get('home', '<unknown>')}")
    report.append(f"Working Directory: {env_info.get('cwd', '<unknown>')}")
    report.append("")
    report.append("Environment Detection:")
    report.append(f"  Jupyter: {'Yes' if env_info.get('is_jupyter') else 'No'}")
    report.append(f"  MetaCentrum: {'Yes (likely)' if env_info.get('is_metacentrum') else 'No'}")
    report.append(f"  e-INFRA: {'Yes (likely)' if env_info.get('is_e_infra') else 'No'}")
    if env_info.get("_error"):
        report.append("")
        report.append(f"  Warning: {env_info['_error']}")
    report.append("=" * 60)

    return "\n".join(report)
