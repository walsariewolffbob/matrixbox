from __main__ import wifi, pool
import varinit, createhtml, microcontroller, json, ipaddress
from varinit import *
import random

mac = [hex(i) for i in wifi.radio.mac_address]
id = "".join(mac)

ap_name = "matrixbox-" + "".join(mac).replace("0x","")[:3] 


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
    event = int(event)

    if event == 1:
        if int(varinit.settings.get("button_mode", 0)):
            
            _combined = int(varinit.settings.get(
                "station_selection_mode",
                1 if int(varinit.settings.get("multiple", 0)) else 0
            )) == 1

            if _combined:
                _next_mode = 1
            else:
                _next_mode = (int(varinit.settings.get("listmode", 0)) + 1) % 3

            varinit.settings["listmode"] = _next_mode

            
            if _next_mode == 1:
                if _combined:
                    varinit.settings["maxdest"] = 5
                    varinit.settings["dest_scroll"] = 0
                else:
                    varinit.settings["maxdest"] = 4
                    varinit.settings["listcolor"] = 1
                    varinit.settings["listcolor_time"] = 1
                    varinit.settings["night_bus_highlight"] = 0
                    varinit.settings["list_line_display"] = 1
                    varinit.settings["clocktime"] = 0

            elif _next_mode == 2:
                varinit.settings["maxdest"] = 3
                varinit.settings["listcolor"] = 0
                varinit.settings["listcolor_time"] = 0
                varinit.settings["night_bus_highlight"] = 1
                varinit.settings["list_line_display"] = 0
                varinit.settings["clocktime"] = 2
                varinit.settings["dlr_scroll_delay"] = 15

            else:
                varinit.settings["maxdest"] = 4
                varinit.settings["clocktime"] = 0
                
                
                varinit.settings["list_line_display"] = 1
                varinit.settings["dlr_scroll_delay"] = 60
                varinit.shared["disruption_timer"] = time.monotonic()

            
            varinit.shared["force_view_rebuild"] = 2

        else:
            toggle_screen()

    elif event == 2:
        _station_mode = int(varinit.settings.get(
            "station_selection_mode",
            1 if int(varinit.settings.get("multiple", 0)) else 0
        ))

        _long_mode = int(varinit.settings.get("long_button_mode", 2))

        if _long_mode == 0:
            toggle_screen()

        elif _long_mode == 1:
            
            
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
    
    
    varinit.button_delay = 20000 
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

            
            varinit.tg1.y = 0
            varinit.tg2.y = 16
            varinit.tg3.y = 32

        else:
            renderstring(
                varinit.text[4] + varinit.settings["stations"]["1"]["mystation"][:16],
                1, 0, large=True, _cls=top
            )

            
            varinit.tg1.y = -32
            varinit.tg2.y = -16
            varinit.tg3.y = 0

        refresh()

    cls(bottom, _refresh=True)
    reset_scroll()

def view_switch_loading(_delay=2.0):
    
    
    
    
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

def request_view_rebuild(splash=False, reset_timing=True):
    if reset_timing:
        varinit.shared["scroll_timer"] = 0
        varinit.shared["loop_counter"] = 0
    varinit.shared["force_view_rebuild"] = 2 if splash else 1


def rebuild_current_view():
    
    try:
        varinit.tg1.x = 0
        varinit.tg2.x = 0
        varinit.tg3.x = 0
    except: pass
    varinit.shared["scroll_timer"] = 0
    varinit.shared["loop_counter"] = 0
    
    
    try: varinit.currentfont = 0
    except: pass
    try: cls(top)
    except: pass
    try: cls(bottom)
    except: pass
    try: cls(topbottom)
    except: pass

    
    
    request_view_rebuild()
    return

