from pathlib import Path

from mixxx_bisect.runner import SnapshotRunner
from mixxx_bisect.options import Options
from mixxx_bisect.utils.run import run

class MacOSSnapshotRunner(SnapshotRunner):
    def __init__(self, opts: Options):
        self.mount_dir = opts.installs_dir / 'mnt'
        self.opts = opts

    @property
    def suffix(self) -> str:
        return '.dmg'
    
    @property
    def download_path(self) -> Path:
        return self.opts.downloads_dir / f'mixxx-current{self.suffix}'
    
    @property
    def cdr_path(self) -> Path:
        return self.download_path.with_suffix('.cdr')

    def _mount_snapshot(self):
        print('Mounting snapshot...')
        self.mount_dir.mkdir(parents=True, exist_ok=True)
        self.cdr_path.unlink(missing_ok=True)
        run(['hdiutil', 'convert', str(self.download_path), '-format', 'UDTO', '-o', str(self.cdr_path)], opts=self.opts)
        run(['hdiutil', 'attach', str(self.cdr_path), '-mountpoint', str(self.mount_dir)], opts=self.opts)

    def _unmount_snapshot(self):
        print('Unmounting snapshot...')
        run(['hdiutil', 'unmount', str(self.mount_dir)], cwd=self.mount_dir.parent, opts=self.opts)

    def _delete_snapshot(self):
        print('Deleting snapshot...')
        self.download_path.unlink(missing_ok=True)
        self.cdr_path.unlink(missing_ok=True)

    def setup_snapshot(self):
        self._mount_snapshot()

    def run_snapshot(self):
        print('Running snapshot...')
        run([str(self.mount_dir / 'mixxx.app' / 'Contents' / 'MacOS' / 'mixxx')], opts=self.opts)
    
    def cleanup_snapshot(self):
        self._unmount_snapshot()
        self._delete_snapshot()
