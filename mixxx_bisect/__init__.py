import argparse
import platform
import re
import requests
import shutil
import subprocess
import sys

from bs4 import BeautifulSoup
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SNAPSHOTS_BASE_URL = 'https://downloads.mixxx.org/snapshots/'

# TODO: Make the base directory customizable
BASE_DIR = Path.home() / '.local' / 'state' / 'mixxx-bisect'
MIXXX_DIR = BASE_DIR / 'mixxx.git'
MOUNT_DIR = BASE_DIR / 'mnt'
LOG_DIR = BASE_DIR / 'log'
DOWNLOADS_DIR = BASE_DIR / 'downloads'

OS = platform.system()

SNAPSHOT_NAME_PATTERNS = [
    # Old pattern, e.g. mixxx-main-r7715-a0f80e8464
    re.compile(r'^mixxx-[\w\.]+-r\d+-(\w+)$'),
    # New pattern, e.g. mixxx-2.4-alpha-6370-g44f29763ed-macosintel
    re.compile(r'^mixxx-[\d\.]+(?:-[a-z]+)?-\d+-g(\w+)-\w+$'),
]

@dataclass
class Options:
    quiet: bool

# Utilities

def run(cmd: list[str], opts: Options, cwd=BASE_DIR):
    subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.DEVNULL if opts.quiet else None,
        stderr=subprocess.DEVNULL if opts.quiet else None,
    )

def run_with_output(cmd: list[str], cwd=BASE_DIR) -> list[str]:
    result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, encoding='utf8')
    return result.stdout.splitlines()

def get(url: str) -> bytes:
    headers = {'User-Agent': 'MixxxRegressionFinder/0.0.1'}
    response = requests.get(url, headers=headers)
    return response.content

def get_soup(url: str) -> BeautifulSoup:
    raw = get(url)
    return BeautifulSoup(raw, 'html.parser')

# Git utils

def clone_mixxx(opts: Options):
    if MIXXX_DIR.exists():
        print('==> Fetching Mixxx...')
        run(['git', 'fetch', 'origin'], opts=opts, cwd=MIXXX_DIR)
    else:
        print('==> Cloning Mixxx...')
        run(['git', 'clone', '--bare', 'https://github.com/mixxxdj/mixxx.git', str(MIXXX_DIR)], opts=opts)

def sort_commits(commits: list[str]) -> list[str]:
    # Windows doesn't like passing too many (long) args, so we truncate commit hashes to 8 chars
    commits = [commit[:8] for commit in commits]
    lines = run_with_output(['git', 'rev-list', '--no-walk'] + commits, cwd=MIXXX_DIR)
    return lines[::-1]

def parse_commit(rev: str) -> str:
    lines = run_with_output(['git', 'rev-parse', rev], cwd=MIXXX_DIR)
    return lines[0]

def try_parse_commit(rev: str) -> Optional[str]:
    try:
        return parse_commit(rev)
    except subprocess.CalledProcessError:
        return None

def show_commit(rev: str, format: str) -> str:
    lines = run_with_output(['git', 'show', '-s', f'--format={format}', rev], cwd=MIXXX_DIR)
    return lines[0]

def describe_commit(rev: str) -> str:
    commit = parse_commit(rev)
    return f"{commit[:10]} from {show_commit(rev, '%ci')} ({show_commit(rev, '%s')})"

def commits_in_order(commits: list[str]) -> bool:
    return commits == sort_commits(commits)

# Snapshot utils

def parse_commit_from_name(name: str, suffix: str) -> Optional[str]:
    name = name.removesuffix(suffix)
    for pattern in SNAPSHOT_NAME_PATTERNS:
        matches = pattern.search(name)
        if matches:
            return matches[1]
    return None

def fetch_snapshots(snapshots_url: str, suffix: str) -> dict[str, str]:
    print(f'==> Fetching snapshots from {snapshots_url}...')
    snapshot_soup = get_soup(snapshots_url)
    links = [a.get('href') for a in snapshot_soup.select('a')]
    commits = [parse_commit_from_name(link.split('/')[-1], suffix) for link in links]
    parsed_commits = [try_parse_commit(commit) if commit else None for commit in commits]
    return {
        commit: f'{snapshots_url}/{link}'
        for commit, link in zip(parsed_commits, links)
        if commit and link.endswith(suffix)
    }

def download_snapshot(url: str, download_path: Path):
    print(f'Downloading snapshot...')
    raw = get(url)
    with open(download_path, 'wb') as f:
        f.write(raw)

# Platform-specific snapshot runners

class WindowsSnapshotRunner:
    def __init__(self, downloads_dir: Path, mount_dir: Path, opts: Options):
        self.download_path = downloads_dir / 'mixxx-current.msi'
        self.mount_dir = mount_dir
        self.install_dir = mount_dir / 'Mixxx'
        self.opts = opts

    def setup_snapshot(self):
        print('Extracting snapshot...')
        run([
            'msiexec',
            '/a', str(self.download_path),           # Install the msi
            '/q',                                    # Install quietly i.e. without GUI
            f'TARGETDIR={MOUNT_DIR}',                # Install to custom target dir
            '/li', str(LOG_DIR / 'msi-install.log'), # Log installation to file
        ], opts=self.opts)

    def run_snapshot(self):
        print('Running snapshot...')
        run([str(self.install_dir / 'mixxx.exe')], opts=self.opts)

    def cleanup_snapshot(self):
        print('Cleaning up snapshot...')
        for path in MOUNT_DIR.iterdir():
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
    
