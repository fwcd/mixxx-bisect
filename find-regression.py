#!/usr/bin/env python3

import requests

from bs4 import BeautifulSoup

def get_soup(url: str) -> BeautifulSoup:
    headers = {'User-Agent': 'MixxxRegressionFinder/0.0.1'}
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.content, 'html.parser')

def main():
    snapshot_soup = get_soup('https://downloads.mixxx.org/snapshots/main/')
    links = [a.get('href') for a in snapshot_soup.select('a')]
    snapshots = [link for link in links if link.endswith('.dmg')]
    print('\n'.join(snapshots))

if __name__ == '__main__':
    main()
