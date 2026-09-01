from __main__ import wifi, pool
import varinit, createhtml, microcontroller, json, ipaddress
from varinit import *
import random

mac = [hex(i) for i in wifi.radio.mac_address]
id = "".join(mac)
#ap_name = "t-skylt" + id[-2:]; varinit.ap_name = ap_name
ap_name = "matrixbox-" + "".join(mac).replace("0x","")[:3] # mac-id för hotspot


def pwd_gen(): return id.replace("0x","")[:8]
def cls(__screen, _refresh=False):
    __screen.fill(0)
    if _refresh: refresh()
def reset():
    displayio.release_displays()
    microcontroller.reset()
def strlen(_string): 
    if isinstance(_string, str): _string = _string.lower()
    return sum(fonts[varinit.currentfont][c][0] for c in _string)

LOGO_CHAR = "Ⓜ"

def temperature_check():
    if round(microcontroller.cpu.temperature) > varinit.temperature_threshold: 
        print("Temp-warning: ", round(microcontroller.cpu.temperature))
        if not varinit.temperature_timer: varinit.temperature_timer = time.monotonic()
        elif time.monotonic() > varinit.temperature_timer + 60*2: 
            print("Temperature fail! Restarting...")
            import safemode
    else: varinit.temperature_timer = False

def ping_screen():
    while varinit.ping:
        start_time = time.monotonic()
        _data = fetch_data("data.t-skylt.se",90,"/get_departures?country=se&operator=sl&station=9001", )
        end_time = time.monotonic()
        varinit.ping_list.append(int(end_time - start_time))
        print("temp: ", str(round(microcontroller.cpu.temperature)))
        if len(varinit.ping_list) > 5: varinit.ping_list.pop(0)
        sysprint(str(varinit.ping_list), 0, color="red", shading=True, _refresh=True, ontop=True)
    return True

def ad_message():
    varinit.ad_timer = time.monotonic()
    data = fetch_data(host="data.t-skylt.se", port=89, args="/settings?ad")
    ad = json.loads(data)
    return str(ad[1]) if ad[0] else False

def handle_button_event(event):
    """Handle a classified MatrixBOX button event.

    1 = short press
    2 = long press

    The real hardware classifier lives in lib/check_button.py.  The desktop
    emulator injects the same event numbers, so the departures app owns the
    resulting behaviour in both environments.
    """
    event = int(event)

    if event == 1:
        if int(varinit.settings.get("button_mode", 0)):
            # Cycle: SL Classic -> SL List -> TfL DLR -> SL Classic.
            _combined = int(varinit.settings.get(
                "station_selection_mode",
                1 if int(varinit.settings.get("multiple", 0)) else 0
            )) == 1

            if _combined:
                _next_mode = 1
            else:
                _next_mode = (int(varinit.settings.get("listmode", 0)) + 1) % 3

            varinit.settings["listmode"] = _next_mode

            # Keep the same per-view standards used by the settings UI.
            if _next_mode == 1:
                varinit.settings["maxdest"] = 5 if _combined else 4
                varinit.settings["listcolor"] = 1
                varinit.settings["listcolor_time"] = 1
                varinit.settings["list_line_display"] = 1
                varinit.settings["clocktime"] = 0
                if _combined:
                    varinit.settings["clock_row_align"] = "left"

            elif _next_mode == 2:
                varinit.settings["maxdest"] = 3
                varinit.settings["listcolor"] = 0
                varinit.settings["listcolor_time"] = 0
                varinit.settings["list_line_display"] = 0
                varinit.settings["clocktime"] = 2
                varinit.settings["dlr_scroll_delay"] = 15

            else:
                varinit.settings["maxdest"] = 3
                varinit.settings["clocktime"] = 0
                varinit.settings["dlr_scroll_delay"] = 60
                varinit.shared["disruption_timer"] = time.monotonic()

            # The normal app/emulator renderer loop performs the actual switch.
            varinit.shared["force_view_rebuild"] = 2

        else:
            toggle_screen()

    elif event == 2:
        _station_mode = int(varinit.settings.get(
            "station_selection_mode",
            1 if int(varinit.settings.get("multiple", 0)) else 0
        ))

        _long_mode = int(varinit.settings.get("long_button_mode", 2))

        # Multiple stations reserves view switching for later logic.
        if _station_mode == 2 and _long_mode == 1:
            _long_mode = 0
            varinit.settings["long_button_mode"] = 0

        if _long_mode == 0:
            toggle_screen()

        elif _long_mode == 1:
            # Reuse the exact same view-cycling behavior as short press,
            # without changing the saved short-press preference.
            _saved_short_mode = int(varinit.settings.get("button_mode", 0))
            varinit.settings["button_mode"] = 1
            try:
                handle_button_event(1)
            finally:
                varinit.settings["button_mode"] = _saved_short_mode

        else:
            varinit.exit = True


def check_button():
    if varinit.last_button_state:
        if not varinit.button.value:
            varinit.time.sleep(varinit.debounce_delay)
            if not varinit.button.value:
                varinit.shared["nightcount"] = 0
                x = 0
                while not varinit.button.value and x < varinit.button_delay * 2:
                    x += 1
                if x > varinit.button_delay and not varinit.group.hidden:
                    handle_button_event(2)
                else:
                    handle_button_event(1)
    varinit.last_button_state = varinit.button.value

def check_timer():
    try:
        for day in varinit.settings["timer"]:
            if varinit.settings["timer"][day] and day[:3] == varinit.today:
                if compare_time(varinit.settings["timer"][day][0]) == compare_time(varinit.settings["timer"][day][1]): return True
                if compare_time(varinit.settings["timer"][day][0]) < compare_time(varinit._currenttime) < compare_time(varinit.settings["timer"][day][1].replace("00:00","24:00")):
                    print(varinit.settings["timer"][day][0], "<", varinit._currenttime, "<", varinit.settings["timer"][day][1])
                    return True
                else: return False
    except Exception as e:
        print(e)
        return True
    return True

def compare_time(time1):
    return time.struct_time(["","","",time1.split(":")[0],time1.split(":")[1],"","","",""])


def version_delay(slowdown=False):
    try:
        if slowdown:
            if slowdown == 1:
                if varinit.cpver == 9 and varinit.if_long > 128: microcontroller.cpu.frequency = 80000000
            elif slowdown == 2:
                if varinit.cpver == 9 and varinit.if_long > 128: microcontroller.cpu.frequency = 180000000
            return
    except: pass
    wifi.radio.stop_ap()
    wifi.radio.tx_power = 17.0
    #wifi.radio.tx_power = 13.0
    
    varinit.button_delay = 20000 #varinit.debounce_delay = 0.5  
    try: microcontroller.cpu.frequency = 180000000
    except: pass
    return 100

def reset_scroll(_delay=0):
    varinit.deviations_timer = time.monotonic()
    varinit.shared["scroll_timer"] = 0
    time.sleep(_delay)
    if varinit.first_start: return
    varinit.shared["loop_counter"] = 0

def sysprint(_string, line, color=True, cls=False, shading=False, _refresh=True, ontop=False, _delay=0):
    _invertcolor = 2 if shading else 0
    renderstring(_string + " ", line, smallfont=True, sys_msg=color, shading=shading, shade=False, invertcolor=_invertcolor, _cls=cls, ontop=ontop)
    refresh() if _refresh else None
    time.sleep(_delay)

def switch(_screen=True, _cls=False, force=False, wifi_screen=False):
    if _cls:
        cls(_cls)

    if _screen:
        direction = -1 if force and not varinit.tg3.y == 0 or not varinit.tg3.y == 0 else 1

        if direction == -1:
            cls(topbottom)

            if not force:
                list_splash(_settings=varinit.shared["startup"])

            if wifi_screen:
                update_screen()

            # Instant switch to scroll/display screen
            varinit.tg1.y = 0
            varinit.tg2.y = 16
            varinit.tg3.y = 32

        else:
            renderstring(
                varinit.text[4] + varinit.settings["stations"]["1"]["mystation"][:16],
                1, 0, large=True, _cls=top
            )

            # Instant switch to list/loading screen
            varinit.tg1.y = -32
            varinit.tg2.y = -16
            varinit.tg3.y = 0

        refresh()

    cls(bottom, _refresh=True)
    reset_scroll()

def view_switch_loading(_delay=2.0):
    """Show the existing station/direction splash briefly during a View change."""
    # The real MatrixBOX already uses the full-screen list surface as its
    # transition/splash surface. Make that transition deterministic for all
    # three views instead of depending on whichever TileGrid happened to be
    # visible before the change.
    try:
        varinit.tg1.x = 0
        varinit.tg2.x = 0
        varinit.tg3.x = 0
    except: pass
    cls(topbottom)
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = -32, -16, 0
    list_splash(_settings=False)
    refresh()
    if _delay:
        time.sleep(_delay)

def rebuild_current_view():
    """Enter the selected View from a clean display state.

    This is application logic used by the real MatrixBOX and by the desktop
    emulator. Renderer transitions must be correct here rather than relying on
    emulator-specific bitmap cleanup.
    """
    # Clear stale scroll positions/string buffers when crossing renderers.
    try:
        varinit.tg1.x = 0
        varinit.tg2.x = 0
        varinit.tg3.x = 0
    except: pass
    varinit.shared["scroll_timer"] = 0
    varinit.shared["loop_counter"] = 0
    # Do not inherit the font selected by the renderer we are leaving.
    # Classic/DLR both assume the normal large font at renderer entry.
    try: varinit.currentfont = 0
    except: pass
    try: cls(top)
    except: pass
    try: cls(bottom)
    except: pass
    try: cls(topbottom)
    except: pass

    mode = int(varinit.settings.get("listmode", 0))
    if mode == 2:
        reset_dlr_message_cycle()
        return dlr_mode()
    if mode == 1:
        return list_mode()

    # Classic owns the two 16px bitmaps and its lower ticker begins off-screen.
    # Establish that complete state here, then force the normal Classic renderer
    # to fetch/draw its first departure immediately.
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = 0, 16, 32
    varinit.tg1.x, varinit.tg3.x = 0, 0
    varinit.tg2.x = varinit.if_long
    varinit.currentfont = 0
    varinit.shared["loop_counter"] = 0
    try:
        varinit.shared["scroll_timer"] = time.monotonic() - updatedelay - 1
    except:
        varinit.shared["scroll_timer"] = -999999
    return scroll_mode()

def load_text():
    
    http = "" if int(varinit.settings["long"]) == -1 else "http://"
    if not varinit.settings["no_more_departures"]: varinit.settings["no_more_departures"] = dicts.language[settings["language"]]["display"]["no_more_departures"]
    _logo = "((" + LOGO_CHAR + " "
    return [_logo+dicts.language[settings["language"]]["display"]["sign"],#+" v" + settings["version"] + "     ",
            "WIFI: " + settings["ssid"] + "      ",
            dicts.language[settings["language"]]["display"]["your_settings"],
            http,
            _logo,
            "",
            varinit.settings["no_more_departures"] + " "*200,
            dicts.language[settings["language"]]["display"]["check_connection"] + ": http://",
            "Besök t-skylt.se för driftstatus",
            dicts.language[settings["language"]]["display"]["_north_south"],
            dicts.language[settings["language"]]["display"]["_north"],
            dicts.language[settings["language"]]["display"]["_south"]]

