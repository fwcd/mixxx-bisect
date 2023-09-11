from importlib.metadata import version, PackageNotFoundError

def pkg_version() -> str:
    try:
        return version('mixxx-bisect')
    except PackageNotFoundError:
        return 'dev'
