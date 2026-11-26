# Your first ten minutes in archelinux

This walkthrough uses the recommended SwayFX, Foot, tmux and Neovim workspace.
These shortcuts use the Alt key (Sway’s Mod1). Older configurations may use the Super key. Return means Enter.
You can read the guide and use the terminal offline. The first normal Neovim
launch needs internet access to install LazyVim and its plugins.

## Open the guide and a terminal

With arche-workspace-defaults 2.0.0-41 or newer, press **Alt+D**, type
**First Session**, and press **Return**. Fuzzel opens this guide in Foot.
Use **Space** to page down, **b** to go back, **/** to search, and **q** to
close the guide. From a shell or a recovery console, open the same file with:

    less /usr/share/doc/arche-workspace-defaults/first-session.md

Press **Alt+Return** to open a second terminal. Use **Alt+H** and
**Alt+L** to move between tiles to the left and right. The thin highlight
marks the focused window. Keep the guide open in one tile while you work in
the other.

## Build a two-pane work session

In the new terminal, run:

    tmux new-session -s practice

Press **Ctrl+B**, release both keys, then press **%**. The new pane opens on
the right. Press **Ctrl+H** to focus the left pane. On the first connected
launch, allow Neovim to finish downloading its plugins. Start an empty editor:

    nvim

Press **i**, type a short line, then press **Esc**. Type **:vsplit** and press
**Return**. You now have two views of the same buffer. In normal mode,
**Ctrl+L** moves right through the editor, then into the shell pane at the
outer edge. **Ctrl+H** takes you back. For a vertical stack the corresponding
keys are **Ctrl+J** (down) and **Ctrl+K** (up).

If the plugins have never been downloaded and you are offline, start
**nvim --clean** instead. You can practice typing and **:vsplit** immediately.
Use **Ctrl+W** followed by **h** or **l** between editor splits and **Ctrl+B**
followed by an arrow key between tmux panes in this mode.

To leave the unsaved practice buffer, press **Esc**, type **:qa!** and press
**Return**. To keep the tmux session in the background, press **Ctrl+B**, then
**d**. Return to it later with **tmux attach -t practice**. If a session named
practice already exists, attach to it instead of starting another.

## Give yourself a shortcut

Your copy of the Sway configuration lives at **~/.config/sway/config**.
Choose an unused chord. For example, the shipped configuration leaves
**Alt+F10** free. To open Foot with it, add this one line to your copy:

    bindsym $mod+F10 exec foot

Save the file, press **Alt+Shift+C** to reload Sway, then press
**Alt+F10** to try it. To undo the change, remove that line and reload.
The packaged template lives under **/usr/share/arche/skel**. Package updates
can replace the template; your own configuration belongs in your home
directory.

## Find your way back

| Where you are | Keys | What happens |
| --- | --- | --- |
| Sway | Alt+D | Find an application by name in Fuzzel |
| Sway | Alt+Return | Open Foot |
| Sway | Alt+H/J/K/L | Focus a tile left/down/up/right |
| tmux or configured Neovim in normal mode | Ctrl+H/J/K/L | Focus an adjacent pane or split |
| Sway | Alt+Shift+C | Apply a saved configuration edit |
| Desktop | Ctrl+Alt+F2 | Switch to a text login on TTY2 |

If the desktop stops responding, press **Ctrl+Alt+F2** and log in with your
usual username and password. You can read this guide there, edit the Sway
configuration, or inspect the current boot with **journalctl -b**. Press
**Alt+F1** from the text console to return to the existing session on TTY1.
