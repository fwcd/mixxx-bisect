# Mixxx Regression Finder

A small tool for finding regressions in [Mixxx](https://github.com/mixxxdj/mixxx). The tool binary searches over a commit range and lets the user tag automatically downloaded Mixxx snapshots with good/bad to identify the commit introducing the regression.

> **Note**: This tool currently only supports macOS, since running Mixxx portably on other platforms is quite a bit more involved than launching an app bundle.

## Usage

Run the following command from the repository directory:

```sh
bin/find-regression -g [good commit] -b [bad commit]
```

To search the entire range of available snapshots, you can also run `bin/find-regression` without arguments.
