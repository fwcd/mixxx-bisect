from pathlib import Path

from mixxx_bisect.utils.request import download

def download_snapshot(url: str, download_path: Path):
    print(f'Downloading snapshot...')
    download(url, download_path)
