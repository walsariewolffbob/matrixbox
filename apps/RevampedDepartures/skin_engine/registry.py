import os

from skin_engine.manifest import validate_manifest
from skin_engine.versioning import read_skin_metadata


_RENDERERS = {}
_MANIFESTS = {}
_MODE_RENDERERS = {}
_REJECTED = {}

_ID_ALIASES = {'sl_list': 'list'}


def _app_root():
    """Return the DepartureBox app directory without using os.path."""
    try:
        path = str(__file__).replace('\\', '/')

        marker = '/skin_engine/registry.py'
        if path.endswith(marker):
            root = path[:-len(marker)]
            return root if root else '.'

        marker = 'skin_engine/registry.py'
        if path.endswith(marker):
            root = path[:-len(marker)].rstrip('/')
            return root if root else '.'

    except Exception:
        pass

    return '.'


def _canonical_id(renderer_id):
    value = str(renderer_id)
    return _ID_ALIASES.get(value, value)


def _class_manifest(renderer_class):
    raw = dict(getattr(renderer_class, 'manifest', {}) or {})
    raw['renderer_class'] = renderer_class
    raw.setdefault('id', str(getattr(renderer_class, 'renderer_id', '')).strip())
    raw.setdefault('name', str(getattr(renderer_class, 'display_name', raw.get('id', ''))))
    return raw


def register_skin(manifest):
    normalized, errors = validate_manifest(manifest)
    skin_id = str(normalized.get('id', '')).strip() or '<unknown>'

    if errors:
        _REJECTED[skin_id] = errors
        print('SKIN rejected:', skin_id, ', '.join(errors))
        return False

    if not bool(normalized.get('enabled', True)):
        return False

    renderer_class = normalized['renderer_class']
    mode = int(normalized['legacy_listmode'])

    existing_id = _MODE_RENDERERS.get(mode)
    if existing_id is not None and existing_id != skin_id:
        errors = ('duplicate legacy_listmode ' + str(mode),)
        _REJECTED[skin_id] = errors
        print('SKIN rejected:', skin_id, errors[0])
        return False

    if skin_id in _RENDERERS and _RENDERERS[skin_id] is not renderer_class:
        errors = ('duplicate skin id',)
        _REJECTED[skin_id] = errors
        print('SKIN rejected:', skin_id, errors[0])
        return False

    _RENDERERS[skin_id] = renderer_class
    _MANIFESTS[skin_id] = normalized
    _MODE_RENDERERS[mode] = skin_id
    _REJECTED.pop(skin_id, None)
    return True


def register_renderer(renderer_class):
    return register_skin(_class_manifest(renderer_class))


def register_skin_parts(manifest, renderer_class):
    raw = dict(manifest or {})
    raw['renderer_class'] = renderer_class
    return register_skin(raw)


def register_skin_module(module):
    try:
        manifest = getattr(module, 'manifest')
        renderer_class = getattr(module, 'Renderer')
        return register_skin_parts(manifest, renderer_class)
    except Exception as exc:
        skin_id = str(getattr(module, '__name__', '<module>'))
        _REJECTED[skin_id] = (str(exc),)
        print('SKIN rejected:', skin_id, str(exc))
        return False


def _skin_package_names():
    names = []

    try:
        base = _app_root().rstrip('/\\') + '/skins'

        for name in os.listdir(base):
            if not name or name.startswith('_'):
                continue

            package_dir = base.rstrip('/\\') + '/' + str(name)

            try:
                entries = os.listdir(package_dir)
            except Exception:
                continue

            if '__init__.py' not in entries:
                continue

            names.append(str(name))

    except Exception as exc:
        _REJECTED['<discovery>'] = (str(exc),)

    names.sort()
    return tuple(names)


def discover_skins():
    for name in _skin_package_names():
        module_name = 'skins.' + name

        try:
            module = __import__(module_name, None, None, ('manifest', 'Renderer'))
        except Exception as exc:
            _REJECTED[module_name] = (str(exc),)
            print('SKIN rejected:', module_name, str(exc))
            continue

        try:
            base = _app_root().rstrip('/\\') + '/skins/' + name
            skin_meta = read_skin_metadata(base)

            if skin_meta.get('id') != name:
                _REJECTED[name] = ('skin.json id does not match folder name',)
                print('SKIN rejected:', name, 'skin.json id does not match folder name')
                continue

            runtime_manifest = dict(getattr(module, 'manifest') or {})

            if str(runtime_manifest.get('id', '')).strip() != skin_meta.get('id'):
                _REJECTED[name] = ('manifest id does not match skin.json id',)
                print('SKIN rejected:', name, 'manifest id does not match skin.json id')
                continue

            if str(runtime_manifest.get('requires_departurebox', '0.2.1')).strip() != skin_meta.get('requires_departurebox'):
                _REJECTED[name] = ('requires_departurebox mismatch between manifest.py and skin.json',)
                print('SKIN rejected:', name, 'requires_departurebox mismatch between manifest.py and skin.json')
                continue

            runtime_manifest['skin_version'] = skin_meta['version']
            runtime_manifest['renderer_class'] = getattr(module, 'Renderer')
            register_skin(runtime_manifest)

        except Exception as exc:
            _REJECTED[module_name] = (str(exc),)
            print('SKIN rejected:', module_name, str(exc))

    return renderer_ids()


