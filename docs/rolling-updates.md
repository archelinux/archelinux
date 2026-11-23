# Rolling updates

Arch mirrors provide the upstream system. The archelinux stable channel provides the distro packages. After the channel is active, update both with a full upgrade:

```sh
sudo pacman -Syu
```

The stable server is `https://raw.githubusercontent.com/archelinux/archelinux/rolling-channel/stable`. ISO release numbers identify installation media. Packages have their own versions. User-owned dotfiles remain yours when packaged templates change.

## Enabling stable on an existing 2.0.0 installation

Use the public release key you verified when you installed. If you need a new copy, obtain it from the signed ISO release and independently check the fingerprint **E446 C26A 0B7B A1A6 6A3D CC9F 7EC5 6400 3573 C80B**. Use the following commands in a shell with Bash syntax, replacing the key path with your own. A failed check stops the transition.

```bash
(
  set -euo pipefail
  key=/path/to/archelinux-release-public.asc
  server=https://raw.githubusercontent.com/archelinux/archelinux/rolling-channel/stable
  signer=E446C26A0B7BA1A66A3DCC9F7EC564003573C80B
  work=$(mktemp -d)
  trap 'rm -rf "$work"' EXIT
  gpg --homedir "$work" --batch --import "$key"
  gpg --homedir "$work" --batch --export "$signer" > "$work/release.gpg"
  test -s "$work/release.gpg"
  curl -fLSs "$server/arche-enable-rolling" -o "$work/enable"
  curl -fLSs "$server/arche-enable-rolling.sig" -o "$work/enable.sig"
  gpgv --homedir "$work" --keyring "$work/release.gpg" "$work/enable.sig" "$work/enable"
  sudo python "$work/enable" --key "$work/release.gpg"
)
```

The helper verifies the signed database against the pinned key, locally signs that key in pacman's keyring, and replaces the `[arche]` section in place. It leaves the Arch mirror configuration alone. The setup refuses an active pacman database lock. It can be run again after pacman finishes. Now run the full upgrade above. Check `pacman-conf --repo arche Server` and `pacman -Si arche/arche-maintenance` to see the selected server and package version.

Future installation media ship the helper and key in `arche-maintenance`. The guided and unattended installers install from the bundled repository first and switch the target at the end. If the channel is unavailable during installation, the installer keeps the bundled repository and prints a retry command. Run `sudo arche-enable-rolling` when the server is reachable. If signature verification fails, the installer keeps the bundled repository and displays a warning. Check project announcements before retrying.

The LTS-only netinstall image verifies stable before changing the target disk and downloads selected packages during installation. If the channel is unavailable, reconnect and retry the installer.

## Recovery

If an update fails signature verification, stop and retry a full upgrade after checking the system clock and network. The database and detached signature are separate HTTP requests. A client crossing a promotion can temporarily receive different revisions from a cache. Verification fails closed until both files match. Keep signature checks enabled. If a new package breaks a previously working setup, the alternate LTS boot entry, TTY2 and `sudo arche-rollback PACKAGE` are available according to the [recovery guide](getting-started.md#recovery-and-maintenance). Cached rollback needs the earlier archive and related packages may need coordinated downgrades.

## Publishing a candidate

The `Promote signed rolling packages` workflow takes a main-branch dispatch. Its existing `package-release` environment supplies the release signing key and optional passphrase. The build and VM jobs have no signing credentials. The promotion job receives only the tested Git bundle. Its ordinary fast-forward push switches the database, signatures, and archives together. Old versioned files stay in the branch so a client using yesterday's database can still download the bytes it expects.

A manual rehearsal on Arch uses approved built package archives and an existing GPG agent with the release key. Verify the commit, packages, and the old ISO's signatures before running the rehearsal:

```sh
scripts/checkout-channel.sh https://github.com/archelinux/archelinux.git /tmp/arche-channel-candidate
python scripts/stage-rolling.py /path/to/built/packages /tmp/arche-channel-candidate
sudo python3 tests/qemu/guided.py /path/to/verified-v2.0.0.iso /path/to/fresh-vm-work /tmp/arche-channel-candidate/stable
```

The staging command stays local. It signs each new archive, validates package metadata and signatures, indexes only the current package set, and signs both databases and the transition helper. Bump the package release when changing its recipe or source checksums. An unchanged version reuses the previously published signed bytes. A missing package, downgraded version, altered recipe at an existing version, invalid signature or blob at least 100 MiB stops staging. Large future binary packages will need an artifact host with a larger size limit.

After the VM passes, a maintainer using the manual path may commit the tested `stable/` directory in the channel checkout and fast-forward its `rolling-channel` branch. Never force-push it. If another promotion lands first, start a fresh checkout and rerun the rehearsal. Recover a bad package through a newer corrected package release. Retain old commits and published archives for existing clients.

The helper pins the current signer. Planned key rotation requires publishing a successor key and updated verifier through the still-trusted channel, then rolling clients forward before retiring the old key. If the old key is lost or suspected compromised, stop promotions and distribute the replacement fingerprint through an independently verified channel.
