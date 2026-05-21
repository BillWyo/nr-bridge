import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# ── Function bodies ────────────────────────────────────────────────────────────

FN_SCAN_MSG = """\
msg.payload = JSON.stringify({"msg":{"cmd":"scan","data":{"account_topic":"reserve"}}});
msg.ip   = "255.255.255.255";
msg.port = 4001;
return msg;"""

FN_PARSE_SCAN = """\
try {
    var d = JSON.parse(msg.payload);
    if (!d.msg || d.msg.cmd !== 'scan') return null;
    var info = d.msg.data;
    var devs = flow.get('govee_devices') || {};
    devs[info.device] = { ip: info.ip, sku: info.sku, device: info.device };
    flow.set('govee_devices', devs);
    node.status({fill:'green', shape:'dot', text: info.sku + ' @ ' + info.ip});
    msg.payload = devs;
    return msg;
} catch(e) {
    node.warn('Govee parse error: ' + e.message);
    return null;
}"""

FN_SEND_DEVICES = """\
// Expects: msg.govee_cmd     = {cmd:'...', data:{...}}
//          msg.govee_targets = 'all' | ['device-id', ...]
var devs = flow.get('govee_devices') || {};
var keys = Object.keys(devs);
if (!keys.length) { node.warn('No Govee devices found - run discovery first'); return null; }

var targets;
if (!msg.govee_targets || msg.govee_targets === 'all') {
    targets = Object.values(devs);
} else {
    var ids = Array.isArray(msg.govee_targets) ? msg.govee_targets : [msg.govee_targets];
    targets = ids.map(function(id) { return devs[id]; }).filter(Boolean);
}
if (!targets.length) { node.warn('No matching Govee devices'); return null; }

var msgs = targets.map(function(d) {
    return { payload: JSON.stringify({msg: msg.govee_cmd}), ip: d.ip, port: 4003 };
});
return [msgs];"""

FN_MQTT_CTRL = """\
// MQTT payload: {cmd, value|r,g,b|kelvin, devices:'all'|[ids]}
var p = msg.payload;
var gcmd;
switch (p.cmd) {
    case 'turn':       gcmd = {cmd:'turn',       data:{value: p.value ? 1 : 0}}; break;
    case 'brightness': gcmd = {cmd:'brightness',  data:{value: p.value}}; break;
    case 'color':      gcmd = {cmd:'colorwc',     data:{color:{r:p.r||0,g:p.g||0,b:p.b||0}, colorTemInKelvin:0}}; break;
    case 'colortemp':  gcmd = {cmd:'colorwc',     data:{color:{r:0,g:0,b:0}, colorTemInKelvin:p.kelvin||4000}}; break;
    default: node.warn('Unknown Govee cmd: ' + p.cmd); return null;
}
msg.govee_cmd     = gcmd;
msg.govee_targets = p.devices || 'all';
return msg;"""

FN_VISITOR_LIGHT = """\
// Doorbell / motion at front door → warm white
msg.govee_cmd     = {cmd:'colorwc', data:{color:{r:0,g:0,b:0}, colorTemInKelvin:3000}};
msg.govee_targets = 'all';
return msg;"""

FN_ALARM_LIGHT = """\
// Smoke / CO alert → solid red; clear → restore warm white
if (!msg.payload) return null;
if (msg.payload.alert === true) {
    msg.govee_cmd = {cmd:'colorwc', data:{color:{r:255,g:0,b:0}, colorTemInKelvin:0}};
} else {
    msg.govee_cmd = {cmd:'colorwc', data:{color:{r:0,g:0,b:0}, colorTemInKelvin:3000}};
}
msg.govee_targets = 'all';
return msg;"""

# ── Flow nodes ─────────────────────────────────────────────────────────────────

