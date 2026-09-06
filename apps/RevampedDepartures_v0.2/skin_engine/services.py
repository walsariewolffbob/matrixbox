class SkinServices:
    def __init__(self, functions):
        self._f = functions

    # Shared state/config -------------------------------------------------
    @property
    def varinit(self):
        return self._f.varinit

    @property
    def settings(self):
        return self._f.varinit.settings

    @property
    def shared(self):
        return self._f.varinit.shared

    @property
    def dicts(self):
        return self._f.dicts

    @property
    def fonts(self):
        return self._f.fonts

    @property
    def station_names_dict(self):
        return self._f.station_names_dict

    @property
    def updatedelay(self):
        return self._f.updatedelay

    @property
    def CLOCK_ROW_MARK(self):
        return self._f.CLOCK_ROW_MARK

    @property
    def MSG_ROW_MARK(self):
        return self._f.MSG_ROW_MARK

    # Drawing/surfaces ----------------------------------------------------
    @property
    def top(self):
        return self._f.top

    @property
    def bottom(self):
        return self._f.bottom

    @property
    def topbottom(self):
        return self._f.topbottom

    def clear(self, surface):
        targets = {
            'top': self._f.top,
            'bottom': self._f.bottom,
            'full': self._f.topbottom,
        }
        return self._f.cls(targets.get(surface, surface))

    def cls(self, surface, *args, **kwargs):
        return self._f.cls(surface, *args, **kwargs)

    def render_text(self, text, *args, **kwargs):
        return self._f.renderstring(text, *args, **kwargs)

    def renderstring(self, text, *args, **kwargs):
        return self._f.renderstring(text, *args, **kwargs)

    def measure_text(self, text):
        return self._f.strlen(text)

    def strlen(self, text):
        return self._f.strlen(text)

    def refresh(self, *args, **kwargs):
        return self._f.refresh(*args, **kwargs)

    def sysprint(self, *args, **kwargs):
        return self._f.sysprint(*args, **kwargs)

    def reset(self):
        return self._f.reset()

    def version_delay(self, *args, **kwargs):
        return self._f.version_delay(*args, **kwargs)

    # Transport/data ------------------------------------------------------
    def get_departures(self):
        return self._f.get_departure()

    def get_departure(self):
        return self.get_departures()

    def prepare_list_departures(self):
        return self._f.prepare_list_data()

    def prepare_list_data(self):
        return self.prepare_list_departures()

    def normalize_departures(self, departures):
        return self._f.reformat_data(departures)

    def reformat_data(self, departures):
        return self.normalize_departures(departures)

    def get_deviations(self):
        return self._f.get_deviations()

    def ad_message(self):
        return self._f.ad_message()

    def nightcheck(self):
        return self._f.nightcheck()

    # Shared formatting/classification -----------------------------------
    def now_text(self):
        return self._f._now_text()

    def _now_text(self):
        return self.now_text()

    def is_night_bus_line(self, line_id):
        return self._f._is_night_bus_line(line_id)

    def _is_night_bus_line(self, line_id):
        return self.is_night_bus_line(line_id)

    def abbreviate_destination(self, *args, **kwargs):
        return self._f.abbreviate_dest(*args, **kwargs)

    def abbreviate_dest(self, *args, **kwargs):
        return self.abbreviate_destination(*args, **kwargs)

    # Shared message-cycle timing ----------------------------------------
    def scroll_delay_seconds(self):
        return self._f._scroll_delay_seconds()

    def _scroll_delay_seconds(self):
        return self.scroll_delay_seconds()

    def disruption_timer(self):
        return self._f._disruption_timer()

    def _disruption_timer(self):
        return self.disruption_timer()

    def mark_disruption_cycle(self, now=None):
        return self._f._mark_disruption_cycle(now)

    def _mark_disruption_cycle(self, now=None):
        return self.mark_disruption_cycle(now)

    def custom_scroll_message(self):
        return self._f._dlr_custom_message()

    def _dlr_custom_message(self):
        return self.custom_scroll_message()

    def scroll_content_mode(self):
        return self._f._dlr_scroll_content_mode()

    def _dlr_scroll_content_mode(self):
        return self.scroll_content_mode()
