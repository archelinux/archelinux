# Arche Linux

Welcome to Arche Linux. This is not just another Arch-based distribution; it is a focused and opinionated take on what a modern, developer-centric Linux environment should be. This document explains the philosophy behind the choices we've made, so you can understand the *why* behind the system you're running.

## The Core Philosophy

Arche Linux is built on three core principles:

1.  **Intentionality**: Every package and configuration is chosen for a specific purpose. We believe in a lean, purposeful system, free from the bloat that can distract and slow you down. If a tool is included, it's because it's considered best-in-class for a keyboard-driven workflow.
2.  **Security by Default**: A secure system shouldn't be something you have to build; it should be the starting point. We have made conscious decisions to harden the system from the kernel up to provide a more secure foundation for your work.
3.  **User in Control**: Arche automates the tedious parts of an Arch Linux installation but never takes control away from you. Key decisions about your system, like partitioning, are yours to make. The system is transparent, and you are encouraged to understand how it works.

## So Why Arche Linux?

This distribution is for developers, system administrators, and Linux enthusiasts who are comfortable with the command line and value a minimalist, keyboard-driven environment.

### The Installation

The `arche-install` script is designed to be your first interaction with the Arche philosophy.

* **Trust and Transparency**: The first step is to verify the integrity of the installation medium. We believe you should be able to trust your system from the very beginning.
* **Deliberate Setup**: You are prompted to make critical decisions, such as setting your locale, keyboard layout, and hostname. The installer uses `cfdisk` which requires you to define your own partition scheme. This is intentional. It ensures you understand and control the foundation of your system.
* **Curated Experience**: The installer sets up a complete, usable environment with a pre-configured `i3` window manager, `zsh` shell with `oh-my-zsh`, and essential security services enabled from the start.

### The Software Stack

The default package set is the strongest statement of our philosophy. We have chosen a minimal base and added a suite of powerful, modern, and efficient command-line tools.

* **The Classics**: We provide the essential, time-tested tools for serious development and administration like `vi`, `vim`, `neovim`, `ranger`, etc.
* **Window Management**: We provide `i3-wm`, `i3blocks`, and `dmenu`. This tiling window manager setup is designed for a keyboard-centric workflow to minimize distractions and maximize screen real estate.
* **The Shell**: `zsh` is our shell of choice, enhanced with `oh-my-zsh`. It provides a more powerful and user-friendly command-line experience than traditional shells.
* **Core Utilities**: We have replaced some traditional utilities with modern alternatives like `exa` (a modern replacement for `ls`), `ripgrep` (a faster `grep`), and `fd` (a simpler and faster `find`). Tools like `htop`, `ncdu`, and `tmux` are included to provide insight and control over your system.
* **Audio**: We use `PipeWire` for a modern, low-latency audio stack that handles everything from desktop audio to professional use cases.

### Security: A Non-Negotiable Foundation

* **Hardened Kernel**: Arche Linux ships with the `linux-hardened` kernel by default. This provides a number of patches and configurations that protect against a wide range of exploits.
* **Secure Boot Parameters**: We enable kernel parameters like `slab_nomerge` and `pti=on` directly from the bootloader. These settings mitigate specific kernel vulnerabilities and are enabled by default, so you don't have to think about them.
* **Firewall**: `iptables` is enabled out of the box to provide a basic layer of network security.
* **Secure Package Management**: `pacman` is configured to require package signatures to ensure the software you install is authentic and has not been tampered with.

### Our Commitment to Freedom

Arche Linux is licensed under the GNU General Public License v3. We believe in free and open-source software. This license guarantees your freedom to use, study, share, and modify the software. It is a commitment to you, the user, and to the community that makes this work possible.

## Acknowledgements

Arche Linux stands on the shoulders of giants. Our project would not be possible without the incredible work of others in the free and open-source community. We would like to extend our sincere gratitude to:

* **The Arch Linux Project**: For providing the rock-solid, flexible, and simple base upon which Arche Linux is built. Your commitment to user-centricity and your incredible documentation make our lives easier every day.
* **The BlackArch Linux Team**: For their work on their installer, which served as a key inspiration for the `arche-install` script.
* **The Free Software Foundation**: For creating and maintaining the GNU General Public License, which provides the legal framework that protects the freedom of our users and our project.
* **All Upstream Developers**: To every developer and maintainer of the tools and packages we include—from the Linux kernel to the i3 window manager to the smallest utility—thank you for your tireless dedication to building high-quality open-source software.

We hope you find Arche Linux to be a powerful, focused, and secure platform for your work. Peace.
