import time


class SlListSkin:
    def __init__(self, services):
        self.f = services
        self.dicts = services.dicts

    def _column_count(self):
        if not int(self.f.settings.get('multiple', 0)):
            return 1
        if self.f.display_width > 128:
            try:
                return max(2, min(3, int(self.f.settings.get('multi_station_columns', 3))))
            except (TypeError, ValueError):
                return 3
        if self.f.physical_display_width > 64:
            return 2
        return 1

    def render(self, prepared_data):
        mini = self.f.settings['mini']
        half = False

        if self.f.rotated:
            mini = True
        elif self.f.physical_display_width <= 64:
            mini = True
        elif self.f.settings['multiple']:
            mini = True
            half = True
        if self.f.settings['long'] == -1 and not self.f.rotated:
            mini = True
            half = True

        if self.f.display_width > 128:
            self.f.version_delay(slowdown=1)

        large_list = not mini and not half and not self.f.rotated and int(self.f.settings.get('large_list', 0))
        xs_line_id = self.f.physical_display_width <= 64 and not self.f.rotated and int(self.f.settings.get('xs_line_id', 0))
        multi_line = half and not self.f.rotated and self.f.physical_display_width > 64 and int(self.f.settings.get('line_length', 0))
        show_line = not self.f.rotated and (self.f.physical_display_width > 64 or xs_line_id) and (not half or multi_line)

        self.f.set_current_font(2 if mini else (0 if large_list else 1))
        extrarow = 1 if mini else 0
        self.f.top_group.y = extrarow - 32
        self.f.middle_group.y = extrarow - 16
        self.f.bottom_group.y = extrarow

        dest_scroll = int(self.f.settings.get('dest_scroll', 0)) and not half
        now = time.monotonic()
        self.f.cls(self.f.topbottom)

        try:
            for group in self.f.destination_groups:
                group.hidden = True
            self.f.overlay_group.hidden = True
            self.f.overlay_bitmap.fill(0)
            self.f.destination_scroll_state = {}
        except Exception:
            pass

        column_count = self._column_count()
        col_w = self.f.display_width // column_count if half else self.f.display_width
        col_margin = 2

        prepared_copy = {}
        if isinstance(prepared_data, dict):
            for key, value in prepared_data.items():
                if isinstance(value, list):
                    prepared_copy[key] = [list(row) if isinstance(row, list) else row for row in value]
                else:
                    prepared_copy[key] = value
        self.f.train_data = prepared_copy

        try:
            for record in self.f.train_data:
                if int(record) > column_count:
                    continue

                trainlist = self.f.train_data[record]
                if isinstance(trainlist, list):
                    trainlist = [row[:] for row in trainlist if isinstance(row, list)]

                if not half and isinstance(trainlist, str):
                    self.f.sysprint(''.join(trainlist[:30]), 100)
                    if self.dicts.language[self.f.settings['language']]['display']['no_more_departures'] in trainlist:
                        return time.monotonic()
                    try:
                        update_delay = float(self.f.updatedelay)
                    except (TypeError, ValueError):
                        update_delay = 20.0
                    return time.monotonic() - update_delay + 2
                if isinstance(trainlist, str):
                    trainlist = [['', '', trainlist[:40], '', self.f.MSG_ROW_MARK]]

                night_mode = int(self.f.settings.get('night_bus_highlight', 0))
                visible_departures = [
                    row for row in trainlist[:max(1, int(self.f.settings.get('maxdest', 4)))]
                    if isinstance(row, list) and len(row) > 4
                    and row[4] not in (self.f.CLOCK_ROW_MARK, self.f.MSG_ROW_MARK)
                ]
                has_night = any(self.f.is_night_bus_line(row[1]) for row in visible_departures)
                has_day = any(not self.f.is_night_bus_line(row[1]) for row in visible_departures)
                night_enabled = night_mode == 2 or (night_mode == 1 and has_night and has_day)

                line_col = 0
                if (large_list or multi_line) and isinstance(trainlist, list):
                    max_line_w = 0
                    use_real_lines = int(self.f.settings.get('list_line_display', 1))
                    for idx, row in enumerate(trainlist):
                        if not isinstance(row, list) or len(row) < 2:
                            continue
                        marker = row[4] if len(row) > 4 else ''
                        if marker in (self.f.CLOCK_ROW_MARK, self.f.MSG_ROW_MARK):
                            continue
                        value = row[1] if use_real_lines else str(idx + 1)
                        width = self.f.strlen(str(value)[:self.f.settings['line_length']])
                        if width > max_line_w:
                            max_line_w = width
                    if large_list:
                        line_col = max_line_w + 6
                    elif max_line_w:
                        line_col = max_line_w + 2

                xs_max_line_w = 0
                if xs_line_id and isinstance(trainlist, list):
                    for row in trainlist:
                        if isinstance(row, list) and len(row) > 1:
                            width = self.f.strlen(str(row[1])[:self.f.settings['line_length']])
                            if width > xs_max_line_w:
                                xs_max_line_w = width

                max_rows = 5 if mini else 4
                for x, row in enumerate(trainlist):
                    if x >= max_rows:
                        continue

                    is_clock_row = len(row) > 4 and row[4] == self.f.CLOCK_ROW_MARK
                    is_msg_row = len(row) > 4 and row[4] == self.f.MSG_ROW_MARK
                    if is_clock_row and int(record) != 1:
                        continue

                    real_line = row[1] if len(row) > 1 else ''
                    if not (is_clock_row or is_msg_row) and not int(self.f.settings.get('list_line_display', 1)):
                        row[1] = str(x + 1)

                    row[2] = row[2].split('(')[0].split(' via')[0]
                    strip_dest = self.f.settings.get('strip_dest', [])
                    if isinstance(strip_dest, list):
                        for value in strip_dest:
                            if value:
                                row[2] = row[2].replace(value, '').strip()

                    if self.f.strlen(row[2]) > 82 and self.f.display_width == 128:
                        for source, replacement in self.dicts.replace_list_destinations:
                            row[2] = row[2].replace(source, replacement)
                        try:
                            row[2] = self.f.station_names_dict[row[2]]
                        except Exception:
                            pass

                    time_text = str(row[3])
                    is_countdown = time_text.strip().isdigit()
                    if int(self.f.settings.get('clocktime', 0)) != 1 and not (is_clock_row or is_msg_row) and is_countdown:
                        time_text += self.f.settings['mins']

                    line = str(row[1])[:self.f.settings['line_length']]
                    dest = str(row[2])
                    full_dest_w = self.f.strlen(dest)
                    line_col_w = 0

                    if self.f.rotated or self.f.physical_display_width <= 64:
                        width = self.f.display_width if self.f.rotated else self.f.physical_display_width
                        max_px = width - self.f.strlen(time_text)
                        if not self.f.rotated and xs_line_id and not (is_clock_row or is_msg_row):
                            max_px -= xs_max_line_w + 2
                    elif large_list:
                        max_px = self.f.display_width - self.f.strlen(time_text) - line_col
                    elif half:
                        if is_clock_row:
                            max_px = self.f.display_width
                        elif is_msg_row:
                            max_px = col_w - (col_margin * 2) - self.f.strlen(time_text)
                        else:
                            max_px = col_w - (col_margin * 2) - self.f.strlen(time_text) - line_col - 1
                    else:
                        line_col_w = 0 if (is_clock_row or is_msg_row) else self.f.settings['line_length'] * (4 if mini else 6)
                        max_px = self.f.display_width - self.f.strlen(time_text) - line_col_w - 2

                    max_px = max(0, max_px)
                    if not (dest_scroll and full_dest_w > max_px):
                        dest = self.f.abbreviate_dest(dest, max_px)
                        while dest and self.f.strlen(dest) > max_px:
                            dest = dest[:-1]

                    multiple_offset = (int(record) - 1) * col_w if half else 0
                    if self.f.rotated:
                        time_x = max(0, self.f.display_width - self.f.strlen(time_text))
                    elif self.f.physical_display_width <= 64:
                        time_x = max(0, self.f.physical_display_width - self.f.strlen(time_text))
                    elif half:
                        time_x = max(multiple_offset, multiple_offset + col_w - col_margin - self.f.strlen(time_text))
                    else:
                        time_x = max(0, self.f.display_width - self.f.strlen(time_text))

                    night_row = not (is_clock_row or is_msg_row) and night_enabled and self.f.is_night_bus_line(real_line)
                    min_color = 'red' if night_row else ('white' if self.f.settings.get('listcolor_time', 0) or self.f.rotated else 'yellow')
                    lin_color = 'red' if night_row else ('yellow' if not self.f.settings['listcolor'] else 'white')
                    clock_color = self.f.settings.get('clock_row_color', 'white')

                    if self.f.rotated or self.f.physical_display_width <= 64:
                        dest_x = 0
                        if not self.f.rotated and xs_line_id and not (is_clock_row or is_msg_row):
                            dest_x = xs_max_line_w + 2
                        else:
                            line = ''
                    elif large_list:
                        dest_x = multiple_offset + line_col
                    elif half:
                        dest_x = multiple_offset + col_margin + (line_col if not (is_clock_row or is_msg_row) else 0)
                    else:
                        dest_x = line_col_w

                    if not self.f.settings['line_length']:
                        line = ''
                        if half and not (is_clock_row or is_msg_row):
                            dest_x = multiple_offset + col_margin
                        elif not half:
                            dest_x = 0

                    if is_clock_row:
                        clock_align = self.f.settings.get('clock_row_align', 'left')
                        clock_pad = max(0, self.f.display_width - self.f.strlen(dest))
                        if clock_align == 'center':
                            clock_pad //= 2
                        elif clock_align == 'left':
                            clock_pad = 0
                        dest_x = clock_pad
                        line = ''
                    elif is_msg_row:
                        line = ''

                    if large_list:
                        part = 100 + x
                        self.f.renderstring(time_text, part, 0, 0, 0, sys_msg=min_color, start_x=time_x)
                        self.f.renderstring(dest, part, 0, 0, 0, sys_msg=(clock_color if is_clock_row else False), start_x=dest_x)
                        if show_line and line and not (is_clock_row or is_msg_row):
                            self.f.renderstring(line, part, 0, 0, 0, sys_msg=lin_color, start_x=multiple_offset)
                        continue

                    use_tg = dest_scroll and not self.f.rotated and self.f.physical_display_width > 64 and full_dest_w > max_px
                    if use_tg:
                        row_step = 6 if mini else 8
                        overflow = full_dest_w - max_px
                        self.f.destination_bitmaps[x].fill(0)
                        self.f.renderstring(dest, 100 + x, 0, 0, 0, mini=mini, target_bmp=self.f.destination_bitmaps[x], target_offs=0)
                        self.f.destination_groups[x].x = line_col_w
                        self.f.destination_groups[x].y = extrarow + x * row_step
                        self.f.destination_groups[x].hidden = False
                        self.f.destination_scroll_state[x] = {
                            'overflow': overflow,
                            'pos': 0,
                            'pause_end': now + x * 0.8 + 2.0,
                            'start_x': line_col_w,
                        }
                        self.f.renderstring(time_text, 100 + x, 0, 0, 0, mini=mini, sys_msg=min_color, target_bmp=self.f.overlay_bitmap, start_x=time_x)
                        if show_line and line and not (is_clock_row or is_msg_row):
                            self.f.renderstring(line, 100 + x, 0, 0, 0, mini=mini, sys_msg=lin_color, target_bmp=self.f.overlay_bitmap, start_x=multiple_offset)
                        self.f.overlay_group.y = extrarow
                        self.f.overlay_group.hidden = False
                    else:
                        self.f.renderstring(time_text, 100 + x, 0, 0, 0, mini=mini, sys_msg=min_color, start_x=time_x)
                        self.f.renderstring(dest, 100 + x, 0, 0, 0, mini=mini, sys_msg=(clock_color if is_clock_row else False), start_x=dest_x)
                        if show_line and line and not (is_clock_row or is_msg_row):
                            line_x = multiple_offset + col_margin if half else multiple_offset
                            self.f.renderstring(line, 100 + x, 0, 0, 0, mini=mini, sys_msg=lin_color, start_x=line_x)

        except Exception as exc:
            print('ERROR ', exc)

        return time.monotonic()
