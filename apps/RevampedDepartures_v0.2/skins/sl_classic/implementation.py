import time


class SlClassicSkin:
    def __init__(self, services):
        self.f = services
        self.v = services.varinit

    def custom_scroll_available(self):
        if int(self.v.settings.get('listmode', 0)):
            return False
        if not int(self.v.settings.get('custom_scroll_show', 0)):
            return False
        return bool(str(self.v.settings.get('custom_scroll_text', '')).strip())

    def reset_scroll_pacing(self, reset_baseline=False):
        self.v.shared['classic_scroll_last_step'] = time.monotonic()
        if reset_baseline:
            self.v.shared['classic_scroll_interval'] = 0
        self.v.shared['classic_scroll_setting'] = int(self.v.settings.get('scroll', 0))

    def render(self, departures):
        """Build the SL Classic ticker from an already-prepared departure snapshot.

        This is the Stage 2 extraction seam: no network access happens here. The
        legacy renderer can still fetch before calling this helper, while the new
        renderer/controller can supply one shared snapshot during a transactional
        view build.
        """
        _departure_text = self.f.reformat_data(departures)

        # SL Classic ticker. When custom text is enabled, both parts are rendered
        # into the SAME bitmap with one full display-width of blank space between
        # them. Another full display-width is added to scrollsum after the final
        # item so the last text can fully clear the display before the ticker is
        # rebuilt with fresh departures.
        if self.custom_scroll_available():
            _custom_text = str(self.v.settings.get("custom_scroll_text", "")).strip()
            _position = int(self.v.settings.get("custom_scroll_position", 0))

            _third_gap = max(1, self.v.if_long // 3)

            if _position == 1:  # Before departures
                # Custom text is the first scrolling item after every rebuild.
                # A third-screen gap is enough before departure 2 enters.
                _custom_end = self.f.renderstring(_custom_text, large=True)
                _departure_start = _custom_end + _third_gap
                _ticker_end = self.f.renderstring(_departure_text, large=True, start_x=_departure_start)
                print("CUSTOM SCROLL prepended:", _custom_text)

            elif _position == 2:  # After first scrolling departure
                # Departure 1 is already on the fixed top row. The bottom ticker
                # therefore begins with departure 2. Split that first ticker item
                # off, insert the custom message, then continue with departures 3+.
                _parts = _departure_text.split("         ", 1)
                _first_departure = _parts[0]
                _remaining_departures = _parts[1] if len(_parts) > 1 else ""

                _first_end = self.f.renderstring(_first_departure, large=True)
                _custom_start = _first_end + _third_gap
                _custom_end = self.f.renderstring(_custom_text, large=True, start_x=_custom_start)

                if _remaining_departures:
                    _remaining_start = _custom_end + _third_gap
                    _ticker_end = self.f.renderstring(_remaining_departures, large=True, start_x=_remaining_start)
                else:
                    _ticker_end = _custom_end
                print("CUSTOM SCROLL after first:", _custom_text)

            else:  # After departures
                _departure_end = self.f.renderstring(_departure_text, large=True)
                _custom_start = _departure_end + self.v.if_long
                _ticker_end = self.f.renderstring(_custom_text, large=True, start_x=_custom_start)
                print("CUSTOM SCROLL appended:", _custom_text)

            # Deliberate blank tail: do not rebuild while the final text is still
            # visible or just touching the left edge.
            return _ticker_end + self.v.if_long

        return self.f.renderstring(_departure_text, large=True)

    def scroll_step(self, refresh_times):
        now = time.monotonic()
        scroll_setting = int(self.v.settings.get("scroll", 0))
        if int(self.v.shared.get("classic_scroll_setting", scroll_setting)) != scroll_setting:
            self.reset_scroll_pacing(reset_baseline=True)
            now = time.monotonic()

        last = float(self.v.shared.get("classic_scroll_last_step", 0) or 0)
        message_active = self.custom_scroll_available() or bool(self.v.active_message)
        baseline = float(self.v.shared.get("classic_scroll_interval", 0) or 0)

        if not last:
            self.v.shared["classic_scroll_last_step"] = now
            last = now

        elapsed = max(0, now - last)

        if message_active and baseline > 0:
            # Message rendering/network work must not change pixels per second.
            if elapsed < baseline:
                return False
            steps = max(1, min(3, int(elapsed / baseline)))
            self.v.tg2.x -= steps
            self.f.refresh(refresh_times)
            self.v.shared["classic_scroll_last_step"] = last + steps * baseline
            return True

        # Ordinary departure ticker: preserve the original one-pixel-per-loop path
        # and learn its real cadence for later custom/disruption text.
        #
        # Important: after a speed-setting change the baseline is intentionally
        # reset to zero. Measure the actual refresh duration here rather than the
        # tiny gap since the previous main-loop call; otherwise the newly learned
        # interval can collapse toward 1 ms and make later message scrolling race.
        self.v.tg2.x -= 1
        _refresh_started = time.monotonic()
        self.f.refresh(refresh_times)
        _refresh_finished = time.monotonic()
        measured = max(0.001, _refresh_finished - _refresh_started)

        old = baseline
        if old <= 0:
            self.v.shared["classic_scroll_interval"] = measured
        else:
            self.v.shared["classic_scroll_interval"] = old * 0.85 + measured * 0.15

        # Store refresh completion as the pacing anchor so switching Low/Normal
        # repeatedly cannot accumulate catch-up steps.
        self.v.shared["classic_scroll_last_step"] = _refresh_finished
        return True
