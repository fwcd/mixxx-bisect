import argparse
import json
import platform
import sys

from pathlib import Path
from mixxx_bisect.error import EmptyRangeError, MixxxBisectError, NoCommitsFoundError, MissingSnapshotsError, UnsupportedOSError
from mixxx_bisect.repository import SnapshotRepository
from mixxx_bisect.repository.m1xxx import M1xxxSnapshotRepository
from mixxx_bisect.repository.mixxx_org import MixxxOrgSnapshotRepository

from mixxx_bisect.options import Options
from mixxx_bisect.runner import SnapshotRunner
from mixxx_bisect.runner.linux import LinuxSnapshotRunner
from mixxx_bisect.runner.macos import MacOSSnapshotRunner
from mixxx_bisect.runner.windows import WindowsSnapshotRunner
from mixxx_bisect.utils.git import clone_mixxx, commits_in_order, describe_commit, parse_commit, sort_commits
from mixxx_bisect.utils.snapshot import download_snapshot
from mixxx_bisect.utils.version import pkg_version

DEFAULT_ROOT = Path.home() / '.local' / 'state' / 'mixxx-bisect'

# Platform-specific snapshot runners

SNAPSHOT_RUNNERS: dict[str, type[SnapshotRunner]] = {
    'Windows': WindowsSnapshotRunner,
    'Darwin': MacOSSnapshotRunner,
    'Linux': LinuxSnapshotRunner,
}

SNAPSHOT_REPOSITORIES: dict[str, type[SnapshotRepository]] = {
    'mixxx-org': MixxxOrgSnapshotRepository,
    'm1xxx': M1xxxSnapshotRepository,
}

# Main

def main():
    os = platform.system()

    parser = argparse.ArgumentParser(description='Finds Mixxx regressions using binary search')
    parser.add_argument('--repository', default='m1xxx' if os == 'Linux' else 'mixxx-org', choices=sorted(SNAPSHOT_REPOSITORIES.keys()), help=f'The snapshot repository to use.')
    parser.add_argument('--branch', default='main', help=f'The branch to search for snapshots on, if supported by the repository.')
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT, help='The root directory where all application-specific state (i.e. the mixxx repo, downloads, installed snapshots etc.) will be stored.')
    parser.add_argument('--dump-snapshots', action='store_true', help='Dumps the fetched snapshots.')
    parser.add_argument('--verbose', action='store_true', help='Enables verbose output.')
    parser.add_argument('--arch', default=platform.machine(), help="The architecture to query for. Defaults to `platform.machine()`, requires the repository to provide corresponding binaries and is primarily useful for machines capable of running multiple architectures, e.g. via Rosetta or QEMU.")
    parser.add_argument('-v', '--version', action='store_true', help='Outputs the version.')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output from subprocesses.')
    parser.add_argument('-g', '--good', help='The lower bound of the commit range (a good commit)')
    parser.add_argument('-b', '--bad', help='The upper bound of the commit range (a bad commit)')

    args = parser.parse_args()

    if args.version:
        print(pkg_version())
        return

    try:
        if os not in SNAPSHOT_RUNNERS.keys():
            raise UnsupportedOSError(f"Unsupported OS: {os} has no snapshot runner (supported are {', '.join(SNAPSHOT_RUNNERS.keys())})")

        SnapshotRunner = SNAPSHOT_RUNNERS[os]
        SnapshotRepository = SNAPSHOT_REPOSITORIES[args.repository]

        opts = Options(
            quiet=args.quiet,
            verbose=args.verbose,
            os=os,
            arch=args.arch,
            root_dir=args.root,
            mixxx_dir=args.root / 'mixxx.git',
            installs_dir=args.root / 'installs',
            log_dir=args.root / 'log',
            downloads_dir=args.root / 'downloads',
        )

        # Ensure that the root directory exists
        opts.root_dir.mkdir(parents=True, exist_ok=True)

        # Clone or fetch git repo
        clone_mixxx(opts)

        # Create auxiliary directories
        for dir in [opts.downloads_dir, opts.installs_dir, opts.log_dir]:
            dir.mkdir(parents=True, exist_ok=True)

        # Set up platform-specific snapshot runner
        runner = SnapshotRunner(opts)

        # Fetch snapshots and match them up with Git commits
        repository = SnapshotRepository(
            branch=args.branch,
            suffix=runner.suffix,
            opts=opts
        )

        snapshots = repository.fetch_snapshots()
        if args.dump_snapshots:
            print(json.dumps(snapshots, indent=2))

        if snapshots:
            commits = sort_commits(list(snapshots.keys()), opts)
        else:
            raise MissingSnapshotsError(f'No snapshots found (for architecture {opts.arch})!')

        if commits:
            print(f'{len(commits)} snapshot commits found.')
            if opts.verbose:
                for commit in commits:
                    print(f'  {describe_commit(commit, opts)}')
        else:
            raise NoCommitsFoundError('No snapshot commits found (or some error occurred while sorting the commits)')

        # Parse search range bounds
        good = parse_commit(args.good or commits[0], opts)
        bad = parse_commit(args.bad or commits[-1], opts)

        if good == bad or not commits_in_order([good, bad], opts):
            raise EmptyRangeError('Please make sure that good < bad!')

        try:
            good_idx = commits.index(good)
        except ValueError:
            raise MissingSnapshotsError(f'Good commit {good} has no associated snapshot!')
        try:
            bad_idx = commits.index(bad)
        except ValueError:
            raise MissingSnapshotsError(f'Bad commit {bad} has no associated snapshot!')

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
    except MixxxBisectError as e:
        print(str(e))
        sys.exit(1)
