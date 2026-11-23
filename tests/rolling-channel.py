"""Exercise the real pacman/GPG archive and database formats with an ephemeral test signer."""
import hashlib
import os
from pathlib import Path
import runpy
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
stage_module = runpy.run_path(str(ROOT / "scripts/stage-rolling.py"))
enable = runpy.run_path(str(ROOT / "pkgs/arche-base/files/usr/bin/arche-enable-rolling"))
output = stage_module["output"]
stage = stage_module["stage"]


def package(directory, version, recipe="fixture recipe"):
    tree = directory / "src"
    tree.mkdir(exist_ok=True)
    metadata = f"pkgname = fixture\npkgbase = fixture\npkgver = {version}\npkgdesc = test\nsize = 6\narch = any\n"
    (tree / ".PKGINFO").write_text(metadata)
    (tree / ".BUILDINFO").write_text("pkgbuild_sha256sum = " + hashlib.sha256(recipe.encode()).hexdigest() + "\n")
    (tree / "fixture-marker").write_text(version)
    path = directory / f"fixture-{version}-any.pkg.tar.zst"
    subprocess.run(["bsdtar", "--zstd", "-cf", path, "-C", tree, ".PKGINFO", ".BUILDINFO", "fixture-marker"], check=True)
    return path


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    channel = root / "channel"
    channel.mkdir()
    inputs = root / "packages"
    inputs.mkdir()
    signing = root / "signing"
    signing.mkdir(mode=0o700)
    os.environ["GNUPGHOME"] = str(signing)
    subprocess.run(["gpg", "--batch", "--passphrase", "", "--quick-generate-key",
                    "QA <qa@example.invalid>", "ed25519", "sign", "1d"], check=True)
    signer = next(l.split(":")[9] for l in output("gpg", "--with-colons", "--list-keys").splitlines() if l.startswith("fpr:"))
    key = root / "release.asc"
    key.write_text(output("gpg", "--armor", "--export", signer) + "\n")

    def prepare(recipe="fixture recipe"):
        stage(inputs, channel, key, signer, {"fixture": hashlib.sha256(recipe.encode()).hexdigest()})

    old = package(inputs, "1-1")
    prepare()
    stable = channel / "stable"
    # libalpm compares remote modification times at whole-second precision.
    # Model two distinct publications even on a sub-second in-memory filesystem.
    for file in ("arche.db", "arche.db.sig"):
        os.utime(stable / file, (1_700_000_000, 1_700_000_000))
    original = (stable / old.name).read_bytes()
    dbpath = root / "db"
    dbpath.mkdir()
    cache = root / "cache"
    cache.mkdir()
    installed = root / "root"
    installed.mkdir()
    conf = root / "pacman.conf"
    fakeconf = "[options]\nArchitecture = x86_64\n[arche]\nSigLevel = Optional TrustAll\nServer = file:///previous\n"
    conf.write_text(enable["configured"](fakeconf, stable.as_uri()))
    pm = ["pacman", "--config", conf, "--gpgdir", signing, "--dbpath", dbpath,
          "--cachedir", cache, "--root", installed, "--logfile", root / "pacman.log", "--disable-sandbox"]

    def pacman(*args, expected=True):
        result = subprocess.run([*pm, *args], capture_output=True, text=True)
        assert (result.returncode == 0) == expected, result.stderr
        return result

    pacman("-Syy", "--noconfirm")
    pacman("-S", "--noconfirm", "fixture")
    assert (installed / "fixture-marker").read_text() == "1-1"
    package(inputs, "1-1", "changed recipe without a version bump")
    try:
        prepare("changed recipe without a version bump")
    except ValueError as err:
        assert "version bump" in str(err)
    else:
        raise AssertionError("Accepted a reused package version")
    old.unlink()
    new = package(inputs, "2-1")
    prepare()
    assert (stable / old.name).read_bytes() == original
    # Users with the previous DB can still download the bytes it advertises.
    assert hashlib.sha256(original).hexdigest() in stage_module["versions"](dbpath / "sync/arche.db")["fixture"]["%SHA256SUM%"]
    pacman("-Syu", "--noconfirm")
    assert (installed / "fixture-marker").read_text() == "2-1"
    (stable / "arche.db.sig").write_bytes(b"invalid signature")
    pacman("-Syy", "--noconfirm", expected=False)
print("Pacman installed, upgraded, retained old signed content, and rejected a damaged database signature.")
