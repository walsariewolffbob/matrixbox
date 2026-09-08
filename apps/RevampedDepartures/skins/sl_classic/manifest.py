
manifest = {
    'id': 'sl_classic',
    'name': 'SL Classic',
    'renderer_class': None,
    'manifest_version': 1,
    'requires_departurebox': '0.2.1',
    'optimized_display_sizes': (
        '128x32',
        '192x32',
    ),
    'departure_count': 4,
    'supports_tick': True,
    'supported_display_sizes': (
        '128x32',
        '192x32',
    ),
    'legacy_listmode': 0,
    'defaults': {
        'maxdest': 4,
        'clocktime': 0,
        'list_line_display': 1,
        'dlr_scroll_delay': 60,
    },
    'combined_defaults': {},
    'reset_disruption_timer_on_enter': True,
    'ui': {'scroll_selector': True, 'custom_text_requires_custom_mode': True, 'message_interval_custom': False, 'line_display_default': 1},
    'capabilities': {
        'custom_scroll': True,
        'custom_scroll_position': True,
        'scroll_speed': True,
        'clock': False,
        'line_minute_colour': False,
        'clock_extra': False,
        'message_interval': False,
    },
    'web_controls': {'scroll_text': True, 'scroll_selector': True, 'custom_text_requires_custom_mode': True, 'message_interval': False, 'message_interval_custom': False, 'scroll_position': True, 'scroll_speed': True, 'clock': False, 'clock_extra': False, 'line_minute_colour': False, 'line_display_default': 1},
    'show_in_view_menu': True,
}
