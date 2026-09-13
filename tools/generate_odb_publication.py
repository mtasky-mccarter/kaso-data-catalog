#!/usr/bin/env python3
"""Reserved ODB publication entrypoint: fail closed until approved materialization."""
import argparse
from pathlib import Path
import sys

from odb_scaffold import ROOT, publication_blockers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        reasons = publication_blockers(args.root)
    except (ValueError, OSError) as exc:
        reasons = [f'HANDOFF BLOCKED: {exc}']
    print('\n'.join(reasons), file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
