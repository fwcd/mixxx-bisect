from typing import Optional

from mixxx_bisect.options import Options
from mixxx_bisect.utils.run import run, run_with_output

import subprocess

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
