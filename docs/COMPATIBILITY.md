# Compatibility and limits

This plugin bundles the tray widget from Omarchy v4.5.0. Installation is gated
on the following SHA-256 hashes of the stock files:

```text
bb0a6d360d885df58ac8ab44ff1a3668a3d913c36257a15e6282c4720dba8d2f  Tray.qml
e2a06e56334a37f41f057ba7ef128a870b9b37e6e489dd502dfde979b5af7247  TrayModel.js
```

An unsupported version requires a source review and renewed testing, rather
than deleting the hash check. The plugin continues to depend on the installed
Omarchy shell's UI and plugin interfaces. A later Omarchy update can change
those interfaces; uninstall this workaround if it stops working, or when an
upstream fix makes it unnecessary.

The fallback is deliberately smaller than an icon-theme implementation:

- It searches exact icon filenames at common bounded directory depths. It does
  not implement theme inheritance, every icon-theme layout, or arbitrary-depth
  searches. The fallback icon may differ from the active theme.
- A normal successful lookup, direct file URL, or Quickshell pixmap source keeps
  the original rendering path. Pixmap-only failure recovery is not implemented.
- Application-provided `?path=` sources keep Quickshell's normal handling;
  filesystem fallback runs if `Image.Error` is reported. A provider that returns
  a ready-state placeholder rather than an error for such a custom source may
  not be detected. The confirmed case is a standard named theme icon.
- This addresses icon resolution. It does not fix disappearing tray hosts,
  symbolic/non-symbolic rendering transitions, menu behavior or app-side bugs.
- A decoded but visually incorrect image cannot be detected. If the selected
  fallback file exists but cannot decode, the marker remains; that case needs
  investigation rather than a promise that every icon can be repaired.
- A separate Python process is started on a failed lookup, and unresolved
  entries retry every 30 seconds. This is not intended for a large collection
  of permanently missing or rapidly changing icons.

The installer requires exactly one stock `omarchy.tray` entry outside the
drawer. It refuses existing custom tray clones, duplicate entries, symlinked
`shell.json`, and an existing destination directory. Backups are saved under
`~/.config/omarchy/tray-icon-fallback-backups/` (or the XDG equivalent).

For a manually managed or symlinked configuration, copy `plugin/` into a new
user-plugin directory, retain its manifest ID, and replace only the existing
tray entry's `id` with `sthuizen.tray-icon-fallback`. Preserve the other entry
properties. Reverse that ID change to uninstall. Check the upstream hashes
above first; the same compatibility limits apply to manual installation.
