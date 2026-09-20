
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

        if allow_messages and services.shared['nightcount'] < 2:
            now = time.monotonic()
            if now > services.ad_timer + services.ad_delay_minutes * 60:
                try:
                    ad = services.ad_message()
                    if ad:
                        services.active_message = True
                        return [['1', ad, '***', '', '']]
                except Exception as exc:
                    print('VIEW Classic ad skipped:', exc)

            try:
                disruption_due = (
                    now > services.disruption_timer()
                    + services.scroll_delay_seconds()
                )
                show_msgs = int(services.settings.get('show_msgs', 0))
                operator = services.settings['stations']['1']['operator']
                if disruption_due and show_msgs and operator in ('sl', 'vt'):
                    try:
                        message = services.get_deviations()
                    except Exception:
                        message = ' '
                    services.mark_disruption_cycle(now)
                    services.set_deviations_timer(now)
                    services.active_message = True
                    return [['1', message, '***', '', '']]
            except Exception:
                pass

        services.active_message = False
        return services.get_departure()

    def build(self, departures, context):
        services = self._services(context)
        data = self._copy_departures(departures)

        
        
        
        _message_frame = bool(services.active_message)
        if not _message_frame:
            services.cls(services.top)
        services.cls(services.bottom)
        services.set_current_font(0)
        services.top_group.y = 0
        services.middle_group.y = 16
        services.bottom_group.y = 32
        services.top_group.x = 0
        services.bottom_group.x = 0
        services.middle_group.x = services.display_width

        if self.skin is None:
            self.skin = SlClassicSkin(services)
        self.scroll_width = self.skin.render(data)
        self.scroll_position = services.display_width
        self.message_active = bool(services.active_message)
        self.built = True
        self.skin.reset_scroll_pacing()

        return {
            'scroll_width': self.scroll_width,
            'scroll_position': self.scroll_position,
        }

    def after_build(self, context):
        services = self._services(context)
        services.set_scroll_extent(self.scroll_width)
        services.shared['scroll_timer'] = (
            time.monotonic() + random.randint(0, 10)
        )
        return True

    def tick(self, now, context):
        if not self.built:
            return False

        services = self._services(context)
        refresh_times = getattr(context, 'classic_refresh_times', 2)
        self.skin.scroll_step(refresh_times)
        self.scroll_position = services.middle_group.x

        
        
        
        
        
        if services.middle_group.x < -self.scroll_width:
            
            
            if bool(services.active_message):
                return 'rebuild'

            try:
                _update_delay = float(services.updatedelay)
            except (TypeError, ValueError):
                _update_delay = 20.0
            try:
                _scroll_timer = float(services.shared.get('scroll_timer', 0) or 0)
            except (TypeError, ValueError):
                _scroll_timer = 0.0

            if now > _scroll_timer + _update_delay:
                return 'rebuild'

            
            
            
            
            services.middle_group.x = services.display_width
            self.scroll_position = services.display_width
            self.skin.reset_scroll_pacing()
            return True

        
        if (not self.skin.custom_scroll_available()
                and not bool(services.active_message)
                and now > float(services.shared.get('scroll_timer', 0) or 0)
                        + float(services.updatedelay)
                and services.shared['loop_counter'] >= 0):
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
