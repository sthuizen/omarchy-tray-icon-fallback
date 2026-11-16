#!/usr/bin/env python3
"""Reproduce the cache miss and exercise the actual bundled QML fallback."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='tray-icon-cache-check-') as directory:
        tmp = Path(directory)
        shutil.copy2(ROOT / 'plugin/resolve-icon.py', tmp / 'resolve-icon.py')
        source = (ROOT / 'plugin/Tray.qml').read_text()
        component = source[source.index('  component TrayIcon: Item {'):source.index("  // The tray section's place")]
        component = component.replace('id: trayIconRoot', 'id: trayIconRoot\n    readonly property int renderedStatus: trayIconImage.status', 1)
        qml = '''//@ pragma IconTheme hicolor
import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Effects
ShellRoot {
  id: root
  property color foreground: "white"
  property string before: ""
  property string after: ""
  property string fixtureName: "tray-cache-repro-fixture"
  function trayIconSource(icon) { return String(icon || "") }
  function iconIsSymbolic(icon) { return false }
''' + component + '''
  TrayIcon { id: probe; width: 24; height: 24; icon: "" }
  Process {
    id: installFixture
    command: ["python3", "-c", "from pathlib import Path; import os; p=Path(os.environ['XDG_DATA_HOME'])/'icons/hicolor/scalable/apps/tray-cache-repro-fixture.svg'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('<svg xmlns=\\"http://www.w3.org/2000/svg\\" viewBox=\\"0 0 24 24\\"><circle cx=\\"12\\" cy=\\"12\\" r=\\"10\\" fill=\\"white\\"/></svg>')"]
    onExited: lookupAfter.start()
  }
  Timer {
    interval: 200; running: true
    onTriggered: {
      root.before = Quickshell.iconPath(root.fixtureName, true)
      installFixture.running = true
    }
  }
  Timer {
    id: lookupAfter; interval: 500
    onTriggered: {
      root.after = Quickshell.iconPath(root.fixtureName, true)
      probe.icon = "image://icon/" + root.fixtureName
      finish.start()
    }
  }
  Timer {
    id: finish; interval: 800
    onTriggered: {
      console.log("CHECK_RESULT " + JSON.stringify({before: root.before, after: root.after,
        fallback: probe.fallbackSource, imageStatus: probe.renderedStatus}))
      Qt.quit()
    }
  }
}
'''
        (tmp / 'shell.qml').write_text(qml)
        env = dict(os.environ, XDG_DATA_HOME=str(tmp / 'data'), QT_QPA_PLATFORM='offscreen')
        results = []
        for _ in range(2):
            run = subprocess.run(['qs', '-p', str(tmp / 'shell.qml')], env=env,
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12)
            lines = [line.split('CHECK_RESULT ', 1)[1] for line in run.stdout.splitlines() if 'CHECK_RESULT ' in line]
            if run.returncode or len(lines) != 1:
                raise RuntimeError('Quickshell check failed:\n' + run.stdout)
            results.append(json.loads(lines[0]))
        first, second = results
        assert first['before'] == '' and first['after'] == '', results
        assert first['fallback'].startswith('file://') and first['imageStatus'] == 1, results
        assert second['before'] == 'image://icon/tray-cache-repro-fixture', results
        assert second['imageStatus'] == 1, results
        print('PASS: first process stays missing after install; filesystem fallback renders (Image.Ready).')
        print('PASS: fresh process resolves the theme icon normally (Image.Ready).')
        print('This verifies the failure described in quickshell-mirror/quickshell#1484 on this environment.')


if __name__ == '__main__':
    main()
