
MANIFEST_VERSION = 1

_REQUIRED_KEYS = (
    'id',
    'name',
    'renderer_class',
    'legacy_listmode',
    'departure_count',
)



def normalize_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('Skin manifest must be a dictionary')

    out = dict(manifest)
    out.setdefault('manifest_version', MANIFEST_VERSION)
    out.setdefault('enabled', True)
    out.setdefault('show_in_view_menu', True)
    out.setdefault('supports_tick', True)
    out.setdefault('supported_display_sizes', ('128x32',))
    out.setdefault('optimized_display_sizes', out.get('supported_display_sizes', ('128x32',)))
    out.setdefault('requires_departurebox', '0.2.1')
    out.setdefault('web_controls', {})
    out.setdefault('defaults', {})
    out.setdefault('combined_defaults', {})
    out.setdefault('capabilities', {})
    out.setdefault('reset_disruption_timer_on_enter', False)

    caps = dict(out.get('capabilities') or {})
    caps.setdefault('custom_scroll', False)
    caps.setdefault('custom_scroll_position', False)
    caps.setdefault('scroll_speed', False)
    caps.setdefault('clock', False)
    caps.setdefault('line_minute_colour', False)
    caps.setdefault('message_interval', False)
    out['capabilities'] = caps

    out['defaults'] = dict(out.get('defaults') or {})
    out['combined_defaults'] = dict(out.get('combined_defaults') or {})
    out['supported_display_sizes'] = tuple(out.get('supported_display_sizes') or ())
    out['optimized_display_sizes'] = tuple(out.get('optimized_display_sizes') or ())
    controls = dict(out.get('web_controls') or {})
    controls.setdefault('scroll_text', False)
    controls.setdefault('scroll_selector', False)
    controls.setdefault('custom_text_requires_custom_mode', False)
    controls.setdefault('message_interval', False)
    controls.setdefault('message_interval_custom', False)
    controls.setdefault('scroll_position', False)
    controls.setdefault('scroll_speed', False)
    controls.setdefault('clock', False)
    controls.setdefault('clock_extra', False)
    controls.setdefault('line_minute_colour', False)
    controls.setdefault('line_display_default', 1)
    out['web_controls'] = controls
    return out


def validate_manifest(manifest):
    m = normalize_manifest(manifest)
    errors = []

    for key in _REQUIRED_KEYS:
        if key not in m or m[key] in (None, ''):
            errors.append('missing ' + key)

    if int(m.get('manifest_version', 0)) != MANIFEST_VERSION:
        errors.append('unsupported manifest_version')

    try:
        from skin_engine.versioning import departurebox_version, version_at_least, version_text
        required_departurebox = version_text(m.get('requires_departurebox', '0.2.1'))
        installed_departurebox = departurebox_version()
        if installed_departurebox is None:
            errors.append('DepartureBox version marker not found')
        elif not version_at_least(installed_departurebox, required_departurebox):
            errors.append(
                'requires DepartureBox ' + required_departurebox +
                ', installed DepartureBox is ' + installed_departurebox
            )
    except Exception as exc:
        errors.append('invalid requires_departurebox: ' + str(exc))

    skin_id = str(m.get('id', '')).strip()
    if skin_id and not skin_id.replace('_', '').replace('-', '').isalnum():
        errors.append('invalid id')

    try:
        int(m.get('legacy_listmode'))
    except Exception:
        errors.append('legacy_listmode must be an integer')

    try:
        if int(m.get('departure_count')) < 1:
            errors.append('departure_count must be >= 1')
    except Exception:
        errors.append('departure_count must be an integer')

    renderer_class = m.get('renderer_class')
    if renderer_class is not None:
        for method in ('enter', 'prepare_data', 'build', 'after_build', 'tick', 'exit'):
            if not callable(getattr(renderer_class, method, None)):
                errors.append('renderer missing ' + method + '()')

    return m, tuple(errors)
