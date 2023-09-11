from pathlib import Path
from typing import Optional

from mixxx_bisect.options import Options

import subprocess

def run(cmd: list[str], opts: Options, cwd: Optional[Path]=None):
    subprocess.run(
        cmd,
        cwd=cwd or opts.root_dir,
        stdout=subprocess.DEVNULL if opts.quiet else None,
        stderr=subprocess.DEVNULL if opts.quiet else None,
    )

def run_with_output(cmd: list[str], opts: Options, cwd: Optional[Path]=None) -> list[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd or opts.root_dir,
        check=True,
        capture_output=True,
        encoding='utf8',
    )
    return result.stdout.splitlines()
