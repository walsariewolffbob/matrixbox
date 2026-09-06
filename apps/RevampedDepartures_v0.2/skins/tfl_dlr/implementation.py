import time


class DlrSkin:
    def __init__(self, services):
        self.f = services
        self.v = services.varinit
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
        """CircuitPython-safe uppercase for Swedish DLR text.

        Some MatrixBOX/CircuitPython builds uppercase ASCII but leave å/ä/ö
        unchanged when those characters occur inside a word.  Apply normal
        uppercasing first, then explicitly promote the Swedish glyphs so the
        emulator and real matrix render identically.
        """
        text = str(text).upper()
        return text.replace("å", "Å").replace("ä", "Ä").replace("ö", "Ö")

    def _dlr_abbreviate_dest(self, text, max_px, font_index, uppercase=False):
        """Apply DLR destination abbreviations using the width actually rendered."""
        raw_text = str(text)
        text = raw_text

        def _fits(candidate):
            rendered = self._dlr_upper(candidate) if uppercase else str(candidate)
            return self._font_width(rendered, font_index) <= max_px

        if _fits(text):
            return text

        # User-configured abbreviations first, matching the existing list renderer.
        for pair in self.v.settings.get("dest_abbrev", []):
            if not isinstance(pair, list) or len(pair) != 2:
                continue
            long, short = pair
            if long and long in text:
                text = text.replace(long, short)
                if _fits(text):
                    return text

        # Generic built-in replacements from self.dicts.py.
        for pair in self.dicts.replace_list_destinations:
            try:
                long, short = pair
            except:
                continue
            if long and long in text:
                text = text.replace(long, short)
                if _fits(text):
                    return text

        # Exact station-name abbreviations are keyed by the original destination,
        # not by the partially transformed generic-replacement string.
        try:
            mapped = self.station_names_dict.get(raw_text)
        except:
            mapped = None
        if mapped and _fits(mapped):
            return mapped

        # If the exact station mapping exists but still cannot fully fit, keep it as
        # the preferred fallback; the final character clipper will trim from there
        # rather than from the un-abbreviated destination.
        if mapped:
            return mapped

        return text

    def _dlr_clock_string(self):
        """Fixed DLR overlay clock: always HH:MM, never date/alignment decoration."""
        t = time.localtime(self.v.currenttime)
        def _z(n):
            s = str(n)
            return "0" + s if len(s) == 1 else s
        return _z(t[3]) + ":" + _z(t[4])

    def _dlr_scroll_delay_seconds(self):
        """Backward-compatible name used by the DLR animation."""
        return self.f._scroll_delay_seconds()

    def reset_message_cycle(self):
        """Reset the DLR lower-half message cycle to its configured dwell."""
        self.v.dlr_message_state = {
            "phase": "normal",
            "normal_since": time.monotonic(),
            "last_step": 0,
            "message": "",
            "message_width": 0,
        }
        try:
            self.v.tg2.x = 0
            self.v.tg2.y = 16
        except:
            pass

    def message_active(self):
        """True while the DLR lower half is sliding away or scrolling a message."""
        try:
            return self.v.dlr_message_state.get("phase", "normal") != "normal"
        except:
            return False

    def _next_message(self):
        """Choose the next DLR lower-half message from the selected source."""
        _content_mode = self.f._dlr_scroll_content_mode()
        if _content_mode == "none":
            return ""
        if _content_mode == "custom":
            return self.f._dlr_custom_message()

        now = time.monotonic()

        try:
            _operator = self.v.settings["stations"]["1"]["operator"]
        except:
            _operator = ""

        if (self.v.shared.get("nightcount", 0) < 2
                and _operator in ("sl", "vt")
                and now > self.f._disruption_timer() + self.f._scroll_delay_seconds()):
            try:
                msg = str(self.f.get_deviations()).strip()
                self.f._mark_disruption_cycle(now)
                self.v.deviations_timer = now
                if msg:
                    return msg
            except Exception as e:
                print("DLR disruption message error:", repr(e))
                # A failed fetch starts a new configured delay before retrying.
                self.f._mark_disruption_cycle(now)
                self.v.deviations_timer = now

        return ""

    def animation_tick(self):
        """Animate the DLR lower-half message cycle one small step.

        Normal rows 2+3 (and the optional clock) remain for the configured delay.
        If a custom or native disruption message is available, the lower TileGrid slides
        downward, the message scrolls horizontally through the lower half, and the
        normal DLR rows are rebuilt when it has completely passed.
        """
        if int(self.v.settings.get("listmode", 0)) != 2:
            return False

        try:
            state = self.v.dlr_message_state
            if not isinstance(state, dict):
                raise TypeError
        except:
            self.reset_message_cycle()
            state = self.v.dlr_message_state

        now = time.monotonic()
        phase = state.get("phase", "normal")

        # If Scroll Text is switched to None while a DLR message is already
        # sliding/scolling, cancel that animation immediately. The renderer
        # wrapper will restore the cached departure frame rather than allowing
        # stale text to continue moving across the screen.
        if phase != "normal" and self.f._dlr_scroll_content_mode() == "none":
            self.reset_message_cycle()
            return "message_cancelled"

        if phase == "normal":
            if now < float(state.get("normal_since", now)) + self._dlr_scroll_delay_seconds():
                return False

            msg = self._next_message()
            # Do not repeatedly test/fetch every main-loop iteration when nothing is
            # available. Start another normal configured dwell instead.
            state["normal_since"] = now
            if not msg:
                return False

            state["phase"] = "slide_down"
            state["message"] = msg
            state["last_step"] = 0
            return True

        # Keep the vertical transition at ~30 fps, but scroll DLR text at ~2x that
        # rate. On the physical MatrixBOX the old shared 0.03 s cadence made the
        # horizontal ticker appear about half as fast as SL Classic.
        _step_delay = 0.015 if phase == "scroll_message" else 0.03
        if now < float(state.get("last_step", 0)) + _step_delay:
            return False
        state["last_step"] = now

        if phase == "slide_down":
            try:
                self.v.tg2.y += 1
                if False:
                    self.f.refresh(1)
            except:
                pass

            if self.v.tg2.y >= 32:
                # Lower departures + clock are now fully below the 32px display.
                # Reuse that same lower bitmap as a normal large-font ticker.
                self.v.tg2.y = 16
                self.v.tg2.x = self.v.if_long
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
                self.v.tg2.x -= 1
                if False:
                    self.f.refresh(1)
            except:
                pass

            if self.v.tg2.x < -int(state.get("message_width", 0)):
                # Tell the renderer that the message cycle is complete. The
                # renderer decides whether the ordinary data-refresh interval is
                # due; otherwise it can rebuild the DLR frame from its cached
                # payload without another network fetch.
                self.v.tg2.x = 0
                self.v.tg2.y = 16
                state["phase"] = "normal"
                state["normal_since"] = now
                state["message"] = ""
                state["message_width"] = 0
                return "message_complete"
            return "refresh"

        self.reset_message_cycle()
        return False

    def render(self, _departure_data):
        """TfL DLR layout: one large departure on self.f.top, two compact departures below."""
        try:
            _dlr_phase = self.v.dlr_message_state.get("phase", "normal")
        except:
            self.reset_message_cycle()
            _dlr_phase = "normal"
        # DLR physically renders up to three rows; the user may request fewer.
        # self.f.renderstring() changes currentfont. DLR has mixed large/small rows, so always
        # begin from a known font state instead of inheriting the previous renderer.
        self.v.currentfont = 0

        # DLR uses the same physical 16px + 16px screen arrangement as SL Classic.
        # Keep the normal self.f.top/self.f.bottom TileGrids visible and hide the full-screen list bitmap.
        self.v.tg1.y, self.v.tg2.y, self.v.tg3.y = 0, 16, 32
        # Classic scroll moves tg2.x continuously. Never inherit that offset in DLR.
        self.v.tg1.x, self.v.tg2.x, self.v.tg3.x = 0, 0, 0

        if self.v.shared["loop_counter"] == -7:
            self.f.reset()

        # Restore the physical DLR split layout after the startup splash.
        self.v.tg1.y, self.v.tg2.y, self.v.tg3.y = 0, 16, 32

        trainlist = self.f.reformat_data(_departure_data)
        if not isinstance(trainlist, list) or not trainlist:
            self.f.cls(self.f.top)
            self.f.cls(self.f.bottom)

            _msg = str(trainlist).strip() if trainlist is not None else ""
            _no_more = str(self.v.settings.get("no_more_departures", "")).strip()
            if not _no_more:
                _no_more = self.dicts.language[self.v.settings["language"]]["display"]["no_more_departures"]

            # DLR empty state: keep it static and readable. The text comes directly
            # from settings.txt (`no_more_departures`) and is shown on the large self.f.top
            # line; the lower half remains blank.
            if _no_more and (_no_more in _msg or not _msg):
                self.v.currentfont = 0
                self.f.renderstring(_no_more, 1, large=True, _cls=self.f.top)
            elif _msg:
                # Preserve useful non-empty status/error strings rather than hiding
                # them, while still keeping DLR's lower half clear.
                self.v.currentfont = 0
                self.f.renderstring(_msg, 1, large=True, _cls=self.f.top)

            return time.monotonic()

        _row_limit = min(3, max(1, int(self.v.settings.get("maxdest", 3))))
        rows = [row[:] for row in trainlist[:_row_limit] if isinstance(row, list) and len(row) >= 4]
        _visible_departures = [row for row in rows if len(row) > 4]
        _all_visible_are_night = bool(_visible_departures)
        for _row in _visible_departures:
            if not self.f._is_night_bus_line(_row[1]):
                _all_visible_are_night = False
                break
        _night_highlight_mode = int(self.v.settings.get("night_bus_highlight", 0))
        _night_highlight_enabled = (_night_highlight_mode == 2 or
                                    (_night_highlight_mode == 1 and not _all_visible_are_night))
        self.f.cls(self.f.top)
        self.f.cls(self.f.bottom)

        # DLR clock is an overlay, not a replacement departure.  Reserve its large-font
        # footprint on the right of the lower 16px and leave exactly 2 blank columns
        # between the row-2/3 time markers and the clock.
        _show_dlr_clock = int(self.v.settings.get("show_clock_row", 0))
        _dlr_clock = self._dlr_clock_string() if _show_dlr_clock else ""
        _dlr_clock_x = max(0, self.v.if_long - self._font_width(_dlr_clock, 0)) if _show_dlr_clock else self.v.if_long
        _lower_value_right = max(0, _dlr_clock_x - 2) if _show_dlr_clock else self.v.if_long

        def _draw_row(row, number, bmp, y, font_index):
            # Shared List/DLR line-label mode:
            #   0 = visible row numbers (1, 2, 3...)
            #   1 = actual transit line number/id from departure data
            _line_mode = int(self.v.settings.get("list_line_display", 0))
            _line_label = str(row[1]).strip() if _line_mode else str(number)
            prefix = _line_label + " "
            raw_dest = str(row[2]).split('(')[0].split(" via")[0].strip()
            dest = raw_dest
            value = str(row[3])

            # self.f.reformat_data() already applies Dynamic / Time / Countdown logic.
            # Only add the configured minute suffix when the returned value is numeric.
            if int(self.v.settings.get("clocktime", 0)) != 1 and value.strip().isdigit():
                value += self.v.settings["mins"]

            # Lower DLR rows are rendered in capitals.  Do this BEFORE measuring the
            # time/value field: uppercase glyphs can be wider than their lowercase
            # counterparts, and the destination must be fitted around the pixels we
            # will actually draw.
            if number != 1:
                value = self._dlr_upper(value)

            value_right = self.v.if_long if number == 1 else _lower_value_right
            if number != 1 and not _show_dlr_clock:
                # The small-font right edge is one pixel tighter than the large self.f.top
                # row.  Keep the final column on-screen instead of clipping it.
                value_right = max(0, value_right - 1)

            actual_value_width = self._font_width(value, font_index)
            is_now = value.strip().lower() == self.f._now_text().lower()

            # Rows 2/3 keep a stable value slot for a given departure.  Once a wider
            # minute/time marker has reserved space, NU does not reclaim those pixels.
            # This keeps both the destination abbreviation and the visual padding
            # unchanged, with or without the DLR clock overlay.
            if number != 1:
                try:
                    _slots = self.v.dlr_lower_value_slots
                except:
                    _slots = {}
                    self.v.dlr_lower_value_slots = _slots
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
                # The reserved slot controls how much room the destination may use,
                # but the visible value itself is always pinned to the slot's right
                # edge. This keeps 2/3-row minutes, clock times and NU aligned the
                # same way on both CircuitPython hardware and the emulator.
                value_x = max(0, value_right - actual_value_width)
            else:
                reserved_value_width = actual_value_width
                slot_x = max(0, value_right - actual_value_width)
                value_x = slot_x

            if is_now and number == 1:
                # Top-row Nu keeps its special 1px right-edge correction plus the
                # requested 3px breathing room on its left.
                value_x = max(0, value_x - 1)

            left_gap = 3 if (number == 1 and is_now) else 1
            max_left = max(0, slot_x - left_gap)
            max_dest = max(0, max_left - self._font_width(prefix, font_index))

            # Top-row DLR abbreviation is sticky for the current first destination.
            # If the destination needed a built-in/user abbreviation while a wider
            # countdown/time value was shown, keep that exact abbreviation when the
            # value later narrows to Nu instead of expanding the name again.
            if number == 1:
                try:
                    _cache = self.v.dlr_top_abbrev_cache
                except:
                    _cache = {}
                    self.v.dlr_top_abbrev_cache = _cache

                if _cache.get("raw") == raw_dest and _cache.get("abbr"):
                    dest = _cache["abbr"]
                else:
                    dest = self._dlr_abbreviate_dest(raw_dest, max_dest, font_index)
                    if dest != raw_dest:
                        self.v.dlr_top_abbrev_cache = {"raw": raw_dest, "abbr": dest}
                    else:
                        self.v.dlr_top_abbrev_cache = {"raw": raw_dest, "abbr": ""}
            else:
                # Fit against the reduced lower-row width (including the clock area,
                # when present) before falling back to clipping.  Keep the selected
                # self.dicts.py abbreviation sticky while this same departure occupies the
                # row, including when its value changes to NU.
                try:
                    _abbrs = self.v.dlr_lower_abbrev_cache
                except:
                    _abbrs = {}
                    self.v.dlr_lower_abbrev_cache = _abbrs
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
                # TfL DLR lower rows use block-capital destination/value text.
                # Apply this after abbreviation selection so self.dicts.py remains the
                # authoritative source of abbreviations.
                dest = self._dlr_upper(dest)

            left = prefix + dest
            while dest and self._font_width(left, font_index) > max_left:
                dest = dest[:-1]
                left = prefix + dest

            # Reuse the SL List colour toggles in DLR:
            #   listcolor      ON = white departure number, OFF = yellow
            #   listcolor_time ON = white time/minutes,     OFF = yellow
            # Keep the destination itself in the normal destination colour.
            _night_highlight = _night_highlight_enabled and self.f._is_night_bus_line(row[1])
            line_colour = "red" if _night_highlight else ("white" if int(self.v.settings.get("listcolor", 0)) else "yellow")
            time_colour = "red" if _night_highlight else ("white" if int(self.v.settings.get("listcolor_time", 0)) else "yellow")
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
            # Large clock spans the two compact lower rows and is pinned to the right edge.
            self.f.renderstring(_dlr_clock, 0, large=True, target_bmp=self.f.bottom, target_offs=3,
                         start_x=_dlr_clock_x, sys_msg=self.v.settings.get("clock_row_color", "white"))

        return time.monotonic()
