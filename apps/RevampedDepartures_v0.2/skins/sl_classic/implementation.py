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
        _departure_text = self.f.reformat_data(departures)

        if self.custom_scroll_available():
            _custom_text = str(self.v.settings.get("custom_scroll_text", "")).strip()
            _position = int(self.v.settings.get("custom_scroll_position", 0))

            _third_gap = max(1, self.v.if_long // 3)

            if _position == 1:  # Before departures
                _custom_end = self.f.renderstring(_custom_text, large=True)
                _departure_start = _custom_end + _third_gap
                _ticker_end = self.f.renderstring(_departure_text, large=True, start_x=_departure_start)
                print("CUSTOM SCROLL prepended:", _custom_text)

            elif _position == 2:  # After first scrolling departure
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

            else:
                _departure_end = self.f.renderstring(_departure_text, large=True)
                _custom_start = _departure_end + self.v.if_long
                _ticker_end = self.f.renderstring(_custom_text, large=True, start_x=_custom_start)
                print("CUSTOM SCROLL appended:", _custom_text)

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
            if elapsed < baseline:
                return False
            steps = max(1, min(3, int(elapsed / baseline)))
            self.v.tg2.x -= steps
            self.f.refresh(refresh_times)
            self.v.shared["classic_scroll_last_step"] = last + steps * baseline
            return True

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

        self.v.shared["classic_scroll_last_step"] = _refresh_finished
        return True
