import os

from skin_engine.manifest import validate_manifest


_RENDERERS = {}
_MANIFESTS = {}
_MODE_RENDERERS = {}
_REJECTED = {}


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
        base = os.path.join(os.path.dirname(__file__), '..', 'skins')
        for name in os.listdir(base):
            if not name or name.startswith('_'):
                continue
            package_dir = os.path.join(base, name)
            try:
                entries = os.listdir(package_dir)
            except Exception:
                continue
            if '__init__.py' not in entries:
                continue
            names.append(str(name))
    except Exception as exc:
        _REJECTED['<discovery>'] = (str(exc),)
        print('SKIN discovery failed:', str(exc))
    names.sort()
    return tuple(names)


def discover_skins():
    for name in _skin_package_names():
        module_name = 'skins.' + name
        try:
            module = __import__(module_name, fromlist=('manifest', 'Renderer'))
        except Exception as exc:
            _REJECTED[module_name] = (str(exc),)
            print('SKIN rejected:', module_name, str(exc))
            continue
        register_skin_module(module)
    return renderer_ids()


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


def get_renderer_class(renderer_id):
    return _RENDERERS.get(str(renderer_id))


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
    manifest = _MANIFESTS.get(str(renderer_id))
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
            'capabilities': dict(manifest.get('capabilities') or {}),
            'defaults': dict(manifest.get('defaults') or {}),
            'ui': dict(manifest.get('ui') or {}),
        }
    return profiles


# Installed skins are discovered through the same package contract.
discover_skins()
