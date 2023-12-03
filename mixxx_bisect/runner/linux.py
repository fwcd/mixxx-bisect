from pathlib import Path

from mixxx_bisect.options import Options
from mixxx_bisect.runner import SnapshotRunner
from mixxx_bisect.utils.run import run

import shutil

class LinuxSnapshotRunner(SnapshotRunner):
    def __init__(self, opts: Options):
        self.opts = opts
    
    @property
    def suffix(self) -> str:
        return '.tar.gz'

    @property
    def download_path(self) -> Path:
        return self.opts.downloads_dir / f'mixxx-current{self.suffix}'

    def setup_snapshot(self):
        print('Extracting snapshot...')
        shutil.unpack_archive(self.download_path, self.opts.installs_dir)

    def run_snapshot(self):
        print('Running snapshot...')
        child_dirs = list(self.opts.installs_dir.iterdir())
        assert len(child_dirs) == 1, 'Mixxx should be extracted to exactly one folder'
        mixxx_dir = child_dirs[0]
        run([str(mixxx_dir / 'bin' / 'mixxx')], opts=self.opts)
    
    def cleanup_snapshot(self):
        print('Cleaning up snapshot...')
        for path in self.opts.installs_dir.iterdir():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