def resync_skins(reload_modules=True):
    """Reconcile the in-memory registry with the skins currently on disk."""
    if reload_modules:
        try:
            import sys
            for module_name in tuple(sys.modules.keys()):
                if module_name.startswith('skins.'):
                    try:
                        del sys.modules[module_name]
                    except Exception:
                        pass
        except Exception as exc:
            print('SKIN module refresh warning:', str(exc))

    _RENDERERS.clear()
    _MANIFESTS.clear()
    _MODE_RENDERERS.clear()
    _REJECTED.clear()
    return discover_skins()


def resolve_renderer_mode(saved_mode):
    try:
        mode = int(saved_mode)
    except Exception:
        mode = None

    if mode in _MODE_RENDERERS:
        return mode

    return default_renderer_mode()


def default_renderer_mode():
    if 0 in _MODE_RENDERERS:
        return 0

    modes = renderer_modes()
    return modes[0] if modes else None


def fallback_renderer_mode():
    manifest = _MANIFESTS.get('list') or _MANIFESTS.get('sl_list')

    if manifest is not None:
        return int(manifest['legacy_listmode'])

    return default_renderer_mode()


def display_optimization_warning(renderer_id, width, height):
    manifest = _MANIFESTS.get(_canonical_id(renderer_id)) or _MANIFESTS.get(str(renderer_id))

    if manifest is None:
        return None

    size = str(int(width)) + 'x' + str(int(height))
    optimized = tuple(manifest.get('optimized_display_sizes') or ())

    if not optimized or size in optimized:
        return None

    return (
        str(manifest.get('name', renderer_id)) +
        ' is not optimized for ' + size +
        ' (optimized: ' + ', '.join(str(v) for v in optimized) + ')'
    )


def get_renderer_class(renderer_id):
    return _RENDERERS.get(_canonical_id(renderer_id)) or _RENDERERS.get(str(renderer_id))


def get_renderer_id_for_mode(legacy_mode):
    try:
        return _MODE_RENDERERS.get(int(legacy_mode))
    except Exception:
        return None


def get_renderer_class_for_mode(legacy_mode):
    renderer_id = get_renderer_id_for_mode(legacy_mode)
    return get_renderer_class(renderer_id) if renderer_id is not None else None


def renderer_ids():
    return tuple(_RENDERERS.keys())


def renderer_modes():
    return tuple(sorted(_MODE_RENDERERS.keys()))


def renderer_manifest(renderer_id):
    manifest = _MANIFESTS.get(_canonical_id(renderer_id)) or _MANIFESTS.get(str(renderer_id))
    return dict(manifest) if manifest is not None else None


def renderer_manifest_for_mode(legacy_mode):
    renderer_id = get_renderer_id_for_mode(legacy_mode)
    return renderer_manifest(renderer_id) if renderer_id is not None else None


def renderer_metadata(renderer_id):
    return renderer_manifest(renderer_id)


def renderer_metadata_for_mode(legacy_mode):
    return renderer_manifest_for_mode(legacy_mode)


def rejected_skins():
    return dict(_REJECTED)


def renderer_view_options():
    options = []

    for mode in renderer_modes():
        renderer_id = _MODE_RENDERERS[mode]
        manifest = _MANIFESTS[renderer_id]

        if not bool(manifest.get('show_in_view_menu', True)):
            continue

        options.append({
            'mode': mode,
            'renderer_id': renderer_id,
            'name': str(manifest.get('name', renderer_id)),
            'manifest': dict(manifest),
            'metadata': dict(manifest),
        })

    return tuple(options)


def renderer_ui_profiles():
    profiles = {}

    for mode in renderer_modes():
        renderer_id = _MODE_RENDERERS[mode]
        manifest = _MANIFESTS[renderer_id]

        profiles[str(mode)] = {
            'id': renderer_id,
            'name': str(manifest.get('name', renderer_id)),
            'departure_count': int(manifest.get('departure_count', 1)),
            'defaults': dict(manifest.get('defaults') or {}),
            'controls': dict(manifest.get('web_controls') or {}),
            'optimized_display_sizes': tuple(manifest.get('optimized_display_sizes') or ()),
            'requires_departurebox': str(manifest.get('requires_departurebox', '0.2.1')),
            'skin_version': str(manifest.get('skin_version', '')),
        }

    return profiles


# Discovery is started explicitly by code.py via resync_skins().
