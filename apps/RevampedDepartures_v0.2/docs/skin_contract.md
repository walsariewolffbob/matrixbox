A skin consists of:
1. A manifest dictionary.
2. A Renderer class implementing enter(), build(), tick(), and exit().

Required manifest fields:
- id
- name
- legacy_listmode
- departure_count
- data_pipeline: raw | classic | list
- renderer_class (injected by register_skin_parts/register_skin_module)

Optional manifest fields:
- manifest_version (currently 1)
- supported_display_sizes, e.g. ('128x32',)
- defaults
- combined_defaults
- post_build: standard | classic_scroll | dlr
- capabilities
- show_in_view_menu
- pre_prepare_nightcheck
- reset_disruption_timer_on_enter

Renderer lifecycle:
enter(context)
build(departures, context)
tick(now, context)
exit(context)
refresh_settings(context) [optional]

Rules:
- Renderer build must not fetch departures.
- Renderer build must not select another View.
- Renderer build must not show the changeover splash.
- Renderer build must not perform the controller's final physical refresh.
- tick() may return 'refresh' or 'rebuild'.
- New skins should prefer SkinContext helpers/properties over direct core access.
- Current built-ins retain context.functions only for compatibility.

Registration:
register_skin_parts(manifest, Renderer)

A malformed skin is rejected by the registry and is not added to the View menu.
If saved settings reference an unavailable skin/mode, the controller falls back
to a valid registered renderer.
