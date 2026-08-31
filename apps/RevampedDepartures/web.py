css = ""
try: from css import _css as css
except: pass
from dicts import language, flag as _flag_img

country_and_operators = {
  "se":[["sl","SL (Stockholm)"],["vt","VT (Västtrafik)"],["otraf","Östgötatrafiken"],["vastmanland","VL (Västmanlands län)"],["dt","DT (Dalatrafik)"],["jlt","JLT (Jönköpings län)"],["krono","KRONO (Kronobergs länstrafik)"],["ul","UL (Uppsala län)"],["klt","KLT (Kalmar länstrafik)"],["orebro","Länstrafiken Örebro"],["xt","X-Trafik (Gävleborg)"],["varm","Värmlandstrafik - Karlstadsbuss"],["skane","Skånetrafiken"],["norrbotten","Norrbotten"],["fe","Trafikverkets färjor"],["dintur","DinTur (Västernorrland)"],["sj","SJ (Trafikverket)"],["sormland","Sörmland (Endast tidtabell)"]],
  "dk":[["kb","Scheduled"],["dk_rt","Real-time (experimental)"]],
  "lu":[["all","All of Luxembourg"]],
  "no":[["no","Entur (entire Norway)"]],
  "fi":[["all","All of Finland"], ["hsl","HSL"]],
  "cr":[["za","ZET (Zagreb)"]],
  "nl":[["all","Countrywide"], ["ns","Nederlandse Spoorwegen"]],
  "ch":[["ch","Switzerland"],["sbb","SBB"]],
  "fr":[["sncf","SNCF"], ["idfm","IDFM (Paris)"], ["ilevia","Ilévia"], ["met","Le MET"]],
  "lt":[["vil","Vilnius"]],
  "be":[["sncb","SNCB"], ["stib","STIB"], ["delijn","De Lijn"]],
  "uk":[["lo","Tfl (London)"],["nr","National Rail"]],
  "hu":[["bu","Budapest"]],
  "us":[["nyc_subway","NYC Subway"],["nyc_lirr","Long Island Rail Road"],["nyc_mnr","Metro-North Railroad"],["nyc_bus_bx","MTA Bus - Bronx"],["nyc_bus_b","MTA Bus - Brooklyn"],["nyc_bus_m","MTA Bus - Manhattan"],["nyc_bus_q","MTA Bus - Queens"],["nyc_bus_si","MTA Bus - Staten Island"],["nyc_bus_co","MTA Bus Company"]],
  "cz":[["pr","Prague (PID)"]],
  "it":[["ro","Rome"]],
  "pt":[["carris","Carris"]],
  "pl":[["wa","Warsaw"],["kr","Krakow"],["wa_tram","Warszawa Tram"],["plk","PLK"]],
  "at":[["wl","Vienna"]],
  "es":[["barcelona","Barcelona (AMB)"]],
  "ie":[["all","All real-time operators"]],
  "de":[["local","Germany (gtfs.de)"],["db_trains","DB-trains (Deutsche Bahn)"],["be","Berlin (Unofficial API)"],["vbb","VBB/BVG (Berlin-Brandenburg)"],["vrr","VRR (Rhein-Ruhr)"],["kvv","KVV (Karlsruhe)"],["rmv","RMV (Frankfurt)"],["hochbahn","HVV (Hamburg etc.)"],["vrn","VRN (Rhein-Neckar)"],["vbn","VBN (Bremen-Niedersachsen)"],["vvo","VVO (Dresden)"]]
}

def _opt(val, cur, label):
    s = " selected" if str(val) == str(cur) else ""
    return "<option value='" + str(val) + "'" + s + ">" + label + "</option>"


def _chk(name, val, url, label):
    c = " checked" if int(val) else ""
    return ('<div class="toggle-row"><label for="' + name + '" class="toggle-label">' + label + '</label>'
            '<label class="switch"><input type="checkbox" id="' + name + '" data-u="' + url + '"' + c + '><span class="slider"></span></label></div>')


def _rssi(functions):
    try:
        ai = functions.wifi.radio.ap_info
        return ai.rssi if ai else -100
    except Exception:
        return -100


def _sig_bars(rssi):
    n = 5 if rssi > -45 else 4 if rssi > -55 else 3 if rssi > -65 else 2 if rssi > -75 else 1 if rssi > -85 else 0
    bars = "".join('<i class="' + ("on" if i < n else "") + '"></i>' for i in range(5))
    return '<span class="sig" id="sig" title="' + str(rssi) + ' dBm">' + bars + "</span>"


