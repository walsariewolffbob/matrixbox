from skin_engine.base import BaseRenderer
from .implementation import SlListSkin


class SlListRenderer(BaseRenderer):
    renderer_id = 'sl_list'
    display_name = 'SL List'
    implemented = True

    def __init__(self):
        super().__init__()
        self.built = False
        self.skin = None

    @staticmethod
    def _services(context):
        services = getattr(context, 'services', None)
        if services is None and isinstance(context, dict):
            services = context.get('services')
        if services is None:
            raise ValueError('SL List renderer requires context.services')
        return services

    def enter(self, context):
        super().enter(context)
        self.built = False
        services = self._services(context)
        self.skin = SlListSkin(services)

    def prepare_data(self, context, allow_messages=True):
        """Prepare the existing SL List data shape for build()."""
        services = self._services(context)
        return services.prepare_list_data()

    def build(self, departures, context):
        services = self._services(context)

        # Establish List's complete display ownership before drawing. This is
        # especially important when entering from Classic/DLR, whose TileGrids
        # use different visible surfaces.
        services.cls(services.top)
        services.cls(services.bottom)
        services.cls(services.topbottom)
        if self.skin is None:
            self.skin = SlListSkin(services)
        self.skin.render(departures)

        # Reassert the List TileGrid positions after the build so the first row
        # is visible on the controller's initial commit, not only after a later
        # timed update.
        _extra = 1 if services.varinit.settings['mini'] else 0
        services.varinit.tg1.y = _extra - 32
        services.varinit.tg2.y = _extra - 16
        services.varinit.tg3.y = _extra

        self.built = True
        return True

    def tick(self, now, context):
        if not self.built:
            return False
        services = self._services(context)
        changed = False

        # Destination TileGrid animation belongs to this renderer now. The
        # renderer changes its own TileGrid state; ViewController performs the
        # physical refresh when 'refresh' is returned.
        if int(services.varinit.settings.get('dest_scroll', 0)):
            try:
                for _rx, _rs in services.varinit.dest_scroll_state.items():
                    _ov = _rs['overflow']
                    if _ov <= 0:
                        continue
                    if now < _rs.get('pause_end', 0):
                        continue
                    _pos = _rs['pos']
                    if _pos >= _ov:
                        _rs['pos'] = 0
                        _rs['pause_end'] = now + 1.5
                        services.varinit.dest_tgs[_rx].x = _rs['start_x']
                    else:
                        _rs['pos'] = _pos + 1
                        services.varinit.dest_tgs[_rx].x = _rs['start_x'] - _pos - 1
                    changed = True
            except Exception:
                pass

        if now > services.varinit.shared['scroll_timer'] + services.updatedelay:
            return 'rebuild'
        if changed:
            return 'refresh'
        return True

    def exit(self, context):
        self.built = False
        services = None
        try:
            services = self._services(context)
        except Exception:
            pass
        if services is not None:
            try:
                services.varinit.dest_scroll_state = {}
                for _tg in services.varinit.dest_tgs:
                    _tg.hidden = True
                services.varinit.overlay_tg.hidden = True
            except Exception:
                pass
        self.skin = None
        super().exit(context)


Renderer = SlListRenderer
