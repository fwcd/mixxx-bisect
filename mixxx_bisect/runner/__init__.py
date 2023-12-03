from pathlib import Path
from typing import Protocol

from mixxx_bisect.options import Options

class SnapshotRunner(Protocol):
    '''A platform-dependent facility for extracting and running snapshots.'''

    def __init__(self, opts: Options):
        pass

    @property
    def suffix(self) -> str:
        '''The file extension for the downloaded artifact.'''
        raise NotImplementedError()

    @property
    def download_path(self) -> Path:
        '''The path to download to.'''
        raise NotImplementedError()

    def setup_snapshot(self) -> None:
        '''Extracts or mounts the snapshot.'''
        raise NotImplementedError()
    
    def run_snapshot(self) -> None:
        '''Runs the snapshot.'''
        raise NotImplementedError()
    
    def cleanup_snapshot(self) -> None:
        '''Cleans up the snapshot.'''
        raise NotImplementedError()
