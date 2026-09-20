

import time
from skin_engine.services import SkinServices


class SkinContext:

    def __init__(self, functions, classic_refresh_times=2):
        self.services = SkinServices(functions)
        self.classic_refresh_times = classic_refresh_times

    @property
    def settings(self):
        return self.services.settings

    @property
    def shared(self):
        return self.services.shared

    @property
    def display_width(self):
        return self.services.physical_display_width

    @property
    def display_height(self):
        return self.services.display_height

    @property
    def now_text(self):
        try:
            return self.services.now_text()
        except Exception:
            return 'Nu'

    def clear(self, surface):
        return self.services.clear(surface)

    def render_text(self, text, *args, **kwargs):
        return self.services.render_text(text, *args, **kwargs)

    def request_refresh(self):
        return 'refresh'

    def request_rebuild(self):
        return 'rebuild'


class BaseRenderer:
    renderer_id = 'base'
    display_name = 'Base renderer'
    implemented = False

    
    
    metadata = {
        'departure_count': None,
        'supports_tick': False,
        'supports_128x32': True,
        'legacy_listmode': None,
        'data_pipeline': 'raw',
        'post_build': 'standard',
        'defaults': {},
        'combined_defaults': {},
        'capabilities': {},
        'show_in_view_menu': True,
    }

    def __init__(self):
        self.active = False
        self.context = None

    def enter(self, context):
        self.context = context
        self.active = True

    def prepare_data(self, context, allow_messages=True):
        return context.services.get_departures()

    def build(self, departures, context):
        raise NotImplementedError('Renderer build() is not implemented')

    def after_build(self, context):
        context.services.shared['scroll_timer'] = time.monotonic()
        return True

    def tick(self, now, context):
        return False

    def exit(self, context):
        self.active = False
        self.context = None

    def refresh_settings(self, context):
        self.context = context
