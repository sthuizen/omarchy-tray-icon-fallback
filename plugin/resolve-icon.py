"""Resolve a named tray icon without relying on Qt's process-local theme cache."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs, unquote, urlsplit


def resolve(source, size=24):
    url = urlsplit(source)
    if url.scheme != 'image' or url.netloc != 'icon':
        return ''
    name = unquote(url.path.lstrip('/'))
    if not name or any(c in name for c in '/\\*?[]\x00') or name in ('.', '..'):
        return ''
    data_home = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    data_dirs = os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')
    roots = [data_home / 'icons', Path.home() / '.icons']
    roots += [Path(p) / 'icons' for p in data_dirs if p]
    # Respect application-provided directories before the standard fallback theme.
    custom = parse_qs(url.query).get('path', [])
    roots = [Path(p) for p in custom if Path(p).is_absolute()] + roots
    filenames = [name] if Path(name).suffix in ('.svg', '.png', '.xpm') else [name + ext for ext in ('.svg', '.png', '.xpm')]
    for root in roots:
        for filename in filenames:
            direct = root / filename
            if direct.is_file():
                return direct.resolve().as_uri()
        candidates = []
        # Theme layouts are normally theme/size/context/icon. Limit traversal
        # to those levels; never recursively follow arbitrary theme symlinks.
        for pattern in ('*/*/*', '*/*', '*'):
            for filename in filenames:
                for p in root.glob(pattern + '/' + filename):
                    if p.is_file():
                        parts = p.relative_to(root).parts
                        scalable = 'scalable' in parts
                        dimension = next((int(part.split('x')[0]) for part in parts if part.split('x')[0].isdigit() and 'x' in part), size)
                        candidates.append(((0 if parts[0] == 'hicolor' else 1,
                                            0 if scalable else 1, abs(dimension - size), str(p)), p))
        if candidates:
            return min(candidates, key=lambda pair: pair[0])[1].resolve().as_uri()
    for directory in data_dirs:
        if directory:
            for filename in filenames:
                p = Path(directory) / 'pixmaps' / filename
                if p.is_file():
                    return p.resolve().as_uri()
    return ''


if __name__ == '__main__':
    print(json.dumps(resolve(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 24)))
