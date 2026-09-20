import time

from skin_engine.base import BaseRenderer
from .line_badges import BLACK, WHITE, resolve_line_badge


class SlModernRenderer(BaseRenderer):
    renderer_id = 'sl_modern'
    display_name = 'SL Modern'
    implemented = True

    ROW_Y = (0, 16, 24)
    BADGE_WIDTH = 13
    BADGE_HEIGHT = 7
    BADGE_GAP = 2
    TICK_STEP_SECONDS = 0.035

    def __init__(self):
        super().__init__()
        self.built = False
        self.last_departures = None
        self.ticker_text = ''
        self.ticker_width = 0
        self.ticker_x = 0
        self.ticker_last_step = 0
        self.ticker_active = False
        self.ticker_y = self.ROW_Y[2]
        self.ticker_height = 7

    @staticmethod
    def _services(context):
        services = getattr(context, 'services', None)
        if services is None and isinstance(context, dict):
            services = context.get('services')
        if services is None:
            raise ValueError('SL_Modern renderer requires context.services')
        return services

    @staticmethod
    def _clean_destination(value):
        return str(value).split('(')[0].split(' via')[0].strip()

    @staticmethod
    def _copy_departures(departures):
        if not isinstance(departures, list):
            return departures
        return [list(row) if isinstance(row, list) else row for row in departures]

    def enter(self, context):
        super().enter(context)
        self.built = False
        self.last_departures = None
        self._reset_ticker()

    def prepare_data(self, context, allow_messages=True):
        services = self._services(context)
        services.nightcheck()
        return services.get_departure()

    def _reset_ticker(self):
        self.ticker_text = ''
        self.ticker_width = 0
        self.ticker_x = 0
        self.ticker_last_step = 0
        self.ticker_active = False
        self.ticker_y = self.ROW_Y[2]
        self.ticker_height = 7

    @staticmethod
    def _font_width(services, text, font_index):
        font = services.fonts[font_index]
        total = 0
        for char in str(text).lower():
            if char not in font:
                char = '_'
            try:
                total += int(font[char][0])
            except Exception:
                pass
        return total

    @staticmethod
    def _fill_rect(bitmap, x, y, width, height, colour):
        max_x = x + width
        max_y = y + height
        for px in range(x, max_x):
            for py in range(y, max_y):
                try:
                    bitmap[px, py] = colour
                except Exception:
                    pass

    @staticmethod
    def _draw_mini_transparent(services, text, target, x, y, colour=2):
        font = services.fonts[2]
        cursor = int(x)
        for raw_char in str(text).lower():
            char = raw_char if raw_char in font else '_'
            try:
                width = int(font[char][0])
            except Exception:
                continue
            for fx in range(width):
                inverted = width - fx
                for fy in range(int(font['fontheight'])):
                    try:
                        row = font[char][fy + 1]
                        if isinstance(row, int):
                            pixel = (row >> inverted) & 1
                        else:
                            pixel = int(row[fx]) != 0
                        if pixel:
                            target[cursor + fx, y + fy] = colour
                    except Exception:
                        pass
            cursor += width
        return cursor

    @staticmethod
    def _draw_small_transparent(services, text, target, x, y, colour=2):
        font = services.fonts[1]
        cursor = int(x)
        display_width = int(services.display_width)
        for raw_char in str(text):
            char = raw_char if raw_char in font else '_'
            try:
                width = int(font[char][0])
            except Exception:
                continue
            for fx in range(width):
                screen_x = cursor + fx
                if screen_x < 0 or screen_x >= display_width:
                    continue
                inverted = width - fx
                for fy in range(int(font['fontheight'])):
                    try:
                        row = font[char][fy + 1]
                        if isinstance(row, int):
                            pixel = (row >> inverted) & 1
                        else:
                            pixel = int(row[fx]) != 0
                        if pixel:
                            target[screen_x, y + fy] = colour
                    except Exception:
                        pass
            cursor += width
        return cursor

    @staticmethod
    def _fixed_palette_index(colour):
        if colour == BLACK:
            return 0
        if colour == WHITE:
            return 2
        return None

    def _draw_badge(self, services, line, metadata, target, row_y, row_index):
        x = 0
        y = row_y
        dynamic_index = 3 + int(row_index)
        style = resolve_line_badge(
            line,
            metadata,
            is_night_bus=services.is_night_bus_line(line),
        )

        background = style.get('background', BLACK)
        foreground = style.get('foreground', WHITE)

        bg_index = self._fixed_palette_index(background)
        fg_index = self._fixed_palette_index(foreground)

        # Each visible row owns one dynamic palette slot. Current badge rules
        # never require both a custom background and custom foreground at once.
        custom_colour = None
        if bg_index is None:
            custom_colour = background
            bg_index = dynamic_index
        elif fg_index is None:
            custom_colour = foreground
            fg_index = dynamic_index
        if custom_colour is not None:
            services.set_palette_color(dynamic_index, custom_colour)

        shape = style.get('shape', 'box')
        if style.get('box', True):
            self._fill_rect(target, x, y, self.BADGE_WIDTH, self.BADGE_HEIGHT, bg_index)
            if style.get('cut_corners'):
                for px, py in (
                    (x, y),
                    (x + self.BADGE_WIDTH - 1, y),
                    (x, y + self.BADGE_HEIGHT - 1),
                    (x + self.BADGE_WIDTH - 1, y + self.BADGE_HEIGHT - 1),
                ):
                    try:
                        target[px, py] = 0
                    except Exception:
                        pass

            if shape == 'flag':
                # Waxholmsbolaget-style swallowtail: carve a centred V-shaped
                # notch in from the right edge while keeping two full tails.
                centre_y = y + (self.BADGE_HEIGHT // 2)
                notch = (
                    (self.BADGE_WIDTH - 3, 0),
                    (self.BADGE_WIDTH - 2, 0),
                    (self.BADGE_WIDTH - 1, 0),
                    (self.BADGE_WIDTH - 2, -1),
                    (self.BADGE_WIDTH - 1, -1),
                    (self.BADGE_WIDTH - 2, 1),
                    (self.BADGE_WIDTH - 1, 1),
                    (self.BADGE_WIDTH - 1, -2),
                    (self.BADGE_WIDTH - 1, 2),
                )
                for rel_x, rel_y in notch:
                    try:
                        target[x + rel_x, centre_y + rel_y] = 0
                    except Exception:
                        pass

        label = str(line).strip()[:3]
        label_width = self._font_width(services, label, 2)
        if shape == 'flag':
            label_x = x + 1
        else:
            label_x = x + max(0, (self.BADGE_WIDTH - label_width) // 2)
        try:
            mini_height = int(services.fonts[2]['fontheight'])
        except Exception:
            mini_height = 5
        label_y = y + max(0, (self.BADGE_HEIGHT - mini_height) // 2)
        self._draw_mini_transparent(services, label, target, label_x, label_y, fg_index)

    def _format_value(self, services, value):
        value = str(value).strip()
        if value.lower() == services.now_text().lower():
            return services.now_text()
        if int(services.settings.get('clocktime', 0)) != 1 and value.isdigit():
            return value + str(services.settings.get('mins', ' min'))
        return value

    def _fit_destination(self, services, destination, max_width):
        """Fit a destination using existing DepartureBox abbreviation rules first."""
        text = str(destination).strip()
        if self._font_width(services, text, 1) <= max_width:
            return text

        # Preserve the existing user-configurable destination abbreviations.
        text = services.abbreviate_dest(text, max_width)
        if self._font_width(services, text, 1) <= max_width:
            return text

        # Then use the built-in exact station abbreviations from dicts.py.
        try:
            abbreviated = services.station_names_dict.get(text)
        except Exception:
            abbreviated = None
        if abbreviated:
            text = abbreviated
            if self._font_width(services, text, 1) <= max_width:
                return text

        # Finally apply the generic built-in replacements, but only while the
        # destination is still too wide. This mirrors the existing list logic
        # without shortening destinations that already fit.
        try:
            replacements = services.dicts.replace_list_destinations
        except Exception:
            replacements = ()
        for long, short in replacements:
            if self._font_width(services, text, 1) <= max_width:
                break
            if long in text:
                text = text.replace(long, short)

        # Pixel-safe final fallback for destinations with no known abbreviation.
        while text and self._font_width(services, text, 1) > max_width:
            text = text[:-1]
        return text.rstrip()

    def _draw_departure_row(self, services, row, target, row_y, row_index):
        if not isinstance(row, list) or len(row) < 4:
            return

        line = str(row[1]).strip()
        destination = self._clean_destination(row[2])
        value = self._format_value(services, row[3])
        metadata = row[5] if len(row) > 5 and isinstance(row[5], dict) else {}

        self._draw_badge(services, line, metadata, target, row_y, row_index)

        dest_x = self.BADGE_WIDTH + self.BADGE_GAP
        value_width = self._font_width(services, value, 1)
        value_x = max(dest_x, services.display_width - value_width)
        max_destination_width = max(0, value_x - dest_x - 2)

        destination = self._fit_destination(services, destination, max_destination_width)

        services.renderstring(
            destination,
            0,
            smallfont=True,
            target_bmp=target,
            target_offs=row_y,
            start_x=dest_x,
            sys_msg='white',
        )
        services.renderstring(
            value,
            0,
            smallfont=True,
            target_bmp=target,
            target_offs=row_y,
            start_x=value_x,
            sys_msg='white',
        )

    @staticmethod
    def _is_wide_layout(services):
        try:
            return int(services.display_width) == 128 and int(services.display_height) == 64
        except Exception:
            return False

    @staticmethod
    def _small_font_height(services):
        try:
            return max(1, int(services.fonts[1]['fontheight']))
        except Exception:
            return 7

    def _wide_layout(self, services):
        """Return the 128x64 (2X) vertical geometry.

        The second and third departures stay pinned to the bottom. One-pixel
        separator rules define the lower section, with a spare pixel of air
        around departure 2.
        """
        height = int(getattr(services, 'display_height', 32) or 32)
        font_height = self._small_font_height(services)
        dep3_y = max(0, height - font_height)
        lower_separator_y = max(0, dep3_y - 2)
        # The small font's visible pixels sit one row short of its nominal
        # font height, so move departure 2 down one pixel to make the visual
        # gap to the separator match departure 3 below it.
        dep2_y = max(0, lower_separator_y - font_height)
        upper_separator_y = max(0, dep2_y - 2)
        ticker_y = self.ROW_Y[0] + font_height
        return {
            'dep1_y': self.ROW_Y[0],
            'dep2_y': dep2_y,
            'dep3_y': dep3_y,
            'upper_separator_y': upper_separator_y,
            'lower_separator_y': lower_separator_y,
            'middle_ticker_y': ticker_y,
            'ticker_height': font_height,
        }

    @staticmethod
    def _draw_separator(services, y):
        width = int(services.display_width)
        for x in range(width):
            try:
                services.topbottom[x, int(y)] = 2
            except Exception:
                pass

    def _ticker_message(self, services):
        mode = services.scroll_content_mode()
        if mode == 'custom':
            return str(services.custom_scroll_message()).strip()
        if mode != 'disruptions':
            return ''

        try:
            operator = services.settings['stations']['1']['operator']
        except Exception:
            operator = ''
        if operator not in ('sl', 'vt'):
            return ''
        try:
            return str(services.get_deviations()).strip()
        except Exception as exc:
            print('SL_Modern disruption ticker error:', repr(exc))
            return ''

    def _clear_ticker_row(self, services):
        self._fill_rect(
            services.topbottom,
            0,
            self.ticker_y,
            services.display_width,
            self.ticker_height,
            0,
        )

    def _draw_ticker_frame(self, services):
        self._clear_ticker_row(services)
        if not self.ticker_active:
            return
        self._draw_small_transparent(
            services,
            self.ticker_text,
            services.topbottom,
            self.ticker_x,
            self.ticker_y,
            2,
        )

    def _build_ticker(self, services, message, ticker_y, ticker_height=None):
        self.ticker_y = int(ticker_y)
        self.ticker_height = int(ticker_height or self._small_font_height(services))
        self.ticker_text = str(message)
        self.ticker_width = self._font_width(services, self.ticker_text, 1)
        self.ticker_x = services.display_width
        self.ticker_last_step = time.monotonic()
        self.ticker_active = bool(self.ticker_text and self.ticker_width > 0)
        services.middle_group.x = services.display_width
        services.middle_group.y = 32
        self._draw_ticker_frame(services)

    def build(self, departures, context):
        services = self._services(context)
        self.last_departures = self._copy_departures(departures)

        services.cls(services.top)
        services.cls(services.bottom)
        services.cls(services.topbottom)

        # SL_Modern renders its board in topbottom; 2X uses a dedicated 128x64 profile.
        services.top_group.x = 0
        services.top_group.y = 32
        services.middle_group.x = 0
        services.middle_group.y = 32
        services.bottom_group.x = 0
        services.bottom_group.y = 0

        services.set_current_font(1)
        rows = services.reformat_data(departures)
        if not isinstance(rows, list) or not rows:
            message = str(rows).strip() if rows is not None else ''
            if message:
                services.renderstring(
                    message,
                    0,
                    smallfont=True,
                    target_bmp=services.topbottom,
                    target_offs=0,
                    start_x=0,
                    sys_msg='white',
                )
            self._reset_ticker()
            self.built = True
            return True

        visible = [
            list(row) for row in rows[:3]
            if isinstance(row, list) and len(row) >= 4
        ]

        ticker_message = self._ticker_message(services)
        try:
            ticker_position = int(services.settings.get('custom_scroll_position', 0))
        except (TypeError, ValueError):
            ticker_position = 0

        if self._is_wide_layout(services):
            layout = self._wide_layout(services)

            if len(visible) > 0:
                self._draw_departure_row(
                    services, visible[0], services.topbottom, layout['dep1_y'], 0
                )

            # The 2X layout always reserves a structured lower section.
            self._draw_separator(services, layout['upper_separator_y'])
            self._draw_separator(services, layout['lower_separator_y'])

            if len(visible) > 1:
                self._draw_departure_row(
                    services, visible[1], services.topbottom, layout['dep2_y'], 1
                )

            if ticker_message and ticker_position == 2:
                # 2X middle placement: the ticker occupies the otherwise free
                # band under departure 1. Departures 2 and 3 remain pinned to
                # the bottom in their normal positions.
                if len(visible) > 2:
                    self._draw_departure_row(
                        services, visible[2], services.topbottom, layout['dep3_y'], 2
                    )
                self._build_ticker(
                    services,
                    ticker_message,
                    layout['middle_ticker_y'],
                    layout['ticker_height'],
                )
            elif ticker_message:
                # Bottom-row placement remains the same conceptually: the
                # third departure disappears and the ticker owns its row.
                self._build_ticker(
                    services,
                    ticker_message,
                    layout['dep3_y'],
                    layout['ticker_height'],
                )
            else:
                self._reset_ticker()
                services.middle_group.x = 0
                services.middle_group.y = 32
                if len(visible) > 2:
                    self._draw_departure_row(
                        services, visible[2], services.topbottom, layout['dep3_y'], 2
                    )
        else:
            # Compact 128x32 behaviour remains unchanged.
            if len(visible) > 0:
                self._draw_departure_row(
                    services, visible[0], services.topbottom, self.ROW_Y[0], 0
                )

            if ticker_message and ticker_position == 2:
                # Middle-spacer placement:
                # row 1 = departure 1, row 2 = ticker, row 3 = blank,
                # row 4 = departure 2. Departure 3 is hidden.
                if len(visible) > 1:
                    self._draw_departure_row(
                        services, visible[1], services.topbottom, self.ROW_Y[2], 1
                    )
                self._build_ticker(services, ticker_message, 8)
            else:
                if len(visible) > 1:
                    self._draw_departure_row(
                        services, visible[1], services.topbottom, self.ROW_Y[1], 1
                    )

                if ticker_message:
                    # Bottom-row placement: departure 3 is replaced completely.
                    self._build_ticker(services, ticker_message, self.ROW_Y[2])
                else:
                    self._reset_ticker()
                    services.middle_group.x = 0
                    services.middle_group.y = 32
                    if len(visible) > 2:
                        self._draw_departure_row(
                            services, visible[2], services.topbottom, self.ROW_Y[2], 2
                        )

        self.built = True
        return True

    def tick(self, now, context):
        if not self.built:
            return False
        services = self._services(context)

        mode = services.scroll_content_mode()
        if mode == 'none' and self.ticker_active:
            return 'rebuild'
        if mode == 'custom':
            current = str(services.custom_scroll_message()).strip()
            if current != self.ticker_text:
                return 'rebuild'

        changed = False
        if self.ticker_active and now >= self.ticker_last_step + self.TICK_STEP_SECONDS:
            self.ticker_last_step = now
            self.ticker_x -= 1
            if self.ticker_x < -self.ticker_width:
                self.ticker_x = services.display_width
            self._draw_ticker_frame(services)
            changed = True

        try:
            update_delay = float(services.updatedelay)
        except (TypeError, ValueError):
            update_delay = 20.0
        if now > float(services.shared.get('scroll_timer', 0) or 0) + update_delay:
            return 'rebuild'
        if changed:
            return 'refresh'
        return True

    def exit(self, context):
        self.built = False
        try:
            services = self._services(context)
            services.top_group.x = 0
            services.top_group.y = 0
            services.middle_group.x = services.display_width
            services.middle_group.y = 16
            services.bottom_group.x = 0
            services.bottom_group.y = 32
        except Exception:
            pass
        self._reset_ticker()
        self.last_departures = None
        super().exit(context)


Renderer = SlModernRenderer
