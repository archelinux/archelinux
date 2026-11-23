#!/usr/bin/env python3
"""Build and verify a signed pacman snapshot in a disposable channel checkout. Never pushes."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FINGERPRINT = "E446C26A0B7BA1A66A3DCC9F7EC564003573C80B"


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def sign(path, signer):
    command = ["gpg", "--batch", "--yes", "--local-user", signer]
    password = os.environ.get("ARCHE_SIGNING_PASSPHRASE")
    if password is not None:
        command += ["--pinentry-mode", "loopback", "--passphrase-fd", "0"]
    subprocess.run([*command, "--detach-sign", path], check=True,
                   input=None if password is None else password + "\n", text=True)


def verify(path, keyring):
    subprocess.run(["gpgv", "--homedir", keyring.parent, "--keyring", keyring,
                    str(path) + ".sig", path], check=True)


def fields(text):
    return dict(line.split(" = ", 1) for line in text.splitlines() if " = " in line)


def package_info(path):
    info = fields(output("bsdtar", "-xOf", path, ".PKGINFO"))
    # Epoch affects version ordering but is omitted from the package filename.
    name = f"{info['pkgname']}-{info['pkgver'].split(':')[-1]}-{info['arch']}.pkg.tar.zst"
    if name != path.name:
        raise ValueError(f"{path.name} does not match its package metadata")
    return info


def versions(db):
    with tarfile.open(db, "r:gz") as archive:
        entries = {}
        for member in archive:
            if member.name.endswith("/desc"):
                parts = archive.extractfile(member).read().decode().strip().split("\n\n")
                data = dict(part.split("\n", 1) for part in parts)
                entries[data["%NAME%"]] = data
        return entries


def recipe_hashes():
    # Read the declared names without executing a PKGBUILD in the signing job.
    expected = {}
    for path in ROOT.glob("pkgs/*/PKGBUILD"):
        declaration = re.search(r"^pkgname=(.+)$", path.read_text(), re.MULTILINE)
        if not declaration:
            raise ValueError(f"Missing package name in {path}")
        names = declaration[1].strip("()").split()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for name in names:
            if not re.fullmatch(r"[a-z0-9@_+][a-z0-9@._+-]*", name) or name in expected:
                raise ValueError(f"Expected unique, literal package names in {path}")
            expected[name] = digest
    return expected


def stage(packages, checkout, key, signer, required):
    stable = checkout / "stable"
    stable.mkdir(exist_ok=True)
    if stable.is_symlink() or any(p.is_symlink() or not p.is_file() for p in stable.iterdir()):
        raise ValueError("The channel must contain regular files only")
    inputs = sorted(packages.glob("*.pkg.tar.zst"))
    if not inputs:
        raise ValueError("No package archives")
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        keyring = work / "release.gpg"
        subprocess.run(["gpg", "--batch", "--dearmor", "--output", keyring, key], check=True)
        previous = {}
        if (stable / "arche.db").exists():
            verify(stable / "arche.db", keyring)
            previous = versions(stable / "arche.db")
        staged, names = [], set()
        for source in inputs:
            if source.stat().st_size >= 100 * 1024 * 1024:
                raise ValueError(f"{source.name} exceeds the channel's Git blob size limit")
            info = package_info(source)
            name = info["pkgname"]
            recipe = fields(output("bsdtar", "-xOf", source, ".BUILDINFO"))["pkgbuild_sha256sum"]
            if required.get(name) != recipe:
                raise ValueError(f"Package {name} does not match a recipe in this checkout")
            if name in names:
                raise ValueError(f"Duplicate package {name}")
            names.add(name)
            if name in previous and int(output("vercmp", info["pkgver"], previous[name]["%VERSION%"])) < 0:
                raise ValueError(f"Refusing to downgrade {name}")
            target = stable / source.name
            if target.exists():
                # Build timestamps may differ. Reuse the original signed bytes
                # only when the recipe (including its source checksums) is unchanged.
                verify(target, keyring)
                previous_recipe = fields(output("bsdtar", "-xOf", target, ".BUILDINFO"))["pkgbuild_sha256sum"]
                if recipe != previous_recipe:
                    raise ValueError(f"Recipe changed without a version bump: {name}")
            else:
                shutil.copyfile(source, target)
                sign(target, signer)
                verify(target, keyring)
            staged.append(target)
        missing = (previous.keys() | required.keys()) - names
        if missing:
            raise ValueError(f"Candidate missing packages: {', '.join(sorted(missing))}")
        subprocess.run(["repo-add", "--include-sigs", work / "arche.db.tar.gz", *staged], check=True)
        entries = versions(work / "arche.db.tar.gz")
        if entries.keys() != names:
            raise ValueError("Repository index does not match candidate packages")
        for path in staged:
            data = entries[package_info(path)["pkgname"]]
            if (data["%FILENAME%"] != path.name or not data.get("%PGPSIG%") or
                    data["%SHA256SUM%"] != hashlib.sha256(path.read_bytes()).hexdigest()):
                raise ValueError(f"Invalid indexed package: {path.name}")
        for name in ("arche.db", "arche.files"):
            dest = stable / name
            shutil.copyfile(work / (name + ".tar.gz"), dest)
            sign(dest, signer)
            verify(dest, keyring)
        helper = stable / "arche-enable-rolling"
        shutil.copyfile(ROOT / "pkgs/arche-base/files/usr/bin/arche-enable-rolling", helper)
        sign(helper, signer)
        verify(helper, keyring)
        shutil.copyfile(key, stable / "archelinux-release.asc")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", type=Path)
    parser.add_argument("channel_checkout", type=Path)
    args = parser.parse_args()
    stage(args.packages.resolve(), args.channel_checkout.resolve(), ROOT / "keys/archelinux-release.asc",
          FINGERPRINT, recipe_hashes())
