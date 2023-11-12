from dataclasses import dataclass
from pathlib import Path

@dataclass
class Options:
    quiet: bool
    verbose: bool
    root_dir: Path
    mixxx_dir: Path
    mount_dir: Path
    log_dir: Path
    downloads_dir: Path
