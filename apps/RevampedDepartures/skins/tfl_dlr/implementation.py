
import time


class DlrSkin:
    def __init__(self, services):
        self.f = services
        self.dicts = services.dicts
        self.station_names_dict = services.station_names_dict
        self.fonts = services.fonts

    def _font_width(self, text, font_index):
        f = self.fonts[font_index]
        total = 0
        for c in str(text):
            if c not in f: c = "_"
            total += f[c][0] if isinstance(f[c][1], int) else len(f[c][1])
        return total

    def _dlr_upper(self, text):
        text = str(text).upper()
        return text.replace("å", "Å").replace("ä", "Ä").replace("ö", "Ö")

    def _dlr_abbreviate_dest(self, text, max_px, font_index, uppercase=False):
        raw_text = str(text)
        text = raw_text

        def _fits(candidate):
            rendered = self._dlr_upper(candidate) if uppercase else str(candidate)
            return self._font_width(rendered, font_index) <= max_px

        if _fits(text):
            return text

        
        for pair in self.f.settings.get("dest_abbrev", []):
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            long, short = pair
            if long and long in text:
                text = text.replace(long, short)
                if _fits(text):
                    return text

        
        for pair in self.dicts.replace_list_destinations:
            try:
                long, short = pair
            except:
                continue
            if long and long in text:
                text = text.replace(long, short)
                if _fits(text):
                    return text

        
        
        try:
            mapped = self.station_names_dict.get(raw_text)
        except:
            mapped = None
        if mapped and _fits(mapped):
            return mapped

        
        
        
        if mapped:
            return mapped

        return text

    def _dlr_clock_string(self):
        t = time.localtime(self.f.current_time)
        def _z(n):
            s = str(n)
            return "0" + s if len(s) == 1 else s
        return _z(t[3]) + ":" + _z(t[4])

    def _dlr_scroll_delay_seconds(self):
        return self.f.scroll_delay_seconds()

    def reset_message_cycle(self):
        self.f.dlr_message_state = {
            "phase": "normal",
            "normal_since": time.monotonic(),
            "last_step": 0,
            "message": "",
            "message_width": 0,
        }
        try:
            self.f.middle_group.x = 0
            self.f.middle_group.y = 16
        except:
            pass

    def message_active(self):
        try:
            return self.f.dlr_message_state.get("phase", "normal") != "normal"
        except:
            return False

    def _next_message(self):
        _content_mode = self.f.scroll_content_mode()
        if _content_mode == "none":
            return ""
        if _content_mode == "custom":
            return self.f.custom_scroll_message()

        now = time.monotonic()

        try:
            _operator = self.f.settings["stations"]["1"]["operator"]
        except:
            _operator = ""

        if (self.f.shared.get("nightcount", 0) < 2
                and _operator in ("sl", "vt")
                and now > self.f.disruption_timer() + self.f.scroll_delay_seconds()):
            try:
                msg = str(self.f.get_deviations()).strip()
                self.f.mark_disruption_cycle(now)
                self.f.set_deviations_timer(now)
                if msg:
                    return msg
            except Exception as e:
                print("DLR disruption message error:", repr(e))
                
                self.f.mark_disruption_cycle(now)
                self.f.set_deviations_timer(now)

        return ""

    def animation_tick(self):
        if int(self.f.settings.get("listmode", 0)) != 2:
            return False

        try:
            state = self.f.dlr_message_state
            if not isinstance(state, dict):
                raise TypeError
        except:
            self.reset_message_cycle()
            state = self.f.dlr_message_state

        now = time.monotonic()
        phase = state.get("phase", "normal")

        
        
        
        
        if phase != "normal" and self.f.scroll_content_mode() == "none":
            self.reset_message_cycle()
            return "message_cancelled"

        if phase == "normal":
            if now < float(state.get("normal_since", now)) + self._dlr_scroll_delay_seconds():
                return False

            msg = self._next_message()
            
            
            state["normal_since"] = now
            if not msg:
                return False

            state["phase"] = "slide_down"
            state["message"] = msg
            state["last_step"] = 0
            return True

        
        
        
        _step_delay = 0.015 if phase == "scroll_message" else 0.03
        if now < float(state.get("last_step", 0)) + _step_delay:
            return False
        state["last_step"] = now

        if phase == "slide_down":
            try:
                self.f.middle_group.y += 1
                if False:
                    self.f.refresh(1)
            except:
                pass

            if self.f.middle_group.y >= 32:
                
                
                self.f.middle_group.y = 16
                self.f.middle_group.x = self.f.display_width
                self.f.cls(self.f.bottom)
                state["message_width"] = self.f.renderstring(
                    state.get("message", ""), large=True, _cls=self.f.bottom
                )
                state["phase"] = "scroll_message"
                if False:
                    self.f.refresh(1)
            return "refresh"

        if phase == "scroll_message":
            try:
                self.f.middle_group.x -= 1
                if False:
                    self.f.refresh(1)
            except:
                pass

            if self.f.middle_group.x < -int(state.get("message_width", 0)):
                
                
                
                
                self.f.middle_group.x = 0
                self.f.middle_group.y = 16
                state["phase"] = "normal"
                state["normal_since"] = now
                state["message"] = ""
                state["message_width"] = 0
                return "message_complete"
            return "refresh"

        self.reset_message_cycle()
        return False

    def render(self, _departure_data):
        try:
            _dlr_phase = self.f.dlr_message_state.get("phase", "normal")
        except:
            self.reset_message_cycle()
            _dlr_phase = "normal"
        
        
        
        self.f.set_current_font(0)

        
        
        self.f.top_group.y, self.f.middle_group.y, self.f.bottom_group.y = 0, 16, 32
        
        self.f.top_group.x, self.f.middle_group.x, self.f.bottom_group.x = 0, 0, 0

        if self.f.shared["loop_counter"] == -7:
            self.f.reset()

        
        self.f.top_group.y, self.f.middle_group.y, self.f.bottom_group.y = 0, 16, 32

        trainlist = self.f.reformat_data(_departure_data)
        if not isinstance(trainlist, list) or not trainlist:
            self.f.cls(self.f.top)
            self.f.cls(self.f.bottom)

            _msg = str(trainlist).strip() if trainlist is not None else ""
            _no_more = str(self.f.settings.get("no_more_departures", "")).strip()
            if not _no_more:
                _no_more = self.dicts.language[self.f.settings["language"]]["display"]["no_more_departures"]

            
            
            
            if _no_more and (_no_more in _msg or not _msg):
                self.f.set_current_font(0)
                self.f.renderstring(_no_more, 1, large=True, _cls=self.f.top)
            elif _msg:
                
                
                self.f.set_current_font(0)
                self.f.renderstring(_msg, 1, large=True, _cls=self.f.top)

            return time.monotonic()

        _row_limit = min(3, max(1, int(self.f.settings.get("maxdest", 3))))
        rows = [row[:] for row in trainlist[:_row_limit] if isinstance(row, list) and len(row) >= 4]
        _visible_departures = [row for row in rows if len(row) > 4]
        _all_visible_are_night = bool(_visible_departures)
        for _row in _visible_departures:
            if not self.f.is_night_bus_line(_row[1]):
                _all_visible_are_night = False
                break
        _night_highlight_mode = int(self.f.settings.get("night_bus_highlight", 0))
        _night_highlight_enabled = (_night_highlight_mode == 2 or
                                    (_night_highlight_mode == 1 and not _all_visible_are_night))
        self.f.cls(self.f.top)
        self.f.cls(self.f.bottom)

        
        
        
        _show_dlr_clock = int(self.f.settings.get("show_clock_row", 0))
        _dlr_clock = self._dlr_clock_string() if _show_dlr_clock else ""
        _dlr_clock_x = max(0, self.f.display_width - self._font_width(_dlr_clock, 0)) if _show_dlr_clock else self.f.display_width
        _lower_value_right = max(0, _dlr_clock_x - 2) if _show_dlr_clock else self.f.display_width

        def _draw_row(row, number, bmp, y, font_index):
            
            
            
            _line_mode = int(self.f.settings.get("list_line_display", 0))
            _line_label = str(row[1]).strip() if _line_mode else str(number)
            prefix = _line_label + " "
            raw_dest = str(row[2]).split('(')[0].split(" via")[0].strip()
            dest = raw_dest
            value = str(row[3])

            
            
            if int(self.f.settings.get("clocktime", 0)) != 1 and value.strip().isdigit():
                value += self.f.settings["mins"]

            
            
            
            
            if number != 1:
                value = self._dlr_upper(value)

            value_right = self.f.display_width if number == 1 else _lower_value_right
            if number != 1 and not _show_dlr_clock:
                
                
                value_right = max(0, value_right - 1)

            actual_value_width = self._font_width(value, font_index)
            is_now = value.strip().lower() == self.f.now_text().lower()

            
            
            
            
            if number != 1:
                try:
                    _slots = self.f.dlr_lower_value_slots
                except:
                    _slots = {}
                    self.f.dlr_lower_value_slots = _slots
                _slot_key = str(number)
                _slot = _slots.get(_slot_key, {})
                _clock_key = 1 if _show_dlr_clock else 0
                if _slot.get("raw") != raw_dest or _slot.get("clock") != _clock_key:
                    _slot = {"raw": raw_dest, "clock": _clock_key, "width": actual_value_width}
                elif not is_now:
                    _slot["width"] = max(int(_slot.get("width", 0)), actual_value_width)
                reserved_value_width = max(actual_value_width, int(_slot.get("width", actual_value_width)))
                _slot["width"] = reserved_value_width
                _slots[_slot_key] = _slot
                slot_x = max(0, value_right - reserved_value_width)
                
                
                
                
                value_x = max(0, value_right - actual_value_width)
            else:
                reserved_value_width = actual_value_width
                slot_x = max(0, value_right - actual_value_width)
                value_x = slot_x

            if is_now and number == 1:
                
                
                value_x = max(0, value_x - 1)

            left_gap = 3 if (number == 1 and is_now) else 1
            max_left = max(0, slot_x - left_gap)
            max_dest = max(0, max_left - self._font_width(prefix, font_index))

            
            
            
            
            if number == 1:
                try:
                    _cache = self.f.dlr_top_abbrev_cache
                except:
                    _cache = {}
                    self.f.dlr_top_abbrev_cache = _cache

                if _cache.get("raw") == raw_dest and _cache.get("abbr"):
                    dest = _cache["abbr"]
                else:
                    dest = self._dlr_abbreviate_dest(raw_dest, max_dest, font_index)
                    if dest != raw_dest:
                        self.f.dlr_top_abbrev_cache = {"raw": raw_dest, "abbr": dest}
                    else:
                        self.f.dlr_top_abbrev_cache = {"raw": raw_dest, "abbr": ""}
            else:
                
                
                
                
                try:
                    _abbrs = self.f.dlr_lower_abbrev_cache
                except:
                    _abbrs = {}
                    self.f.dlr_lower_abbrev_cache = _abbrs
                _abbr_key = str(number)
                _cached = _abbrs.get(_abbr_key, {})
                _clock_key = 1 if _show_dlr_clock else 0
                if (_cached.get("raw") == raw_dest and
                        _cached.get("clock") == _clock_key and _cached.get("abbr")):
                    dest = _cached["abbr"]
                else:
                    dest = self._dlr_abbreviate_dest(raw_dest, max_dest, font_index, uppercase=True)
                    _abbrs[_abbr_key] = {
                        "raw": raw_dest,
                        "clock": _clock_key,
                        "abbr": dest if dest != raw_dest else "",
                    }
                
                
                
                dest = self._dlr_upper(dest)

            left = prefix + dest
            while dest and self._font_width(left, font_index) > max_left:
                dest = dest[:-1]
                left = prefix + dest

            
            
            
            
            _night_highlight = _night_highlight_enabled and self.f.is_night_bus_line(row[1])
            line_colour = "red" if _night_highlight else ("white" if int(self.f.settings.get("listcolor", 0)) else "yellow")
            time_colour = "red" if _night_highlight else ("white" if int(self.f.settings.get("listcolor_time", 0)) else "yellow")
            prefix_width = self._font_width(prefix, font_index)
            self.f.renderstring(prefix, 0, large=(font_index == 0), smallfont=(font_index != 0),
                         target_bmp=bmp, target_offs=y, start_x=0, sys_msg=line_colour)
            self.f.renderstring(dest, 0, large=(font_index == 0), smallfont=(font_index != 0),
                         target_bmp=bmp, target_offs=y, start_x=prefix_width)
            self.f.renderstring(value, 0, large=(font_index == 0), smallfont=(font_index != 0),
                         target_bmp=bmp, target_offs=y, start_x=value_x, sys_msg=time_colour)

        if len(rows) > 0:
            _draw_row(rows[0], 1, self.f.top, 2, 0)
        if len(rows) > 1:
            _draw_row(rows[1], 2, self.f.bottom, 0, 1)
        if len(rows) > 2:
            _draw_row(rows[2], 3, self.f.bottom, 8, 1)

        if _show_dlr_clock:
            
            self.f.renderstring(_dlr_clock, 0, large=True, target_bmp=self.f.bottom, target_offs=3,
                         start_x=_dlr_clock_x, sys_msg=self.f.settings.get("clock_row_color", "white"))

        return time.monotonic()
