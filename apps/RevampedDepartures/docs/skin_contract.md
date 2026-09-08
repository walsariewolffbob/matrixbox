DepartureBox Skin Contract

A skin consists of:
1. A manifest dictionary.
2. A Renderer class implementing the renderer lifecycle.
3. A vX.Y[.Z] version marker in the skin directory.

Required manifest fields:
- id
- name
- legacy_listmode
- departure_count
- data_pipeline: raw | classic | list
- requires_departurebox
- renderer_class (injected by register_skin_parts/register_skin_module)

Optional manifest fields:
- manifest_version (currently 1)
- optimized_display_sizes, e.g. ('128x32',)
- defaults
- combined_defaults
- post_build: standard | classic_scroll | dlr
- capabilities
- web_controls
- show_in_view_menu
- pre_prepare_nightcheck
- reset_disruption_timer_on_enter

Renderer lifecycle:
enter(context)
prepare_data(context, allow_messages=True) [optional]
build(departures, context)
after_build(context) [optional]
tick(now, context)
exit(context)
refresh_settings(context) [optional]

Skin boundary:
- Skins access DepartureBox through context.services and SkinContext helpers.
- context.functions is not part of the skin API.
- SkinServices.varinit is not part of the skin API.
- Skins must not import or depend directly on functions.py or varinit.py.
- Low-level display objects intentionally exposed by SkinServices may be used
  when required for rendering.
- SkinServices public names are the supported interface. Removed legacy
  underscore aliases are not part of the contract.

Lifecycle rules:
- Renderer build must not fetch departures.
- Renderer build must not select another View.
- Renderer build must not show the changeover splash.
- Renderer build must not perform the controller's final physical refresh.
- tick() may return 'refresh' or 'rebuild'.

Registration:
register_skin_parts(manifest, Renderer)

A malformed or incompatible skin is rejected by the registry and is not added
to the View menu. If saved settings reference an unavailable skin/mode, the
controller falls back to a valid registered renderer.

Versioning, display policy and recovery:
- The app root vX.Y[.Z] marker is the authoritative DepartureBox release version.
- Each skin directory has its own vX.Y[.Z] release marker.
- requires_departurebox declares the minimum compatible DepartureBox version.
- manifest_version describes the manifest schema, not the skin release version.
- Skins requiring a newer DepartureBox release are rejected during discovery.
- optimized_display_sizes is advisory: other display sizes remain allowed, but
  the controller and Web UI may warn that the active skin is not optimized.
- web_controls is the manifest-owned declaration for View-specific Web controls.
- Runtime renderer faults are logged only when they occur to logs/skin_fault.log.
- After a renderer fault the controller exits the failed skin, shows an error
  splash, and falls back to SL List when available.
