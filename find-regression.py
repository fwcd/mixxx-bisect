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
    raw_commit = name.split('-')[-1]
    # Slightly hacky, we rely on the fact that commit hashes are no longer than 10
    # characters to strip out the 'g' that the commit revision in newer Mixxx downloads
    # begin with.
    return raw_commit[-10:]

def fetch_snapshots() -> dict[str, str]:
    snapshot_soup = get_soup(SNAPSHOTS_URL)
    links = [a.get('href') for a in snapshot_soup.select('a')]
    return {parse_commit_from_link(link): link for link in links if link.endswith(SUFFIX)}

def clone_mixxx():
    if not MIXXX_DIR.exists():
        print('==> Cloning Mixxx...')
        subprocess.run(['git', 'clone', '--bare', 'https://github.com/mixxxdj/mixxx.git', str(MIXXX_DIR)], cwd=BASE_DIR)

def sort_commits(commits: list[str]) -> list[str]:
    print(commits)
    raw = subprocess.run(['git', 'rev-list', '--no-walk'] + commits, cwd=MIXXX_DIR, capture_output=True, encoding='utf8').stdout
    return raw.splitlines()[::-1]

def parse_commit(rev: str) -> str:
    raw = subprocess.run(['git', 'rev-parse', rev], cwd=MIXXX_DIR, capture_output=True, encoding='utf8').stdout
    return raw.splitlines()[0]

def commits_in_order(commits: list[str]) -> bool:
    return commits == sort_commits(commits)

def main():
    parser = argparse.ArgumentParser(description='Finds Mixxx regressions using binary search')
    parser.add_argument('-g', '--good', help='The lower bound of the commit range (a good commit)')
    parser.add_argument('-b', '--bad', help='The upper bound of the commit range (a bad commit)')

    args = parser.parse_args()

    clone_mixxx()

    snapshots = fetch_snapshots()
    commits = sort_commits(list(snapshots.keys()))

    good = parse_commit(args.good or commits[0])
    bad = parse_commit(args.bad or commits[-1])

    if good == bad or not commits_in_order([good, bad]):
        print('Please make sure that good < bad!')
        sys.exit(1)

    try:
        good_idx = commits.index(good)
    except ValueError:
        print(f'Good commit {good} has no associated snapshot!')
        sys.exit(1)
    try:
        bad_idx = commits.index(bad)
    except ValueError:
        print(f'Bad commit {bad} has no associated snapshot!')
        sys.exit(1)

    # Binary search over the commits
    while good_idx < bad_idx - 1:
        print(f'==> Searching {good} to {bad}...')
        # TODO
        break

    print(f'Last good: {commits[good_idx]}')
    print(f'First bad: {commits[bad_idx]}')

if __name__ == '__main__':
    main()
