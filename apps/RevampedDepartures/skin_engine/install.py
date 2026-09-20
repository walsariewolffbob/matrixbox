import json
import os

from skin_engine.versioning import read_skin_metadata

_REQUIRED_RUNTIME_FILES = ('__init__.py', 'manifest.py', 'renderer.py', 'skin.json')


def _copy_file(src, dst):
    with open(src, 'rb') as source:
        data = source.read()
    with open(dst, 'wb') as target:
        target.write(data)


def _safe_name(value):
    value = str(value or '').strip()
    if not value:
        return ''
    for char in value:
        if not (char.isalnum() or char in ('_', '-')):
            return ''
    return value


def read_package_manifest(package_dir):
    path = os.path.join(package_dir, 'manifest.json')
    with open(path, 'r') as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError('Skin package manifest must be a dictionary')
    return data


def validate_package(package_dir):
    errors = []
    try:
        package_manifest = read_package_manifest(package_dir)
    except Exception as exc:
        return {}, ('manifest.json: ' + str(exc),)

    try:
        skin_metadata = read_skin_metadata(package_dir)
    except Exception as exc:
        skin_metadata = {}
        errors.append('skin.json: ' + str(exc))
    package_id = _safe_name(package_manifest.get('id'))
    skin_id = _safe_name(skin_metadata.get('id')) if skin_metadata else ''
    if not package_id:
        errors.append('invalid or missing id in manifest.json')
    if skin_metadata and not skin_id:
        errors.append('invalid id in skin.json')
    if package_id and skin_id and package_id != skin_id:
        errors.append('manifest.json id does not match skin.json id')
    try:
        package_format = int(package_manifest.get('format', 1))
        if package_format < 1:
            errors.append('format must be >= 1')
    except Exception:
        package_format = 0
        errors.append('format must be an integer')

    files = package_manifest.get('files', ())
    if not isinstance(files, (list, tuple)):
        errors.append('files must be a list')
        files = ()
    normalized_files = []
    for name in files:
        name = str(name)
        if '/' in name or '\\' in name or name in ('', '.', '..'):
            errors.append('invalid file name: ' + name)
            continue
        if name not in normalized_files:
            normalized_files.append(name)

    for required in _REQUIRED_RUNTIME_FILES:
        if required not in normalized_files:
            errors.append('missing required file entry: ' + required)
    for name in normalized_files:
        if not os.path.isfile(os.path.join(package_dir, name)):
            errors.append('missing package file: ' + name)
    out = dict(package_manifest)
    out['id'] = skin_id or package_id
    out['format'] = package_format
    out['files'] = tuple(normalized_files)
    if skin_metadata:
        out['name'] = skin_metadata['name']
        out['version'] = skin_metadata['version']
        out['requires_departurebox'] = skin_metadata['requires_departurebox']
    return out, tuple(errors)


def install_package(package_dir, skins_dir):
    manifest, errors = validate_package(package_dir)
    if errors:
        raise ValueError('; '.join(errors))

    target = os.path.join(skins_dir, manifest['id'])
    try:
        os.mkdir(target)
    except OSError:
        pass

    for name in manifest['files']:
        _copy_file(os.path.join(package_dir, name), os.path.join(target, name))
    _copy_file(
        os.path.join(package_dir, 'manifest.json'),
        os.path.join(target, 'manifest.json'),
    )
    return target
