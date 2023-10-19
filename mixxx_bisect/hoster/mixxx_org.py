from typing import Optional, cast

from mixxx_bisect.hoster import SnapshotHoster
from mixxx_bisect.options import Options
from mixxx_bisect.utils.git import try_parse_commit
from mixxx_bisect.utils.request import get_soup

import re

SNAPSHOTS_BASE_URL = 'https://downloads.mixxx.org/snapshots/'
SNAPSHOT_NAME_PATTERNS = [
    # Old pattern, e.g. mixxx-main-r7715-a0f80e8464
    re.compile(r'^mixxx-[\w\.]+-r\d+-(\w+)$'),
    # New pattern, e.g. mixxx-2.4-alpha-6370-g44f29763ed-macosintel
    re.compile(r'^mixxx-[\d\.]+(?:-[a-z]+)?-\d+-g(\w+)-\w+$'),
]

def parse_commit_from_name(name: str, suffix: str) -> Optional[str]:
    name = name.removesuffix(suffix)
    for pattern in SNAPSHOT_NAME_PATTERNS:
        matches = pattern.search(name)
        if matches:
            return matches[1]
    return None

class MixxxOrgSnapshotHoster(SnapshotHoster):
    def __init__(self, branch: str, suffix: str, opts: Options):
        self.snapshots_url = f'{SNAPSHOTS_BASE_URL}{branch}/'
        self.branch = branch
        self.suffix = suffix
        self.opts = opts
    
    def fetch_snapshots(self) -> dict[str, str]:
        print(f'==> Fetching snapshots from {self.snapshots_url}...')
        snapshot_soup = get_soup(self.snapshots_url)
        links = [cast(str, a.get('href')) for a in snapshot_soup.select('a')]
        commits = [parse_commit_from_name(link.split('/')[-1], self.suffix) for link in links]
        parsed_commits = [try_parse_commit(commit, self.opts) if commit else None for commit in commits]
        return {
            commit: f'{self.snapshots_url}/{link}'
            for commit, link in zip(parsed_commits, links)
            if commit and link.endswith(self.suffix)
        }