def colors():
    varinit.group.hidden = False
    factor = int(varinit.settings["brightness"])+1
    if not varinit.settings["color"]: _color = (factor*50,factor*20,0)
    elif varinit.settings["color"] == 1: _color = (factor*40,factor*20,0)
    elif varinit.settings["color"] == 2: _color = (factor*20,factor*20,factor*20)
    varinit.palette[1] = _color
    try: varinit.dest_palette[1] = _color
    except: pass
    try:
        varinit.overlay_palette[1] = _color
        varinit.overlay_palette[2] = varinit.palette[2]
    except: pass

def get_deviations():
    country = varinit.settings["stations"]["1"]["country"]
    operator = varinit.settings["stations"]["1"]["operator"]
    siteid = varinit.settings["stations"]["1"]["siteid"]
    if not len(varinit.deviations_list):
        data = fetch_data(host="data.t-skylt.se", port=90, args="/get_deviations?country=" + country + "&operator=" + operator + "&station=" + siteid)
        data = json.loads(data)
        varinit.deviations_list = data
    print(*varinit.deviations_list, sep='\n')
    return varinit.deviations_list.pop(0)

def convert_date(dt):
    if_gmt = 60 * (60*2) if "GMT" in dt else 0
    print("■ RFC1123: ", dt)
    try: varinit.today = dt.split(",")[0].replace(" ", "")
    except: pass
    for x in dicts.weekday:
        try: dt = dt.split(x)[1][2:]
        except: continue
    _date = dt.split()[0][:2]
    __month = dt.split(_date + " ")[1][:3]
    _month = dicts.month[__month]
    _year = dt.split(__month + " ")[1][:4]
    _hour = dt.split(_year + " ")[1][:2]
    _minute = dt.split(_hour + ":")[1][:2]
    _second = dt.split(_minute + ":")[1][:2]
    
    if not varinit.first_start: varinit._currenttime = (_hour + ":" + _minute)
    _newtime = time.mktime(time.struct_time((int(_year), int(_month), int(_date), int(_hour), int(_minute), int(_second), 0, 0, -1)))
    return _newtime + if_gmt

def manual_dns():
    try:
        print("Attempting manual DNS settings:")
        with open("no_dhcp") as f: no_dhcp = json.loads(f.read())
        for lines in no_dhcp: print(lines, no_dhcp[lines])
        print("---------------------------------------")
        wifi.radio.stop_dhcp()
        new_ip = no_dhcp["ip"]
        new_netmask = no_dhcp["netmask"]
        new_gateway = no_dhcp["gateway"]
        new_dns = no_dhcp["dns"] if len(no_dhcp["dns"]) > 5 else "8.8.8.8"
        wifi.radio.set_ipv4_address(ipv4=ipaddress.IPv4Address(new_ip), netmask=ipaddress.IPv4Address(new_netmask), gateway=ipaddress.IPv4Address(new_gateway), ipv4_dns=ipaddress.IPv4Address(new_dns)) # 
        print("Setting new IP: ", new_ip)
    except: pass

def wifiattempt(errmsg=True, _timeout=None, skipversion=False):
    _timeout = 5
    if "no_dhcp" in os.listdir(): manual_dns()
    #if varinit.settings["ssid"] == "my_ssid": return
    if wifi.radio.connected == True: return
    try:
        wifi.radio.enabled = True
        wifi.radio.connect(ssid=varinit.settings["ssid"], password=varinit.settings["password"].replace("%23","#"), timeout=_timeout)
        print("Connected to ", varinit.settings["ssid"])
        if not varinit.first_start: sysprint(varinit.settings["ssid"], 100, cls=topbottom)
    except Exception as e: 
        print("WIFI fail for " + varinit.settings["ssid"] + ": ", e)
        varinit.network_delay = 20 if "authentication" in str(e).lower() else 5
        if errmsg:
            if not varinit.first_start: sysprint(str(e), 100, _refresh=True, cls=topbottom, _delay=1)

def check_version():
    try: 
        try: 
            ver_txt = json.loads(fetch_data(host="t-skylt.se", port=80, args="/update/ver.txt",filetype="text"))
            varinit.new_ver = ver_txt["ver"]
            print(varinit.new_ver)
        except: print("Failed to download ver.txt")
        
        if float(varinit.new_ver) > float(varinit.settings["version"]): varinit.new_version_available = 1
        else: print("No new version available")
        #try: varinit.dicts.country_and_operators = ver_txt["country_and_operators"]
        #except: print("Failed to append Operators/Countries")
        try: varinit.ad_delay = ver_txt["ad_delay"]
        except: print("Failed to set advertisement-delay, using default: ", varinit.ad_delay)
        try: varinit.temperature_threshold = ver_txt["temperature_threshold"]
        except: print("Failed to set temperature_threshold, using default: ", varinit.temperature_threshold)
        try: varinit.socket_timeout = ver_txt["socket_timeout"]
        except: print("Failed to set socket_timeout, using default: ", varinit.socket_timeout)
    except:
        varinit.new_version_available = 0
        print("Failed to verify latest version")

def start_ap():
    try:
        #wifi.radio.start_ap(ssid=varinit.ap_name, password=str(pwd_gen()), authmode=(wifi.AuthMode.PSK, wifi.AuthMode.WPA2))
        ap_name = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] # mac-id för hotspot
        ap_name = str(ap_name)
        wifi.radio.start_ap(ssid=ap_name)
        #wifi.radio.start_dhcp_ap() # Removed DHCP, maybe causing bug http://None ?
        print("Started AP: ", varinit.ap_name)#,pwd_gen())
    except Exception as e: print("Failed to start AP: ", e)

def scan():
    netlist = []
    for networks in wifi.radio.start_scanning_networks(start_channel=1, stop_channel=14):
        if not networks.ssid == varinit.settings["ssid"]: netlist.append(networks.ssid)
        print(networks.ssid)
    wifi.radio.stop_scanning_networks()
    return(netlist)

