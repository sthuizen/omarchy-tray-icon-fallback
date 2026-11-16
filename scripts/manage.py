#!/usr/bin/env python3
"""Install a version-checked user plugin; never modify packaged Omarchy files."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PLUGIN_ID = 'sthuizen.tray-icon-fallback'
STOCK_ID = 'omarchy.tray'
ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {
    'Tray.qml': 'bb0a6d360d885df58ac8ab44ff1a3668a3d913c36257a15e6282c4720dba8d2f',
    'TrayModel.js': 'e2a06e56334a37f41f057ba7ef128a870b9b37e6e489dd502dfde979b5af7247',
}


def change_entry(config, old_id, new_id):
    result = deepcopy(config)
    found = []
    layout = result['bar']['layout']
    for section, entries in layout.items():
        if not isinstance(entries, list):
            continue
        for index, entry in enumerate(entries):
            entry_id = entry if isinstance(entry, str) else entry.get('id')
            if entry_id == new_id:
                raise ValueError(f'{new_id} is already in the layout')
            if entry_id == old_id:
                found.append((section, index))
    if len(found) != 1 or found[0][0] == 'tray':
        raise ValueError(f'Expected exactly one {old_id} outside the tray drawer; found {found}')
    section, index = found[0]
    entry = layout[section][index]
    if isinstance(entry, str):
        layout[section][index] = new_id
    else:
        entry['id'] = new_id
    return result


def check_stock(directory):
    for name, expected in SUPPORTED.items():
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Unsupported upstream {name}; see docs/COMPATIBILITY.md. No configuration changed.')


def save_config(path, config):
    # Keep user backups outside the plugin registry. Do not replace a symlink.
    if path.is_symlink():
        raise ValueError('shell.json is a symlink; use the documented manual installation')
    backup_dir = path.parent / 'tray-icon-fallback-backups'
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup = backup_dir / f'shell.{stamp}.json'
    shutil.copy2(path, backup)
    fd, temporary = tempfile.mkstemp(prefix='.shell.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(json.dumps(config, indent=2) + '\n')
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall'])
    parser.add_argument('--check', action='store_true', help='validate and show the intended action without writing')
    args = parser.parse_args()
    config_home = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    if not config_home.is_absolute():
        raise ValueError('XDG_CONFIG_HOME must be absolute')
    config_path = config_home / 'omarchy/shell.json'
    if config_path.is_symlink():
        raise ValueError('shell.json is a symlink; use the documented manual installation')
    config = json.loads(config_path.read_text())
    target = config_home / 'omarchy/plugins' / PLUGIN_ID
    if args.action == 'install':
        check_stock(Path('/usr/share/omarchy/shell/plugins/bar/widgets'))
        if target.exists() or target.is_symlink():
            raise ValueError(f'{target} already exists; no files overwritten')
        updated = change_entry(config, STOCK_ID, PLUGIN_ID)
    else:
        updated = change_entry(config, PLUGIN_ID, STOCK_ID)
    print(f'{args.action}: switch the existing tray widget; preserve its settings and position')
    if args.check:
        print('Check passed; no files changed.')
        return
    for command in ('omarchy-shell', 'omarchy'):
        if not shutil.which(command):
            raise ValueError(f'Required command not found: {command}')
    if args.action == 'install':
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='.tray-fallback.', dir=target.parent))
        installed = False
        try:
            for filename in ('manifest.json', 'Tray.qml', 'TrayModel.js', 'resolve-icon.py'):
                shutil.copy2(ROOT / 'plugin' / filename, stage / filename)
            shutil.copy2(ROOT / 'LICENSE', stage / 'LICENSE')
            shutil.copy2(ROOT / 'NOTICE.md', stage / 'NOTICE.md')
            stage.rename(target)
            installed = True
            subprocess.run(['omarchy-shell', 'shell', 'rescanPlugins'], check=True, timeout=15)
            backup = save_config(config_path, updated)
        except Exception:
            shutil.rmtree(stage, ignore_errors=True)
            if installed:
                shutil.rmtree(target, ignore_errors=True)
            raise
    else:
        # Keep plugin files for recoverability; only switch back to the stock widget.
        backup = save_config(config_path, updated)
    print(f'Configuration backup: {backup}')
    print('Restart the shell to load the component reliably: omarchy restart shell')
    if args.action == 'uninstall':
        print(f'Inactive plugin files retained at {target}; remove them manually if no longer needed.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Error: {error}') from error
