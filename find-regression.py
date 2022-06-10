#!/usr/bin/env python3

import argparse
import requests
import subprocess
import sys

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

def parse_commit_from_link(link: str) -> str:
    name = link.split('/')[-1].removesuffix(SUFFIX).removesuffix('-macosintel')
    return name.split('-')[-1]

def fetch_snapshots() -> dict[str, str]:
    snapshot_soup = get_soup(SNAPSHOTS_URL)
    links = [a.get('href') for a in snapshot_soup.select('a')]
    return {parse_commit_from_link(link): link for link in links if link.endswith(SUFFIX)}

def clone_mixxx():
    if not MIXXX_DIR.exists():
        print('==> Cloning Mixxx...')
        subprocess.run(['git', 'clone', '--bare', 'https://github.com/mixxxdj/mixxx.git', str(MIXXX_DIR)], cwd=BASE_DIR)

def sort_commits(commits: list[str]) -> list[str]:
    raw = subprocess.run(['git', 'rev-list', '--no-walk'] + commits, cwd=MIXXX_DIR, capture_output=True, encoding='utf8').stdout
    return raw.splitlines()[::-1]

def parse_commit(rev: str) -> str:
    raw = subprocess.run(['git', 'rev-parse', rev], cwd=MIXXX_DIR, capture_output=True, encoding='utf8').stdout
    return raw.splitlines()[0]

def main():
    parser = argparse.ArgumentParser(description='Finds Mixxx regressions using binary search')
    parser.add_argument('-g', '--good', required=True, help='The lower bound of the commit range (a good commit)')
    parser.add_argument('-b', '--bad', default='HEAD', help='The upper bound of the commit range (a bad commit)')

    args = parser.parse_args()

    clone_mixxx()

    good = parse_commit(args.good)
    bad = parse_commit(args.bad)

    if sort_commits([good, bad]) != [good, bad]:
        print('Please make sure that good < bad!')
        sys.exit(1)

    print(f'==> Searching {good} to {bad}...')

if __name__ == '__main__':
    main()
