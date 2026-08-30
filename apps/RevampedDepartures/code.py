import os
from __main__ import *
stop_wifi = True
from functions import *
from check_button import *
varinit.last_button_state = last_button_state
varinit.button = button
varinit.gbutton = gbutton
varinit.debounce_delay = debounce_delay

def check_button():
    b = check_if_button_pressed()
    if b == 1:
        handle_button_event(1)
    elif b == 2:
        handle_button_event(2)

delay = version_delay()
#microcontroller.cpu.frequency = 240000000
from functions import refresh
disp_init()
if varinit.display.width <= 64 or varinit.display.height > 32:
    varinit.settings["listmode"] = 1
if int(varinit.settings.get("listmode", 0)) == 2:
    dlr_mode()
elif int(varinit.settings.get("listmode", 0)) == 1:
    list_mode()
else:
    scroll_mode()

# Renderer ownership lives in this main loop, not in the HTTP callback.
# This prevents a web request from changing TileGrid state halfway through a draw.
_active_view_mode = int(varinit.settings.get("listmode", 0))
varinit.shared["force_view_rebuild"] = 0
#################################
try:
    if wifi.radio.connected == True:
        with open("/settings.txt") as f:
            data = json.loads(f.read())
            for line in data:
                if line == "ssid": varinit.settings["ssid"] = data["ssid"]
                if line == "password": varinit.settings["password"] = data["password"]
except Exception as e:
    print("Error loading underlying WIFI settings:", e)
#################################
while not varinit.exit:
    while wifi.radio.connected == False and not varinit.exit:           # CHECK CONNECTION ###################
        try: wifi.radio.stop_ap()
        except: pass
        
        start_ap()
        stop_wifi = False
        if varinit.tg3.y == 32: functions.switch(force=True, wifi_screen=True)
        varinit.reset_timer = time.monotonic()
        while wifi.radio.connected == False and not varinit.exit:
            if time.monotonic() > varinit.reset_timer + varinit.network_delay:
                varinit.reset_timer = time.monotonic()
                wifiattempt(errmsg=False, _timeout=10, skipversion=True)
                update_screen()
            ampule.listen(socket)
    if varinit.settings["listmode"] and not varinit.tg3.y == 0: functions.switch(force=False, _cls=bottom)
    varinit.first_start = False
    if stop_wifi: wifi.radio.stop_ap()
    x = 1
    while wifi.radio.connected == True and not varinit.exit:            # MAINLOOP ###########################
        x = 1 - x
        if x: 
            ampule.listen(socket)
            check_button()

        _requested_mode = int(varinit.settings.get("listmode", 0))
        _rebuild_requested = int(varinit.shared.get("force_view_rebuild", 0))
        if _requested_mode != _active_view_mode or _rebuild_requested:
            _view_changed = (_requested_mode != _active_view_mode)
            _splash_rebuild = (_rebuild_requested == 2)
            varinit.shared["force_view_rebuild"] = 0

            # True View changes always get the existing ~2s loading splash:
            # MatrixBOX logo + station, then direction(s) on line two.
            # Ordinary filter/settings rebuilds remain immediate.
            if _view_changed or _splash_rebuild:
                view_switch_loading(2.0)

            rebuild_current_view()
            _active_view_mode = _requested_mode
            varinit.shared["scroll_timer"] = time.monotonic()
            continue

        if int(varinit.settings["listmode"]) == 2:
            # DLR owns a lightweight per-loop animation state machine for its
            # lower-half custom/disruption ticker. Do not let the normal timed
            # departure refresh overwrite the bitmap while that animation is active.
            dlr_animation_tick()
            if (not dlr_message_active()
                    and time.monotonic() > varinit.shared["scroll_timer"] + updatedelay):
                varinit.shared["scroll_timer"] = dlr_mode()
        elif int(varinit.settings["listmode"]) == 1 and time.monotonic() > varinit.shared["scroll_timer"] + updatedelay: varinit.shared["scroll_timer"] = list_mode()
        elif not int(varinit.settings["listmode"]) and varinit.display.width > 64: 
            varinit.tg2.x -= 1
            refresh(int(delay + varinit.settings["scroll"]) + 1 * (delay*2))
            if varinit.tg2.x < -varinit.scrollsum:
                scroll_mode()
            elif (not custom_scroll_available()
                  and time.monotonic() > varinit.shared["scroll_timer"] + updatedelay
                  and shared["loop_counter"] >= 0):
                scroll_mode()
        # Dest TileGrid smooth scroll (runs every main-loop iteration in listmode)
        if int(varinit.settings["listmode"]) == 1 and int(varinit.settings.get("dest_scroll", 0)):
            try:
                _nt = time.monotonic()
                _scrolled = False
                for _rx, _rs in varinit.dest_scroll_state.items():
                    _ov = _rs["overflow"]
                    if _ov <= 0: continue
                    if _nt < _rs.get("pause_end", 0): continue
                    _pos = _rs["pos"]
                    if _pos >= _ov:
                        # End of scroll: reset to start with pause
                        _rs["pos"] = 0
                        _rs["pause_end"] = _nt + 1.5
                        varinit.dest_tgs[_rx].x = _rs["start_x"]
                    else:
                        _rs["pos"] = _pos + 1
                        varinit.dest_tgs[_rx].x = _rs["start_x"] - _pos - 1
                    _scrolled = True
                if _scrolled: refresh()
            except: pass
        