def load_text():
    
    http = "" if int(varinit.settings["long"]) == -1 else "http://"
    if not varinit.settings["no_more_departures"]: varinit.settings["no_more_departures"] = dicts.language[settings["language"]]["display"]["no_more_departures"]
    _logo = "((" + LOGO_CHAR + " "
    return [_logo+dicts.language[settings["language"]]["display"]["sign"],
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
        wifi.radio.set_ipv4_address(ipv4=ipaddress.IPv4Address(new_ip), netmask=ipaddress.IPv4Address(new_netmask), gateway=ipaddress.IPv4Address(new_gateway), ipv4_dns=ipaddress.IPv4Address(new_dns)) 
        print("Setting new IP: ", new_ip)
    except: pass

def wifiattempt(errmsg=True, _timeout=None, skipversion=False):
    _timeout = 5
    if "no_dhcp" in os.listdir(): manual_dns()
    
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
        
        ap_name = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] 
        ap_name = str(ap_name)
        wifi.radio.start_ap(ssid=ap_name)
        
        print("Started AP: ", varinit.ap_name)
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
    varinit.palette[2] = (50,50,50)    
    varinit.palette[3] = 0x000765      
    varinit.palette[4] = (100,0,0)     
    varinit.palette[5] = (20,20,20)    
    varinit.palette[6] = (20,20,20)    
    varinit.palette[7] = (0,20,0)    
    varinit.display.root_group = varinit.group
    varinit.text = load_text()
    
    _max_rows = max(8, varinit.if_tall // 6)
    _dest_bmp_w = max(400, varinit.if_long * 3)
    _dest_palette = displayio.Palette(2)
    _dest_palette[0] = 0x000000
    _dest_palette.make_transparent(0)
    _dest_palette[1] = 0xFF6600  
    varinit.dest_palette = _dest_palette
    varinit.dest_bmps = [displayio.Bitmap(_dest_bmp_w, 13, 2) for _ in range(_max_rows)]
    varinit.dest_tgs = [displayio.TileGrid(varinit.dest_bmps[i], pixel_shader=_dest_palette, x=0, y=0) for i in range(_max_rows)]
    _dest_tg_group = displayio.Group()
    for _dtg in varinit.dest_tgs:
        _dtg.hidden = True
        _dest_tg_group.append(_dtg)
    varinit.group.append(_dest_tg_group)
    
    varinit.overlay_palette = displayio.Palette(10)
    for _i in range(10): varinit.overlay_palette[_i] = varinit.palette[_i]
    varinit.overlay_palette.make_transparent(0)
    varinit.overlay_bmp = displayio.Bitmap(topbottom.width, topbottom.height, 10)
    varinit.overlay_tg = displayio.TileGrid(varinit.overlay_bmp, pixel_shader=varinit.overlay_palette, x=0, y=0)
    varinit.overlay_tg.hidden = True
    _overlay_group = displayio.Group()
    _overlay_group.append(varinit.overlay_tg)
    varinit.group.append(_overlay_group)
    varinit.dest_scroll_state = {}  
    


def refresh(times = 2):
    if cpver == 9 and microcontroller.cpu.frequency == 160000000:
        if varinit.if_long > 128: return display.refresh(minimum_frames_per_second=0)
        if varinit.tg2.x > 64:
            time.sleep(0.001) 
        display.refresh(minimum_frames_per_second=0)
        delay = 0.002
        if not int(varinit.settings["scroll"]): return
        if varinit.tg2.x > 64:
            time.sleep(0.001) 
        for i in range(2 + int(varinit.settings["scroll"])):
            if varinit.cpver == 9: time.sleep(delay)
            display.refresh(minimum_frames_per_second=0)
    else:
        for i in range(times): display.refresh(minimum_frames_per_second=0)

def lights(switch):    
    varinit.group.hidden = True
    if switch: colors()

def get_screen_state():
    return not bool(varinit.group.hidden)

def set_screen_state(on):
    _on = bool(on)

    
    
    
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
        
        with pool.socket() as s:
            cache = bytearray(1024)                                
            
            s.settimeout(varinit.socket_timeout)
            s.connect((host, port))
            sent = s.sendall(request)
            
            buff = bytearray(512)
            data = s.recv_into(buff)
            while data:
                cache += buff[:data]
                data = s.recv_into(buff)
    except Exception as e: 
        print("Socket error: ", e)
        
        
            
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
    
    return data

def _now_text():
    try:
        return str(varinit.settings.get("now_text", "Nu")).strip() or "Nu"
    except:
        return "Nu"

def _is_night_bus_line(line_id):
    try:
        return str(line_id)[-2:-1] == "9"
    except:
        return False

def sort_by_minutes(lst):
    def get_minutes(sub_lst):
        value = str(sub_lst[3]).strip().lower()

        if value == _now_text().lower():
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

def traffic_parser(data, traffic_type, num="1"):
    
    stn = varinit.settings["stations"][num]
    direction = int(stn["direction"])
    night_buses_only = int(stn["buses_option"])
    if traffic_type in ("TRAIN", "BUS", "TRAM") and direction:
        direction = 3 - direction
    
    print(" >>", traffic_type)
    dataout = []
    _maxdest = max(1, int(varinit.settings["maxdest"]))
    _view_mode = int(varinit.settings.get("listmode", 0))
    if _view_mode == 2:
        
        _maxdest = min(_maxdest, 3)
    elif _view_mode == 1:
        
        _maxdest = min(_maxdest, 4)
    elif _view_mode:
        _maxdest = min(_maxdest, varinit.if_tall // 8)
    
    
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
                    _minsleft = _now_text()
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
            if str(wifi.radio.ipv4_address) == "0.0.0.0":   
                pass
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
        if errno == "ValueError": err_msg = "***"
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
        
        
        
        
        
        
        
        offs = max(0, varinit.if_long - strlen(tlist[3]))
        
        if str(tlist[3]).strip().lower() == _now_text().lower():
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
    
    if dicts.language[varinit.settings["language"]]["display"]["no_more_departures"] in _string: varinit.shared["nightcount"] += 1 
    elif str(_string) == "-" or str(_string) == "*": pass 
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

        
        
        
        if character == LOGO_CHAR and LOGO_CHAR not in font: character = "%"
        if not character in font: character = "_"
        
        for width in range(font[character][0]):
            for height in range(font["fontheight"]):
                invertedwidth = font[character][0] - width
                if isinstance(font[character][1],int):
                    try: color = (font[character][height+1] >> invertedwidth) & 1
                    except: color = color
                    
                    
                    
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
    
    if int(varinit.settings.get("listmode", 0)):
        return False
    if not int(varinit.settings.get("custom_scroll_show", 0)):
        return False
    return bool(str(varinit.settings.get("custom_scroll_text", "")).strip())


def reset_classic_scroll_pacing(reset_baseline=False):
    
    
    varinit.shared["classic_scroll_last_step"] = time.monotonic()
    if reset_baseline:
        varinit.shared["classic_scroll_interval"] = 0
    varinit.shared["classic_scroll_setting"] = int(varinit.settings.get("scroll", 0))

def clock_string():
    t = time.localtime(varinit.currenttime)
    def _z(n):
        s = str(n)
        return "0" + s if len(s) == 1 else s
    hhmm = _z(t[3]) + ":" + _z(t[4])
    if int(varinit.settings.get("clock_row_date", 0)):
        datepart = _z(t[2]) + "." + _z(t[1]) + "." + _z(t[0] % 100)
        return datepart + " * " + hhmm
    return hhmm

def apply_clock_row(trainlist, is_clock_station=True):
    if not int(varinit.settings.get("show_clock_row", 0)):
        return trainlist
    if isinstance(trainlist, str):
        trainlist = [["", "", trainlist[:40], "", MSG_ROW_MARK]]
    if not isinstance(trainlist, list) or not trainlist:
        return trainlist
    if not isinstance(trainlist[0], list):
        return trainlist
    n = max(1, int(varinit.settings.get("maxdest", 1)))
    kept = trainlist[:max(0, n - 1)]
    clock_row = ["0", "", clock_string() if is_clock_station else "", "", CLOCK_ROW_MARK]
    if varinit.settings.get("clock_row_position", "bottom") == "top":
        kept.insert(0, clock_row)
    else:
        kept.append(clock_row)
    return kept

def refresh_clock_settings_now():
    request_view_rebuild()


def refresh_dlr_settings_now():
    request_view_rebuild()


def _scroll_delay_seconds():
    try:
        delay = int(varinit.settings.get("dlr_scroll_delay", 15))
    except:
        delay = 15
    return max(1, min(300, delay))

def _disruption_timer():
    try:
        return float(varinit.shared.get("disruption_timer", 0))
    except:
        return 0

def _mark_disruption_cycle(now=None):
    if now is None:
        now = time.monotonic()
    varinit.shared["disruption_timer"] = now

def _dlr_custom_message():
    if not int(varinit.settings.get("custom_scroll_show", 0)):
        return ""
    return str(varinit.settings.get("custom_scroll_text", "")).strip()

def _dlr_scroll_content_mode():
    if int(varinit.settings.get("custom_scroll_show", 0)):
        return "custom"
    if int(varinit.settings.get("show_msgs", 0)):
        return "disruptions"
    return "none"

def refresh_dlr_message_settings_now():
    request_view_rebuild()


CLOCK_ROW_MARK = "__clock__"
MSG_ROW_MARK = "__msg__"


def prepare_list_data(mini=False, half=False):
    mini = varinit.settings["mini"]
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

    _r = 1
    if int(varinit.settings.get("multiple", 0)):
        if varinit.if_long > 128:
            try:
                _r = max(2, min(3, int(varinit.settings.get("multi_station_columns", 3))))
            except (TypeError, ValueError):
                _r = 3
        elif varinit.display.width > 64:
            _r = 2

    prepared = {}
    merge_list_mode = int(varinit.settings["multiple"]) and varinit.display.width <= 64 and not varinit.rotated
    if merge_list_mode:
        print("Fetching merged stops")
        prepared[1] = apply_clock_row(reformat_data(merge_departures(("1", "2", "3"))))
    else:
        for i in range(_r):
            print("Fetching: ", i + 1)
            _data = reformat_data(get_departure(num=str(i + 1)))
            prepared[i + 1] = apply_clock_row(_data, is_clock_station=(i == 0))
            if not half or i + 1 == _r:
                break
    return prepared

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

    macid = "matrixbox-" + "".join([hex(i) for i in wifi.radio.mac_address]).replace("0x","")[:3] 
    renderstring(str(macid), 101, shading=True, smallfont=True)
    
    
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
        
        
        
        cls(top)
        renderstring(saved + " ", 0, smallfont=True, sys_msg="red",
                     shading=True, invertcolor=2, target_bmp=top, target_offs=0)
        refresh()
        time.sleep(0.5)
        varinit.shared["force_view_rebuild"] = 1
        varinit.shared["scroll_timer"] = time.monotonic()
    else:
        sysprint(saved, 0, color="red", shading=True, _refresh=True, ontop=True)
        time.sleep(0.5)
        
        
        varinit.shared["force_view_rebuild"] = 1
        varinit.shared["scroll_timer"] = time.monotonic()

try: 
    import font_mini
    dicts.font_mini = font_mini
    varinit.fonts.append(font_mini.font_mini)
    
except:
    print("Not imported: font_mini")
    print("Attempting download...")
