# Mixxx Bisect

[![Typecheck](https://github.com/fwcd/mixxx-bisect/actions/workflows/typecheck.yml/badge.svg)](https://github.com/fwcd/mixxx-bisect/actions/workflows/typecheck.yml)

A small tool for finding regressions in [Mixxx](https://github.com/mixxxdj/mixxx), inspired by [`mozregression`](https://github.com/mozilla/mozregression). The tool binary searches over a commit range and lets the user tag automatically downloaded Mixxx snapshots with good/bad to identify the commit introducing the regression.

> **Note**: This tool currently only supports macOS and Windows, since the [Mixxx downloads server](https://downloads.mixxx.org/) does not seem to host binary distributions for Linux. The script should be easy to adapt for new OSes though.

## Usage

Run the following command from the repository directory:

```sh
bin/mixxx-bisect -g [good commit] -b [bad commit]
```

To search the entire range of available snapshots, you can also run `bin/mixxx-bisect` without arguments.

> Note: On Windows you have to preprend `python3` before the command.
