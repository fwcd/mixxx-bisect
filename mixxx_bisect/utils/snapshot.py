from pathlib import Path
from typing import Optional, cast

from mixxx_bisect.options import Options
from mixxx_bisect.utils.git import try_parse_commit
from mixxx_bisect.utils.request import download, get_soup

import re

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

def fetch_snapshots(snapshots_url: str, suffix: str, opts: Options) -> dict[str, str]:
    print(f'==> Fetching snapshots from {snapshots_url}...')
    snapshot_soup = get_soup(snapshots_url)
    links = [cast(str, a.get('href')) for a in snapshot_soup.select('a')]
    commits = [parse_commit_from_name(link.split('/')[-1], suffix) for link in links]
    parsed_commits = [try_parse_commit(commit, opts) if commit else None for commit in commits]
    return {
        commit: f'{snapshots_url}/{link}'
        for commit, link in zip(parsed_commits, links)
        if commit and link.endswith(suffix)
    }

def download_snapshot(url: str, download_path: Path):
    print(f'Downloading snapshot...')
    download(url, download_path)
