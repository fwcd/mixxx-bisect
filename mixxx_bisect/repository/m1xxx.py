from typing import Optional, cast
from mixxx_bisect.error import UnsupportedArchError, UnsupportedOSError

from mixxx_bisect.repository import SnapshotRepository
from mixxx_bisect.options import Options
from mixxx_bisect.utils.git import try_parse_commit
from mixxx_bisect.utils.request import get

import re

RELEASES_API_URL = 'https://api.github.com/repos/fwcd/m1xxx/releases'

class M1xxxSnapshotRepository(SnapshotRepository):
    def __init__(self, branch: str, suffix: str, opts: Options):
        self.suffix = suffix
        self.opts = opts

        arch = {
            'arm64': 'arm64',
            'aarch64': 'arm64',
            'x86_64': 'x64',
            'x86-64': 'x64',
        }.get(opts.arch)

        if arch is None:
            raise UnsupportedArchError(f'The architecture {opts.arch} is not supported by the m1xxx repository.')

        os = {
            'Darwin': 'osx',
            'Linux': 'linux',
        }.get(opts.os)

        if os is None:
            raise UnsupportedOSError(f'The os {opts.os} is not supported by the m1xxx repository.')
        
        # TODO: Should we use the 'debugasserts' variant? Perhaps as an optional flag?
        base_triplet_pattern = re.escape(arch) + r'-' + re.escape(os) + r'(?:-min\d+)?(?:-release)?'

        self.snapshot_name_patterns = [
            # Newer pattern, e.g. mixxx-2.5.0.c45818.r30bca40dad-arm64-osx-min1100-release
            re.compile(r'^mixxx-[\d\.]+\.c\d+\.r(\w+)-' + base_triplet_pattern + r'$'),
            # New pattern, e.g. mixxx-arm64-osx-min1100-2.5.0.c45818.r30bca40dad
            re.compile(r'^mixxx-' + base_triplet_pattern + r'-[\d\.]+\.c\d+\.r(\w+)$'),
            # Old pattern, e.g. mixxx-2.5.0.c45816.r7c1bb1b997
            *([re.compile(r'^mixxx-[\d\.]+\.c\d+\.r(\w+)$')] if arch == 'arm64' else []),
        ]
    
    def fetch_snapshots(self) -> dict[str, str]:
        print(f'==> Fetching snapshots from {RELEASES_API_URL}...')
        # TODO: Proper paging over more than the latest 100 snapshots
        releases = get(f'{RELEASES_API_URL}?per_page=100', json=True).json()
        urls = [
            asset['browser_download_url']
            for release in releases
            for asset in release.get('assets', [])
            if cast(str, asset['name']).endswith(self.suffix)
        ]
        commits = [self._parse_commit_from_name(url.split('/')[-1], self.suffix) for url in urls]
        parsed_commits = [try_parse_commit(commit, self.opts) if commit else None for commit in commits]
        return {
            commit: url
            for commit, url in zip(parsed_commits, urls)
            if commit and url.endswith(self.suffix)
        }

    def _parse_commit_from_name(self, name: str, suffix: str) -> Optional[str]:
        name = name.removesuffix(suffix)
        for pattern in self.snapshot_name_patterns:
            matches = pattern.search(name)
            if matches:
                return matches[1]
        return None