PAGE_TPL = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1" charset="UTF-8">
<link href="data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAA/SURBVDhPY2RgYPgPxGQDsAFAAOGRCBgZGREGgDikAJgeJiifbDDwBuAMRPQwwaVmGITBqAHUykwQLjmAgQEA3oYYFR16cP8AAAAASUVORK5CYII=" rel="icon" type="image/x-icon"/>
<title>{TITLE}</title><style>{CSS}</style></head><body>
<nav class="navbar">
<a class="nav-x" href="/exit" title="Exit" style="margin-left:0;margin-right:4px">&#8592;</a>
<span class="nav-title">{HEADER}</span>
<div class="nav-spacer"></div>
<div class="nav-info"><span id="clk"></span><span>{IP_DISPLAY}</span></div>
{SIG_BARS}
<button type="button" class="nav-led{LED_OFF_CLS}" id="ledbtn" onclick="fetch('/?onoff=active').then(function(r){return r.json()}).then(function(s){document.getElementById('ledbtn').classList.toggle('led-off',!s.on)})" title="Turn display on/off">&#x1F4A1;</button>
<a class="nav-x" href="/exit" title="Exit">&#x2715;</a>
</nav>
<div class="page">
<form method="post" action="/">
<div class="card">
<div class="section-title">{T_CONNECTIONS}</div>
<div class="form-row">
<div class="col">
<label for="ssid"><a href="#" onclick="doScan();return false" title="Scan">&#128268;</a> {T_WIFI_LABEL}</label>
<select id="ssid" class="form-control" name="ssid" data-p="ssid" data-e="change" {NET_DIS}>{SSID_OPTIONS}</select>
</div>
<div class="col">
<label for="password">{T_PASSWORD}</label>
<input type="text" id="password" class="form-control" name="password" placeholder="*******" data-p="password" data-e="blur" data-enc="1" {NET_DIS}>
</div>
</div>
<button type="button" class="btn btn-outline-secondary btn-sm" id="connect_wifi" style="margin-top:10px" data-u="/?connect_wifi=true" {NET_DIS}>{T_CONNECT}</button>
{CONNECTION_ADVANCED}
</div>
<div class="card">
<div class="section-title">Station selection</div>
{STATION_SELECTION_MODE}
<div class="form-row" style="margin-top:12px">
<div class="dropdown" id="opdd"><button type="button" class="dropbtn" id="opbtn" {OPBTN_PULSE} onclick="toggleDropdown(event)">{COUNTRY_FLAG} {OPERATOR} &#9660;</button>
<div class="dropdown-content">{COMBINED_LIST}</div></div>
<div id="screenbtns" style="{SCREEN_BTN_DISP}display:flex;align-items:center;gap:6px">
<span style="font-size:.68rem;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">Editing</span>
{SCREEN_BUTTONS}
</div>
<div class="col" style="min-width:150px">
<select id="newstation" class="form-control" name="newstation" data-p="newstation" data-e="change" {RESULT_DIS} {RESULT_STYLE} onchange="this.style.animation=''">{RESULTS}</select>
</div>
</div>
<div class="form-row" style="margin-top:10px">
<div class="col">
<input type="text" id="sstring" class="form-control" name="sstring" placeholder="{STATION_PH}" {SEARCH_DIS} {SSTRING_PULSE} onkeydown="if(event.key==='Enter'){event.preventDefault();doSearch()}">
</div>
<button type="button" class="btn" id="searchbtn" onclick="doSearch()" {SEARCH_DIS}>{T_SEARCH}</button>
</div>
</div>
<div class="card">
<div class="grp-title">{T_TRAFFIC_TYPES}</div>
<div class="tt-grid">
{METRO_SECTION}
{BUS_SECTION}
{TRAIN_CHK}
{TRAM_SECTION}
{SHIP_SECTION}
</div>
{SL_SECTION}
</div>
<div class="card">
<div class="grp">
<div class="form-row">{CLOCKTIME_CHK}<div class="col">
<label for="maxdest">{T_NO_DEPARTURES}</label>
<select id="maxdest" name="maxdest" class="form-control" data-p="maxdest" data-e="change"{MAXDEST_DISABLED}>{MAXDEST_OPTIONS}</select>
</div></div></div>
<div class="grp">
<div class="form-row"><div class="col">
<label for="offset">{T_HIDE_DEPARTURES}</label>
<select id="offset" name="offset" class="form-control" data-p="offset" data-e="change">{OFFSET_OPTIONS}</select>
</div><div class="col">{DIRECTION_SECTION}</div></div></div>
{SLEEP_CHK}
</div>
<div class="card">
{LISTMODE_CHK}
{SCROLL_SECTION}
{DEVIATIONS_SECTION}
{CUSTOM_SCROLL_HTML}
{CLOCK_INLINE_HTML}
{VIEW_COLOR_TOGGLES}
</div>
<div class="card"><details>
<summary>&#9881; {T_ADVANCED}</summary>
{BUTTON_MODE_CHK}
<table>
<tr><td><b>{T_TONE}</b></td><td><div style="display:flex;gap:10px">{TONE_SWATCHES}</div></td></tr>
<tr><td><b>{T_LINE_LENGTH}</b></td><td><input type="text" id="line_length" class="form-control" style="width:80px;display:inline" placeholder="{LINE_LENGTH_VAL}" data-p="line_length" data-e="blur"><br><small>{T_LINE_LENGTH_HELP}</small></td></tr>
<tr><td><b>{T_SHOW_LINES}</b></td><td><input type="text" id="show_lines" class="form-control" style="width:160px;display:inline" placeholder="{SHOW_LINES_VAL}" data-p="show_lines" data-e="blur"></td></tr>
<tr><td><b>Strip from destination</b></td><td><input type="text" id="strip_dest" class="form-control" style="width:160px;display:inline" placeholder="{STRIP_DEST_VAL}" data-p="strip_dest" data-e="blur" data-enc="1"></td></tr>
<tr><td><b>{T_NO_MORE_DEP}</b></td><td><input type="text" id="no_more_departures" class="form-control" style="width:160px;display:inline" placeholder="{NO_MORE_DEP_VAL}" data-p="no_more_departures" data-e="blur" data-enc="1"></td></tr>
<tr><td><b>{T_MINS}</b></td><td><input type="text" id="mins" class="form-control" style="width:160px;display:inline" placeholder="{MINS_VAL}" data-p="mins" data-e="blur" data-enc="1"></td></tr>
</table>
{SHOW_STATION_CHK}
{XS_LINE_ID_CHK}
{DEST_SCROLL_CHK}
{DNS_SECTION}
</details></div>
<button type="button" class="btn btn-full" data-u="/?save=true">&#128190; {T_SAVE}</button>
<div style="text-align:center;margin-top:14px"><small>For support, visit <a href="https://shop.t-skylt.se/">T-Skylt.se</a><br>Unofficial app by B.WW. See <a href="https://github.com/walsariewolffbob/matrixbox">GitHub</a></small></div>
<div id="opsdata" style="display:none">{OPS_JSON}</div>
<div id="stndata" style="display:none">{STN_JSON}</div>
<script>
function _ck(){var d=new Date(),h=d.getHours(),m=d.getMinutes();document.getElementById('clk').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}_ck();setInterval(_ck,15000);
var OPS=JSON.parse(document.getElementById('opsdata').textContent);var STN=JSON.parse(document.getElementById('stndata').textContent);
function toggleDropdown(e){e.stopPropagation();document.getElementById('opdd').classList.toggle('open');}
document.addEventListener('click',function(e){var dd=document.getElementById('opdd');if(dd&&!dd.contains(e.target))dd.classList.remove('open');});
function pickScr(n){fetch('/?screen='+n);var d=STN[n];if(!d)return;document.querySelectorAll('.scr-btn').forEach(function(b){b.classList.toggle('act',b.textContent==String(n));});var co=d.co,op=d.op.toLowerCase();var el=document.querySelector('.dd-grid img[data-c="'+co+'"]');var f=el?el.outerHTML.replace(/dd-sel/g,'')+' ':'';var nm=d.op?d.op.toUpperCase():'OPERATOR';var ops=OPS[co]||[];for(var i=0;i<ops.length;i++){if(ops[i][0]===op){nm=ops[i][1];break;}}document.getElementById('opbtn').innerHTML=f+nm+' &#9660;';document.getElementById('sstring').placeholder=d.ms||'';var cb={METRO:d.M,BUS:d.B,TRAIN:d.T,TRAM:d.R,SHIP:d.S,r:d.r,g:d.g,b:d.b};for(var k in cb){var e=document.getElementById(k);if(e)e.checked=!!cb[k];}var sl=document.getElementById('slsection');if(sl)sl.style.display=op==='sl'?'':'none';var nb=document.getElementById('night_buses');if(nb)nb.checked=!!d.bo;var nbr=document.getElementById('night-buses-row');if(nbr)nbr.style.display=(String(d.op).toLowerCase()==='sl'&&d.B)?'':'none';var of2=document.getElementById('offset');if(of2)of2.value=d.of;var di=document.getElementById('direction');if(di)di.value=d.di;}
function pickC(c){var d=document.getElementById('ddops');d.innerHTML='';var ops=OPS[c]||[];for(var i=0;i<ops.length;i++){var a=document.createElement('a');a.href='#';a.textContent=ops[i][1];(function(cc,code,name){a.onclick=function(e){e.preventDefault();chCO(cc,code,name);return false;};})(c,ops[i][0],ops[i][1]);d.appendChild(a);}document.querySelectorAll('.dd-grid img').forEach(function(im){im.classList.toggle('dd-sel',im.dataset.c===c);});}
function chCO(c,o,n){fetch('/?country='+c+'&operator='+o);var el=document.querySelector('.dd-grid img[data-c="'+c+'"');var f='';if(el)f=el.outerHTML.replace(/dd-sel/g,'')+' ';document.getElementById('opbtn').innerHTML=f+n+' &#9660;';document.getElementById('opbtn').style.animation='';document.getElementById('sstring').style.animation='guide-pulse 2.5s ease-in-out infinite';var sl=document.getElementById('slsection');if(sl)sl.style.display=o==='sl'?'':'none';var nbr=document.getElementById('night-buses-row'),bus=document.getElementById('BUS');if(nbr)nbr.style.display=(o==='sl'&&bus&&bus.checked)?'':'none';document.getElementById('opdd').classList.remove('open');}
function doSearch(){var s=document.getElementById('sstring').value;if(!s)return;var b=document.getElementById('searchbtn');b.disabled=true;b.innerHTML='<span class="spin"></span>';fetch('/search?sstring='+encodeURIComponent(s)).then(function(r){return r.text();}).then(function(h){var sel=document.getElementById('newstation');sel.innerHTML=h;sel.disabled=false;sel.style.borderColor='#ff6060';sel.style.animation='guide-pulse 2.5s ease-in-out infinite';document.getElementById('sstring').style.animation='';b.disabled=false;b.textContent='{T_SEARCH}';}).catch(function(){b.disabled=false;b.textContent='{T_SEARCH}';});}
function doScan(){fetch('/checknet').then(function(r){return r.text();}).then(function(h){var sel=document.getElementById('ssid');sel.innerHTML=h;sel.disabled=false;document.getElementById('password').disabled=false;document.getElementById('connect_wifi').disabled=false;}).catch(function(){});}

