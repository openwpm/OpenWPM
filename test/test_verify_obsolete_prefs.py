import os
import subprocess
import sys
from pathlib import Path

from openwpm.utilities.platform_utils import get_firefox_binary_path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "verify_obsolete_prefs.py"


def test_every_default_pref_is_defined_by_the_pinned_firefox():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        env={**os.environ, "FIREFOX_BINARY": get_firefox_binary_path()},
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout + result.stderr
