from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from mixxx_bisect.options import Options

import functools
import requests
import shutil
import subprocess

def run(cmd: list[str], opts: Options, cwd: Optional[Path]=None):
    subprocess.run(
        cmd,
        cwd=cwd or opts.root_dir,
        stdout=subprocess.DEVNULL if opts.quiet else None,
        stderr=subprocess.DEVNULL if opts.quiet else None,
    )

def run_with_output(cmd: list[str], opts: Options, cwd: Optional[Path]=None) -> list[str]:
    result = subprocess.run(
        cmd,
        cwd=cwd or opts.root_dir,
        check=True,
        capture_output=True,
        encoding='utf8',
    )
    return result.stdout.splitlines()

def get(url: str, **kwargs) -> requests.Response:
    headers = {'User-Agent': 'mixxx-bisect/0.1.0'}
    response = requests.get(url, headers=headers, **kwargs)
    response.raise_for_status()
    return response

def download(url: str, output: Path):
    # https://stackoverflow.com/a/63831344
    response = get(url, stream=True, allow_redirects=True)
    file_size = int(response.headers.get('Content-Length', 0))

    # Decompress if needed
    response.raw.read = functools.partial(response.raw.read, decode_content=True)

    with tqdm.wrapattr(response.raw, 'read', total=file_size) as raw:
        with output.open('wb') as f:
            shutil.copyfileobj(raw, f)

def get_soup(url: str) -> BeautifulSoup:
    raw = get(url).content
    return BeautifulSoup(raw, 'html.parser')
