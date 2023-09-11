# Mixxx Bisect

[![PyPI](https://img.shields.io/pypi/v/mixxx-bisect)](https://pypi.org/project/mixxx-bisect)
[![Typecheck](https://github.com/fwcd/mixxx-bisect/actions/workflows/typecheck.yml/badge.svg)](https://github.com/fwcd/mixxx-bisect/actions/workflows/typecheck.yml)

A small tool for finding regressions in [Mixxx](https://github.com/mixxxdj/mixxx), inspired by [`mozregression`](https://github.com/mozilla/mozregression). The tool binary searches over a commit range and lets the user tag automatically downloaded Mixxx snapshots with good/bad to identify the commit introducing the regression.

> **Note**: This tool currently only supports macOS and Windows, since the [Mixxx downloads server](https://downloads.mixxx.org/) does not seem to host binary distributions for Linux. The script should be easy to adapt for new OSes though.

## Usage

To search a specific range of commits, run:

```sh
mixxx-bisect -g <good commit> -b <bad commit>
```

To search the entire range of available snapshots, run `mixxx-bisect` without arguments.

## Development

To set up a development environment, create a venv with

```sh
python3 -m venv venv
. venv/bin/activate
```

Then, install the package along with its dependencies in editable mode:

```sh
pip3 install -e .
```

`mixxx-bisect` should now be on the `PATH` in the venv.
