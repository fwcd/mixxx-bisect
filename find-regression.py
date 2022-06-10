#!/usr/bin/env python3

import requests

from bs4 import BeautifulSoup

SNAPSHOTS_URL = 'https://downloads.mixxx.org/snapshots/main/'
SUFFIX = '.dmg'

def get_soup(url: str) -> BeautifulSoup:
    headers = {'User-Agent': 'MixxxRegressionFinder/0.0.1'}
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

def parse_commit(link: str):
    name = link.split('/')[-1].removesuffix(SUFFIX).removesuffix('-macosintel')
    return name.split('-')[-1]

def main():
    snapshot_soup = get_soup(SNAPSHOTS_URL)
    links = [a.get('href') for a in snapshot_soup.select('a')]
    snapshots = [(parse_commit(link), link) for link in links if link.endswith(SUFFIX)]
    print('\n'.join(commit + ', ' + link for commit, link in snapshots))

if __name__ == '__main__':
    main()
