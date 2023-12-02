from dataclasses import dataclass
from pathlib import Path

@dataclass
class Options:
    quiet: bool
    verbose: bool
    os: str
    arch: str
    root_dir: Path
    mixxx_dir: Path
    installs_dir: Path
    log_dir: Path
    downloads_dir: Path
