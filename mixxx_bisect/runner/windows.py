from pathlib import Path

from mixxx_bisect.options import Options
from mixxx_bisect.runner import SnapshotRunner
from mixxx_bisect.utils.run import run

import shutil

class WindowsSnapshotRunner(SnapshotRunner):
    def __init__(self, opts: Options):
        self.install_dir = opts.installs_dir / 'Mixxx'
        self.opts = opts
    
    @property
    def suffix(self) -> str:
        return '.msi'

    @property
    def download_path(self) -> Path:
        return self.opts.downloads_dir / f'mixxx-current{self.suffix}'

    def setup_snapshot(self):
        print('Extracting snapshot...')
        run([
            'msiexec',
            '/a', str(self.download_path),           # Install the msi
            '/q',                                    # Install quietly i.e. without GUI
            f'TARGETDIR={self.opts.installs_dir}',                # Install to custom target dir
            '/li', str(self.opts.log_dir / 'msi-install.log'), # Log installation to file
        ], opts=self.opts)

    def run_snapshot(self):
        print('Running snapshot...')
        run([str(self.install_dir / 'mixxx.exe')], opts=self.opts)

    def cleanup_snapshot(self):
        print('Cleaning up snapshot...')
        for path in self.opts.installs_dir.iterdir():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
