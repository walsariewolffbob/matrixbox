import os
import sys
import skin_engine.registry as _skin_registry

# The desktop simulator may restart this app without restarting the Python
# interpreter. Reconcile the skin registry with the current filesystem before
# any view is activated so installed/removed/updated skins are reflected.
try:
    if hasattr(_skin_registry, 'resync_skins'):
        _skin_registry.resync_skins(reload_modules=True)
    else:
        # Compatibility with a registry module that survived from an older app
        # run before resync_skins() existed.
        for _module_name in tuple(sys.modules.keys()):
            if _module_name.startswith('skins.'):
                try:
                    del sys.modules[_module_name]
                except Exception:
                    pass
        _skin_registry._RENDERERS.clear()
        _skin_registry._MANIFESTS.clear()
        _skin_registry._MODE_RENDERERS.clear()
        _skin_registry._REJECTED.clear()
        _skin_registry.discover_skins()
except Exception as _skin_sync_error:
    print('SKIN registry resync failed:', repr(_skin_sync_error))

import functions
from view_controller import controller
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

from functions import refresh
disp_init()



if varinit.display.width <= 64:
    _list_mode = functions.skin_mode('list')
    if _list_mode is not None:
        varinit.settings['listmode'] = _list_mode

_active_view_mode = int(varinit.settings.get('listmode', 0))
_classic_refresh_times = int(delay + varinit.settings['scroll']) + 1 * (delay * 2)
controller.activate_mode(
    _active_view_mode,
    functions,
    classic_refresh_times=_classic_refresh_times,
    splash=False,
    source='startup',
)
_active_view_mode = int(varinit.settings.get('listmode', _active_view_mode))
varinit.shared['force_view_rebuild'] = 0

try:
    if wifi.radio.connected == True:
        with open("/settings.txt") as f:
            data = json.loads(f.read())
            for line in data:
                if line == "ssid": varinit.settings["ssid"] = data["ssid"]
                if line == "password": varinit.settings["password"] = data["password"]
except Exception as e:
    print("Error loading underlying WIFI settings:", e)

while not varinit.exit:
    while wifi.radio.connected == False and not varinit.exit:           
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
    if not functions.active_skin_is_classic_ticker() and not varinit.tg3.y == 0: functions.switch(force=False, _cls=bottom)
    varinit.first_start = False
    if stop_wifi: wifi.radio.stop_ap()
    x = 1
    while wifi.radio.connected == True and not varinit.exit:            
        x = 1 - x
        if x: 
            ampule.listen(socket)
            check_button()

        _requested_mode = int(varinit.settings.get('listmode', 0))
        _rebuild_requested = int(varinit.shared.get('force_view_rebuild', 0))

        if _requested_mode != _active_view_mode or _rebuild_requested:
            _view_changed = (_requested_mode != _active_view_mode)
            _splash_rebuild = (_rebuild_requested == 2)
            varinit.shared['force_view_rebuild'] = 0

            _classic_refresh_times = int(delay + varinit.settings['scroll']) + 1 * (delay * 2)

            if _view_changed:
                controller.activate_mode(
                    _requested_mode,
                    functions,
                    classic_refresh_times=_classic_refresh_times,
                    splash=True,
                    source='view-change',
                )
                _active_view_mode = int(varinit.settings.get('listmode', _requested_mode))
            else:
                
                
                if _splash_rebuild:
                    view_switch_loading(2.0)
                controller.rebuild_active(functions, allow_messages=False)

            varinit.shared['scroll_timer'] = time.monotonic()
            continue

        
        controller.tick(time.monotonic())
        _active_view_mode = int(varinit.settings.get('listmode', _active_view_mode))
