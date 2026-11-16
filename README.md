# Omarchy tray icon cache fallback

A user plugin for Omarchy that can recover named tray icons when Qt's normal
icon-theme lookup stays cached as missing. Created after KeePassXC appeared as
a black/magenta missing-image square following installation during a running
desktop session.

The cache failure described in
[Quickshell #1484](https://github.com/quickshell-mirror/quickshell/issues/1484)
was reproduced on the affected machine. In the same test process, this
workaround loaded the newly installed SVG while `Quickshell.iconPath(name, true)`
still returned an empty string. A fresh process resolved the icon normally.
See [the evidence and reproduction](docs/REPRODUCTION.md).

This is a temporary, Omarchy-specific workaround. It does not fix Qt's cache or
provide a general Quickshell icon-theme invalidation API. Restarting the shell
is the simpler recovery for a one-off occurrence:

```sh
omarchy restart shell
```

## How it works

The normal tray icon source is retained when available. If a standard named
icon cannot be found, or the image reports a loading error, a small Python
helper searches installed icon files and returns a `file://` URL. That bypasses
the failing theme lookup. Unresolved icons get a `?` marker and retry every
30 seconds. Arguments are passed directly to Python, without a shell.

The search covers user and system XDG icon directories, the legacy `~/.icons`
directory, application-provided absolute search directories, and `pixmaps`.
Within a root it prefers `hicolor`, scalable images and nearby raster sizes.
Existing pin/hide settings and the tray's position are preserved by the installer.

## Compatibility

Tested on **Omarchy 4.5.0-3**, **Quickshell 0.3.2.r7.g2b4501a-1**, **Qt 6.12.0**,
Arch Linux / Hyprland, with `QT_QPA_PLATFORMTHEME=gtk3`.

The installer checks the stock tray source hashes and refuses unknown versions.
A cloned widget does not receive future upstream tray updates automatically.
Read [compatibility and limits](docs/COMPATIBILITY.md) before installing.

## Install

Requires an existing Omarchy desktop session, Python 3.10+, Git, Quickshell and
SVG support (`qt6-svg` on Arch). Run as your desktop user, without `sudo`.

```sh
git clone https://github.com/sthuizen/omarchy-tray-icon-fallback.git
cd omarchy-tray-icon-fallback
python3 scripts/manage.py install --check
python3 scripts/manage.py install
omarchy restart shell
```

Installation adds `sthuizen.tray-icon-fallback` under
`~/.config/omarchy/plugins/` and changes the existing `omarchy.tray` layout entry
in `shell.json`. It saves a timestamped configuration backup first. No files
under `/usr/share/omarchy/` are changed. An existing destination or a custom
tray clone is not overwritten. `XDG_CONFIG_HOME` is respected.

## Uninstall

```sh
python3 scripts/manage.py uninstall --check
python3 scripts/manage.py uninstall
omarchy restart shell
```

This switches the current layout entry back to `omarchy.tray`, preserving
current settings rather than restoring an old copy of the whole layout.
The inactive plugin directory and backups are retained. Move or remove the
inactive directory manually before reinstalling.

## Test

```sh
python3 -m unittest discover -s tests -v
# Optional: run inside your graphical session; uses only temporary test files.
python3 scripts/check-quickshell.py
```

The optional check expects the upstream bug to reproduce. If your Qt/platform
setup already refreshes icons correctly, it fails its reproduction assertion;
that alone is not a regression in your system. The Python tests run in CI;
the graphical Quickshell check was run locally on the environment above.

## Credits and license

MIT. The tray widget and model originate from Omarchy, copyright David
Heinemeier Hansson; the cache report is by swiaam. Workaround additions are by
sthuizen with OpenAI Codex assistance. See [NOTICE.md](NOTICE.md) for exact
source references, modification details and attribution.
