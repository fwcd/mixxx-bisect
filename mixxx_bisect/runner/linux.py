from pathlib import Path

from mixxx_bisect.options import Options
from mixxx_bisect.runner import SnapshotRunner
from mixxx_bisect.utils.run import run

import shutil

class LinuxSnapshotRunner(SnapshotRunner):
    def __init__(self, opts: Options):
        self.mount_dir = opts.mount_dir
        self.install_dir = opts.mount_dir / 'mixxx'
        self.opts = opts
    
    @property
    def suffix(self) -> str:
        return '.tar.gz'

    @property
    def download_path(self) -> Path:
        return self.opts.downloads_dir / f'mixxx-current{self.suffix}'

    def setup_snapshot(self):
        print('Extracting snapshot...')
        shutil.unpack_archive(self.download_path, self.install_dir)

    def run_snapshot(self):
        print('Running snapshot...')
        run([str(self.install_dir / 'bin' / 'mixxx')], opts=self.opts)
    
    def cleanup_snapshot(self):
        print('Cleaning up snapshot...')
        shutil.rmtree(self.install_dir)
