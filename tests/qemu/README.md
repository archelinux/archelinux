# Disposable UEFI installation acceptance

Run from the repository root on a Linux host with KVM, QEMU, OVMF, and Python:

```sh
sudo python3 tests/qemu/run.py out/rc1/archelinux-YYYY.MM.DD-x86_64.iso \
  2>&1 | tee tests/install-test.log
```

The runner creates a fresh 25 GiB qcow2 disk under `out/e2e/`, installs from
that ISO, removes the CD-ROM, and cold-boots Zen and LTS separately. Existing
disks are never overwritten. Use `--work` to choose another fresh directory.
Package downloads use the target disk cache. An optional share/cache/ containing
public package archives is offered as a test-only pacman CacheServer; official
signature checks still apply, repository databases come from the official mirror,
and the cache URL is removed before the installed-system test. Missing cached
packages fall back to the mirror. Official repositories must remain reachable.

Only the disposable work directory is shared with the guest. The installer uses
explicit `--unattended --disk /dev/vda --erase-disk /dev/vda --locked-accounts`
arguments. The guest has locked accounts, a test-only console autologin, and a
root test-control service. These fixtures are not included in shipped packages
or the ISO. Do not distribute the qcow2 as an installed release image.

Logs, serial output, and guest command results are retained in the work directory.
Screenshots are written under `out/e2e-*.png`. The 1 GiB ESP is mounted at `/boot`;
the remaining partition uses XFS. Linux reports `allocsize=64M` as `65536k` in
`findmnt`; the verifier accepts this equivalent spelling and checks the literal
`64M` setting in fstab.

The live-ISO bootstrap uses QMP keyboard input after a 60-second boot allowance.
All disk installation, verification, and desktop interaction thereafter is
scripted. Slow machines may require increasing that boot allowance.

The test exercises virtual hardware, not proprietary NVIDIA/CUDA driver loading,
physical Wi-Fi, suspend/resume, or the BIOS installation path.

## Acceptance record — 2026-11-11

The final fresh-disk run used out/rc5/archelinux-2026.11.10-x86_64.iso and
out/e2e-rc5/. It exited successfully with ARCHE_E2E_PASS. The ISO was promoted
to out/archelinux-2026.11.10-x86_64.iso without changing its contents.
Both Zen (7.2.15-zen1-1-zen) and LTS (6.18.62-1-lts) passed the complete suite.

No manual interaction was needed during the final install-to-desktop run.
Earlier failed attempts remain in tests/install-test.log.

Issues fixed before acceptance:

- Added explicit unattended UEFI partitioning, mounted-disk guards, a repeated
  erase-disk argument, a 1 GiB ESP, and explicitly locked test accounts.
- Locale validation now handles the whitespace in Arch's locale.gen.
- The live ISO now includes an enabled official HTTPS mirror; missing server
  configuration is detected before formatting.
- The installer initializes fresh live Arch keyring trust before formatting.
  Official package signatures remain required; only the bundled Arche staging
  repository has relaxed trust.
- Neovim now checks for an actual Treesitter parser before starting highlighting.
  Filetypes without a seeded parser, including SVG, open and split without errors.
- The Waybar status modules share one pill background, removing the network
  module's broken left seam when optional audio/backlight widgets disappear.

Harness corrections included closing QMP streams, encoding comma key events,
creating the test-only service enablement symlink directly, testing reflink on
XFS under /var/tmp rather than tmpfs /tmp, and explicitly loading the user init
when invoking Neovim's Lua-script mode. These are test-fixture changes; console
autologin and the root control service are not part of the released ISO defaults.

Screenshots were inspected after capture. The refreshed Fuzzel capture shows
two Neovim panes without the earlier parser error. The live and installed
desktop captures show the text-free SVG logo and continuous network pill.
These visual checks cover wired/offline layout, not physical Wi-Fi operation
or a full accessibility audit.
