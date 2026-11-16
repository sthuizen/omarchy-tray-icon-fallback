import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('resolver', ROOT / 'plugin/resolve-icon.py')
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        env = patch.dict(os.environ, {
            'HOME': str(self.base / 'home'),
            'XDG_DATA_HOME': str(self.base / 'user'),
            'XDG_DATA_DIRS': str(self.base / 'system'),
        })
        env.start()
        self.addCleanup(env.stop)

    def icon(self, relative):
        path = self.base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<svg/>')
        return path.as_uri()

    def test_newly_installed_icon_recovers_after_initial_miss(self):
        self.assertEqual(resolver.resolve('image://icon/new-app'), '')
        expected = self.icon('system/icons/hicolor/scalable/apps/new-app.svg')
        self.assertEqual(resolver.resolve('image://icon/new-app'), expected)

    def test_user_icon_precedes_system_icon(self):
        self.icon('system/icons/hicolor/scalable/apps/app.svg')
        expected = self.icon('user/icons/hicolor/scalable/apps/app.svg')
        self.assertEqual(resolver.resolve('image://icon/app'), expected)

    def test_hicolor_precedes_unrelated_theme(self):
        self.icon('system/icons/a-theme/scalable/apps/app.svg')
        expected = self.icon('system/icons/hicolor/scalable/apps/app.svg')
        self.assertEqual(resolver.resolve('image://icon/app'), expected)

    def test_custom_flat_directory_with_spaces(self):
        expected = self.icon('app icons/app.png')
        source = 'image://icon/app?path=' + quote(str(self.base / 'app icons'))
        self.assertEqual(resolver.resolve(source), expected)

    def test_custom_theme_root(self):
        expected = self.icon('app-icons/hicolor/32x32/apps/app.png')
        self.assertEqual(resolver.resolve('image://icon/app?path=' + quote(str(self.base / 'app-icons'))), expected)

    def test_closest_raster_size(self):
        self.icon('system/icons/hicolor/16x16/apps/app.png')
        expected = self.icon('system/icons/hicolor/48x48/apps/app.png')
        self.assertEqual(resolver.resolve('image://icon/app', 48), expected)

    def test_pixmaps_fallback(self):
        expected = self.icon('system/pixmaps/app.png')
        self.assertEqual(resolver.resolve('image://icon/app'), expected)

    def test_no_reinterpretation_of_other_sources(self):
        for source in ('image://pixmap/1', 'file:///tmp/app.svg', 'https://example.invalid/app.svg', ''):
            with self.subTest(source=source):
                self.assertEqual(resolver.resolve(source), '')

    def test_invalid_names_cannot_traverse_or_expand_globs(self):
        self.icon('system/icons/hicolor/scalable/apps/app.svg')
        for name in ('..%2Fapp', '%2Fetc%2Fpasswd', '*', 'app%3F', '[a]*', '%00', '.', '..', 'a%5Cb'):
            with self.subTest(name=name):
                self.assertEqual(resolver.resolve('image://icon/' + name), '')


if __name__ == '__main__':
    unittest.main()