class MacOSSnapshotRunner:
    def __init__(self, downloads_dir: Path, mount_dir: Path, opts: Options):
        self.download_path = downloads_dir / 'mixxx-current.dmg'
        self.cdr_path = self.download_path.with_suffix('.cdr')
        self.mount_dir = mount_dir
        self.opts = opts

    def _mount_snapshot(self):
        print('Mounting snapshot...')
        self.cdr_path.unlink(missing_ok=True)
        run(['hdiutil', 'convert', str(self.download_path), '-format', 'UDTO', '-o', str(self.cdr_path)], opts=self.opts)
        run(['hdiutil', 'attach', str(self.cdr_path), '-mountpoint', str(self.mount_dir)], opts=self.opts)

    def _unmount_snapshot(self):
        print('Unmounting snapshot...')
        run(['hdiutil', 'unmount', str(self.mount_dir)], cwd=self.mount_dir.parent, opts=self.opts)

    def _delete_snapshot(self):
        print('Deleting snapshot...')
        self.download_path.unlink(missing_ok=True)
        self.cdr_path.unlink(missing_ok=True)

    def setup_snapshot(self):
        self._mount_snapshot()

    def run_snapshot(self):
        print('Running snapshot...')
        run([str(self.mount_dir / 'mixxx.app' / 'Contents' / 'MacOS' / 'mixxx')], opts=self.opts)
    
    def cleanup_snapshot(self):
        self._unmount_snapshot()
        self._delete_snapshot()

SNAPSHOT_RUNNERS = {
    'Windows': WindowsSnapshotRunner,
    'Darwin': MacOSSnapshotRunner,
}

if OS not in SNAPSHOT_RUNNERS.keys():
    print(f"Unsupported OS: {OS} has no snapshot runner (supported are {', '.join(SNAPSHOT_RUNNERS.values())})")
    sys.exit(1)

SnapshotRunner = SNAPSHOT_RUNNERS[OS]

# Main

def main():
    parser = argparse.ArgumentParser(description='Finds Mixxx regressions using binary search')
    parser.add_argument('--branch', default='main', help=f'The branch to search for snapshots on. Can be anything in {SNAPSHOTS_BASE_URL}')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output from subprocesses.')
    parser.add_argument('-g', '--good', help='The lower bound of the commit range (a good commit)')
    parser.add_argument('-b', '--bad', help='The upper bound of the commit range (a bad commit)')

    args = parser.parse_args()
    opts = Options(
        quiet=args.quiet,
    )

    # Ensure that the base directory exists
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # Clone or fetch repo
    clone_mixxx(opts)

    # Create auxiliary directories
    for dir in [DOWNLOADS_DIR, MOUNT_DIR, LOG_DIR]:
        dir.mkdir(parents=True, exist_ok=True)

    # Set up platform-specific snapshot runner
    runner = SnapshotRunner(DOWNLOADS_DIR, MOUNT_DIR, opts)

    # Fetch snapshots and match them up with Git commits
    snapshots_url = f'{SNAPSHOTS_BASE_URL}{args.branch}/'
    snapshots = fetch_snapshots(
        snapshots_url=snapshots_url,
        suffix=runner.download_path.suffix,
    )
    commits = sort_commits(list(snapshots.keys()))

    if commits:
        print(f'{len(commits)} snapshot commits found')
    else:
        print('No snapshot commits found (or some error occurred while sorting the commits)')
        sys.exit(1)

    # Parse search range bounds
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
        print(f'==> Searching {commits[good_idx][:10]} to {commits[bad_idx][:10]} ({bad_idx - good_idx} commits)...')
        mid_idx = (bad_idx + good_idx) // 2
        mid = commits[mid_idx]

        print(f'==> Checking {describe_commit(mid)}')
        download_snapshot(snapshots[mid], runner.download_path)
        runner.setup_snapshot()
        runner.run_snapshot()
        runner.cleanup_snapshot()

        answer = ''
        while not answer or answer not in 'yn':
            answer = input('Good? [y/n] ')

        if answer == 'y':
            good_idx = mid_idx
        else:
            bad_idx = mid_idx

    print(f'Last good: {describe_commit(commits[good_idx])}')
    print(f'First bad: {describe_commit(commits[bad_idx])}')
    print(f'Trees:     https://github.com/mixxxdj/mixxx/tree/{commits[good_idx]}')
    print(f'           https://github.com/mixxxdj/mixxx/tree/{commits[bad_idx]}')
    print(f'Diff:      https://github.com/mixxxdj/mixxx/compare/{commits[good_idx]}...{commits[bad_idx]}')