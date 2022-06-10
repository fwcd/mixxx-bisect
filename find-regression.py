#!/usr/bin/env python3

import requests
import subprocess

from bs4 import BeautifulSoup
from pathlib import Path

SNAPSHOTS_URL = 'https://downloads.mixxx.org/snapshots/main/'
SUFFIX = '.dmg'
BASE_DIR = Path(__file__).resolve().parent
MIXXX_DIR = BASE_DIR / 'mixxx.git'

def get_soup(url: str) -> BeautifulSoup:
    headers = {'User-Agent': 'MixxxRegressionFinder/0.0.1'}
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

def parse_commit(link: str) -> str:
    name = link.split('/')[-1].removesuffix(SUFFIX).removesuffix('-macosintel')
    return name.split('-')[-1]

def fetch_snapshots() -> dict[str, str]:
    snapshot_soup = get_soup(SNAPSHOTS_URL)
    links = [a.get('href') for a in snapshot_soup.select('a')]
    return {parse_commit(link): link) for link in links if link.endswith(SUFFIX)}

def clone_mixxx():
    if not MIXXX_DIR.exists():
        print('==> Cloning Mixxx...')
        subprocess.run(['git', 'clone', '--bare', 'https://github.com/mixxxdj/mixxx.git', str(MIXXX_DIR)], cwd=BASE_DIR)

def sort_commits(commits: list[str]) -> list[str]:
    raw = subprocess.run(['git', 'rev-list', '--no-walk'] + commits, cwd=MIXXX_DIR, capture_output=True, encoding='utf8').stdout
    return raw.splitlines()

def main():
    clone_mixxx()

if __name__ == '__main__':
    main()
