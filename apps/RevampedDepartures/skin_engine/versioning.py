import os
import json


SKIN_METADATA_FILENAME = 'skin.json'


def parse_version(value):
    text = str(value or '').strip()
    if text.startswith('v'):
        text = text[1:]

    parts = text.split('.')
    if len(parts) not in (2, 3, 4):
        raise ValueError('version must use X.Y, X.Y.Z or X.Y.Z.W')

    numbers = []
    for part in parts:
        if part == '' or not part.isdigit():
            raise ValueError('version must be numeric')
        numbers.append(int(part))

    if len(numbers) == 2:
        numbers.append(0)

    return tuple(numbers)


def version_text(value):
    text = str(value or '').strip()
    if text.startswith('v'):
        text = text[1:]

    parse_version(text)
    return text


def version_at_least(installed, required):
    return parse_version(installed) >= parse_version(required)


def _valid_marker_filename(name):
    name = str(name or '')
    if not name.startswith('v'):
        return False

    try:
        parse_version(name)
        return True
    except Exception:
        return False


def find_version_marker(directory):
    candidates = []

    for name in os.listdir(directory):
        if not _valid_marker_filename(name):
            continue

        path = directory.rstrip('/\\') + '/' + name

        try:
            with open(path) as handle:
                json.loads(handle.read())
        except Exception:
            continue

        candidates.append((parse_version(name), name))

    if not candidates:
        return None, None

    candidates.sort()
    name = candidates[-1][1]
    return version_text(name), name


def app_root():
    try:
        path = str(__file__).replace('\\', '/')

        marker = '/skin_engine/versioning.py'
        if path.endswith(marker):
            root = path[:-len(marker)]
            return root if root else '.'

        marker = 'skin_engine/versioning.py'
        if path.endswith(marker):
            root = path[:-len(marker)].rstrip('/')
            return root if root else '.'

    except Exception:
        pass

    return '.'


def departurebox_version():
    version, _ = find_version_marker(app_root())
    return version


def read_skin_metadata(skin_directory):
    path = skin_directory.rstrip('/\\') + '/' + SKIN_METADATA_FILENAME

    with open(path, 'r') as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError('skin.json must contain an object')

    skin_id = str(data.get('id', '')).strip()
    if not skin_id:
        raise ValueError('skin.json missing id')

    name = str(data.get('name', '')).strip()
    if not name:
        raise ValueError('skin.json missing name')

    version = version_text(data.get('version'))
    required = version_text(data.get('requires_departurebox', '0.2.1'))

    out = dict(data)
    out['id'] = skin_id
    out['name'] = name
    out['version'] = version
    out['requires_departurebox'] = required
    return out


def skin_version(skin_directory):
    try:
        return read_skin_metadata(skin_directory)['version']
    except Exception:
        return None
