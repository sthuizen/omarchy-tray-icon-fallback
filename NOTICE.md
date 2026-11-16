# Source and attribution

`plugin/Tray.qml` is a modified copy of Omarchy's tray widget. `plugin/TrayModel.js`
is an unmodified copy of its model. Both originate from
[Omarchy v4.5.0](https://github.com/omacom/omarchy/tree/97e664bd971fa5a8691d89440d3738143499c438),
as distributed by the Arch package `omarchy 4.5.0-3`:

- [Tray.qml](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/shell/plugins/bar/widgets/Tray.qml)
- [TrayModel.js](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/shell/plugins/bar/widgets/TrayModel.js)
- [Upstream MIT license](https://github.com/omacom/omarchy/blob/97e664bd971fa5a8691d89440d3738143499c438/LICENSE), copyright David Heinemeier Hansson.

The installed originals' Git blob hashes were checked against that tag:

```text
Tray.qml      ff00f8de6db04d22372a78c828ff68da0e28c6ac
TrayModel.js  ea34a97c09abc1a6c7b92f90e1259d31fdc5f5ea
```

The inherited license and copyright are retained in `LICENSE`. The widget's
menus, layout, pin/hide behavior, styling and symbolic-icon rendering remain
Omarchy's work. This project adds fallback resolution, a missing-icon marker,
retry handling, installation tooling, tests and documentation. The manifest is
adapted from Omarchy's cloned tray manifest.

Credit to **swiaam** for reporting and explaining the stale lookup in
[Quickshell #1484](https://github.com/quickshell-mirror/quickshell/issues/1484).
The reproduction here independently implements the same missing-before-install
sequence; it is informed by that report. This repository does not implement the
reporter's proposed upstream cache-invalidation API.

[Quickshell](https://quickshell.org/) and Qt are runtime dependencies; their
implementation is not included. KeePassXC is the application that exposed the
problem locally; its icons and other assets are not redistributed here.

The workaround additions are maintained by **sthuizen**. Implementation, tests
and documentation were prepared with assistance from **OpenAI Codex**. This is
an independent community workaround, with no claimed endorsement by Omarchy,
Quickshell, Qt or KeePassXC.
