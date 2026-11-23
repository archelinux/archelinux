#!/usr/bin/env python3
"""Check whether pacman would upgrade each changed recipe between two source trees."""
import argparse
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def packages(root, scratch):
    entries = {}
    paths = sorted((root / "pkgs").glob("*/PKGBUILD"))
    if not paths:
        raise ValueError(f"No package recipes under {root}/pkgs")
    for path in paths:
        metadata = subprocess.check_output(
            ["makepkg", "--printsrcinfo"], cwd=path.parent, text=True,
            env=dict(os.environ, BUILDDIR=scratch, SRCDEST=scratch, PKGDEST=scratch),
        )
        fields = {}
        names = []
        for line in metadata.splitlines():
            field, sep, value = line.strip().partition(" = ")
            if field == "pkgname":
                names.append(value)
            elif sep and field in {"epoch", "pkgver", "pkgrel"}:
                fields[field] = value
        version = f"{fields.get('epoch', '0')}:{fields['pkgver']}-{fields['pkgrel']}"
        recipe = path.read_bytes()
        for name in names:
            if name in entries:
                raise ValueError(f"Duplicate package {name} in {root}")
            entries[name] = (version, recipe)
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    with TemporaryDirectory() as scratch:
        previous = packages(args.base, scratch)
        candidate = packages(args.candidate, scratch)
    errors = []
    for name, (old_version, old_recipe) in previous.items():
        if name not in candidate:
            errors.append(f"{name}: stable promotion requires existing packages to be retained")
            continue
        version, recipe = candidate[name]
        if recipe == old_recipe:
            continue
        if int(subprocess.check_output(["vercmp", version, old_version], text=True)) <= 0:
            errors.append(f"{name}: changed recipe must upgrade {old_version} (candidate {version})")
        else:
            print(f"{name}: {old_version} -> {version}")
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    main()
