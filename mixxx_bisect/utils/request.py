from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from typing import Any

from mixxx_bisect.utils.version import pkg_version

import functools
import requests
import shutil

def get(url: str, **kwargs: Any) -> requests.Response:
    headers = {'User-Agent': f'mixxx-bisect/{pkg_version()}'}
    response = requests.get(url, headers=headers, **kwargs)
    response.raise_for_status()
    return response

def download(url: str, output: Path):
    # https://stackoverflow.com/a/63831344
    response = get(url, stream=True, allow_redirects=True)
    file_size = int(response.headers.get('Content-Length', 0))

    # Decompress if needed
    response.raw.read = functools.partial(response.raw.read, decode_content=True)

    with tqdm.wrapattr(response.raw, 'read', total=file_size) as raw: # type: ignore
        with output.open('wb') as f:
            shutil.copyfileobj(raw, f)

def get_soup(url: str) -> BeautifulSoup:
    raw = get(url).content
    return BeautifulSoup(raw, 'html.parser')
