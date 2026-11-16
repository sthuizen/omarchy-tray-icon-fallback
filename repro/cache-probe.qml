//@ pragma IconTheme hicolor
import QtQuick
import Quickshell
import Quickshell.Io

ShellRoot {
    id: root
    readonly property string iconName: "sthuizen-cache-probe-20261116"
    readonly property string iconFile: Quickshell.env("XDG_DATA_HOME") + "/icons/hicolor/scalable/apps/" + iconName + ".svg"
    Process {
        id: installIcon
        command: ["python3", "-c", "from pathlib import Path; import sys; p=Path(sys.argv[1]); p.parent.mkdir(parents=True,exist_ok=True); p.write_text('<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"10\" fill=\"white\"/></svg>')", root.iconFile]
        onExited: after.start()
    }
    Timer {
        interval: 200; running: true
        onTriggered: {
            console.log("CACHE_PROBE before=" + JSON.stringify(Quickshell.iconPath(root.iconName, true)))
            installIcon.running = true
        }
    }
    Timer {
        id: after; interval: 500
        onTriggered: {
            console.log("CACHE_PROBE after=" + JSON.stringify(Quickshell.iconPath(root.iconName, true)))
            Qt.quit()
        }
    }
}
