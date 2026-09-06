import time


class SlListSkin:
    def __init__(self, services):
        self.f = services
        self.v = services.varinit
        self.dicts = services.dicts

    def render(self, prepared_data):
        # SL List physically renders up to four rows; the user may request fewer.
        mini = self.v.settings["mini"]
        half = False

        #### debug
        #mini = True
        if self.v.rotated:
            mini = True
            half = False
        elif self.v.display.width <= 64:
            mini = True
            half = False
        elif self.v.settings["multiple"]: 
            half = True
            mini = True
        if self.v.settings["long"] == -1 and not self.v.rotated: 
            mini = True
            half = True
     


        if self.v.if_long > 128: self.f.version_delay(slowdown=1)
        large_list = not mini and not half and not self.v.rotated and int(self.v.settings.get("large_list", 0))
        xs_line_id = self.v.display.width <= 64 and not self.v.rotated and int(self.v.settings.get("xs_line_id", 0))
        self.v.currentfont = 1
        if mini: self.v.currentfont = 2
        elif large_list: self.v.currentfont = 0
        extrarow = 1 if mini else 0
        self.v.tg1.y, self.v.tg2.y, self.v.tg3.y = extrarow + 0-32, extrarow + 16-32, extrarow + 0

        _dest_scroll = int(self.v.settings.get("dest_scroll", 0))
        _now = time.monotonic()
        self.f.cls(self.f.topbottom)
        # Hide dest TileGrids and overlay; will be shown per-row if dest_scroll active
        try:
            for _dtg in self.v.dest_tgs: _dtg.hidden = True
            self.v.overlay_tg.hidden = True
            self.v.overlay_bmp.fill(0)
            self.v.dest_scroll_state = {}
        except: pass


        # trainlist = reformat_data(get_departure())
        ### DEBUG
    
        _r = 1
        try:
            if self.v.settings["multiple"]:
                if self.v.settings["long"] == 0: _r = 2
                if self.v.settings["long"] == 1: _r = 3
            else: _r = 1
        except: pass
    
        # Copy prepared records because the List drawing path mutates row strings
        # (abbreviations, countdown padding, etc.). Controller-owned snapshots must
        # remain reusable for the full build transaction.
        _prepared_copy = {}
        if isinstance(prepared_data, dict):
            for _key, _value in prepared_data.items():
                if isinstance(_value, list):
                    _prepared_copy[_key] = [list(_row) if isinstance(_row, list) else _row for _row in _value]
                else:
                    _prepared_copy[_key] = _value
        self.v.traindata = _prepared_copy

        try:
    
            if self.v.settings["long"] == -1: num = 1
            if self.v.settings["long"] == 0: num = 2
            if self.v.settings["long"] == 1: num = 3

            #num=self.v.no_of_screens_flag
        
            for record in self.v.traindata:
                print(record)
                trainlist = self.v.traindata[record]
                if isinstance(trainlist, list):
                    trainlist = [row[:] for row in trainlist if isinstance(row, list)]

                # Determine night/day composition from the original transit line
                # IDs before departure-order mode can replace visible line labels
                # with 1/2/3/4. This result must stay identical for every row.
                _night_mode = int(self.v.settings.get("night_bus_highlight", 0))
                _visible_departures = [
                    r for r in trainlist[:min(4, max(1, int(self.v.settings.get("maxdest", 4))))]
                    if isinstance(r, list)
                    and len(r) > 4
                    and r[4] not in (self.f.CLOCK_ROW_MARK, self.f.MSG_ROW_MARK)
                ]
                _has_night = False
                _has_day = False
                for _rnb in _visible_departures:
                    if self.f._is_night_bus_line(_rnb[1]):
                        _has_night = True
                    else:
                        _has_day = True

                # Off = never; On = whenever a night bus is present;
                # Mixed Traffic = only when night and day services coexist.
                _night_enabled = (
                    _night_mode == 2
                    or (_night_mode == 1 and _has_night and _has_day)
                )

                if int(record) > _r: continue
                if not half and "str" in str(type(trainlist)): 
                    self.f.sysprint("".join(trainlist[:30]), 100)
                    if self.dicts.language[self.v.settings["language"]]["display"]["no_more_departures"] in trainlist: return time.monotonic()
                    try:
                        _update_delay = float(self.v.updatedelay)
                    except (TypeError, ValueError):
                        _update_delay = 20.0
                    return time.monotonic() - _update_delay + 2
                elif "str" in str(type(trainlist)): 
                    print(trainlist)
                    #self.f.sysprint("".join(trainlist[:30]), 100)
                    trainlist = [["","",trainlist[:40],"",self.f.MSG_ROW_MARK]]
                        #continue
                    #if self.dicts.language[self.v.settings["language"]]["display"]["no_more_departures"] in trainlist: 
                    #    return time.monotonic()
                    #if not half: return time.monotonic() - self.v.updatedelay + 2
        
                if large_list and isinstance(trainlist, list):
                    _max_lw = 0
                    for _a in trainlist:
                        if isinstance(_a, list) and len(_a) > 1:
                            _w = self.f.strlen(_a[1][:self.v.settings["line_length"]])
                            if _w > _max_lw: _max_lw = _w
                    line_col = _max_lw + 6
                else:
                    line_col = 0

                _xs_max_lw = 0
                if xs_line_id and isinstance(trainlist, list):
                    for _a in trainlist:
                        if isinstance(_a, list) and len(_a) > 1:
                            _w = self.f.strlen(_a[1][:self.v.settings["line_length"]])
                            if _w > _xs_max_lw: _xs_max_lw = _w

                for x, all in enumerate(trainlist):

                    is_clock_row = len(all) > 4 and all[4] == self.f.CLOCK_ROW_MARK
                    is_msg_row = len(all) > 4 and all[4] == self.f.MSG_ROW_MARK

                    # Preserve the actual transit line for classification and
                    # highlighting even when the visible label is departure order.
                    _real_line = all[1] if len(all) > 1 else ""

                    # Shared List/DLR line-label mode. SL List defaults to actual
                    # line numbers, but can instead show visible row numbers 1..4.
                    if not (is_clock_row or is_msg_row) and not int(self.v.settings.get("list_line_display", 1)):
                        all[1] = str(x + 1)
                    all[2] = all[2].split('(')[0].split(" via")[0]#.lower()
                    _strip_dest = self.v.settings.get("strip_dest", [])
                    if isinstance(_strip_dest, list):
                        for _sd in _strip_dest:
                            if _sd: all[2] = all[2].replace(_sd, "").strip()
                    if self.f.strlen(all[2]) > 82 and self.v.if_long == 128:
                        for items in self.dicts.replace_list_destinations:
                            all[2] = all[2].replace(items[0], items[1])
                        try: all[2] = self.f.station_names_dict[all[2]]
                        except: pass

                    mins_cut = 23 - len(self.v.settings["mins"]) - (int(self.v.settings["line_length"]))

                    if len(all[3]) > 1:
                           mins_cut -= 1

                    if int(self.v.settings.get("clocktime", 0)) != 1 and not is_msg_row:
                        _mins_ref_w = self.f.strlen("00")
                        if self.f.strlen(all[3]) < _mins_ref_w:
                            all[3] = (_mins_ref_w - self.f.strlen(all[3])) * "(" + all[3]

                    is_countdown = str(all[3]).replace("(", "").strip().isdigit()
                    if_not_clocktime = (
                        self.v.settings["mins"]
                        if all[3] and int(self.v.settings.get("clocktime", 0)) != 1 and not (is_clock_row or is_msg_row) and is_countdown
                        else ""
                    )

                    all[3] += if_not_clocktime

                    _full_dest_w = 0
                    _max_px = 0
                    _line_col_w = 0
                    if self.v.rotated or self.v.display.width <= 64:
                        _w = self.v.if_long if self.v.rotated else self.v.display.width
                        _max_px = _w - self.f.strlen(all[3])
                        if not self.v.rotated and xs_line_id and not (is_clock_row or is_msg_row):
                            _max_px -= _xs_max_lw + 2
                        all[2] = self.f.abbreviate_dest(all[2], _max_px)
                        while len(all[2]) > 0 and self.f.strlen(all[2]) > _max_px:
                            all[2] = all[2][:-1]
                    elif large_list:
                        _max_px = self.v.if_long - self.f.strlen(all[3]) - line_col
                        _font = self.f.fonts[self.v.currentfont]
                        all[2] = self.f.abbreviate_dest(all[2], _max_px)
                        while len(all[2]) > 0 and sum(_font.get(c, _font['_'])[0] for c in all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                    elif not half:
                        _line_col_w = 0 if (is_clock_row or is_msg_row) else self.f.strlen(self.v.settings["line_length"] * ("((((" if mini else "(((((("))
                        _max_px = self.v.if_long - self.f.strlen(all[3]) - _line_col_w - 2
                        _full_dest_w = self.f.strlen(all[2])
                        if not (_dest_scroll and _full_dest_w > max(0, _max_px)):
                            all[2] = self.f.abbreviate_dest(all[2], _max_px)
                            while len(all[2]) > 0 and self.f.strlen(all[2]) > max(0, _max_px):
                                all[2] = all[2][:-1]
                    if half:
                        if is_clock_row:
                            _max_px = 64 - self.f.strlen(all[3]) - 1
                            while len(all[2]) > 0 and self.f.strlen(all[2]) > max(0, _max_px):
                                all[2] = all[2][:-1]
                        elif is_msg_row:
                            _max_px = 64 - self.f.strlen(all[3]) - 1
                            while len(all[2]) > 0 and self.f.strlen(all[2]) > max(0, _max_px):
                                all[2] = all[2][:-1]
                        else:
                            all[2] = all[2][:15 - len(self.v.settings["mins"])]
                            if int(self.v.settings.get("clocktime", 0)) == 1:
                                all[2] = all[2][:11]
                    mins = all[2]
                    if int(self.v.settings.get("clocktime", 0)) != 1: all[1] = "1(1(" if all[1] == "11" else all[1]

                    if mini: all[2] = mins
                    all[1] = all[1][:self.v.settings["line_length"]]
                
                    line = all[1]
                    dest = all[2]
                
                    if self.v.rotated:
                        offs = self.v.if_long - self.f.strlen(all[3])
                    elif self.v.display.width <= 64:
                        offs = self.v.display.width - self.f.strlen(all[3])
                    else:
                        offs = self.v.if_long - self.f.strlen(all[3])

                    # SL List: one pixel is enough to keep "Nu" clear of the edge.
                    if str(all[3]).replace("(", "").strip().lower() == self.f._now_text().lower():
                        offs = max(0, offs - 1)
                    if half: 
                        all[3] = all[3].replace(" " + if_not_clocktime,"")
                        offs = 64 - self.f.strlen(all[3])

                    

                    minsleft = offs*"(" + all[3]
                
                    inv = 0

                    if half: minsleft = minsleft.replace(" " + if_not_clocktime, "")
                
                    if half: multiple_offset = int(num - 1) * (" " * 64)
                    
                
                    else: multiple_offset = ""
        
                    _night_row = (not (is_clock_row or is_msg_row)
                                  and _night_enabled
                                  and self.f._is_night_bus_line(_real_line))
                    min_color = "red" if _night_row else ("white" if self.v.settings.get("listcolor_time", 0) or self.v.rotated else "yellow")
                    lin_color = "red" if _night_row else ("yellow" if not self.v.settings["listcolor"] else "white")
                    clock_color = self.v.settings.get("clock_row_color", "white")
                    if self.v.rotated or self.v.display.width <= 64:
                        added_space = ""
                        line = ""
                        if not self.v.rotated and xs_line_id:
                            line = all[1][:self.v.settings["line_length"]]
                            added_space = (_xs_max_lw + 2) * "("
                    elif mini:
                        added_space = self.v.settings["line_length"] * "(((("
                        if half: added_space = ""
                    else: added_space = self.v.settings["line_length"] * "(((((("
                    if not self.v.settings["line_length"]:
                        added_space = ""
                        line = ""

                    if is_clock_row:
                        _clock_align = self.v.settings.get("clock_row_align", "left")
                        _clock_avail = self.v.display.width if self.v.display.width <= 64 else self.v.if_long
                        _clock_pad = max(0, _clock_avail - self.f.strlen(dest))
                        if _clock_align == "center": _clock_pad = _clock_pad // 2
                        elif _clock_align == "left": _clock_pad = 0
                        added_space = _clock_pad * "("
                        line = ""

                    elif is_msg_row:
                        added_space = ""
                        line = ""

                    if large_list:
                        _lpart = 100 + x
                        _dest_pad = line_col * "("
                        self.f.renderstring(multiple_offset + minsleft, _lpart, 0, 0, inv, sys_msg=min_color)
                        self.f.renderstring(multiple_offset + _dest_pad + dest, _lpart, 0, 0, inv, sys_msg=(clock_color if is_clock_row else False))
                        if not half and not self.v.rotated: self.f.renderstring(multiple_offset + line, _lpart, 0, 0, inv, sys_msg=lin_color)
                        if x > 4: continue
                    else:
                        _use_tg = (_dest_scroll and not half and not self.v.rotated
                                   and self.v.display.width > 64
                                   and _full_dest_w > max(0, _max_px))
                        if _use_tg:
                            # TileGrid smooth scroll: dest in dest_bmp, line+mins in overlay_bmp
                            _row_step = 6 if mini else 8
                            _overflow = _full_dest_w - _max_px
                            self.v.dest_bmps[x].fill(0)
                            self.f.renderstring(dest, 100+x, 0, 0, inv, mini=mini,
                                         target_bmp=self.v.dest_bmps[x], target_offs=0)
                            self.v.dest_tgs[x].x = _line_col_w
                            self.v.dest_tgs[x].y = extrarow + x * _row_step
                            self.v.dest_tgs[x].hidden = False
                            self.v.dest_scroll_state[x] = {
                                "overflow": _overflow, "pos": 0,
                                "pause_end": _now + x * 0.8 + 2.0, "start_x": _line_col_w
                            }
                            self.f.renderstring(multiple_offset + minsleft, 100+x, 0, 0, inv, mini=mini,
                                         sys_msg=min_color, target_bmp=self.v.overlay_bmp)
                            if not half and not self.v.rotated and (self.v.display.width > 64 or xs_line_id):
                                self.f.renderstring(multiple_offset + line, 100+x, 0, 0, inv, mini=mini,
                                             sys_msg=lin_color, target_bmp=self.v.overlay_bmp)
                            self.v.overlay_tg.y = extrarow
                            self.v.overlay_tg.hidden = False
                        else:
                            self.f.renderstring(multiple_offset + minsleft, 100+x, 0, 0, inv, mini=mini, sys_msg=min_color)
                            self.f.renderstring(multiple_offset + added_space + dest, 100+x, 0, 0, inv, mini=mini, sys_msg=(clock_color if is_clock_row else False))
                            if not half and not self.v.rotated and (self.v.display.width > 64 or xs_line_id):
                                self.f.renderstring(multiple_offset + line, 100+x, 0, 0, inv, mini=mini, sys_msg=lin_color)
                        if x > self.v.if_tall // 8 - 1: continue
                num -= 1
            
        except Exception as e: print("ERROR ", e)
        return time.monotonic()
