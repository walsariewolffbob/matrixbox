import random
import time

from skin_engine.base import BaseRenderer
from .implementation import SlClassicSkin


class SlClassicRenderer(BaseRenderer):
    renderer_id = 'sl_classic'
    display_name = 'SL Classic'
    implemented = True

    def __init__(self):
        super().__init__()
        self.scroll_position = 0
        self.scroll_width = 0
        self.message_active = False
        self.built = False
        self.skin = None

    def enter(self, context):
        super().enter(context)
        self.scroll_position = 0
        self.scroll_width = 0
        self.message_active = False
        self.built = False
        services = self._services(context)
        self.skin = SlClassicSkin(services)

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
            raise ValueError('SL Classic renderer requires context.services')
        return services

    def prepare_data(self, context, allow_messages=True):
        services = self._services(context)

        if allow_messages and services.varinit.shared['nightcount'] < 2:
            now = time.monotonic()
            if now > services.varinit.ad_timer + services.varinit.ad_delay * 60:
                try:
                    ad = services.ad_message()
                    if ad:
                        services.varinit.active_message = True
                        return [['1', ad, '***', '', '']]
                except Exception as exc:
                    print('VIEW Classic ad skipped:', exc)

            try:
                disruption_due = (
                    now > services._disruption_timer()
                    + services._scroll_delay_seconds()
                )
                show_msgs = int(services.varinit.settings.get('show_msgs', 0))
                operator = services.varinit.settings['stations']['1']['operator']
                if disruption_due and show_msgs and operator in ('sl', 'vt'):
                    try:
                        message = services.get_deviations()
                    except Exception:
                        message = ' '
                    services._mark_disruption_cycle(now)
                    services.varinit.deviations_timer = now
                    services.varinit.active_message = True
                    return [['1', message, '***', '', '']]
            except Exception:
                pass

        services.varinit.active_message = False
        return services.get_departure()

    def build(self, departures, context):
        services = self._services(context)
        data = self._copy_departures(departures)

        _message_frame = bool(services.varinit.active_message)
        if not _message_frame:
            services.cls(services.top)
        services.cls(services.bottom)
        services.varinit.currentfont = 0
        services.varinit.tg1.y = 0
        services.varinit.tg2.y = 16
        services.varinit.tg3.y = 32
        services.varinit.tg1.x = 0
        services.varinit.tg3.x = 0
        services.varinit.tg2.x = services.varinit.if_long

        if self.skin is None:
            self.skin = SlClassicSkin(services)
        self.scroll_width = self.skin.render(data)
        self.scroll_position = services.varinit.if_long
        self.message_active = bool(services.varinit.active_message)
        self.built = True
        self.skin.reset_scroll_pacing()

        return {
            'scroll_width': self.scroll_width,
            'scroll_position': self.scroll_position,
        }

    def after_build(self, context):
        services = self._services(context)
        services.varinit.scrollsum = self.scroll_width
        services.varinit.shared['scroll_timer'] = (
            time.monotonic() + random.randint(0, 10)
        )
        return True

    def tick(self, now, context):
        if not self.built:
            return False

        services = self._services(context)
        refresh_times = getattr(context, 'classic_refresh_times', 2)
        self.skin.scroll_step(refresh_times)
        self.scroll_position = services.varinit.tg2.x

        if services.varinit.tg2.x < -self.scroll_width:
            if bool(services.varinit.active_message):
                return 'rebuild'

            try:
                _update_delay = float(services.updatedelay)
            except (TypeError, ValueError):
                _update_delay = 20.0
            try:
                _scroll_timer = float(services.varinit.shared.get('scroll_timer', 0) or 0)
            except (TypeError, ValueError):
                _scroll_timer = 0.0

            if now > _scroll_timer + _update_delay:
                return 'rebuild'

            services.varinit.tg2.x = services.varinit.if_long
            self.scroll_position = services.varinit.if_long
            self.skin.reset_scroll_pacing()
            return True

        if (not self.skin.custom_scroll_available()
                and not bool(services.varinit.active_message)
                and now > float(services.varinit.shared.get('scroll_timer', 0) or 0)
                        + float(services.updatedelay)
                and services.varinit.shared['loop_counter'] >= 0):
            return 'rebuild'

        return True

    def exit(self, context):
        self.built = False
        self.scroll_position = 0
        self.scroll_width = 0
        self.message_active = False
        self.skin = None
        super().exit(context)


Renderer = SlClassicRenderer
