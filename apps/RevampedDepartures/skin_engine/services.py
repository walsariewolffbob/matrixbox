

class SkinServices:
    def __init__(self, functions):
        self._f = functions

    
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
    def display_width(self):
        return self._f.varinit.if_long

    @property
    def top_group(self):
        return self._f.varinit.tg1

    @property
    def middle_group(self):
        return self._f.varinit.tg2

    @property
    def bottom_group(self):
        return self._f.varinit.tg3

    @property
    def active_message(self):
        return bool(self._f.varinit.active_message)

    @active_message.setter
    def active_message(self, value):
        self._f.varinit.active_message = bool(value)

    @property
    def ad_timer(self):
        return self._f.varinit.ad_timer

    @property
    def ad_delay_minutes(self):
        return self._f.varinit.ad_delay

    def set_current_font(self, value):
        self._f.varinit.currentfont = value

    def set_deviations_timer(self, value):
        self._f.varinit.deviations_timer = value

    def set_scroll_extent(self, value):
        self._f.varinit.scrollsum = value

    
    @property
    def physical_display_width(self):
        return self._f.varinit.display.width

    @property
    def display_height(self):
        return self._f.varinit.if_tall

    @property
    def rotated(self):
        return bool(self._f.varinit.rotated)

    @property
    def current_font_index(self):
        return self._f.varinit.currentfont

    @property
    def destination_bitmaps(self):
        return self._f.varinit.dest_bmps

    @property
    def destination_groups(self):
        return self._f.varinit.dest_tgs

    @property
    def destination_scroll_state(self):
        return self._f.varinit.dest_scroll_state

    @destination_scroll_state.setter
    def destination_scroll_state(self, value):
        self._f.varinit.dest_scroll_state = value

    @property
    def overlay_bitmap(self):
        return self._f.varinit.overlay_bmp

    @property
    def overlay_group(self):
        return self._f.varinit.overlay_tg

    @property
    def train_data(self):
        return self._f.varinit.traindata

    @train_data.setter
    def train_data(self, value):
        self._f.varinit.traindata = value

    
    @property
    def current_time(self):
        return self._f.varinit.currenttime

    @property
    def dlr_message_state(self):
        return self._f.varinit.dlr_message_state

    @dlr_message_state.setter
    def dlr_message_state(self, value):
        self._f.varinit.dlr_message_state = value

    @property
    def dlr_lower_value_slots(self):
        return self._f.varinit.dlr_lower_value_slots

    @dlr_lower_value_slots.setter
    def dlr_lower_value_slots(self, value):
        self._f.varinit.dlr_lower_value_slots = value

    @property
    def dlr_top_abbrev_cache(self):
        return self._f.varinit.dlr_top_abbrev_cache

    @dlr_top_abbrev_cache.setter
    def dlr_top_abbrev_cache(self, value):
        self._f.varinit.dlr_top_abbrev_cache = value

    @property
    def dlr_lower_abbrev_cache(self):
        return self._f.varinit.dlr_lower_abbrev_cache

    @dlr_lower_abbrev_cache.setter
    def dlr_lower_abbrev_cache(self, value):
        self._f.varinit.dlr_lower_abbrev_cache = value

    @property
    def CLOCK_ROW_MARK(self):
        return self._f.CLOCK_ROW_MARK

    @property
    def MSG_ROW_MARK(self):
        return self._f.MSG_ROW_MARK

    
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

    
    def now_text(self):
        return self._f._now_text()


    def is_night_bus_line(self, line_id):
        return self._f._is_night_bus_line(line_id)


    def abbreviate_destination(self, *args, **kwargs):
        return self._f.abbreviate_dest(*args, **kwargs)

    def abbreviate_dest(self, *args, **kwargs):
        return self.abbreviate_destination(*args, **kwargs)

    
    def scroll_delay_seconds(self):
        return self._f._scroll_delay_seconds()


    def disruption_timer(self):
        return self._f._disruption_timer()


    def mark_disruption_cycle(self, now=None):
        return self._f._mark_disruption_cycle(now)


    def custom_scroll_message(self):
        return self._f._dlr_custom_message()


    def scroll_content_mode(self):
        return self._f._dlr_scroll_content_mode()

