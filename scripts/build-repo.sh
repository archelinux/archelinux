#!/usr/bin/env bash
# Run on a disposable Arch build host. Root creates a temporary non-root builder.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=$root/pkgs/local-repo
work=$(mktemp -d /tmp/arche-pkgs.XXXXXX)
builder=
sudoers=
host_config_saved=false
privileged() {
  if (( EUID == 0 )); then "$@"; else sudo -- "$@"; fi
}
cleanup() {
  local status=$?
  trap - EXIT
  if [[ $host_config_saved == true ]]; then
    privileged cp -p "$work/pacman.conf.original" /etc/pacman.conf
  fi
  if [[ -n $sudoers ]]; then privileged rm -f -- "$sudoers"; fi
  if [[ -n $builder ]]; then privileged userdel -r "$builder"; fi
  privileged rm -rf -- "$work"
  exit "$status"
}
trap cleanup EXIT
# Bootstrap before adding the temporary staging repository.
# All calls to makepkg below run without root privileges.
privileged pacman -Syu --needed --noconfirm base-devel git namcap python sudo zoxide direnv zsh
if (( EUID == 0 )); then
  builder="archebuild$$"
  useradd -m -U "$builder"
  sudoers="/etc/sudoers.d/$builder"
  printf '%s ALL=(root) NOPASSWD: /usr/bin/pacman\n' "$builder" > "$sudoers"
  chmod 440 "$sudoers"
  visudo -cf "$sudoers"
fi
as_builder() {
  if [[ -n $builder ]]; then
    runuser -u "$builder" -- "$@"
  else
    "$@"
  fi
}
stage_recipe() {
  cp -rL "$1" "$2"
  if [[ -n $builder ]]; then chown -R "$builder:$builder" "$2"; fi
}
chmod 755 "$work"
# Retry transient connection resets as well as HTTP errors for binary sources.
sed 's/--retry 3/--retry 5 --retry-all-errors/g' /etc/makepkg.conf > "$work/makepkg.conf"
mkdir -p "$repo"
# Avoid silently publishing old packages left over from earlier invocations.
if compgen -G "$repo/*.pkg.tar.*" >/dev/null; then
  echo "Staging repository is not empty: $repo. Use a clean checkout/build directory." >&2
  exit 1
fi
# cargo-binstall is in Arch extra. Pin the two required external binary recipes.
aur_names=(bun-bin basedpyright-bin)
aur_revisions=(b4673dcbe5f068ad8d8a5fa1944ce84a1ab772a4 efdc804aaf6a6e8d21bcd7841f2962273a0c5d69)
for index in "${!aur_names[@]}"; do
  name=${aur_names[$index]}
  mkdir -p "$work/$name"
  if [[ -n $builder ]]; then chown "$builder:$builder" "$work/$name"; fi
  as_builder git clone "https://aur.archlinux.org/$name.git" "$work/$name"
  (
    cd "$work/$name"
    as_builder git checkout --detach "${aur_revisions[$index]}"
    as_builder makepkg --config "$work/makepkg.conf" --cleanbuild --force --syncdeps --needed --noconfirm
  )
  cp "$work/$name/"*.pkg.tar.zst "$repo/"
  repo-add "$repo/arche.db.tar.zst" "$work/$name/"*.pkg.tar.zst
done
# Register the already populated staging database before resolving internal dependencies.
privileged cp -p /etc/pacman.conf "$work/pacman.conf.original"
host_config_saved=true
privileged python3 "$root/scripts/configure-repo.py" /etc/pacman.conf /etc/pacman.conf "$repo"
privileged pacman -Sy --noconfirm
for name in arche-base arche-tui-stack arche-agentic-core arche-cuda; do
  stage_recipe "$root/pkgs/$name" "$work/$name"
  (
    cd "$work/$name"
    namcap PKGBUILD | tee recipe.lint
    if grep -q ' E: ' recipe.lint; then exit 1; fi
    if [[ $name == arche-cuda ]]; then
      # This package contains only dependency metadata. Resolve its complete
      # transaction, but do not install GPU drivers/run DKMS on the CI builder.
      # shellcheck disable=SC2016 # Expanded in the unprivileged child shell.
      mapfile -t runtime_deps < <(as_builder bash -c 'source "$1"; printf "%s\n" "${depends[@]}"' _ "$PWD/PKGBUILD")
      privileged pacman -Sp --needed --noconfirm "${runtime_deps[@]}" > dependencies.resolved
      as_builder makepkg --config "$work/makepkg.conf" --cleanbuild --force --nodeps --noconfirm
    else
      as_builder makepkg --config "$work/makepkg.conf" --cleanbuild --force --syncdeps --needed --noconfirm
    fi
    namcap ./*.pkg.tar.zst | tee package.lint
    if grep -q ' E: ' package.lint; then exit 1; fi
  )
  cp "$work/$name/"*.pkg.tar.zst "$repo/"
  repo-add "$repo/arche.db.tar.zst" "$work/$name/"*.pkg.tar.zst
  privileged pacman -Sy --noconfirm
done
# The live filesystem needs its own copy at a path that survives the ISO build.
mkdir -p "$root/airootfs/usr/share/arche/repo"
cp -a "$repo/." "$root/airootfs/usr/share/arche/repo/"
python3 "$root/scripts/configure-repo.py" "$root/pacman.conf" "$root/pacman.conf" "$repo"
python3 "$root/scripts/configure-repo.py" "$root/pacman.conf" "$root/airootfs/etc/pacman.conf" /usr/share/arche/repo
