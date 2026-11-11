#!/usr/bin/env python3
"""Replace only [arche]; preserve all official repository trust settings."""
from pathlib import Path
import re
import sys


def configure(text, repo):
    text = re.sub(r'^\[arche\][ \t]*\n.*?(?=^\[[^\]\n]+\][ \t]*$|\Z)', '', text, flags=re.M | re.S)
    return text.rstrip() + '\n\n[arche]\nSigLevel = Optional TrustAll\nServer = file://' + repo + '\n'


if __name__ == '__main__':
    source, destination, repo = sys.argv[1:]
    Path(destination).write_text(configure(Path(source).read_text(), repo))
