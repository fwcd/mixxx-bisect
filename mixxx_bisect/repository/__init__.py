from typing import Protocol

from mixxx_bisect.options import Options

class SnapshotRepository(Protocol):
    '''A repository/archive of (binary) Mixxx snapshots, usually hosted on the web.'''

    def __init__(self, branch: str, suffix: str, opts: Options):
        pass

    def fetch_snapshots(self) -> dict[str, str]:
        '''Fetches the snapshots as a dictionary from commit SHAs to URLs..'''
        raise NotImplementedError()