function setStationSelectionMode(v,el){
var p=el.parentNode;if(p)p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
el.classList.add('on');
fetch('/?station_selection_mode='+encodeURIComponent(v)).then(function(){location.reload();});
}
function setFont(v,el){fetch('/?font_size='+v);var bs=el.parentNode.querySelectorAll('button');bs.forEach(function(b){b.classList.remove('on');});el.classList.add('on');}
function setColor(v,el){fetch('/?color='+v);el.parentNode.querySelectorAll('.color-swatch-btn').forEach(function(b){b.classList.remove('active');});el.classList.add('active');}
function updateDlrScrollControls(){
var lm=document.getElementById('listmode'),mode=lm?String(lm.value):'',classic=mode==='0',dlr=mode==='2',supported=classic||dlr;
var seg=document.getElementById('dlr-scroll-mode'),active=seg?seg.querySelector('button.on'):null,isCustom=!!(active&&active.textContent==='Custom'),isDisruptions=!!(active&&active.textContent==='Disruptions');
var delayEnabled=isDisruptions||(dlr&&isCustom);
var tr=document.getElementById('custom-scroll-text-row'),ti=document.getElementById('custom_scroll_text');
var dr=document.getElementById('dlr-scroll-delay-row'),di=document.getElementById('dlr_scroll_delay');
var pr=document.getElementById('custom-scroll-position-row'),pi=document.getElementById('custom_scroll_position');
var sr=document.getElementById('custom-scroll-show-row');
if(seg)seg.parentNode.style.display=supported?'':'none';
if(sr)sr.style.display='none';
if(tr)tr.style.opacity=(!supported||isCustom)?'1':'.35';
if(dr){dr.style.display=dlr?'':'none';dr.style.opacity=delayEnabled?'1':'.35';}
if(pr){pr.style.display=classic?'':'none';pr.style.opacity=isCustom?'1':'.35';}
if(ti)ti.disabled=supported&&!isCustom;
if(di)di.disabled=supported&&!delayEnabled;
if(pi)pi.disabled=classic&&!isCustom;
}
function setDlrScrollMode(v,el){
fetch('/?dlr_scroll_content='+encodeURIComponent(v));
var p=el.parentNode;if(p)p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
el.classList.add('on');updateDlrScrollControls();
}
function setListLineDisplay(v,el){
fetch('/?list_line_display='+encodeURIComponent(v));
var p=el.parentNode;if(p)p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
el.classList.add('on');
}
function setNightBusHighlight(v,el){
fetch('/?night_bus_highlight='+encodeURIComponent(v));
var p=el.parentNode;if(p)p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
el.classList.add('on');
}
function setNightBusHighlightUI(v){
var seg=document.getElementById('night-bus-highlight');if(!seg)return;
seg.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
var b=seg.querySelector('button[data-v="'+String(v)+'"]');if(b)b.classList.add('on');
}
function applyButtonViewLock(v){
var lm=document.getElementById('listmode');
if(lm){
var combined=document.getElementById('station-selection-mode');
var cb=combined&&combined.querySelector('button.on');
var combinedLocked=!!(cb&&cb.textContent==='Combined list');
var locked=combinedLocked;
lm.disabled=locked;
lm.style.opacity=locked?'.35':'1';
}
}
function setButtonMode(v,el){
fetch('/?button_mode='+encodeURIComponent(v)).then(function(r){
if(!r.ok)return;
var p=el.parentNode;if(p)p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
el.classList.add('on');
applyButtonViewLock(v);
});
}
function setLongButtonMode(v,el){
fetch('/?long_button_mode='+encodeURIComponent(v)).then(function(r){
if(!r.ok)return;
var p=el.parentNode;if(p)p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});
el.classList.add('on');
});
}
document.querySelectorAll('[data-u],[data-p]').forEach(function(el){
el.addEventListener(el.dataset.e||'click',function(ev){
var u=el.dataset.u;
if(!u){var v=ev.target.value.replace(/#/g,'%23');if(el.dataset.enc)v=encodeURIComponent(v);u='/?'+el.dataset.p+'='+v;}
fetch(u,{method:'GET'});
if(el.id==='BUS'){var nbr=document.getElementById('night-buses-row'),sl=document.getElementById('slsection');if(nbr)nbr.style.display=(ev.target.checked&&sl&&sl.style.display!=='none')?'':'none';}
if(el.id==='listmode'){var mode=String(ev.target.value),classic=(mode==='0'),list=(mode==='1'),dlr=(mode==='2');var cs=document.getElementById('custom-scroll-section');if(cs)cs.style.display=(classic||dlr)?'':'none';var cp=document.getElementById('custom-scroll-position-row');if(cp)cp.style.display=classic?'':'none';var cps=document.getElementById('custom-scroll-position-separator');if(cps)cps.style.display=classic?'':'none';var dr=document.getElementById('dlr-scroll-delay-row'),di=document.getElementById('dlr_scroll_delay');if(dr)dr.style.display=dlr?'':'none';if(dlr&&di)di.value='15';var ds=document.getElementById('disruption-msg-section');if(ds)ds.style.display='none';var ss=document.getElementById('classic-scroll-speed-section');if(ss)ss.style.display=classic?'':'none';var cc=document.getElementById('clock-list-section');if(cc)cc.style.display=(list||dlr)?'':'none';var le=document.getElementById('clock-list-extra');if(le)le.style.display=list?'':'none';var lcs=document.getElementById('clock-list-color-separator');if(lcs)lcs.style.display=list?'':'none';var md=document.getElementById('maxdest');if(md){if(dlr){md.value='3';md.disabled=true;}else if(list){md.value='4';md.disabled=true;}else{md.value='3';md.disabled=false;}}var vc=document.getElementById('view-colour-section');if(vc)vc.style.display=(list||dlr)?'':'none';var lc=document.getElementById('LISTCOLOR'),lt=document.getElementById('LISTCOLOR_TIME'),ct=document.getElementById('clocktime'),lds=document.getElementById('list-line-display');if(list){if(lc)lc.checked=true;if(lt)lt.checked=true;if(ct)ct.value='0';setNightBusHighlightUI(0);if(lds){lds.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});var b=lds.querySelector('button[data-v="1"]');if(b)b.classList.add('on');}}else if(dlr){if(lc)lc.checked=false;if(lt)lt.checked=false;if(ct)ct.value='2';setNightBusHighlightUI(1);if(lds){lds.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});var b=lds.querySelector('button[data-v="0"]');if(b)b.classList.add('on');}}else{if(ct)ct.value='0';}updateDlrScrollControls();}
});});
updateDlrScrollControls();
applyButtonViewLock({BUTTON_MODE_VALUE});
</script>
</form></div></body></html>"""

# Pre-split template at import time: list of (text_fragment, placeholder_key)
_PARTS = []
_tpl_pos = 0
_tpl_last = 0
while _tpl_pos < len(PAGE_TPL):
    _i = PAGE_TPL.find('{', _tpl_pos)
    if _i < 0: break
    _j = PAGE_TPL.find('}', _i + 1)
    if _j < 0: break
    _k = PAGE_TPL[_i+1:_j]
    _ok = len(_k) > 0
    if _ok:
        for _c in _k:
            if _c != '_' and not ('A' <= _c <= 'Z'):
                _ok = False
                break
    if _ok:
        _PARTS.append((PAGE_TPL[_tpl_last:_i], _k))
        _tpl_last = _j + 1
        _tpl_pos = _j + 1
    else:
        _tpl_pos = _i + 1
_PARTS.append((PAGE_TPL[_tpl_last:], ""))


def html():
    import varinit, functions
    num = varinit.screen_selector
    s = varinit.settings
    stn = s["stations"][num]
    lg = s["language"]
    T = language[lg]["settings"]
    D = language[lg]["display"]
    connected = functions.wifi.radio.connected
    co = stn["country"].lower()
    op_code = stn["operator"].upper()
    op = op_code
    for _op_code, _op_label in country_and_operators.get(co, []):
        if _op_code == stn["operator"].lower():
            op = _op_label
            break
    if not op: op = T["operator"]
    ip = str(functions.wifi.radio.ipv4_address) if connected else "OFFLINE"
    if_long = varinit.if_long

    # ssid options (populated by a /checknet scan; always includes the current ssid)
    _p = ["<option value='", str(s["ssid"]), "' selected>", str(s["ssid"]), "</option>"]
    if hasattr(varinit, "netlist"):
        for n in varinit.netlist:
            _ns = str(n)
            _p.append("<option value='" + _ns + "'>" + _ns + "</option>")
    ssid_opt = "".join(_p)

    # network fields disabled once connected, unless a scan is in progress
    net_dis = "disabled" if connected and not (hasattr(varinit, "checknet") and varinit.checknet) else ""

    # dns section (hidden unless the on-device /dns route has been hit). Closes
    # the page's main form early and opens its own, isolated one, so this
    # submit only posts ip/netmask/gateway/dns to /setdns, not every other
    # setting on the page too.
    dns_html = ""
    if getattr(varinit, "dns", False):
        dns_html = ''.join([
            '</form>',
            '<div class="section-title" style="margin-top:12px">DNS</div>',
            '<form action="/setdns" method="POST"><table>',
            '<tr><td><label>IP</label></td><td><input type="text" id="ip" class="form-control" name="ip" required></td></tr>',
            '<tr><td><label>Netmask</label></td><td><input type="text" id="netmask" class="form-control" name="netmask" required></td></tr>',
            '<tr><td><label>Gateway</label></td><td><input type="text" id="gateway" class="form-control" name="gateway" required></td></tr>',
            '<tr><td><label>DNS (', T["not_required"], ')</label></td><td><input type="text" id="dns_input" class="form-control" name="dns"></td></tr>',
            '</table>',
            '<div class="action-row" style="margin-top:8px">',
            '<button type="submit" class="btn btn-sm">', T["save"], '</button>',
            '<button type="button" class="btn btn-sm btn-danger" onclick="location.href=\'/setdns?clear=true\'">', T["clear"], '</button>',
            '</div></form>'])

    # country flag
    country_flag = _flag_img(co)

    # flag grid + operator data
    _p = ["<div class='dd-grid'>"]
    for c in country_and_operators:
        _p.append(_flag_img(c).replace("<img ", "<img onclick=\"pickC('" + c + "')\" data-c='" + c + "' "))
    _p.append("</div><div class='dd-ops' id='ddops'></div>")
    combined_list = "".join(_p)

    # operator data JSON for client-side
    import json
    ops_json = "".join(c if ord(c) < 128 else "\\u{:04x}".format(ord(c)) for c in json.dumps(country_and_operators))

    # station settings JSON for client-side screen switching
    _stn_data = {}
    _ns = 2 if if_long == 128 else 3
    for _i in range(1, _ns + 1):
        _si = str(_i)
        _st = s["stations"][_si]
        _stn_data[_si] = {"op": _st["operator"], "co": _st["country"],
            "ms": _st["mystation"],
            "M": int(_st["METRO"]), "B": int(_st["BUS"]),
            "T": int(_st["TRAIN"]), "R": int(_st["TRAM"]),
            "S": int(_st["SHIP"]),
            "r": int(_st["red"]), "g": int(_st["green"]), "b": int(_st["blue"]),
            "bo": int(_st["buses_option"]),
            "of": int(_st["offset"]), "di": int(_st["direction"])}
    stn_json = json.dumps(_stn_data)

    # Station selection selector. Mode 1 maps to the legacy multiple-stop/combined-list logic.
    # Mode 2 is intentionally reserved for the future true Multiple mode and currently behaves like Single.
    _station_selection_mode = int(s.get("station_selection_mode", 1 if int(s.get("multiple", 0)) else 0))
    if _station_selection_mode not in (0, 1, 2):
        _station_selection_mode = 1 if int(s.get("multiple", 0)) else 0
    _combined_station_mode = _station_selection_mode == 1
    station_selection_html = ''.join([
        '<div style="margin-top:10px">',
        '<span class="seg" id="station-selection-mode" style="width:100%">',
        '<button type="button" onclick="setStationSelectionMode(0,this)" class="', ("on" if _station_selection_mode == 0 else ""), '">Single</button>',
        '<button type="button" onclick="setStationSelectionMode(1,this)" class="', ("on" if _station_selection_mode == 1 else ""), '">Combined list</button>',
        '<button type="button" disabled style="opacity:.35;cursor:not-allowed;pointer-events:none;" title="Not available yet">Multiple</button>',
        '</span></div>'
    ])

    # screen buttons (used both for wide side-by-side lists and XS merged list stop selection)
    screen_btns = ""
    screen_btn_disp = ""
    if _station_selection_mode != 1:
        screen_btn_disp = "visibility:hidden;"
    ns = 2 if if_long == 128 else 3
    _p = []
    for i in range(1, ns + 1):
        _si = str(i)
        _cls = "scr-btn act" if _si == str(num) else "scr-btn"
        _p.append("<button class='" + _cls + "' type='button' title='Edit station " + _si + "' onclick=\"pickScr(" + _si + ")\">"+_si+"</button>")
    screen_btns = "".join(_p)

    # search disable
    search_dis = "" if connected else "disabled"
    station_ph = T["not_connected"] if not connected else stn["mystation"]

    # results
    result_dis = "disabled"
    result_style = ""
    if varinit.results:
        result_dis = ""
        result_style = "style='border-color:#ff6060;animation:guide-pulse 2.5s ease-in-out infinite'"

    # maxdest options. List and DLR have fixed physical row counts.
    _view_mode = int(s.get("listmode", 0))
    _maxdest_value = 5 if _combined_station_mode else (3 if _view_mode == 2 else (4 if _view_mode == 1 else s["maxdest"]))
    _p = []
    for i in range(1, 21):
        _p.append(_opt(i, _maxdest_value, str(i)))
    maxdest_opt = "".join(_p)
    maxdest_disabled = " disabled" if _combined_station_mode or _view_mode in (1, 2) else ""

    # metro section
    metro_html = _chk("METRO", stn["METRO"], "/?type=metro", "Metro")


        

    # SL-specific controls. Keep the original Night buses only filter in the
    # traffic-type card, while red highlighting lives in the List/DLR colour submenu.
    rc = " checked" if int(stn["red"]) else ""
    gc = " checked" if int(stn["green"]) else ""
    bc = " checked" if int(stn["blue"]) else ""
    sl_disp = "" if op_code == "SL" else "display:none;"
    _night_bus_show = "" if op_code == "SL" and int(stn["BUS"]) else "display:none;"
    night_bus_filter_html = '<div id="night-buses-row" style="' + _night_bus_show + '">' + _chk("night_buses", stn["buses_option"], "/?buses_option=1", T["only_nightbuses"]) + '</div>'
    _night_bus_highlight_mode = int(s.get("night_bus_highlight", 0))
    night_bus_highlight_html = ''.join([
        '<div style="margin-top:10px"><label class="control-label" style="margin-bottom:6px">', T["highlight_nightbuses"], '</label>',
        '<span class="seg" id="night-bus-highlight" style="width:100%">',
        '<button type="button" data-v="0" onclick="setNightBusHighlight(0,this)" class="', ("on" if _night_bus_highlight_mode == 0 else ""), '">Off</button>',
        '<button type="button" data-v="2" onclick="setNightBusHighlight(2,this)" class="', ("on" if _night_bus_highlight_mode == 2 else ""), '">On</button>',
        '<button type="button" data-v="1" onclick="setNightBusHighlight(1,this)" class="', ("on" if _night_bus_highlight_mode == 1 else ""), '">Mixed Traffic</button>',
        '</span></div>'
    ])
    devs_html = _chk("show_msgs", s["show_msgs"], "/?show_msgs=1", T["t_info"])
    _devs_show = "display:none;"
    devs_html = '<div id="disruption-msg-section" style="' + _devs_show + '"><div style="border-top:1px solid var(--border);margin:0"></div>' + devs_html + '</div>' 
    sl_section = ''.join(['<div id="slsection" style="', sl_disp, ';margin-top:10px">',
        '<label class="control-label" style="margin-bottom:6px">Metro line filter</label>',
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">',
        '<input type="checkbox" class="btn-check" id="r" name="red" data-u="/?line=red"', rc, '>',
        '<label class="line-chip" for="r"><span class="dot" style="background:#dc2626"></span>Red</label>',
        '<input type="checkbox" class="btn-check" id="g" name="green" data-u="/?line=green"', gc, '>',
        '<label class="line-chip" for="g"><span class="dot" style="background:#16a34a"></span>Green</label>',
        '<input type="checkbox" class="btn-check" id="b" name="blue" data-u="/?line=blue"', bc, '>',
        '<label class="line-chip" for="b"><span class="dot" style="background:#2563eb"></span>Blue</label>',
        '</div>', night_bus_filter_html, '</div>',])

    
    disruptions = devs_html if op_code in ["VT"] else ""


    # bus section
    bus_html = ""
    if op_code != "SJ":
        bus_html = _chk("BUS", stn["BUS"], "/?type=bus", T["buses"])

    # train
    train_html = _chk("TRAIN", stn["TRAIN"], "/?type=train", T["trains"])

    # tram
    tram_html = ""
    if op_code != "SJ":
        tram_html = _chk("TRAM", stn["TRAM"], "/?type=tram", T["trams"])

    # ship
    ship_html = ""
    if op_code != "SJ":
        ship_html = _chk("SHIP", stn["SHIP"], "/?type=ship", T["ships"])

    # offset options
    _p = []
    for i in range(0, 31):
        _p.append(_opt(i, stn["offset"], str(i) + " min"))
    offset_opt = "".join(_p)

    # direction
    dirs = [D["north_south"], D["north"], D["south"]]
    _p = ['<label class="control-label" for="direction">', T["direction"], '</label><select id="direction" name="direction" class="form-control" data-p="direction" data-e="change">']
    for i in range(3):
        _p.append(_opt(i, stn["direction"], dirs[i]))
    _p.append("</select>")
    dir_html = "".join(_p)

    # Scroll speed belongs to the View card and is only relevant to SL Classic.
    scroll_html = ""
    if if_long == 128:
        _scroll_show = "" if not int(s.get("listmode", 0)) else "display:none;"
        scroll_html = ''.join([
            '<div id="classic-scroll-speed-section" style="', _scroll_show, '">',
            '<div style="border-top:1px solid var(--border);margin:10px 0 0"></div>',
            '<div class="toggle-row"><label for="scroll" class="toggle-label">', T["scroll"], '</label>',
            '<select id="scroll" name="scroll" class="form-control" ',
            'style="width:auto;min-width:165px;margin-left:12px;display:inline-block" data-p="scroll" data-e="change">',
            _opt(0, s["scroll"], "Normal"), _opt(1, s["scroll"], T["low"]),
            '</select></div></div>'
        ])

    # display mode
    listmode_html = ""
    if if_long > 64 and varinit.display.height <= 32:
        listmode_html = ''.join([
            '<div class="col"><label for="listmode">View</label>',
            '<select id="listmode" name="listmode" class="form-control" data-p="listmode" data-e="change"' + (" disabled style=\"opacity:.35\"" if _combined_station_mode else "") + '>',
            _opt(0, s["listmode"], "SL Classic"),
            _opt(1, s["listmode"], "SL List"),
            _opt(2, s["listmode"], "TfL DLR"),
            '</select></div>'
        ])

    # SL Classic custom scroll message. Kept in the DOM so changing the view
    # selector can show/hide it immediately without reloading the page.
    _cs_show = "" if int(s.get("listmode", 0)) in (0, 2) else "display:none;"
    _cs_pos_show = "" if int(s.get("listmode", 0)) == 0 else "display:none;"
    _cs_checked = " checked" if int(s.get("custom_scroll_show", 0)) else ""
    _cs_text = str(s.get("custom_scroll_text", ""))
    _cs_text = _cs_text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    _scroll_content = "custom" if int(s.get("custom_scroll_show", 0)) else ("disruptions" if int(s.get("show_msgs", 0)) else "none")
    _scroll_custom_disabled = "" if _scroll_content == "custom" else " disabled"
    _scroll_custom_opacity = "1" if _scroll_content == "custom" else ".35"
    _view_mode_now = int(s.get("listmode", 0))
    _scroll_delay_enabled = (_scroll_content == "disruptions" or (_view_mode_now == 2 and _scroll_content == "custom"))
    _scroll_delay_disabled = "" if _scroll_delay_enabled else " disabled"
    _scroll_delay_opacity = "1" if _scroll_delay_enabled else ".35"
    custom_scroll_html = ''.join([
        '<div id="custom-scroll-section" style="', _cs_show, '">',
        '<div style="border-top:1px solid var(--border);margin:10px 0"></div>',
        '<details><summary>&#9998; Scroll Text</summary>',

        # Classic + DLR three-way content selector, using the official MatrixBOX .seg control.
        '<div id="dlr-scroll-mode-row" style="', ("" if int(s.get("listmode", 0)) in (0, 2) else "display:none;"), 'margin-bottom:10px">',
        '<span class="seg" id="dlr-scroll-mode" style="width:100%">',
        '<button type="button" onclick="setDlrScrollMode(\'none\',this)" class="', ("on" if _scroll_content == "none" else ""), '">None</button>',
        '<button type="button" onclick="setDlrScrollMode(\'disruptions\',this)" class="', ("on" if _scroll_content == "disruptions" else ""), '">Disruptions</button>',
        '<button type="button" onclick="setDlrScrollMode(\'custom\',this)" class="', ("on" if _scroll_content == "custom" else ""), '">Custom</button>',
        '</span></div>',

        # Text field is shared with Classic, but DLR grays/disables it unless Custom is selected.
        '<div id="custom-scroll-text-row" style="opacity:', (_scroll_custom_opacity if int(s.get("listmode", 0)) in (0, 2) else "1"), '">',
        '<label for="custom_scroll_text"><b>Text</b></label>',
        '<input type="text" id="custom_scroll_text" class="form-control" style="margin-top:5px" value="', _cs_text, '" ',
        'placeholder="Enter custom message" data-p="custom_scroll_text" data-e="blur" data-enc="1"',
        (_scroll_custom_disabled if int(s.get("listmode", 0)) in (0, 2) else ""), '></div>',

        '<div style="border-top:1px solid var(--border);margin:10px 0 0"></div>',
        '<div id="dlr-scroll-delay-row" class="toggle-row" style="border-bottom:none;', ("" if int(s.get("listmode", 0)) == 2 else "display:none;"), ';opacity:', _scroll_delay_opacity, '">',
        '<label for="dlr_scroll_delay" class="toggle-label">Message interval</label>',
        '<div style="display:flex;align-items:center;gap:7px"><input type="number" id="dlr_scroll_delay" class="form-control" min="1" max="300" step="1" value="', str(s.get("dlr_scroll_delay", 15)), '" data-p="dlr_scroll_delay" data-e="change" style="width:82px"',
        _scroll_delay_disabled, '><span style="color:var(--muted)">sec</span></div></div>',

        # Classic-only placement and master toggle remain untouched.
        '<div id="custom-scroll-position-separator" style="border-top:1px solid var(--border);margin:0;', _cs_pos_show, '"></div>',
        '<div id="custom-scroll-position-row" class="toggle-row" style="border-bottom:none;', _cs_pos_show, ';opacity:', (_scroll_custom_opacity if int(s.get("listmode", 0)) == 0 else "1"), '"><label for="custom_scroll_position" class="toggle-label">Position</label>',
        '<select id="custom_scroll_position" name="custom_scroll_position" class="form-control" ',
        'style="width:auto;min-width:165px;margin-left:12px;display:inline-block" data-p="custom_scroll_position" data-e="change"',
        (_scroll_custom_disabled if int(s.get("listmode", 0)) == 0 else ""), '>',
        _opt(0, s.get("custom_scroll_position", 0), "After departures"),
        _opt(1, s.get("custom_scroll_position", 0), "Before departures"),
        _opt(2, s.get("custom_scroll_position", 0), "After first departure"),
        '</select></div>',
        '<div id="custom-scroll-show-row" style="display:none;">',
        '<div style="border-top:1px solid var(--border);margin:0"></div>',
        '<div class="toggle-row" style="border-bottom:none"><label for="CUSTOM_SCROLL_SHOW" class="toggle-label">Show custom scroll text</label>',
        '<label class="switch"><input type="checkbox" id="CUSTOM_SCROLL_SHOW" data-u="/?custom_scroll_show=switch"', _cs_checked, '><span class="slider"></span></label></div>',
        '</div>',
        '</details></div>'
    ])

    # departure time display mode: 0 dynamic, 1 always time, 2 always countdown
    # This is a general departure option, so it lives in the options card above View.
    clock_html = ''.join([
        '<div class="col">',
        '<label for="clocktime">', T["time_display_type"], '</label>',
        '<select id="clocktime" name="clocktime" class="form-control" data-p="clocktime" data-e="change">',
        _opt(0, s.get("clocktime", 0), T["time_display_dynamic"]),
        _opt(1, s.get("clocktime", 0), T["time_display_time"]),
        _opt(2, s.get("clocktime", 0), T["time_display_countdown"]),
        '</select></div>'
    ])

    # sleep
    sleep_html = _chk("sleep", s["sleep"], "/?sleep=1", T["turn_off"])

    _button_mode = int(s.get("button_mode", 0))
    _long_button_mode = int(s.get("long_button_mode", 2))
    if _long_button_mode not in (0, 1, 2):
        _long_button_mode = 2

    _short_locked = _station_selection_mode == 2

    # Multiple mode reserves long-press Switch view for future station logic.
    # Toggle screen is forced/default there.
    if _station_selection_mode == 2:
        _long_button_mode = 0

    button_mode_html = ''.join([
        '<div style="margin:12px 0 10px 0">',
        '<label class="control-label" style="margin-bottom:6px">Short button press</label>',
        '<span class="seg" id="button-behaviour" style="width:100%;', ("opacity:.35;pointer-events:none;" if _short_locked else ""), '">',
        '<button type="button" data-v="0" onclick="setButtonMode(0,this)" class="', ("on" if _button_mode == 0 else ""), '">Toggle screen</button>',
        '<button type="button" data-v="1" onclick="setButtonMode(1,this)" class="', ("on" if _button_mode == 1 else ""), '">Switch view</button>',
        '</span>',
        '</div>',
        '<div style="margin:10px 0 14px 0">',
        '<label class="control-label" style="margin-bottom:6px">Long button press</label>',
        '<span class="seg" id="long-button-behaviour" style="width:100%">',
        '<button type="button" data-v="0" onclick="setLongButtonMode(0,this)" class="', ("on" if _long_button_mode == 0 else ""), '">Toggle screen</button>',
        '<button type="button" data-v="1" onclick="setLongButtonMode(1,this)"',
        (" disabled style=\"opacity:.35;cursor:not-allowed\"" if _station_selection_mode == 2 else ""),
        ' class="', ("on" if _long_button_mode == 1 else ""), '">Switch view</button>',
        '<button type="button" data-v="2" onclick="setLongButtonMode(2,this)" class="', ("on" if _long_button_mode == 2 else ""), '">Exit app</button>',
        '</span>',
        '</div>',
        '<div style="border-top:1px solid var(--border);margin:0 0 12px 0"></div>'
    ])

    # show station
    show_stn_html = _chk("show_my_station", s["show_my_station"], "/?show_station=1", T["show_station"])

    # LED tone swatches (128-wide boards also get a white option)
    _color_cur = s.get("color", 1)
    def _swatch(value, color, title):
        active = " active" if int(_color_cur) == value else ""
        return ('<button type="button" class="color-swatch-btn' + active + '" style="background:' + color
                + '" title="' + title + '" onclick="setColor(' + str(value) + ',this)"></button>')
    tone_html = _swatch(0, "#e09d00", "Orange") + _swatch(1, "#f5d105", "Yellow")
    if if_long == 128:
        tone_html += _swatch(2, "#ffffff", "White")

    # font size segmented control (mini / small / large)
    _fs = "mini" if s["mini"] else ("large" if s.get("large_list", 0) else "small")
    font_size_html = (
        '<span class="seg">'
        '<button type="button" onclick="setFont(\'mini\',this)" class="' + ("on" if _fs == "mini" else "") + '">mini</button>'
        '<button type="button" onclick="setFont(\'small\',this)" class="' + ("on" if _fs == "small" else "") + '">small</button>'
        '<button type="button" onclick="setFont(\'large\',this)" class="' + ("on" if _fs == "large" else "") + '">large</button>'
        '</span>'
    )
    xs_line_id_chk = _chk("XS_LINE_ID", s.get("xs_line_id", 0), "/?xs_line_id=switch", "Show line ID") if if_long <= 64 else ""
    _clock_list_extra_show = "" if int(s.get("listmode", 0)) == 1 else "display:none;"
    clock_row_html = (
        _chk("SHOW_CLOCK_ROW", s.get("show_clock_row", 0), "/?show_clock_row=switch", "Show clock row")
        + '<div id="clock-list-extra" style="' + _clock_list_extra_show + '">'
        + _chk("CLOCK_ROW_DATE", s.get("clock_row_date", 0), "/?clock_row_date=switch", "Include date")
        + '<table>'
        '<tr><td><b>Clock: position</b></td><td><select id="clock_row_position" class="form-control" style="width:130px;display:inline" data-p="clock_row_position" data-e="change">'
        + _opt("bottom", s.get("clock_row_position", "bottom"), "Bottom row")
        + _opt("top", s.get("clock_row_position", "bottom"), "Top row")
        + '</select></td></tr>'
        '<tr><td><b>Clock: align</b></td><td><select id="clock_row_align" class="form-control" style="width:130px;display:inline" data-p="clock_row_align" data-e="change"' + (" disabled" if _combined_station_mode else "") + '>'
        + _opt("left", "left" if _combined_station_mode else s.get("clock_row_align", "left"), "Left")
        + _opt("center", "left" if _combined_station_mode else s.get("clock_row_align", "left"), "Center")
        + _opt("right", "left" if _combined_station_mode else s.get("clock_row_align", "left"), "Right")
        + '</select></td></tr>'
        + '</table></div>'
        + '<div id="clock-list-color-separator" style="border-top:1px solid var(--border);margin:10px 0;' + ("" if int(s.get("listmode", 0)) == 1 else "display:none;") + '"></div>'
        + '<table><tr><td><b>Clock: color</b></td><td><select id="clock_row_color" class="form-control" style="width:130px;display:inline" data-p="clock_row_color" data-e="change">'
        + _opt("white", s.get("clock_row_color", "white"), "White")
        + _opt("yellow", s.get("clock_row_color", "white"), "Yellow / amber")
        + _opt("red", s.get("clock_row_color", "white"), "Red")
        + _opt("green", s.get("clock_row_color", "white"), "Green")
        + _opt("blue", s.get("clock_row_color", "white"), "Blue")
        + '</select></td></tr></table>'
    )
    # Clock controls live inside the View card for SL List and TfL DLR.
    # DLR deliberately hides date/position/alignment: its clock is fixed HH:MM at bottom-right.
    _clock_show = "" if int(s.get("listmode", 0)) in (1, 2) else "display:none;"
    clock_inline_html = ''.join([
        '<div id="clock-list-section" style="', _clock_show, '">',
        '<div style="border-top:1px solid var(--border);margin:10px 0"></div>',
        '<details><summary>&#128336; ', T["clock"], '</summary>',
        clock_row_html,
        '</details></div>'
    ])

    # dest_scroll
    dest_scroll_html = _chk("DEST_SCROLL", s.get("dest_scroll", 0), "/?dest_scroll=switch", "Scroll long destination names")
    # Combined list standard: show both colour toggles ON (and disabled below).
    _listcolor_value = 1 if _combined_station_mode else s["listcolor"]
    _listcolor_time_value = 1 if _combined_station_mode else s.get("listcolor_time", 0)
    listcolor_html = _chk("LISTCOLOR", _listcolor_value, "/?listcolor=switch", T["list_colors_line"])
    if _combined_station_mode:
        listcolor_html = listcolor_html.replace('<div class="toggle-row">', '<div class="toggle-row" id="listcolor-row" style="opacity:.35">', 1).replace('id="LISTCOLOR"', 'id="LISTCOLOR" disabled', 1)
    else:
        listcolor_html = listcolor_html.replace('<div class="toggle-row">', '<div class="toggle-row" id="listcolor-row">', 1)
    listcolor_time_html = _chk("LISTCOLOR_TIME", _listcolor_time_value, "/?listcolor_time=switch", T["list_colors_time"])
    if _combined_station_mode:
        listcolor_time_html = listcolor_time_html.replace('<div class="toggle-row">', '<div class="toggle-row" id="listcolor-time-row" style="opacity:.35">', 1).replace('id="LISTCOLOR_TIME"', 'id="LISTCOLOR_TIME" disabled', 1)
    else:
        listcolor_time_html = listcolor_time_html.replace('<div class="toggle-row">', '<div class="toggle-row" id="listcolor-time-row">', 1)
    _line_display_default = 0 if int(s.get("listmode", 0)) == 2 else 1
    _line_display = int(s.get("list_line_display", _line_display_default))
    line_display_html = ''.join([
        '<div style="margin-bottom:10px;opacity:', ('.35' if _combined_station_mode else '1'), '"><label class="control-label" style="margin-bottom:6px">Line display</label>',
        '<span class="seg" id="list-line-display" style="width:100%">',
        '<button type="button" data-v="0" onclick="setListLineDisplay(0,this)"', (' disabled' if _combined_station_mode else ''), ' class="', ("on" if _line_display == 0 else ""), '">Departure order</button>',
        '<button type="button" data-v="1" onclick="setListLineDisplay(1,this)"', (' disabled' if _combined_station_mode else ''), ' class="', ("on" if _line_display == 1 else ""), '">Line number</button>',
        '</span></div>',
        '<div style="border-top:1px solid var(--border);margin:10px 0"></div>',
    ])

    # View-specific colour controls: only relevant to SL List and TfL DLR.
    _view_colour_show = "" if int(s.get("listmode", 0)) in (1, 2) else "display:none;"
    view_color_toggles = ''.join([
        '<div id="view-colour-section" style="', _view_colour_show, '">',
        '<div style="border-top:1px solid var(--border);margin:10px 0"></div>',
        '<details><summary>🎨 Line / Minute colour</summary>',
        line_display_html, listcolor_html, listcolor_time_html, night_bus_highlight_html,
        '</details></div>'
    ])

    # Connection-only advanced tools. Their backend routes already exist;
    # this merely restores the controls inside a collapsed subsection.
    connection_advanced = ''.join([
        '<details style="margin-top:12px"><summary>&#9881; ', T["advanced"], '</summary>',
        '<div style="margin-top:8px">',
        '<div class="toggle-row"><span class="toggle-label">', T["timer_title"].split(' - ')[0], '</span>',
        "<button type='button' class='btn btn-sm' onclick=\"location.href='/?timer=true'\">Open</button></div>",
        '<div class="toggle-row"><span class="toggle-label">', T["rotation"], '</span>',
        '<button type="button" class="btn btn-sm" data-u="/?rotate=true">', T["rotation"], '</button></div>',
        '<div class="toggle-row" style="border-bottom:none"><label for="wifi_power" class="toggle-label">', T["power"], '</label>',
        '<input type="number" id="wifi_power" class="form-control" min="7" max="20" step="1" value="', str(s.get("power", 20)), '" data-p="power" data-e="change" style="width:84px"></div>',
        '</div></details>'
    ])

    # Navbar lightbulb reflects the display's actual current visibility.
    led_off_cls = "" if functions.get_screen_state() else " led-off"
    sig_bars = _sig_bars(_rssi(functions))

    # build page using pre-split template (single pass, no scanning)
    _v = {
        "CSS": css, "TITLE": T["title"],
        "HEADER": T["title"],
        "LED_OFF_CLS": led_off_cls,
        "SIG_BARS": sig_bars,
        "IP_DISPLAY": ip,
        "T_CONNECTIONS": "Connections & Screen",
        "T_WIFI_LABEL": T["network"],
        "SSID_OPTIONS": ssid_opt,
        "NET_DIS": net_dis,
        "T_PASSWORD": T["password"],
        "T_CONNECT": T["connect"],
        "CONNECTION_ADVANCED": connection_advanced,
        "DNS_SECTION": dns_html,
        "T_NETWORK_LABEL": T["search"],
        "STATION_SELECTION_MODE": station_selection_html,
        "COUNTRY_FLAG": country_flag,
        "OPERATOR": op, "COMBINED_LIST": combined_list,
        "SCREEN_BUTTONS": screen_btns, "SCREEN_BTN_DISP": screen_btn_disp,
        "STATION_PH": station_ph, "SEARCH_DIS": search_dis,
        "T_SEARCH": T["_search"],
        "OPBTN_PULSE": 'style="animation:guide-pulse 2.5s ease-in-out infinite"' if (not co or not stn["operator"]) else "",
        "SSTRING_PULSE": 'style="animation:guide-pulse 2.5s ease-in-out infinite"' if (co and stn["operator"] and connected and not stn["mystation"]) else "",
        "RESULTS": varinit.results, "RESULT_DIS": result_dis,
        "RESULT_STYLE": result_style,
        "T_NO_DEPARTURES": T["no_departures"],
        "MAXDEST_OPTIONS": maxdest_opt, "MAXDEST_DISABLED": maxdest_disabled,
        "METRO_SECTION": metro_html, "SL_SECTION": sl_section,
        "BUS_SECTION": bus_html,
        "TRAIN_CHK": train_html, "TRAM_SECTION": tram_html,
        "SHIP_SECTION": ship_html,
        "T_HIDE_DEPARTURES": T["hide_departures"],
        "OFFSET_OPTIONS": offset_opt,
        "DIRECTION_SECTION": dir_html,
        "SCROLL_SECTION": scroll_html,
        "T_TRAFFIC_TYPES": T["traffic_types"],
        "LISTMODE_CHK": listmode_html, "VIEW_COLOR_TOGGLES": view_color_toggles, "CUSTOM_SCROLL_HTML": custom_scroll_html, "CLOCKTIME_CHK": clock_html,
        "CLOCK_INLINE_HTML": clock_inline_html,
        "DEVIATIONS_SECTION": devs_html,
        "SLEEP_CHK": sleep_html, "BUTTON_MODE_CHK": button_mode_html, "BUTTON_MODE_VALUE": str(_button_mode), "SHOW_STATION_CHK": show_stn_html,
        "T_SAVE": T["save"],
        "T_ADVANCED": T["advanced"],
        "T_CLOCK": T["clock"],
        "T_TONE": T["tone"], "TONE_SWATCHES": tone_html,
        "XS_LINE_ID_CHK": xs_line_id_chk,
        "DEST_SCROLL_CHK": dest_scroll_html,
        "LISTCOLOR_CHK": listcolor_html,
        "LISTCOLOR_TIME_CHK": listcolor_time_html,
        "T_LINE_LENGTH": T["line_length"],
        "T_LINE_LENGTH_HELP": "Most line numbers are 1-2 characters, so this often looks the same until a line uses a longer code.",
        "LINE_LENGTH_VAL": str(s["line_length"]),
        "T_SHOW_LINES": T["show_lines"],
        "SHOW_LINES_VAL": ",".join(s["show_lines"]) if isinstance(s["show_lines"], list) else str(s["show_lines"]),
        "STRIP_DEST_VAL": ",".join(s.get("strip_dest", [])) if isinstance(s.get("strip_dest"), list) else str(s.get("strip_dest", "")),
        "T_NO_MORE_DEP": T["no_more_departures_label"],
        "NO_MORE_DEP_VAL": str(s["no_more_departures"]),
        "T_MINS": T["mins_label"],
        "MINS_VAL": str(s["mins"]),
        "OPS_JSON": ops_json, "STN_JSON": stn_json,
        
    }
    _out = []
    for _frag, _key in _PARTS:
        _out.append(_frag)
        if _key: _out.append(_v.get(_key, ""))
    return "".join(_out)


def timer(_language, timer):
    for i in timer:
        try: timer[i][1]
        except: timer[i] = ["00:00", "00:00"]
    T = language[_language]["settings"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rows = ""
    for day in days:
        label = T[day.lower()]
        did = day.lower()
        rows += ('<div class="form-row" style="align-items:center;margin-bottom:8px">'
                 '<div class="col" style="flex:0 0 90px;text-transform:capitalize;font-size:.85rem">' + label + '</div>'
                 '<div class="col"><input type="time" id="' + did + 'S" class="form-control" value="' + timer[day][0] + '"></div>'
                 '<div class="col"><input type="time" id="' + did + 'E" class="form-control" value="' + timer[day][1] + '"></div>'
                 '</div>'
                 '<script>(function(){var s=document.getElementById("' + did + 'S"),e=document.getElementById("' + did + 'E");'
                 'function send(){if(s.value&&e.value)fetch("/?set_timer=' + day + '&start="+encodeURIComponent(s.value+"to="+e.value),{method:"GET"})}'
                 's.addEventListener("change",send);e.addEventListener("change",send);})()</script>')
    body = ('<div class="card"><div class="section-title">' + T["timer_title"] + '</div>' + rows
            + '<button type="button" class="btn btn-full btn-ghost" onclick="location.href=\'/\'">' + T["return"] + '</button>'
            + '<button type="button" class="btn btn-full btn-danger" onclick="location.href=\'/?cleartimer=true\'">' + T["clear"] + '</button></div>')
    return ('<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1" charset="UTF-8">'
            '<title>' + T["timer_title"] + '</title><style>' + css + '</style></head>'
            '<body><nav class="navbar"><a class="nav-x" href="/" title="Back" style="margin-left:0">&#8592;</a>'
            '<span class="nav-title">' + T["timer_title"] + '</span></nav><div class="page">' + body + '</div></body></html>')