def disp_init():
    varinit.tg1, varinit.tg2 = displayio.TileGrid(top, pixel_shader=palette), displayio.TileGrid(bottom, pixel_shader=palette)
    varinit.tg3 = displayio.TileGrid(topbottom, pixel_shader=palette)
    varinit.group = displayio.Group()
    tg1group, tg2group = displayio.Group(), displayio.Group()
    tg1group.append(varinit.tg1); tg2group.append(varinit.tg2)
    varinit.group.append(tg1group); varinit.group.append(tg2group)
    tg3group = displayio.Group()
    tg3group.append(varinit.tg3)
    varinit.group.append(tg3group)
    varinit.tg1.x = 0; varinit.tg1.y = 0
    varinit.tg2.x = varinit.if_long; varinit.tg2.y = 16
    varinit.tg3.y = 32
    varinit.palette[2] = (50,50,50)    # vit
    varinit.palette[3] = 0x000765      # morkbla
    varinit.palette[4] = (100,0,0)     # rod
    varinit.palette[5] = (20,20,20)    # grå
    varinit.palette[6] = (20,20,20)    # grå
    varinit.palette[7] = (0,20,0)    # grå
    varinit.display.root_group = varinit.group
    varinit.text = load_text()
    # Destination text smooth-scroll TileGrids (one bitmap per row, transparent background)
    _max_rows = max(8, varinit.if_tall // 6)
    _dest_bmp_w = max(400, varinit.if_long * 3)
    _dest_palette = displayio.Palette(2)
    _dest_palette[0] = 0x000000
    _dest_palette.make_transparent(0)
    _dest_palette[1] = 0xFF6600  # will be updated by colors()
    varinit.dest_palette = _dest_palette
    varinit.dest_bmps = [displayio.Bitmap(_dest_bmp_w, 13, 2) for _ in range(_max_rows)]
    varinit.dest_tgs = [displayio.TileGrid(varinit.dest_bmps[i], pixel_shader=_dest_palette, x=0, y=0) for i in range(_max_rows)]
    _dest_tg_group = displayio.Group()
    for _dtg in varinit.dest_tgs:
        _dtg.hidden = True
        _dest_tg_group.append(_dtg)
    varinit.group.append(_dest_tg_group)
    # Overlay TileGrid: line ID + minutes text drawn on top of dest TileGrids (transparent bg)
    varinit.overlay_palette = displayio.Palette(10)
    for _i in range(10): varinit.overlay_palette[_i] = varinit.palette[_i]
    varinit.overlay_palette.make_transparent(0)
    varinit.overlay_bmp = displayio.Bitmap(topbottom.width, topbottom.height, 10)
    varinit.overlay_tg = displayio.TileGrid(varinit.overlay_bmp, pixel_shader=varinit.overlay_palette, x=0, y=0)
    varinit.overlay_tg.hidden = True
    _overlay_group = displayio.Group()
    _overlay_group.append(varinit.overlay_tg)
    varinit.group.append(_overlay_group)
    varinit.dest_scroll_state = {}  # row_x -> {"overflow": int, "pos": int, "pause_end": float, "start_x": int}
    #if varinit.if_long > 128: varinit.palette[2] = (50,30,0)      # svart


def refresh(times = 2):
    if cpver == 9 and microcontroller.cpu.frequency == 160000000:
        if varinit.if_long > 128: return display.refresh(minimum_frames_per_second=0)
        if varinit.tg2.x > 64:
            time.sleep(0.001) ########## REMOVED for smoother scroll
        display.refresh(minimum_frames_per_second=0)
        delay = 0.002
        if not int(varinit.settings["scroll"]): return
        if varinit.tg2.x > 64:
            time.sleep(0.001) ########## REMOVED for smoother scroll
        for i in range(2 + int(varinit.settings["scroll"])):
            if varinit.cpver == 9: time.sleep(delay)
            display.refresh(minimum_frames_per_second=0)
    else:
        for i in range(times): display.refresh(minimum_frames_per_second=0)

def lights(switch):    
    varinit.group.hidden = True
    if switch: colors()

def get_screen_state():
    """Return True when the display is actually visible."""
    return not bool(varinit.group.hidden)

def set_screen_state(on):
    """Explicitly set the display ON/OFF. Safe to call repeatedly."""
    _on = bool(on)

    # Idempotent guard: if the display is already in the requested state,
    # do nothing. This avoids unnecessary refreshes from repeated remote
    # ON/OFF commands (for example from Home Assistant).
    if get_screen_state() == _on:
        varinit.on_off_counter = 1 if _on else 0
        return _on

    varinit.on_off_counter = 1 if _on else 0

    if _on:
        varinit.shared["nightcount"] = 0

    lights(_on)
    refresh()
    return get_screen_state()

def toggle_screen():
    """Toggle from the display's actual current state."""
    return set_screen_state(not get_screen_state())

def nightcheck(force=False, _switch=False, turnon=False):
    if not check_timer(): 
        varinit.group.hidden = 1
        return


    if _switch: varinit.on_off_counter = 1 - varinit.on_off_counter
    if turnon: 
        varinit.group.hidden = 1 - varinit.group.hidden
        varinit.shared["nightcount"] = 0
        return
    
    if force: return lights(True)
    elif varinit.on_off_counter == 0 or int(varinit.settings["sleep"]) == 1 and varinit.shared["nightcount"] > 1:
        if not varinit.group.hidden: return lights(False)
    else: lights(True)
    
def fetch_data(host, port=80, args="", headers = "", filetype="text"):
    if varinit.if_long > 128 and not int(varinit.settings["listmode"]): version_delay(slowdown=1)
    
    data = ""
    cache = ""
    try: _from = binascii.hexlify(varinit.settings["stations"]["1"]["mystation"]).decode("utf-8")
    except: _from = binascii.hexlify(bytearray(varinit.settings["stations"]["1"]["mystation"])).decode("utf-8")
    headers = "User-Agent: " + str(id) + "\r\n"
    headers += "Accept: application/json\r\n" + "Content-Type: application/json\r\n" + "Host: " + host + "\r\n" + "Version: " + str(varinit.settings["version"]) + "\r\n"
    headers += "Uptime: " + str(round((time.monotonic() - varinit.starttime)/60)) + "\r\n"
    headers += "OS-Version: " + str(varinit.cpver) + "\r\n"
    headers += "Country: " + str(varinit.settings["stations"]["1"]["country"]) + "\r\n"
    headers += "Operator: " + str(varinit.settings["stations"]["1"]["operator"]) + "\r\n"
    headers += "Siteid: " + str(varinit.settings["stations"]["1"]["siteid"]) + "\r\n"
    headers += "From: " + str(_from) + "\r\n"
    headers += "Version: " + "d" + str(varinit.version) + "\r\n"
    headers += "User: " + str(varinit.settings["user"]) + "\r\n"
    headers += "Temperature: " + str(round(microcontroller.cpu.temperature))
    print("-Fetching------------------------------------------------ ")
    print("■ HOST: ", host)
    print("■ ARGS: ", args)
    print("■ PORT: ", port)
    print("■ FILETYPE: ", filetype)
    request = b"GET " + args + " HTTP/1.0\r\n" + headers + "\r\n\r\n"
    try:
        #with pool.socket(pool.AF_INET, pool.SOCK_STREAM) as s:
        with pool.socket() as s:
            cache = bytearray(1024)                                # MAX FILESIZE
            #s.setblocking(False)
            s.settimeout(varinit.socket_timeout)
            s.connect((host, port))
            sent = s.sendall(request)
            #buff = bytearray(512)
            buff = bytearray(512)
            data = s.recv_into(buff)
            while data:
                cache += buff[:data]
                data = s.recv_into(buff)
    except Exception as e: 
        print("Socket error: ", e)
        #if "-2" in str(e): reset()
        #if "-2" in str(e): wifi.radio.enabled = False                  ######## TESTAR
            
    except: print("Socket error")
    try:
        if filetype == "binary":
            separator = b'\r\n\r\n'
            index = cache.find(separator)
            if index != -1: cache = cache[index+len(separator):]
            return cache
        x = cache.decode("utf-8")
        data = x.split("\r\n\r\n",1)[1]
    except: print("Reading error")
    
    try:
        date = x.split("Date:",1)[1]
        date = date.split("\r\n")[0]
        varinit.currenttime = convert_date(date)
    except: pass
    print("--------------------------------------------------------- ")
    if varinit.if_long > 128 and not int(varinit.settings["listmode"]): version_delay(slowdown=2)
    #print("DATA ", data)
    return data

def sort_by_minutes(lst):
    def get_minutes(sub_lst):
        value = str(sub_lst[3]).strip().lower()

        if value == "nu":
            return 0

        if ":" in value:
            try:
                hour, minute = value.split(":")[:2]
                departure_minutes = int(hour) * 60 + int(minute)

                now = time.localtime(varinit.currenttime)
                current_minutes = now.tm_hour * 60 + now.tm_min

                difference = departure_minutes - current_minutes
                if difference < -720:
                    difference += 1440
                return difference
            except:
                return 9999

        try:
            return int(value.split()[0])
        except:
            return 9999

    lst.sort(key=get_minutes)
    return lst

def sort_by_hours(lst):
    def __sort(lst):
        return sorted(lst, key=lambda x: x[3])

    if "23:" in str(lst):
        lst = json.dumps(lst)
        lst = json.loads(lst.replace("00:", "24:"))
        lst = __sort(lst)
        lst = json.dumps(lst)
        lst = json.loads(lst.replace("24:", "00:"))
        return lst
    return __sort(lst)


def _converttime(ts, age = 0): return time.mktime(time.struct_time((int(ts[:4]),int(ts[5:7]),int(ts[8:10]),int(ts[11:13]),int(ts[14:16]),int(ts[17:19]) + int(age),0,-1,-1)))

def _is_night_bus_line(line_id):
    '''Return True for SL night-bus line IDs using MatrixBOX's existing rule.'''
    try:
        return str(line_id)[-2:-1] == '9'
    except:
        return False

def traffic_parser(data, traffic_type, num="1"):
    ## Vänder "DIRECTION" på BUSES och TRAINS ##############
    stn = varinit.settings["stations"][num]
    direction = int(stn["direction"])
    night_buses_only = int(stn["buses_option"])
    if traffic_type in ("TRAIN", "BUS", "TRAM") and direction:
        direction = 3 - direction
    ########################################################
    print(" >>", traffic_type)
    dataout = []
    _maxdest = int(varinit.settings["maxdest"])
    _view_mode = int(varinit.settings.get("listmode", 0))
    if _view_mode == 2:
        # TfL DLR has exactly three visible departure slots.
        _maxdest = 3
    elif _view_mode == 1:
        # SL List on the 128x32 departures display has exactly four visible rows.
        _maxdest = 4
    elif _view_mode:
        _maxdest = varinit.if_tall // 8
    #show_lines = varinit.settings["show_lines"]
    #has_line_filter = isinstance(show_lines, list) and len(show_lines) > 0
    clocktime = varinit.settings["clocktime"]
    rt_indicator = varinit.settings["rt_indicator"]
    offset = int(stn["offset"])
    try: 
        if not data["departures"] and "msg" in data:
            return [["1", data["msg"], "***","",""]]
    except: pass
    for all in data["departures"]:
        if _view_mode == 2:
            if len(dataout) >= _maxdest: break
        elif len(dataout) > _maxdest:
            break
        line = all["line"]
        if traffic_type != line["transport_mode"]: continue
        if traffic_type == "BUS" and stn["operator"] == "sl" and night_buses_only:
            if str(line["id"])[-2:-1] != "9":
                continue
        if len(str(varinit.settings["show_lines"])) > 4:
            print(str(varinit.settings["show_lines"]))
            if not all["line"]["id"].lower() in varinit.settings["show_lines"]: continue
        difference = _converttime(all["expected"]) - varinit.currenttime
        if difference < 0: continue
        minsleft = str(round(difference / 60))
        if int(minsleft[:2]) > offset:
            if line["transport_mode"] == "ZET":
                if int(line["id"]) < 18:
                    line["transport_mode"] = "TRAM"
                else: line["transport_mode"] = "BUS"

            if not int(all["direction_code"]) or not int(direction) or int(direction) == int(all["direction_code"]):
                departure_time = str(all["expected"].split("T")[1][:5])

                if int(clocktime) == 1:
                    _minsleft = departure_time
                elif difference < 60:
                    _minsleft = "Nu"
                elif int(clocktime) == 2:
                    _minsleft = minsleft
                elif difference > 30 * 60:
                    _minsleft = departure_time
                else:
                    _minsleft = minsleft
                if line["id"] == "0": line["id"] = ""
                try: 
                    delay = all["deviations"][0] if rt_indicator else ""
                except: delay = ""
                dep = ["0", str(line["id"]), delay + all["destination"], _minsleft, str(all["direction_code"])]
                _strip_dest = varinit.settings.get("strip_dest", [])
                if isinstance(_strip_dest, list):
                    for _sd in _strip_dest:
                        if _sd: dep[2] = dep[2].replace(_sd, "").strip()
                if traffic_type != "METRO":
                    if line["transport_mode"] == traffic_type:
                        dep[2] = dep[2].split('(')[0]
                        dataout.append(dep)
                elif line["transport_mode"] == traffic_type:
                    if stn["operator"] != "sl":
                        dataout.append(dep)
                    else:
                        line_id = int(line["id"])
                        if (int(stn["green"]) and line_id in (17, 18, 19)) or \
                           (int(stn["red"]) and line_id in (13, 14)) or \
                           (int(stn["blue"]) and line_id in (10, 11)):
                            dataout.append(dep)
    return dataout

def get_departure(num = "1", dataout = [["1", "^ Data error","","",""]]):
    
    if varinit.settings["stations"][num]["siteid"] == "00" or not varinit.settings["stations"][num]["operator"]: return [["1", dicts.language[varinit.settings["language"]]["settings"]["select_operator"], "***","",""]]
    if varinit.settings["stations"][num]["siteid"] == "0": return [["1", dicts.language[varinit.settings["language"]]["settings"]["search"], "***","",""]]
    if varinit.settings["stations"][num]["siteid"] == "000": return [["1", dicts.language[varinit.settings["language"]]["display"]["select_station"], "***","",""]]
    if time.monotonic() > varinit.show_station_timer + varinit.show_station_interval and not varinit.shared["nightcount"]:
        if "demo" in os.listdir() or int(settings["show_my_station"]):
            _out = varinit.text[4]+ settings["stations"][num]["mystation"]
            if "demo" in os.listdir(): _out = "%-Skylt.se"
            if not varinit.settings["listmode"]: renderstring(_out, 1,0,1, _cls=top)
            else: renderstring(_out, 100, 0, 1)
        varinit.show_station_timer = time.monotonic()
    if varinit.use_cached_data and num in varinit.cached_departure_data:
        data = varinit.cached_departure_data[num]
        varinit.use_cached_data = False
        print("■ Using cached data for station", num)
    else:
      try: 
        temperature_check()
        _data = fetch_data(host="data.t-skylt.se", port=90, args='/get_departures?country=' + varinit.settings["stations"][num]["country"] + '&operator=' + varinit.settings["stations"][num]["operator"] + "&station=" + str(varinit.settings["stations"][num]["siteid"]))
        if _data: data = json.loads(_data)
        else: 
            varinit.active_message = True
            if str(wifi.radio.ipv4_address) == "0.0.0.0":   ########
                pass#wifi.radio.enabled = False                  ######## TESTAR
            return [["1", "-","","",""]]
      except Exception as e: 
        cls(topbottom)
        print(e)
        varinit.active_message = True
        errno = type(e).__name__
        try:
            if varinit.settings["debug"]: return [["1", str(errno) + " " + str(e),"","",""]] 
        except: pass
        err_msg = "*"
        if errno == "TypeError": err_msg = "**"
        if errno == "ValueError": err_msg = "***"#dicts.language[varinit.settings["language"]]["display"]["decoding_error"]
        print("Avkodningsfel: ", errno)
        return [["1", err_msg,"","",""]]
      except: 
        cls(topbottom)
        varinit.active_message = True
        print("Avkodningsfel.")
        return [["1", "^ Unknown error: 1","","",""]]
      varinit.cached_departure_data[num] = data
    try:
        dataout = []
        print("■", varinit.settings["stations"][num]["mystation"], varinit.settings["stations"][num]["siteid"])
        for t_types in varinit.traffic_dict:
            if varinit.settings["stations"][num][t_types]: dataout.extend(traffic_parser(data, t_types, num))
        if int(varinit.settings.get("clocktime", 0)) == 1: dataout = sort_by_hours(dataout)[slice(varinit.settings["maxdest"])]
        else: dataout = sort_by_minutes(dataout)[slice(varinit.settings["maxdest"])]
        print(*dataout, sep='\n')
    except Exception as e: 
        print(e)
        cls(topbottom)
        try:
            if not data["departures"] and "msg" in data: return [["1", data["msg"], "***","",""]]
        except: pass
        return [["1", dicts.language[varinit.settings["language"]]["settings"]["no_data"],"***","",""]]
    return dataout

def merge_departures(nums):
    # Fetch each configured stop's departures and merge them into one list,
    # sorted by departure time, for devices too narrow to show separate lists side by side.
    combined = []
    fallback_msg = None
    for num in nums:
        stn = varinit.settings["stations"].get(num)
        if not stn: continue
        if stn["siteid"] in ("00", "0", "000", "") or not stn["operator"]: continue
        rows = get_departure(num=num)
        if rows and rows[0][0] == "1":
            fallback_msg = rows
            continue
        combined.extend(rows)
    if not combined:
        if fallback_msg: return fallback_msg
        return [["1", dicts.language[varinit.settings["language"]]["display"]["no_more_departures"], "***", "", ""]]
    if int(varinit.settings.get("clocktime", 0)) == 1: combined = sort_by_hours(combined)
    else: combined = sort_by_minutes(combined)
    return combined[slice(varinit.settings["maxdest"])]

def abbreviate_dest(text, max_px):
    # Only shorten when the destination would otherwise be truncated; leaves short names untouched.
    if strlen(text) <= max_px: return text
    for pair in varinit.settings.get("dest_abbrev", []):
        if not isinstance(pair, list) or len(pair) != 2: continue
        long, short = pair
        if long and long in text:
            text = text.replace(long, short)
            if strlen(text) <= max_px: return text
    return text

def reformat_data(trainlist):
    def format_departure_value(value):
        value = str(value)
        if int(varinit.settings.get("clocktime", 0)) != 1 and value.strip().isdigit():
            return value + varinit.settings["mins"]
        return value

    def top_screen_filter(tlist):
        try: tlist[1] = tlist[1][:varinit.settings["line_length"]]
        except: pass
        tlist[3] = format_departure_value(tlist[3])
        spacing = "((((((((("
        if varinit.if_long == 128:
            spacing = "((("
            if tlist[2] in station_names_dict:
                tlist[2] = station_names_dict[tlist[2]]
            else: 
                for items in dicts.replace_list_destinations:
                    if strlen(tlist[2]) > 75: tlist[2] = tlist[2].replace(items[0], items[1])

        # Keep the top row non-scrolling text from colliding with minutes-left text.
        # Measure widths with the top-row (large) font so fitting is stable.
        def _strlen_top(s):
            f = fonts[0]
            total = 0
            for c in s:
                if c in f:
                    total += f[c][0]
                else:
                    total += f["_"][0]
            return total

        max_left_w = max(0, varinit.if_long - _strlen_top(tlist[3]))

        # First consume extra gap before touching destination text.
        while len(spacing) > 1 and _strlen_top(tlist[1] + spacing + tlist[2]) > max_left_w:
            spacing = spacing[:-1]

        max_dest_w = max_left_w - _strlen_top(tlist[1] + spacing)
        if max_dest_w < 0:
            max_dest_w = 0

        if _strlen_top(tlist[2]) > max_dest_w:
            if max_dest_w <= 0:
                tlist[2] = ""
            else:
                trimmed = tlist[2]
                while trimmed and _strlen_top(trimmed + ".") > max_dest_w:
                    trimmed = trimmed[:-1]
                tlist[2] = trimmed + ("." if trimmed and trimmed != tlist[2] else "")

        offs = varinit.if_long - (strlen(tlist[3]) + strlen(tlist[1] + spacing + tlist[2]))
        if int(trainlist[0][0]): return trainlist
        
        #if varinit.if_long > 128: renderstring(tlist[1] + spacing + tlist[2] + ("(" * offs) + tlist[3], 1)
        #else:
        #    offs = 128 - strlen(tlist[3])
        #    renderstring(offs*"(" + tlist[3], 1)
        #    renderstring(tlist[1] + spacing + tlist[2], 1)
        
        offs = max(0, varinit.if_long - strlen(tlist[3]))
        # SL Classic: capital "Nu" needs one extra pixel at the right edge.
        if str(tlist[3]).strip().lower() == "nu":
            offs = max(0, offs - 1)
        renderstring(offs*"(" + tlist[3], 1)
        renderstring(tlist[1] + spacing + tlist[2], 1)

        return trainlist[1:]
    spacing = "" if varinit.if_long == 128 else "(("
    long_buffer = "("*120 if varinit.if_long > 128 else ""
    if not len(trainlist):                                                                             
        cls(top)
        cls(bottom)
        return varinit.text[6]
    if trainlist[0][0] == "1": return trainlist[0][1] + "  " + trainlist[0][2] + "  " + trainlist[0][3]  
    elif int(varinit.settings["listmode"]): return trainlist
    else: return long_buffer + "         ".join(["  ".join([a[1][:varinit.settings["line_length"]] + (spacing * 2), a[2] + (6 * spacing), format_departure_value(a[3]) + (spacing * 10)]) for a in top_screen_filter(trainlist[0])])

def renderstring(_string, screen_partition = 0, min = 0, slow = 0, invertcolor = 0, shading=False, smallfont=False, sys_msg=False, shade=False, large=False, _cls=False, _refresh=False, ontop=False, block=False, logo=False, mini=False, start_x=0, clip_x=None, target_bmp=None, target_offs=None):
    
    if varinit.settings["long"] == -1: 
        mini = True
    if varinit.rotated:
        mini = True
    if varinit.display.width <= 64:
        mini = True
    
    if sys_msg: font_before = varinit.currentfont
    cls(_cls) if _cls else None
    #print("LEN: ", len(_string), _string, type(_string))
    if dicts.language[varinit.settings["language"]]["display"]["no_more_departures"] in _string: varinit.shared["nightcount"] += 1 
    elif str(_string) == "-" or str(_string) == "*": pass # testing
    else:
        if varinit.shared["nightcount"] > 1: varinit.on_off_counter = 1
        varinit.shared["nightcount"] = 0
    nightcheck()
    _color = False
    offs = 2
    pixwidth = start_x
    
    if not ontop and not varinit.settings["listmode"] and sys_msg:
        varinit.currentfont = 1
        varinit.tg3.y = 0
        
    if ontop: 
        screen_partition = 1
        if varinit.settings["listmode"]: offs = 0
    elif smallfont: varinit.currentfont = 1
    elif large: varinit.currentfont = 0
    
    
    if varinit.currentfont or screen_partition > 2: screen_location = [topbottom, topbottom, topbottom, topbottom]
    else: screen_location = [bottom, top, top, bottom]
    
    if screen_partition > 2: 
        _row_step = 6 if mini else (13 if varinit.currentfont == 0 else 8)
        offs = int(str(screen_partition)[1:]) * _row_step
        screen_partition = 0
    
    
    if sys_msg == "red": _color = (0,4)
    elif sys_msg == "blue": _color = (0,3)
    elif sys_msg == "green": _color = (0,7)
    elif sys_msg == "white": _color = (0,2)
    elif sys_msg == "yellow": _color = (0,1)
    
    font = fonts[varinit.currentfont]
    if smallfont == True: font = fonts[1]
    shade = False
    shading_width = 15
    _write_bmp = target_bmp if target_bmp is not None else screen_location[screen_partition]
    _write_offs = target_offs if target_offs is not None else offs
    
    if not sys_msg and int(varinit.settings["listcolor"]): shade = True
    if not sys_msg and wifi.radio.connected == False: 
        shade = True
        shading_width = 8
    
    
    for character in _string:
        if mini:
            character = character.lower()
            varinit.currentfont = 2
            font = fonts[varinit.currentfont]

        # LOGO_CHAR is only defined in fonts updated to carry the logo glyph;
        # older font files (or a font not yet updated) still hold it under
        # "%", so fall back per-character against whichever font renders it.
        if character == LOGO_CHAR and LOGO_CHAR not in font: character = "%"
        if not character in font: character = "_"
        
        for width in range(font[character][0]):
            for height in range(font["fontheight"]):
                invertedwidth = font[character][0] - width
                if isinstance(font[character][1],int):
                    try: color = (font[character][height+1] >> invertedwidth) & 1
                    except: color = color
                    
                    #if logo and color == 1: color = 5
                    #if invertcolor and int(varinit.settings["listmode"]) and pixwidth > 98: color = 1 - color
                    if invertcolor == 2: color = 1 - color
                    if _color:
                        if not int(color): color = _color[0]
                        else: color = _color[1]
                    if clip_x is None or width + pixwidth < clip_x:
                        try: _write_bmp[width+pixwidth,(height)+_write_offs] = color
                        except: pass
                else: 
                    __color = int(font[character][height+1][width])
                    if varinit.settings["long"] == 1:
                        if __color == 5: __color = 1
                    
                    if clip_x is None or width + pixwidth < clip_x:
                        try: _write_bmp[width+pixwidth,(height)+_write_offs] = __color
                        except: pass
            if slow: varinit.display.refresh(minimum_frames_per_second=0)
        if isinstance(font[character][1],int):
            pixwidth += font[character][0]
        else: pixwidth += len(font[character][1])
    if _refresh: refresh()
    if sys_msg: varinit.currentfont = font_before
    return(pixwidth)

def custom_scroll_available():
    # Custom free text is an SL Classic-only feature.
    if int(varinit.settings.get("listmode", 0)):
        return False
    if not int(varinit.settings.get("custom_scroll_show", 0)):
        return False
    return bool(str(varinit.settings.get("custom_scroll_text", "")).strip())


def render_departure_scroll():
    # SL Classic ticker. When custom text is enabled, both parts are rendered
    # into the SAME bitmap with one full display-width of blank space between
    # them. Another full display-width is added to scrollsum after the final
    # item so the last text can fully clear the display before the ticker is
    # rebuilt with fresh departures.
    _departure_text = reformat_data(get_departure())

    if custom_scroll_available():
        _custom_text = str(varinit.settings.get("custom_scroll_text", "")).strip()
        _position = int(varinit.settings.get("custom_scroll_position", 0))

        _third_gap = max(1, varinit.if_long // 3)

        if _position == 1:  # Before departures
            # Custom text is the first scrolling item after every rebuild.
            # A third-screen gap is enough before departure 2 enters.
            _custom_end = renderstring(_custom_text, large=True)
            _departure_start = _custom_end + _third_gap
            _ticker_end = renderstring(_departure_text, large=True, start_x=_departure_start)
            print("CUSTOM SCROLL prepended:", _custom_text)

        elif _position == 2:  # After first scrolling departure
            # Departure 1 is already on the fixed top row. The bottom ticker
            # therefore begins with departure 2. Split that first ticker item
            # off, insert the custom message, then continue with departures 3+.
            _parts = _departure_text.split("         ", 1)
            _first_departure = _parts[0]
            _remaining_departures = _parts[1] if len(_parts) > 1 else ""

            _first_end = renderstring(_first_departure, large=True)
            _custom_start = _first_end + _third_gap
            _custom_end = renderstring(_custom_text, large=True, start_x=_custom_start)

            if _remaining_departures:
                _remaining_start = _custom_end + _third_gap
                _ticker_end = renderstring(_remaining_departures, large=True, start_x=_remaining_start)
            else:
                _ticker_end = _custom_end
            print("CUSTOM SCROLL after first:", _custom_text)

        else:  # After departures
            _departure_end = renderstring(_departure_text, large=True)
            _custom_start = _departure_end + varinit.if_long
            _ticker_end = renderstring(_custom_text, large=True, start_x=_custom_start)
            print("CUSTOM SCROLL appended:", _custom_text)

        # Deliberate blank tail: do not rebuild while the final text is still
        # visible or just touching the left edge.
        return _ticker_end + varinit.if_long

    return renderstring(_departure_text, large=True)


def scroll_mode():
    # Renderer-transition guard. A previously scheduled Classic tick can fire
    # just after the View setting changes. Never let Classic process the raw
    # departure list that List/DLR modes intentionally return.
    _mode = int(varinit.settings.get("listmode", 0))
    if _mode == 2:
        return dlr_mode()
    if _mode == 1:
        return list_mode()

    if varinit.matrix.height == 64: microcontroller.cpu.frequency = 180000000
    if varinit.if_long > 128: version_delay(slowdown=2)
    nightcheck()
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = 0, 16, 32
    direction = varinit.text[9]
    scroll_buff = varinit.text[1]
    if varinit.shared["loop_counter"] == -7: reset()
    elif varinit.shared["loop_counter"] == -5:
        varinit.font = varinit.fonts[0]
        _logo = varinit.text[0]# if "boot.py" in os.listdir() else "% DEBUG"
        
        renderstring(_logo, 1, 0, 1, large=True, block=True, logo=True)
        wifiattempt()
        #check_version()
        varinit.first_start = False
        if varinit.settings["long"] == -1:
            varinit.settings["listmode"] = 1

        if varinit.new_version_available == 1: scroll_buff += " -    ^ " + dicts.language[varinit.settings["language"]]["display"]["new_version_available"] + str(varinit.new_ver)
        varinit.scrollsum = renderstring(scroll_buff, _cls=bottom)
        
    elif varinit.shared["loop_counter"] == -4:        
        if "textfil.txt" in os.listdir():
            
            try:
                varinit.scrollsum = renderstring(varinit.textfil.pop(0), _cls=bottom)
            except: 
                renderstring("Läser in text...", 1, 0, large=True, _cls=top)
                varinit.scrollsum = renderstring("***", _cls=bottom)
                with open("textfil.txt") as f:
                    varinit.textfil = f.read().splitlines()
                print(varinit.textfil)
                renderstring("", 1, 0, large=True, _cls=top)
            varinit.shared["loop_counter"] = -5
            
            print("TEXT")
        else:
            renderstring(str(varinit.text[2]), 1, 0, large=True)
            varinit.scrollsum = renderstring(varinit.text[3]+str(wifi.radio.ipv4_address)+"         ", _cls=bottom)


    elif varinit.shared["loop_counter"] == -3:   
        
        
        renderstring(varinit.text[4]+ varinit.settings["stations"]["1"]["mystation"][:16], 1, 0, large=True, _cls=top)
        if varinit.settings["direction"] == 1: direction = varinit.text[10]
        elif varinit.settings["direction"] == 2: direction = varinit.text[11]
        ifoffset = " + " + str(varinit.settings["stations"]["1"]["offset"]) + varinit.settings["mins"] if int(varinit.settings["stations"]["1"]["offset"]) else ""
        varinit.text[5] = direction + "   >   " + str(varinit.settings["maxdest"]) + dicts.language[varinit.settings["language"]]["display"]["departures"] + ifoffset
        varinit.scrollsum = renderstring(varinit.text[5], large=True, _cls=bottom)
        varinit.shared["loop_counter"] = -2
    varinit.tg2.x = varinit.if_long
    varinit.shared["loop_counter"]+=1
    if varinit.shared["loop_counter"] > 0:
        if varinit.active_message == True:
            reset_scroll()
            varinit.active_message = False
        elif time.monotonic() > varinit.shared["scroll_timer"] + updatedelay:
            cls(bottom, _refresh=True)
            if time.monotonic() > varinit.ad_timer + varinit.ad_delay * 60 and varinit.shared["nightcount"] < 2:
                try: 
                    ad = ad_message() 
                    if ad: 
                        varinit.scrollsum = renderstring(reformat_data([["1", ad,"***","",""]]), large=True, _cls=bottom)
                        varinit.active_message = True
                    else: varinit.scrollsum = render_departure_scroll()
                except: varinit.scrollsum = render_departure_scroll()
            
            elif time.monotonic() > _disruption_timer() + _scroll_delay_seconds() \
                and int(varinit.settings["show_msgs"]) and varinit.shared["nightcount"] < 2 \
                and varinit.settings["stations"]["1"]["operator"] in ["sl","vt"]:
                _disruption_now = time.monotonic()
                try: varinit.scrollsum = renderstring(reformat_data([["1", get_deviations(),"***","",""]]), large=True, _cls=bottom)
                except: varinit.scrollsum = renderstring(reformat_data([["1", " ","***","",""]]), large=True, _cls=bottom)
                _mark_disruption_cycle(_disruption_now)
                varinit.deviations_timer = _disruption_now
                varinit.active_message = True
            else: varinit.scrollsum = render_departure_scroll()
            rnd = random.randint(0, 10)
            varinit.shared["scroll_timer"] = time.monotonic() + rnd
            print("RND: ", rnd)

CLOCK_ROW_MARK = "__clock__"

def clock_string():
    t = time.localtime(varinit.currenttime)
    def _z(n):
        s = str(n)
        return "0" + s if len(s) == 1 else s
    hhmm = _z(t[3]) + ":" + _z(t[4])
    if int(varinit.settings.get("clock_row_date", 0)):
        datepart = _z(t[2]) + "." + _z(t[1]) + "." + _z(t[0] % 100)
        return datepart + " * " + hhmm
    if varinit.settings.get("clock_row_align", "left") == "center":
        return "*** " + hhmm + " ***"
    return hhmm

def apply_clock_row(trainlist):
    # Replaces a departure row with the current date/time, if enabled.
    if not int(varinit.settings.get("show_clock_row", 0)): return trainlist
    if not isinstance(trainlist, list) or not trainlist: return trainlist
    if not isinstance(trainlist[0], list): return trainlist
    n = max(1, int(varinit.settings.get("maxdest", 1)))
    kept = trainlist[:max(0, n - 1)]
    clock_row = ["0", "", clock_string(), "", CLOCK_ROW_MARK]
    if varinit.settings.get("clock_row_position", "bottom") == "top":
        kept.insert(0, clock_row)
    else:
        kept.append(clock_row)
    return kept


def _font_width(text, font_index):
    f = fonts[font_index]
    total = 0
    for c in str(text):
        if c not in f: c = "_"
        total += f[c][0] if isinstance(f[c][1], int) else len(f[c][1])
    return total

def _dlr_upper(text):
    """CircuitPython-safe uppercase for Swedish DLR text.

    Some MatrixBOX/CircuitPython builds uppercase ASCII but leave å/ä/ö
    unchanged when those characters occur inside a word.  Apply normal
    uppercasing first, then explicitly promote the Swedish glyphs so the
    emulator and real matrix render identically.
    """
    text = str(text).upper()
    return text.replace("å", "Å").replace("ä", "Ä").replace("ö", "Ö")


def _dlr_abbreviate_dest(text, max_px, font_index, uppercase=False):
    """Apply DLR destination abbreviations using the width actually rendered."""
    raw_text = str(text)
    text = raw_text

    def _fits(candidate):
        rendered = _dlr_upper(candidate) if uppercase else str(candidate)
        return _font_width(rendered, font_index) <= max_px

    if _fits(text):
        return text

    # User-configured abbreviations first, matching the existing list renderer.
    for pair in varinit.settings.get("dest_abbrev", []):
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        long, short = pair
        if long and long in text:
            text = text.replace(long, short)
            if _fits(text):
                return text

    # Generic built-in replacements from dicts.py.
    for pair in dicts.replace_list_destinations:
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
        mapped = station_names_dict.get(raw_text)
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

def _dlr_clock_string():
    """Fixed DLR overlay clock: always HH:MM, never date/alignment decoration."""
    t = time.localtime(varinit.currenttime)
    def _z(n):
        s = str(n)
        return "0" + s if len(s) == 1 else s
    return _z(t[3]) + ":" + _z(t[4])

def refresh_clock_settings_now():
    """Immediately rebuild List/DLR after a clock web-setting change.

    This is departures-app behavior, so the same update path is used on the
    physical MatrixBOX and in the desktop emulator.
    """
    if int(varinit.settings.get("listmode", 0)) not in (1, 2):
        return
    varinit.shared["force_view_rebuild"] = 0
    rebuild_current_view()

def refresh_dlr_settings_now():
    """Backward-compatible alias for older web handlers."""
    refresh_clock_settings_now()



def _scroll_delay_seconds():
    """Return the shared Scroll Text delay in seconds.

    DLR uses it as the lower-half dwell. When Disruptions is selected, both
    Classic and DLR also use it as the minimum interval between disruption
    cycles. The legacy setting key is kept for settings-file compatibility.
    """
    try:
        delay = int(varinit.settings.get("dlr_scroll_delay", 15))
    except:
        delay = 15
    return max(1, min(300, delay))

def _dlr_scroll_delay_seconds():
    """Backward-compatible name used by the DLR animation."""
    return _scroll_delay_seconds()

def _disruption_timer():
    """Independent disruption-cycle timer, unaffected by ordinary scroll resets."""
    try:
        return float(varinit.shared.get("disruption_timer", 0))
    except:
        return 0

def _mark_disruption_cycle(now=None):
    if now is None:
        now = time.monotonic()
    varinit.shared["disruption_timer"] = now

def reset_dlr_message_cycle():
    """Reset the DLR lower-half message cycle to its configured dwell."""
    varinit.dlr_message_state = {
        "phase": "normal",
        "normal_since": time.monotonic(),
        "last_step": 0,
        "message": "",
        "message_width": 0,
    }
    try:
        varinit.tg2.x = 0
        varinit.tg2.y = 16
    except:
        pass

def dlr_message_active():
    """True while the DLR lower half is sliding away or scrolling a message."""
    try:
        return varinit.dlr_message_state.get("phase", "normal") != "normal"
    except:
        return False

def _dlr_custom_message():
    if not int(varinit.settings.get("custom_scroll_show", 0)):
        return ""
    return str(varinit.settings.get("custom_scroll_text", "")).strip()

def _dlr_scroll_content_mode():
    """Return DLR's exclusive message source using the existing settings.

    Custom wins for legacy settings files where both switches happened to be on;
    the web UI now keeps them mutually exclusive.
    """
    if int(varinit.settings.get("custom_scroll_show", 0)):
        return "custom"
    if int(varinit.settings.get("show_msgs", 0)):
        return "disruptions"
    return "none"

def _dlr_next_message():
    """Choose the next DLR lower-half message from the selected source."""
    _content_mode = _dlr_scroll_content_mode()
    if _content_mode == "none":
        return ""
    if _content_mode == "custom":
        return _dlr_custom_message()

    now = time.monotonic()

    try:
        _operator = varinit.settings["stations"]["1"]["operator"]
    except:
        _operator = ""

    if (varinit.shared.get("nightcount", 0) < 2
            and _operator in ("sl", "vt")
            and now > _disruption_timer() + _scroll_delay_seconds()):
        try:
            msg = str(get_deviations()).strip()
            _mark_disruption_cycle(now)
            varinit.deviations_timer = now
            if msg:
                return msg
        except Exception as e:
            print("DLR disruption message error:", repr(e))
            # A failed fetch starts a new configured delay before retrying.
            _mark_disruption_cycle(now)
            varinit.deviations_timer = now

    return ""

def refresh_dlr_message_settings_now():
    """Rebuild DLR and restart the configured message dwell after web changes."""
    if int(varinit.settings.get("listmode", 0)) != 2:
        return
    reset_dlr_message_cycle()
    varinit.shared["force_view_rebuild"] = 0
    dlr_mode()
    varinit.shared["scroll_timer"] = time.monotonic()

def dlr_animation_tick():
    """Animate the DLR lower-half message cycle one small step.

    Normal rows 2+3 (and the optional clock) remain for the configured delay.
    If a custom or native disruption message is available, the lower TileGrid slides
    downward, the message scrolls horizontally through the lower half, and the
    normal DLR rows are rebuilt when it has completely passed.
    """
    if int(varinit.settings.get("listmode", 0)) != 2:
        return False

    try:
        state = varinit.dlr_message_state
        if not isinstance(state, dict):
            raise TypeError
    except:
        reset_dlr_message_cycle()
        state = varinit.dlr_message_state

    now = time.monotonic()
    phase = state.get("phase", "normal")

    if phase == "normal":
        if now < float(state.get("normal_since", now)) + _dlr_scroll_delay_seconds():
            return False

        msg = _dlr_next_message()
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
            varinit.tg2.y += 1
            refresh(1)
        except:
            pass

        if varinit.tg2.y >= 32:
            # Lower departures + clock are now fully below the 32px display.
            # Reuse that same lower bitmap as a normal large-font ticker.
            varinit.tg2.y = 16
            varinit.tg2.x = varinit.if_long
            cls(bottom)
            state["message_width"] = renderstring(
                state.get("message", ""), large=True, _cls=bottom
            )
            state["phase"] = "scroll_message"
            refresh(1)
        return True

    if phase == "scroll_message":
        try:
            varinit.tg2.x -= 1
            refresh(1)
        except:
            pass

        if varinit.tg2.x < -int(state.get("message_width", 0)):
            # Restore the normal DLR lower half. dlr_mode() also redraws the top
            # departure, so data stays fresh after a potentially long message.
            varinit.tg2.x = 0
            varinit.tg2.y = 16
            state["phase"] = "normal"
            state["normal_since"] = now
            state["message"] = ""
            state["message_width"] = 0
            dlr_mode()
            varinit.shared["scroll_timer"] = time.monotonic()
        return True

    reset_dlr_message_cycle()
    return False

def dlr_mode():
    """TfL DLR layout: one large departure on top, two compact departures below."""
    try:
        _dlr_phase = varinit.dlr_message_state.get("phase", "normal")
    except:
        reset_dlr_message_cycle()
        _dlr_phase = "normal"
    # DLR physically has three departure rows. Keep the app setting consistent
    # even when the mode was loaded from saved settings rather than selected in the UI.
    varinit.settings["maxdest"] = 3
    nightcheck()
    # renderstring() changes currentfont. DLR has mixed large/small rows, so always
    # begin from a known font state instead of inheriting the previous renderer.
    varinit.currentfont = 0

    # DLR uses the same physical 16px + 16px screen arrangement as SL Classic.
    # Keep the normal top/bottom TileGrids visible and hide the full-screen list bitmap.
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = 0, 16, 32
    # Classic scroll moves tg2.x continuously. Never inherit that offset in DLR.
    varinit.tg1.x, varinit.tg2.x, varinit.tg3.x = 0, 0, 0

    if varinit.shared["loop_counter"] == -7:
        reset()

    # Match the existing SL startup/loading experience. DLR normally uses the
    # split top/bottom surfaces, but the established station/direction splash is
    # drawn on the full-screen list surface. Show it once before the first DLR
    # departure fetch, then the next DLR pass restores the normal split layout.
    if varinit.shared["startup"]:
        cls(topbottom)
        varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = -32, -16, 0
        list_splash()
        refresh()
        varinit.shared["startup"] = False
        return time.monotonic() - varinit.updatedelay + 2

    # Restore the physical DLR split layout after the startup splash.
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = 0, 16, 32

    trainlist = reformat_data(get_departure())
    if not isinstance(trainlist, list) or not trainlist:
        cls(top)
        cls(bottom)

        _msg = str(trainlist).strip() if trainlist is not None else ""
        _no_more = str(varinit.settings.get("no_more_departures", "")).strip()
        if not _no_more:
            _no_more = dicts.language[varinit.settings["language"]]["display"]["no_more_departures"]

        # DLR empty state: keep it static and readable. The text comes directly
        # from settings.txt (`no_more_departures`) and is shown on the large top
        # line; the lower half remains blank.
        if _no_more and (_no_more in _msg or not _msg):
            varinit.currentfont = 0
            renderstring(_no_more, 1, large=True, _cls=top)
        elif _msg:
            # Preserve useful non-empty status/error strings rather than hiding
            # them, while still keeping DLR's lower half clear.
            varinit.currentfont = 0
            renderstring(_msg, 1, large=True, _cls=top)

        refresh()
        return time.monotonic()

    rows = [row[:] for row in trainlist[:3] if isinstance(row, list) and len(row) >= 4]

    # Night-bus highlighting is derived at render time from the existing line ID.
    # No extra night-bus flag is carried in the departure data structure.
    _night_highlight_mode = int(varinit.settings.get('night_bus_highlight', 0))
    _visible_departures = [row for row in rows if len(row) > 4]
    _all_visible_are_night = bool(_visible_departures)
    for _row in _visible_departures:
        if not _is_night_bus_line(_row[1]):
            _all_visible_are_night = False
            break
    _night_highlight_enabled = (
        _night_highlight_mode == 2 or
        (_night_highlight_mode == 1 and not _all_visible_are_night)
    )

    cls(top)
    cls(bottom)

    # DLR clock is an overlay, not a replacement departure.  Reserve its large-font
    # footprint on the right of the lower 16px and leave exactly 2 blank columns
    # between the row-2/3 time markers and the clock.
    _show_dlr_clock = int(varinit.settings.get("show_clock_row", 0))
    _dlr_clock = _dlr_clock_string() if _show_dlr_clock else ""
    _dlr_clock_x = max(0, varinit.if_long - _font_width(_dlr_clock, 0)) if _show_dlr_clock else varinit.if_long
    _lower_value_right = max(0, _dlr_clock_x - 2) if _show_dlr_clock else varinit.if_long

    def _draw_row(row, number, bmp, y, font_index):
        # Shared List/DLR line-label mode:
        #   0 = visible row numbers (1, 2, 3...)
        #   1 = actual transit line number/id from departure data
        _line_mode = int(varinit.settings.get("list_line_display", 0))
        _night_highlight = _night_highlight_enabled and _is_night_bus_line(row[1])
        _line_label = str(row[1]).strip() if _line_mode else str(number)
        prefix = _line_label + " "
        raw_dest = str(row[2]).split('(')[0].split(" via")[0].strip()
        dest = raw_dest
        value = str(row[3])

        # reformat_data() already applies Dynamic / Time / Countdown logic.
        # Only add the configured minute suffix when the returned value is numeric.
        if int(varinit.settings.get("clocktime", 0)) != 1 and value.strip().isdigit():
            value += varinit.settings["mins"]

        # Lower DLR rows are rendered in capitals.  Do this BEFORE measuring the
        # time/value field: uppercase glyphs can be wider than their lowercase
        # counterparts, and the destination must be fitted around the pixels we
        # will actually draw.
        if number != 1:
            value = _dlr_upper(value)

        value_right = varinit.if_long if number == 1 else _lower_value_right
        if number != 1 and not _show_dlr_clock:
            # The small-font right edge is one pixel tighter than the large top
            # row.  Keep the final column on-screen instead of clipping it.
            value_right = max(0, value_right - 1)

        actual_value_width = _font_width(value, font_index)
        is_now = value.strip().lower() == "nu"

        # Rows 2/3 keep a stable value slot for a given departure.  Once a wider
        # minute/time marker has reserved space, NU does not reclaim those pixels.
        # This keeps both the destination abbreviation and the visual padding
        # unchanged, with or without the DLR clock overlay.
        if number != 1:
            try:
                _slots = varinit.dlr_lower_value_slots
            except:
                _slots = {}
                varinit.dlr_lower_value_slots = _slots
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
        max_dest = max(0, max_left - _font_width(prefix, font_index))

        # Top-row DLR abbreviation is sticky for the current first destination.
        # If the destination needed a built-in/user abbreviation while a wider
        # countdown/time value was shown, keep that exact abbreviation when the
        # value later narrows to Nu instead of expanding the name again.
        if number == 1:
            try:
                _cache = varinit.dlr_top_abbrev_cache
            except:
                _cache = {}
                varinit.dlr_top_abbrev_cache = _cache

            if _cache.get("raw") == raw_dest and _cache.get("abbr"):
                dest = _cache["abbr"]
            else:
                dest = _dlr_abbreviate_dest(raw_dest, max_dest, font_index)
                if dest != raw_dest:
                    varinit.dlr_top_abbrev_cache = {"raw": raw_dest, "abbr": dest}
                else:
                    varinit.dlr_top_abbrev_cache = {"raw": raw_dest, "abbr": ""}
        else:
            # Fit against the reduced lower-row width (including the clock area,
            # when present) before falling back to clipping.  Keep the selected
            # dicts.py abbreviation sticky while this same departure occupies the
            # row, including when its value changes to NU.
            try:
                _abbrs = varinit.dlr_lower_abbrev_cache
            except:
                _abbrs = {}
                varinit.dlr_lower_abbrev_cache = _abbrs
            _abbr_key = str(number)
            _cached = _abbrs.get(_abbr_key, {})
            _clock_key = 1 if _show_dlr_clock else 0
            if (_cached.get("raw") == raw_dest and
                    _cached.get("clock") == _clock_key and _cached.get("abbr")):
                dest = _cached["abbr"]
            else:
                dest = _dlr_abbreviate_dest(raw_dest, max_dest, font_index, uppercase=True)
                _abbrs[_abbr_key] = {
                    "raw": raw_dest,
                    "clock": _clock_key,
                    "abbr": dest if dest != raw_dest else "",
                }
            # TfL DLR lower rows use block-capital destination/value text.
            # Apply this after abbreviation selection so dicts.py remains the
            # authoritative source of abbreviations.
            dest = _dlr_upper(dest)

        left = prefix + dest
        while dest and _font_width(left, font_index) > max_left:
            dest = dest[:-1]
            left = prefix + dest

        # Reuse the SL List colour toggles in DLR:
        #   listcolor      ON = white departure number, OFF = yellow
        #   listcolor_time ON = white time/minutes,     OFF = yellow
        # Keep the destination itself in the normal destination colour.
        line_colour = "white" if int(varinit.settings.get("listcolor", 0)) else "yellow"
        time_colour = "white" if int(varinit.settings.get("listcolor_time", 0)) else "yellow"
        if _night_highlight:
            line_colour = 'red'
            time_colour = 'red'
        prefix_width = _font_width(prefix, font_index)
        renderstring(prefix, 0, large=(font_index == 0), smallfont=(font_index != 0),
                     target_bmp=bmp, target_offs=y, start_x=0, sys_msg=line_colour)
        renderstring(dest, 0, large=(font_index == 0), smallfont=(font_index != 0),
                     target_bmp=bmp, target_offs=y, start_x=prefix_width,
                     sys_msg=('red' if _night_highlight else False))
        renderstring(value, 0, large=(font_index == 0), smallfont=(font_index != 0),
                     target_bmp=bmp, target_offs=y, start_x=value_x, sys_msg=time_colour)

    if len(rows) > 0:
        _draw_row(rows[0], 1, top, 2, 0)
    if len(rows) > 1:
        _draw_row(rows[1], 2, bottom, 0, 1)
    if len(rows) > 2:
        _draw_row(rows[2], 3, bottom, 8, 1)

    if _show_dlr_clock:
        # Large clock spans the two compact lower rows and is pinned to the right edge.
        renderstring(_dlr_clock, 0, large=True, target_bmp=bottom, target_offs=3,
                     start_x=_dlr_clock_x, sys_msg=varinit.settings.get("clock_row_color", "white"))

    refresh()
    return time.monotonic()

def list_mode(mini=False, half=False):
    # SL List physically has four departure rows on this 128x32 layout. Keep the
    # app setting consistent even when List was restored directly from settings.
    if int(varinit.settings.get("listmode", 0)) == 1:
        varinit.settings["maxdest"] = 4
    mini = varinit.settings["mini"]

    #### debug
    #mini = True
    if varinit.rotated:
        mini = True
        half = False
    elif varinit.display.width <= 64:
        mini = True
        half = False
    elif varinit.settings["multiple"]: 
        half = True
        mini = True
    if varinit.settings["long"] == -1 and not varinit.rotated: 
        mini = True
        half = True
     


    if varinit.if_long > 128: version_delay(slowdown=1)
    large_list = not mini and not half and not varinit.rotated and int(varinit.settings.get("large_list", 0))
    xs_line_id = varinit.display.width <= 64 and not varinit.rotated and int(varinit.settings.get("xs_line_id", 0))
    varinit.currentfont = 1
    if mini: varinit.currentfont = 2
    elif large_list: varinit.currentfont = 0
    extrarow = 1 if mini else 0
    varinit.tg1.y, varinit.tg2.y, varinit.tg3.y = extrarow + 0-32, extrarow + 16-32, extrarow + 0

    _dest_scroll = int(varinit.settings.get("dest_scroll", 0))
    _now = time.monotonic()
    cls(topbottom)
    # Hide dest TileGrids and overlay; will be shown per-row if dest_scroll active
    try:
        for _dtg in varinit.dest_tgs: _dtg.hidden = True
        varinit.overlay_tg.hidden = True
        varinit.overlay_bmp.fill(0)
        varinit.dest_scroll_state = {}
    except: pass

    if varinit.shared["startup"]:
        list_splash()
        varinit.shared["startup"] = False
        return time.monotonic() - varinit.updatedelay + 2
    if varinit.shared["loop_counter"] == -7: reset()
    if time.monotonic() > varinit.ad_timer + varinit.ad_delay * 60 and varinit.shared["nightcount"] < 2:
        try: 
            ad = ad_message()
            if ad:
                index = 0
                for i in range(0, 4):
                    _ad = ad[index:index+15].lstrip(" ")
                    renderstring(str(_ad), 100+i, shading=True, smallfont=True)
                    refresh()
                    index += 15
            else: return 0
        except: pass
        return time.monotonic() - varinit.updatedelay + 2
    
    # trainlist = reformat_data(get_departure())
    ### DEBUG
    
    _r = 1
    try:
        if varinit.settings["multiple"]:
            if varinit.settings["long"] == 0: _r = 2
            if varinit.settings["long"] == 1: _r = 3
        else: _r = 1
    except: pass
    
    merge_list_mode = int(varinit.settings["multiple"]) and varinit.display.width <= 64 and not varinit.rotated
    if merge_list_mode:
        print("Fetching merged stops")
        varinit.traindata[1] = apply_clock_row(reformat_data(merge_departures(("1", "2", "3"))))
    else:
        for i in range(_r):
            print("Fetching: ", i+1)
            _data = reformat_data(get_departure(num = str(i+1)))
            varinit.traindata[i+1] = apply_clock_row(_data) if i == 0 else _data
            if not half or i+1 == _r: break
        
    
    
    
    try:
    
        if varinit.settings["long"] == -1: num = 1
        if varinit.settings["long"] == 0: num = 2
        if varinit.settings["long"] == 1: num = 3

        #num=varinit.no_of_screens_flag
        
        for record in varinit.traindata:
            print(record)
            trainlist = varinit.traindata[record]
            if isinstance(trainlist, list):
                trainlist = [row[:] for row in trainlist if isinstance(row, list)]
            if int(record) > _r: continue
            if not half and "str" in str(type(trainlist)): 
                sysprint("".join(trainlist[:30]), 100)
                if dicts.language[settings["language"]]["display"]["no_more_departures"] in trainlist: return time.monotonic()
                return time.monotonic() - varinit.updatedelay + 2
            elif "str" in str(type(trainlist)): 
                print(trainlist)
                #sysprint("".join(trainlist[:30]), 100)
                trainlist = [["","",trainlist[:40],"",""]]
                    #continue
                #if dicts.language[settings["language"]]["display"]["no_more_departures"] in trainlist: 
                #    return time.monotonic()
                #if not half: return time.monotonic() - varinit.updatedelay + 2
        
            if large_list and isinstance(trainlist, list):
                _max_lw = 0
                for _a in trainlist:
                    if isinstance(_a, list) and len(_a) > 1:
                        _w = strlen(_a[1][:varinit.settings["line_length"]])
                        if _w > _max_lw: _max_lw = _w
                line_col = _max_lw + 6
            else:
                line_col = 0

            _xs_max_lw = 0
            if xs_line_id and isinstance(trainlist, list):
                for _a in trainlist:
                    if isinstance(_a, list) and len(_a) > 1:
                        _w = strlen(_a[1][:varinit.settings["line_length"]])
                        if _w > _xs_max_lw: _xs_max_lw = _w

            # Determine highlighting from the original line IDs before List
            # optionally replaces them with visible row numbers.
            _night_highlight_mode = int(varinit.settings.get('night_bus_highlight', 0))
            _visible_departures = [
                row for row in trainlist[:4]
                if isinstance(row, list) and len(row) > 4 and row[4] != CLOCK_ROW_MARK
            ]
            _all_visible_are_night = bool(_visible_departures)
            for _row in _visible_departures:
                if not _is_night_bus_line(_row[1]):
                    _all_visible_are_night = False
                    break
            _night_highlight_enabled = (
                _night_highlight_mode == 2 or
                (_night_highlight_mode == 1 and not _all_visible_are_night)
            )

            for x, all in enumerate(trainlist):

                is_clock_row = len(all) > 4 and all[4] == CLOCK_ROW_MARK
                _row_is_night_bus = (
                    not is_clock_row and _is_night_bus_line(all[1])
                )
                _night_highlight = _night_highlight_enabled and _row_is_night_bus
                # Shared List/DLR line-label mode. SL List defaults to actual
                # line numbers, but can instead show visible row numbers 1..4.
                if not is_clock_row and not int(varinit.settings.get("list_line_display", 1)):
                    all[1] = str(x + 1)
                all[2] = all[2].split('(')[0].split(" via")[0]#.lower()
                _strip_dest = varinit.settings.get("strip_dest", [])
                if isinstance(_strip_dest, list):
                    for _sd in _strip_dest:
                        if _sd: all[2] = all[2].replace(_sd, "").strip()
                if strlen(all[2]) > 82 and varinit.if_long == 128:
                    for items in dicts.replace_list_destinations:
                        all[2] = all[2].replace(items[0], items[1])
                    try: all[2] = station_names_dict[all[2]]
                    except: pass

                mins_cut = 23 - len(varinit.settings["mins"]) - (int(varinit.settings["line_length"]))

                if len(all[3]) > 1:
                       mins_cut -= 1

                if int(varinit.settings.get("clocktime", 0)) != 1:
                    _mins_ref_w = strlen("00")
                    if strlen(all[3]) < _mins_ref_w:
                        all[3] = (_mins_ref_w - strlen(all[3])) * "(" + all[3]

                is_countdown = str(all[3]).replace("(", "").strip().isdigit()
                if_not_clocktime = (
                    varinit.settings["mins"]
                    if all[3] and int(varinit.settings.get("clocktime", 0)) != 1 and not is_clock_row and is_countdown
                    else ""
                )

                all[3] += if_not_clocktime

                _full_dest_w = 0
                _max_px = 0
                _line_col_w = 0
                if varinit.rotated or varinit.display.width <= 64:
                    _w = varinit.if_long if varinit.rotated else varinit.display.width
                    _max_px = _w - strlen(all[3])
                    if not varinit.rotated and xs_line_id and not is_clock_row:
                        _max_px -= _xs_max_lw + 2
                    all[2] = abbreviate_dest(all[2], _max_px)
                    while len(all[2]) > 0 and strlen(all[2]) > _max_px:
                        all[2] = all[2][:-1]
                elif large_list:
                    _max_px = varinit.if_long - strlen(all[3]) - line_col
                    _font = fonts[varinit.currentfont]
                    all[2] = abbreviate_dest(all[2], _max_px)
                    while len(all[2]) > 0 and sum(_font.get(c, _font['_'])[0] for c in all[2]) > max(0, _max_px):
                        all[2] = all[2][:-1]
                elif not half:
                    _line_col_w = strlen(varinit.settings["line_length"] * ("((((" if mini else "(((((("))
                    _max_px = varinit.if_long - strlen(all[3]) - _line_col_w - 2
                    _full_dest_w = strlen(all[2])
                    if not (_dest_scroll and _full_dest_w > max(0, _max_px)):
                        all[2] = abbreviate_dest(all[2], _max_px)
                        while len(all[2]) > 0 and strlen(all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                if half:
                    if is_clock_row:
                        _max_px = 64 - strlen(all[3]) - 1
                        while len(all[2]) > 0 and strlen(all[2]) > max(0, _max_px):
                            all[2] = all[2][:-1]
                    else:
                        all[2] = all[2][:15 - len(varinit.settings["mins"])]
                        if int(varinit.settings.get("clocktime", 0)) == 1:
                            all[2] = all[2][:11]
                mins = all[2]
                if int(varinit.settings.get("clocktime", 0)) != 1: all[1] = "1(1(" if all[1] == "11" else all[1]

                if mini: all[2] = mins
                all[1] = all[1][:varinit.settings["line_length"]]
                
                line = all[1]
                dest = all[2]
                
                if varinit.rotated:
                    offs = varinit.if_long - strlen(all[3])
                elif varinit.display.width <= 64:
                    offs = varinit.display.width - strlen(all[3])
                else:
                    offs = varinit.if_long - strlen(all[3])

                # SL List: one pixel is enough to keep "Nu" clear of the edge.
                if str(all[3]).replace("(", "").strip().lower() == "nu":
                    offs = max(0, offs - 1)
                if half: 
                    all[3] = all[3].replace(" " + if_not_clocktime,"")
                    offs = 64 - strlen(all[3])

                    

                minsleft = offs*"(" + all[3]
                
                inv = 0

                if half: minsleft = minsleft.replace(" " + if_not_clocktime, "")
                
                if half: multiple_offset = int(num - 1) * (" " * 64)
                    
                
                else: multiple_offset = ""
        
                min_color = "white" if varinit.settings.get("listcolor_time", 0) or varinit.rotated else "yellow"
                lin_color = "yellow" if not varinit.settings["listcolor"] else "white"
                clock_color = varinit.settings.get("clock_row_color", "white")
                if _night_highlight:
                    min_color = 'red'
                    lin_color = 'red'
                if varinit.rotated or varinit.display.width <= 64:
                    added_space = ""
                    line = ""
                    if not varinit.rotated and xs_line_id:
                        line = all[1][:varinit.settings["line_length"]]
                        added_space = (_xs_max_lw + 2) * "("
                elif mini:
                    added_space = varinit.settings["line_length"] * "(((("
                    if half: added_space = ""
                else: added_space = varinit.settings["line_length"] * "(((((("
                if not varinit.settings["line_length"]:
                    added_space = ""
                    line = ""

                if is_clock_row:
                    _clock_align = varinit.settings.get("clock_row_align", "left")
                    _clock_avail = varinit.display.width if varinit.display.width <= 64 else varinit.if_long
                    _clock_pad = max(0, _clock_avail - strlen(dest))
                    if _clock_align == "center": _clock_pad = _clock_pad // 2
                    elif _clock_align == "left": _clock_pad = 0
                    added_space = _clock_pad * "("
                    line = ""

                if large_list:
                    _lpart = 100 + x
                    _dest_pad = line_col * "("
                    renderstring(multiple_offset + minsleft, _lpart, 0, 0, inv, sys_msg=min_color)
                    renderstring(multiple_offset + _dest_pad + dest, _lpart, 0, 0, inv, sys_msg=(clock_color if is_clock_row else ('red' if _night_highlight else False)))
                    if not half and not varinit.rotated: renderstring(multiple_offset + line, _lpart, 0, 0, inv, sys_msg=lin_color)
                    if x > 4: continue
                else:
                    _use_tg = (_dest_scroll and not half and not varinit.rotated
                               and varinit.display.width > 64
                               and _full_dest_w > max(0, _max_px))
                    if _use_tg:
                        # TileGrid smooth scroll: dest in dest_bmp, line+mins in overlay_bmp
                        _row_step = 6 if mini else 8
                        _overflow = _full_dest_w - _max_px
                        varinit.dest_bmps[x].fill(0)
                        renderstring(dest, 100+x, 0, 0, inv, mini=mini,
                                     target_bmp=varinit.dest_bmps[x], target_offs=0,
                                     sys_msg=('red' if _night_highlight else False))
                        varinit.dest_tgs[x].x = _line_col_w
                        varinit.dest_tgs[x].y = extrarow + x * _row_step
                        varinit.dest_tgs[x].hidden = False
                        varinit.dest_scroll_state[x] = {
                            "overflow": _overflow, "pos": 0,
                            "pause_end": _now + x * 0.8 + 2.0, "start_x": _line_col_w
                        }
                        renderstring(multiple_offset + minsleft, 100+x, 0, 0, inv, mini=mini,
                                     sys_msg=min_color, target_bmp=varinit.overlay_bmp)
                        if not half and not varinit.rotated and (varinit.display.width > 64 or xs_line_id):
                            renderstring(multiple_offset + line, 100+x, 0, 0, inv, mini=mini,
                                         sys_msg=lin_color, target_bmp=varinit.overlay_bmp)
                        varinit.overlay_tg.y = extrarow
                        varinit.overlay_tg.hidden = False
                    else:
                        renderstring(multiple_offset + minsleft, 100+x, 0, 0, inv, mini=mini, sys_msg=min_color)
                        renderstring(multiple_offset + added_space + dest, 100+x, 0, 0, inv, mini=mini, sys_msg=(clock_color if is_clock_row else ('red' if _night_highlight else False)))
                        if not half and not varinit.rotated and (varinit.display.width > 64 or xs_line_id):
                            renderstring(multiple_offset + line, 100+x, 0, 0, inv, mini=mini, sys_msg=lin_color)
                    if x > varinit.if_tall // 8 - 1: continue
            num -= 1
            
    except Exception as e: print("ERROR ", e)
    refresh()

    return time.monotonic()

def list_splash(_settings=False):
    direction = varinit.text[9]
    lastrow = 103 if int(varinit.settings["long"]) == -1 else 102
    extra_space = " " if int(varinit.settings["long"]) == -1 else ""
    if varinit.settings["direction"] == 1: direction = varinit.text[10]
    if varinit.settings["direction"] == 2: direction = varinit.text[11]
    varinit.text[5] = extra_space + direction
    if varinit.shared["startup"] == 1 or _settings:
        sysprint(extra_space + varinit.text[2], lastrow, _refresh=False)
        sysprint(varinit.text[3]+str(wifi.radio.ipv4_address), lastrow+1, _refresh=False)
    else:
        if int(varinit.settings["stations"]["1"]["offset"]):
            sysprint(str(dicts.language[settings["language"]]["display"]["hiding"]) + str(varinit.settings["stations"]["1"]["offset"]) + varinit.settings["mins"], 102, _refresh=False)
    sysprint(LOGO_CHAR+str(varinit.settings["stations"]["1"]["mystation"]), 100, _refresh=False)
    sysprint(varinit.text[5], 101, _refresh=True)

def update_screen():
    
    lastrow = 103 if int(varinit.settings["long"]) == -1 else 102
        
    if wifi.radio.connected == True: return
    renderstring("1. " + dicts.language[varinit.settings["language"]]["display"]["connect_to"], 100, shading=True, smallfont=True, _cls=topbottom)
    renderstring("1. ", 100, shading=True, smallfont=True, sys_msg="white")

    macid = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] # mac-id för hotspot
    renderstring(str(macid), 101, shading=True, smallfont=True)
    #renderstring("t-skylt" + id[-2:], 101, shading=True, smallfont=True)
    
    renderstring("2. " + dicts.language[varinit.settings["language"]]["display"]["go_to"], lastrow,shading=True, smallfont=True)
    
    renderstring("2. ", lastrow,shading=True, smallfont=True, sys_msg="white")
    
    renderstring("http://" + str(wifi.radio.ipv4_address_ap), lastrow+1,shading=True, smallfont=True, _refresh=True)

def savesettings(_settings=varinit.settings, saved=dicts.language[varinit.settings["language"]]["display"]["saving"]):
    varinit.group.hidden = True; refresh()
    try:
        with open("settings.txt", "w") as f:
            f.write(json.dumps(_settings))
        print("Saved!")
    except: saved = "Read only"
    varinit.group.hidden = False; refresh()

    if int(varinit.settings.get("listmode", 0)) == 2:
        # DLR's visible top surface is `top`, while the generic ontop system
        # message path targets the full-screen list bitmap. Draw the same red,
        # shaded notice directly onto DLR's visible top bitmap, then restore DLR.
        cls(top)
        renderstring(saved + " ", 0, smallfont=True, sys_msg="red",
                     shading=True, invertcolor=2, target_bmp=top, target_offs=0)
        refresh()
        time.sleep(0.5)
        dlr_mode()
        varinit.shared["scroll_timer"] = time.monotonic()
    else:
        sysprint(saved, 0, color="red", shading=True, _refresh=True, ontop=True)
        reset_scroll(_delay=0.5)

try: 
    import font_mini
    dicts.font_mini = font_mini
    varinit.fonts.append(font_mini.font_mini)
    #print(len(varinit.fonts))
except:
    print("Not imported: font_mini")
    print("Attempting download...")
