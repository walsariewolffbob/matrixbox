from skin_engine.base import BaseRenderer
from .implementation import DlrSkin


class DlrRenderer(BaseRenderer):
    renderer_id = 'tfl_dlr'
    display_name = 'TfL DLR'
    implemented = True

    def __init__(self):
        super().__init__()
        self.built = False
        self.skin = None
        self.last_departures = None

    @staticmethod
    def _copy_departures(departures):
        if not isinstance(departures, list):
            return departures
        copied = []
        for row in departures:
            copied.append(list(row) if isinstance(row, list) else row)
        return copied

    @staticmethod
    def _services(context):
        services = getattr(context, 'services', None)
        if services is None and isinstance(context, dict):
            services = context.get('services')
        if services is None:
            raise ValueError('DLR renderer requires context.services')
        return services

    def enter(self, context):
        super().enter(context)
        self.built = False
        self.last_departures = None
        services = self._services(context)
        self.skin = DlrSkin(services)
        self.skin.reset_message_cycle()

    def prepare_data(self, context, allow_messages=True):
        """Prepare the raw departure feed used by the DLR skin."""
        services = self._services(context)
        services.nightcheck()
        return services.get_departure()

    def build(self, departures, context):
        services = self._services(context)
        if self.skin is None:
            self.skin = DlrSkin(services)

        # A settings rebuild after Scroll Text -> None must not inherit an
        # in-flight message phase or ticker offset.
        if services._dlr_scroll_content_mode() == 'none':
            self.skin.reset_message_cycle()

        # Preserve an untouched renderer-local copy of the most recently
        # prepared departure snapshot. Message-cycle redraws can reuse this
        # without asking the controller for another fetch.
        self.last_departures = self._copy_departures(departures)
        self.skin.render(self._copy_departures(self.last_departures))
        self.built = True
        return True

    def tick(self, now, context):
        if not self.built:
            return False
        services = self._services(context)

        if self.skin is None:
            self.skin = DlrSkin(services)
        action = self.skin.animation_tick()
        if action == 'rebuild':
            return 'rebuild'
        if action == 'message_cancelled':
            if self.last_departures is not None:
                self.skin.render(self._copy_departures(self.last_departures))
                return 'refresh'
            return 'rebuild'
        if action == 'message_complete':
            try:
                _update_delay = float(services.updatedelay)
            except (TypeError, ValueError):
                _update_delay = 20.0
            try:
                _scroll_timer = float(
                    services.varinit.shared.get('scroll_timer', 0) or 0
                )
            except (TypeError, ValueError):
                _scroll_timer = 0.0

            # Fetch only when the ordinary departure-update interval is due.
            if now > _scroll_timer + _update_delay:
                return 'rebuild'

            # Otherwise reconstruct the lower DLR rows from the most recently
            # prepared snapshot. This is a renderer-local redraw only; the
            # controller still owns the physical display commit.
            if self.last_departures is not None:
                self.skin.render(self._copy_departures(self.last_departures))
                return 'refresh'
            return 'rebuild'
        if action == 'refresh':
            return 'refresh'

        try:
            _update_delay = float(services.updatedelay)
        except (TypeError, ValueError):
            _update_delay = 20.0
        if (not self.skin.message_active()
                and now > float(services.varinit.shared.get('scroll_timer', 0) or 0)
                        + _update_delay):
            return 'rebuild'
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
                if self.skin is not None:
                    self.skin.reset_message_cycle()
                services.varinit.tg2.x = 0
                services.varinit.tg2.y = 16
            except Exception:
                pass
        self.skin = None
        self.last_departures = None
        super().exit(context)


Renderer = DlrRenderer
