# Reproduction and evidence

Checked on 16 November 2026 on Arch Linux / Hyprland:

| Component | Installed version |
| --- | --- |
| Omarchy | `4.5.0-3` |
| Quickshell | `0.3.2.r7.g2b4501a-1` |
| Quickshell revision | `2b4501a282689792b62e94f3fb30d8f512324fe6` |
| Qt base | `6.12.0-3` |
| Qt SVG | `6.12.0-1` |
| KeePassXC | `2.7.12-5` |
| Python | `3.14.8-1` |
| Qt platform theme | `gtk3` |

## The observed tray symptom

KeePassXC was installed while Omarchy's shell was already running. Its tray
slot displayed a black/magenta missing-image square. The shell logged:

```text
Could not load icon "keepassxc-monochrome-light-locked" at size QSize(48, 48) from request
```

The matching SVG existed at
`/usr/share/icons/hicolor/scalable/apps/keepassxc-monochrome-light-locked.svg`.
D-Bus inspection showed that KeePassXC advertised that same `IconName`.
The icon rendered correctly after the local workaround was loaded and the
shell restarted. That visual check alone cannot distinguish cache recovery
from workaround recovery, so an independent same-process check was added.

## Controlled check against upstream #1484

[Quickshell #1484](https://github.com/quickshell-mirror/quickshell/issues/1484),
reported by swiaam on 13 November 2026, describes a missing lookup persisting
after icon installation until the shell restarts. It reports the same Quickshell
revision and Qt version. It was open with no comments when checked for this
write-up.

Run in a graphical session with the affected Qt platform theme available:

```sh
python3 scripts/check-quickshell.py
```

The script extracts the actual bundled `TrayIcon` component, rather than a
second implementation. It creates an isolated temporary XDG data directory
and performs this sequence:

1. Start Quickshell with a unique fixture icon absent; look up its name.
2. Create a small SVG under that directory's `icons/hicolor/scalable/apps`.
3. Look up the same name again in the same process.
4. Give that name to the bundled tray component and inspect the decoded image.
5. Start a fresh Quickshell process using the same fixture directory.

Observed results:

```text
First process: before="", after=""
Same process: fallback=file://.../tray-cache-repro-fixture.svg, Image.status=1 (Ready)
Fresh process: before="image://icon/tray-cache-repro-fixture", Image.status=1 (Ready)
```

The automated check passed locally. Temporary files are removed when the test
finishes; installed applications, system icons and the live bar are untouched.
The two-process minimal cache probe in `repro/cache-probe.qml` is also included
for inspection. It requires `XDG_DATA_HOME` to point to a disposable directory.

These results confirm that #1484's failure reproduces here and that the
filesystem fallback bypasses it. They make the KeePassXC symptom consistent
with that bug; they do not retrospectively prove every detail of its original
cache state, or establish that all broken tray icons have the same cause.
