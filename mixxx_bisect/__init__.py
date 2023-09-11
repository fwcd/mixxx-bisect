import argparse
import platform
import re
import subprocess
import sys

from pathlib import Path
from tqdm import tqdm
from typing import Optional, cast

from mixxx_bisect.options import Options
from mixxx_bisect.runner import SnapshotRunner
from mixxx_bisect.runner.macos import MacOSSnapshotRunner
from mixxx_bisect.runner.windows import WindowsSnapshotRunner
from mixxx_bisect.utils import download, get_soup, run, run_with_output

SNAPSHOTS_BASE_URL = 'https://downloads.mixxx.org/snapshots/'
DEFAULT_ROOT = Path.home() / '.local' / 'state' / 'mixxx-bisect'
OS = platform.system()

SNAPSHOT_NAME_PATTERNS = [
    # Old pattern, e.g. mixxx-main-r7715-a0f80e8464
    re.compile(r'^mixxx-[\w\.]+-r\d+-(\w+)$'),
    # New pattern, e.g. mixxx-2.4-alpha-6370-g44f29763ed-macosintel
    re.compile(r'^mixxx-[\d\.]+(?:-[a-z]+)?-\d+-g(\w+)-\w+$'),
]

# Git utils

def clone_mixxx(opts: Options):
    if opts.mixxx_dir.exists():
        print('==> Fetching Mixxx...')
        run(['git', 'fetch', 'origin'], opts=opts, cwd=opts.mixxx_dir)
    else:
        print('==> Cloning Mixxx...')
        run(['git', 'clone', '--bare', 'https://github.com/mixxxdj/mixxx.git', str(opts.mixxx_dir)], opts=opts)

def sort_commits(commits: list[str], opts: Options) -> list[str]:
    # Windows doesn't like passing too many (long) args, so we truncate commit hashes to 8 chars
    commits = [commit[:8] for commit in commits]
    lines = run_with_output(['git', 'rev-list', '--no-walk'] + commits, cwd=opts.mixxx_dir, opts=opts)
    return lines[::-1]

def parse_commit(rev: str, opts: Options) -> str:
    lines = run_with_output(['git', 'rev-parse', rev], cwd=opts.mixxx_dir, opts=opts)
    return lines[0]

def try_parse_commit(rev: str, opts: Options) -> Optional[str]:
    try:
        return parse_commit(rev, opts)
    except subprocess.CalledProcessError:
        return None

def show_commit(rev: str, format: str, opts: Options) -> str:
    lines = run_with_output(['git', 'show', '-s', f'--format={format}', rev], cwd=opts.mixxx_dir, opts=opts)
    return lines[0]

def describe_commit(rev: str, opts: Options) -> str:
    commit = parse_commit(rev, opts)
    return f"{commit[:10]} from {show_commit(rev, '%ci', opts)} ({show_commit(rev, '%s', opts)})"

def commits_in_order(commits: list[str], opts: Options) -> bool:
    return commits == sort_commits(commits, opts)

# Snapshot utils

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

# Platform-specific snapshot runners

SNAPSHOT_RUNNERS: dict[str, type[SnapshotRunner]] = {
    'Windows': WindowsSnapshotRunner,
    'Darwin': MacOSSnapshotRunner,
}

if OS not in SNAPSHOT_RUNNERS.keys():
    print(f"Unsupported OS: {OS} has no snapshot runner (supported are {', '.join(SNAPSHOT_RUNNERS.keys())})")
    sys.exit(1)

SnapshotRunner = SNAPSHOT_RUNNERS[OS]

# Main

def main():
    parser = argparse.ArgumentParser(description='Finds Mixxx regressions using binary search')
    parser.add_argument('--branch', default='main', help=f'The branch to search for snapshots on. Can be anything in {SNAPSHOTS_BASE_URL}')
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT, help='The root directory where all application-specific state (i.e. the mixxx repo, downloads, mounted snapshots etc.) will be stored.')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output from subprocesses.')
    parser.add_argument('-g', '--good', help='The lower bound of the commit range (a good commit)')
    parser.add_argument('-b', '--bad', help='The upper bound of the commit range (a bad commit)')

    args = parser.parse_args()
    opts = Options(
        quiet=args.quiet,
        root_dir=args.root,
        mixxx_dir=args.root / 'mixxx.git',
        mount_dir=args.root / 'mnt',
        log_dir=args.root / 'log',
        downloads_dir=args.root / 'downloads',
    )

    # Ensure that the root directory exists
    opts.root_dir.mkdir(parents=True, exist_ok=True)

    # Clone or fetch repo
    clone_mixxx(opts)

    # Create auxiliary directories
    for dir in [opts.downloads_dir, opts.mount_dir, opts.log_dir]:
        dir.mkdir(parents=True, exist_ok=True)

    # Set up platform-specific snapshot runner
    runner = SnapshotRunner(opts)

    # Fetch snapshots and match them up with Git commits
    snapshots_url = f'{SNAPSHOTS_BASE_URL}{args.branch}/'
    snapshots = fetch_snapshots(
        snapshots_url=snapshots_url,
        suffix=runner.download_path.suffix,
        opts=opts,
    )
    commits = sort_commits(list(snapshots.keys()), opts)

    if commits:
        print(f'{len(commits)} snapshot commits found')
    else:
        print('No snapshot commits found (or some error occurred while sorting the commits)')
        sys.exit(1)

    # Parse search range bounds
    good = parse_commit(args.good or commits[0], opts)
    bad = parse_commit(args.bad or commits[-1], opts)

    if good == bad or not commits_in_order([good, bad], opts):
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

        print(f'==> Checking {describe_commit(mid, opts)}')
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

    print(f'Last good: {describe_commit(commits[good_idx], opts)}')
    print(f'First bad: {describe_commit(commits[bad_idx], opts)}')
    print(f'Trees:     https://github.com/mixxxdj/mixxx/tree/{commits[good_idx]}')
    print(f'           https://github.com/mixxxdj/mixxx/tree/{commits[bad_idx]}')
    print(f'Diff:      https://github.com/mixxxdj/mixxx/compare/{commits[good_idx]}...{commits[bad_idx]}')
