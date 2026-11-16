import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manage', ROOT / 'scripts/manage.py')
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)


class LayoutTests(unittest.TestCase):
    def test_round_trip_preserves_position_settings_and_unrelated_config(self):
        original = {'idle': {'lock': 300}, 'bar': {'layout': {
            'right': [{'id': 'clock'}, {'id': 'omarchy.tray', 'pinned': ['KeePassXC'], 'hidden': ['Other']}],
            'tray': [{'id': 'third.party'}],
        }}}
        installed = manage.change_entry(original, manage.STOCK_ID, manage.PLUGIN_ID)
        self.assertEqual(installed['bar']['layout']['right'][1]['pinned'], ['KeePassXC'])
        self.assertEqual(manage.change_entry(installed, manage.PLUGIN_ID, manage.STOCK_ID), original)
        self.assertEqual(original['bar']['layout']['right'][1]['id'], 'omarchy.tray')

    def test_string_entry(self):
        result = manage.change_entry({'bar': {'layout': {'right': ['omarchy.tray']}}}, manage.STOCK_ID, manage.PLUGIN_ID)
        self.assertEqual(result['bar']['layout']['right'], [manage.PLUGIN_ID])

    def test_missing_duplicate_and_drawer_entries_are_rejected(self):
        for layout in ({'right': []}, {'right': ['omarchy.tray', 'omarchy.tray']}, {'tray': ['omarchy.tray']},
                       {'right': ['omarchy.tray', manage.PLUGIN_ID]}):
            with self.subTest(layout=layout), self.assertRaises(ValueError):
                manage.change_entry({'bar': {'layout': layout}}, manage.STOCK_ID, manage.PLUGIN_ID)

    def test_unknown_upstream_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'Tray.qml').write_text('changed upstream')
            with self.assertRaises(ValueError):
                manage.check_stock(path)

    def test_install_and_uninstall_in_isolated_config(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config_path = home / 'omarchy/shell.json'
            config_path.parent.mkdir()
            original = {'bar': {'layout': {'right': [{'id': 'omarchy.tray', 'pinned': ['KeePassXC']}]}}}
            config_path.write_text(json.dumps(original))
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': directory}), \
                 patch.object(manage, 'check_stock'), \
                 patch.object(manage.shutil, 'which', return_value='/usr/bin/omarchy'), \
                 patch.object(manage.subprocess, 'run'), contextlib.redirect_stdout(io.StringIO()):
                with patch('sys.argv', ['manage.py', 'install']):
                    manage.main()
                target = home / 'omarchy/plugins' / manage.PLUGIN_ID
                self.assertTrue((target / 'LICENSE').is_file())
                self.assertTrue((target / 'resolve-icon.py').is_file())
                installed = json.loads(config_path.read_text())
                self.assertEqual(installed['bar']['layout']['right'][0]['id'], manage.PLUGIN_ID)
                self.assertEqual(installed['bar']['layout']['right'][0]['pinned'], ['KeePassXC'])
                self.assertEqual(len(list((home / 'omarchy/tray-icon-fallback-backups').glob('*.json'))), 1)
                with patch('sys.argv', ['manage.py', 'uninstall']):
                    manage.main()
                self.assertEqual(json.loads(config_path.read_text()), original)
                self.assertTrue(target.is_dir())

    def test_failed_rescan_preserves_configuration_and_removes_staged_plugin(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config_path = home / 'omarchy/shell.json'
            config_path.parent.mkdir()
            original = '{"bar":{"layout":{"right":["omarchy.tray"]}}}'
            config_path.write_text(original)
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': directory}), \
                 patch.object(manage, 'check_stock'), \
                 patch.object(manage.shutil, 'which', return_value='/usr/bin/omarchy'), \
                 patch.object(manage.subprocess, 'run', side_effect=OSError('rescan failed')), \
                 patch('sys.argv', ['manage.py', 'install']), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError):
                    manage.main()
            self.assertEqual(config_path.read_text(), original)
            self.assertFalse((home / 'omarchy/plugins' / manage.PLUGIN_ID).exists())


if __name__ == '__main__':
    unittest.main()
