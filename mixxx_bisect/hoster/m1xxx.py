from typing import Optional, cast

from mixxx_bisect.hoster import SnapshotHoster
from mixxx_bisect.options import Options
from mixxx_bisect.utils.git import try_parse_commit
from mixxx_bisect.utils.request import get

import re

RELEASES_API_URL = 'https://api.github.com/repos/fwcd/m1xxx/releases'
SNAPSHOT_NAME_PATTERNS = [
    # New pattern, e.g. mixxx-arm64-osx-min1100-2.5.0.c45818.r30bca40dad
    re.compile(r'^mixxx-\w+-osx-min\d+-[\d\.]+\.c\d+\.r(\w+)$'),
    # Old pattern, e.g. mixxx-2.5.0.c45816.r7c1bb1b997
    re.compile(r'^mixxx-[\d\.]+\.c\d+\.r(\w+)$'),
]

def parse_commit_from_name(name: str, suffix: str) -> Optional[str]:
    name = name.removesuffix(suffix)
    for pattern in SNAPSHOT_NAME_PATTERNS:
        matches = pattern.search(name)
        if matches:
            return matches[1]
    return None

class M1xxxSnapshotHoster(SnapshotHoster):
    def __init__(self, branch: str, suffix: str, opts: Options):
        self.suffix = suffix
        self.opts = opts
    
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
        commits = [parse_commit_from_name(url.split('/')[-1], self.suffix) for url in urls]
        parsed_commits = [try_parse_commit(commit, self.opts) if commit else None for commit in commits]
        return {
            commit: url
            for commit, url in zip(parsed_commits, urls)
            if commit and url.endswith(self.suffix)
        }