GOV_NODES = [
    # Flow tab
    {"id":"gov-flow","type":"tab","label":"Govee Lights",
     "disabled":False,"info":"Govee LAN API — 4 bulbs"},

    # ── Discovery ──────────────────────────────────────────────────────────────
    {"id":"gov-inject-scan","type":"inject","z":"gov-flow",
     "name":"Discover bulbs","props":[{"p":"payload"}],
     "repeat":"","crontab":"","once":False,
     "payload":"","payloadType":"date",
     "x":180,"y":80,"wires":[["gov-fn-scan-msg"]]},

    {"id":"gov-fn-scan-msg","type":"function","z":"gov-flow",
     "name":"build scan","func":FN_SCAN_MSG,"outputs":1,"noerr":0,
     "x":380,"y":80,"wires":[["gov-udp-out"]]},

    # UDP out — destination set by msg.ip / msg.port on each message
    {"id":"gov-udp-out","type":"udp out","z":"gov-flow",
     "name":"UDP send","addr":"255.255.255.255","iface":"","port":"4001",
     "ipv":"udp4","outport":"","base64":False,"multicast":"false",
     "x":760,"y":200,"wires":[]},

    # UDP in — Govee devices respond on port 4002
    {"id":"gov-udp-in","type":"udp in","z":"gov-flow",
     "name":"device responses","iface":"","port":"4002",
     "ipv":"udp4","multicast":"false","group":"","datatype":"utf8",
     "x":180,"y":160,"wires":[["gov-fn-parse-scan"]]},

    {"id":"gov-fn-parse-scan","type":"function","z":"gov-flow",
     "name":"parse + store","func":FN_PARSE_SCAN,"outputs":1,"noerr":0,
     "x":400,"y":160,"wires":[["gov-debug-devices"]]},

    {"id":"gov-debug-devices","type":"debug","z":"gov-flow",
     "name":"device map","active":True,"tosidebar":True,"console":False,
     "tostatus":True,"complete":"payload","targetType":"msg",
     "x":600,"y":160,"wires":[]},

    # ── Command router (shared by all control paths) ───────────────────────────
    {"id":"gov-fn-send","type":"function","z":"gov-flow",
     "name":"send to devices","func":FN_SEND_DEVICES,"outputs":1,"noerr":0,
     "x":580,"y":300,"wires":[["gov-udp-out"]]},

    # ── MQTT control interface ─────────────────────────────────────────────────
    # home/lights/set payload: {cmd, value|r,g,b|kelvin, devices:'all'|[ids]}
    {"id":"gov-mqtt-ctrl","type":"mqtt in","z":"gov-flow",
     "name":"home/lights/set","topic":"home/lights/set",
     "qos":"0","datatype":"json","broker":"his-broker",
     "nl":False,"rap":False,
     "x":180,"y":300,"wires":[["gov-fn-mqtt-ctrl"]]},

    {"id":"gov-fn-mqtt-ctrl","type":"function","z":"gov-flow",
     "name":"MQTT → Govee cmd","func":FN_MQTT_CTRL,"outputs":1,"noerr":0,
     "x":390,"y":300,"wires":[["gov-fn-send"]]},

    # ── HIS event wiring ───────────────────────────────────────────────────────
    {"id":"gov-mqtt-visitor","type":"mqtt in","z":"gov-flow",
     "name":"home/frontdoor/visitor","topic":"home/frontdoor/visitor",
     "qos":"0","datatype":"json","broker":"his-broker",
     "nl":False,"rap":False,
     "x":180,"y":380,"wires":[["gov-fn-visitor"]]},

    {"id":"gov-fn-visitor","type":"function","z":"gov-flow",
     "name":"visitor → warm white","func":FN_VISITOR_LIGHT,"outputs":1,"noerr":0,
     "x":400,"y":380,"wires":[["gov-fn-send"]]},

    {"id":"gov-mqtt-alarm","type":"mqtt in","z":"gov-flow",
     "name":"home/+/alarm","topic":"home/+/alarm",
     "qos":"1","datatype":"json","broker":"his-broker",
     "nl":False,"rap":False,
     "x":180,"y":440,"wires":[["gov-fn-alarm"]]},

    {"id":"gov-fn-alarm","type":"function","z":"gov-flow",
     "name":"alarm → red / clear → white","func":FN_ALARM_LIGHT,"outputs":1,"noerr":0,
     "x":400,"y":440,"wires":[["gov-fn-send"]]},
]

# ── Append and save ────────────────────────────────────────────────────────────
with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

flows.extend(GOV_NODES)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Added {len(GOV_NODES)} Govee nodes. Total: {len(flows)}')
