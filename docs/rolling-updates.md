# Rolling updates

Arch mirrors provide the upstream system. The archelinux stable channel provides the distro packages. After the channel is active, update both with a full upgrade:

```sh
sudo pacman -Syu
```

The stable server is `https://raw.githubusercontent.com/archelinux/archelinux/rolling-channel/stable`. ISO release numbers identify installation media. Packages have their own versions. User-owned dotfiles remain yours when packaged templates change.

## Keeping an installed machine current

Before a full upgrade, read the [archelinux announcements](https://archelinux.github.io/archelinux.org/news/) and [Arch Linux news](https://archlinux.org/news/) for any manual steps. Run `sudo pacman -Syu` when you are ready to update, review the transaction and let it finish. Reboot after a kernel upgrade to start the new kernel. Review any `.pacnew` files reported by pacman and merge the settings you want to keep.

You can keep using the same installation across ISO releases. Check the channel with `pacman-conf --repo arche Server`. An HTTPS stable server indicates the rolling channel is configured. A `file://` URL points to the installation snapshot and needs the one-time transition below.

If you build extra packages from the AUR, update them separately after the full upgrade. Review changes to each PKGBUILD and its accompanying files before rebuilding as your regular user. An Arch library update can also require rebuilding a locally installed AUR package.

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

## Recovery

If an update fails signature verification, stop and retry a full upgrade after checking the system clock and network. The database and detached signature are separate HTTP requests. A client crossing a promotion can temporarily receive different revisions from a cache. Verification fails closed until both files match. Keep signature checks enabled. If a new package breaks a previously working setup, the alternate LTS boot entry, TTY2 and `sudo arche-rollback PACKAGE` are available according to the [recovery guide](getting-started.md#recovery-and-maintenance). Cached rollback needs the earlier archive and related packages may need coordinated downgrades.

## Shipping an archelinux update

1. For a change to software that installed users should receive, update its recipe under `pkgs/` and the files it ships. For an upstream release, set `pkgver` and reset `pkgrel` to 1 (for example, `2.0.0-3` to `2.0.1-1`). For a packaging fix, changed default or rebuild of the same upstream version, increment `pkgrel` (for example, `2.0.0-3` to `2.0.0-4`). Update source checksums when the inputs change. For a split recipe, all its output packages share the bump.
2. Open a pull request. The version check compares each changed recipe with the base branch using Arch's `vercmp`. The ISO build verifies the source checksums and builds the packages. Describe any manual steps existing users need and publish those steps in the project news before promotion.
3. Merge the reviewed change into `main`. Choose the merged commit for the next stable promotion. You can group compatible package updates in one promotion. Upstream Arch packages already arrive from Arch mirrors and require no archelinux release.
4. Build, sign and test the stable candidate using one of the paths below. After promotion, run `sudo pacman -Syu` on a machine subscribed to stable. Compare `pacman -Q PACKAGE` with the intended version. Existing installations receive the package at their next full upgrade.

Installer-only changes reach new installations through a new ISO snapshot. An AUR recipe for a standalone tool is published separately when that tool changes. Neither step is required to ship an archelinux binary package to existing users.

## Publishing a candidate

When GitHub Actions holds the release signing key, dispatch the workflow on the reviewed main revision:

```sh
gh workflow run release-pkgs.yml --repo archelinux/archelinux --ref main
```

Check the run's commit and the result of its promotion job. The workflow uses the `package-release` environment and expects the `ARCHE_SIGNING_KEY` secret and, for a passphrase-protected key, `ARCHE_SIGNING_PASSPHRASE`. When the key is kept on a release machine, use the local procedure below. The build and VM jobs have no signing credentials. The promotion job receives only the tested Git bundle. Its ordinary fast-forward push switches the database, signatures, and archives together. Old versioned files stay in the branch so a client using yesterday's database can still download the bytes it expects.

For a local promotion, check out the reviewed main commit on a clean, disposable Arch build host and run `bash scripts/build-repo.sh`. It writes the binary packages to `pkgs/local-repo/`. On the release machine, use the same source revision, those archives and the release signing key. Verify the baseline 2.0.0 ISO and its checksum against the project key before starting the VM:

```sh
scripts/checkout-channel.sh https://github.com/archelinux/archelinux.git /tmp/arche-channel-candidate
python scripts/stage-rolling.py pkgs/local-repo /tmp/arche-channel-candidate
sudo python3 tests/qemu/guided.py /path/to/verified-v2.0.0.iso /path/to/fresh-vm-work /tmp/arche-channel-candidate/stable
```

The staging command stays local. It signs each new archive, validates package metadata and signatures, indexes only the current package set, and signs both databases and the transition helper. Bump the package release when changing its recipe or source checksums. An unchanged version reuses the previously published signed bytes. A missing package, downgraded version, altered recipe at an existing version, invalid signature or blob at least 100 MiB stops staging. Large future binary packages will need an artifact host with a larger size limit.

After the VM passes, publish the tested files from the same channel checkout:

```sh
channel=/tmp/arche-channel-candidate
git -C "$channel" add stable
git -C "$channel" commit -m "Promote packages from $(git rev-parse HEAD)"
git -C "$channel" push origin HEAD:refs/heads/rolling-channel
```

Use an ordinary fast-forward push. If another promotion lands first, start a fresh checkout and rerun the rehearsal. Recover a bad package through a newer corrected package release. Retain old commits and published archives for existing clients.

The helper pins the current signer. Planned key rotation requires publishing a successor key and updated verifier through the still-trusted channel, then rolling clients forward before retiring the old key. If the old key is lost or suspected compromised, stop promotions and distribute the replacement fingerprint through an independently verified channel.
