import json

FLOWS_PATH   = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'
PRESETS_FILE = r'C:\Users\johan\.node-red\projects\Home_PTRH\govee_presets.json'

# ── Function bodies ────────────────────────────────────────────────────────────

FN_APPLY_PRESET = """\
var name = msg.payload;
var devs    = flow.get('govee_devices') || {};
var nameMap = flow.get('govee_names')   || {};
if (!Object.keys(devs).length) { node.warn('Run discovery first'); return null; }

if (name === 'All Off') {
    var msgs = Object.values(devs).map(function(d) {
        return {payload:JSON.stringify({msg:{cmd:'turn',data:{value:0}}}), ip:d.ip, port:4003};
    });
    return [msgs];
}

var presets = flow.get('govee_presets') || {};
var preset  = presets[name];
if (!preset) { node.warn('Preset not found: ' + name); return null; }

var msgs = [];
Object.keys(preset).forEach(function(devName) {
    var state = preset[devName];
    var dev   = devs[nameMap[devName]];
    if (!dev) return;
    msgs.push({payload:JSON.stringify({msg:{cmd:'turn',      data:{value:state.onOff}}}),                                                            ip:dev.ip, port:4003});
    msgs.push({payload:JSON.stringify({msg:{cmd:'brightness', data:{value:state.brightness}}}),                                                       ip:dev.ip, port:4003});
    msgs.push({payload:JSON.stringify({msg:{cmd:'colorwc',    data:{color:state.color||{r:0,g:0,b:0}, colorTemInKelvin:state.colorTemInKelvin||0}}}), ip:dev.ip, port:4003});
});
return [msgs];"""

FN_ALL_BRIGHTNESS = """\
var devs = flow.get('govee_devices') || {};
var msgs = Object.values(devs).map(function(d) {
    return {payload:JSON.stringify({msg:{cmd:'brightness',data:{value:msg.payload}}}), ip:d.ip, port:4003};
});
return [msgs];"""

FN_ALL_COLORTEMP = """\
var devs = flow.get('govee_devices') || {};
var msgs = Object.values(devs).map(function(d) {
    return {payload:JSON.stringify({msg:{cmd:'colorwc',data:{color:{r:0,g:0,b:0},colorTemInKelvin:msg.payload}}}), ip:d.ip, port:4003};
});
return [msgs];"""

FN_SAVE_PRESET = """\
var name     = msg.payload;
var snapshot = flow.get('govee_snapshot') || {};
if (!Object.keys(snapshot).length) { node.warn('No snapshot - click Read state first'); return null; }
var presets  = flow.get('govee_presets') || {};
presets[name] = JSON.parse(JSON.stringify(snapshot));
flow.set('govee_presets', presets);
node.status({fill:'green', shape:'dot', text: name + ' saved'});
msg.payload  = JSON.stringify(presets, null, 2);
return msg;"""

FN_LOAD_PRESETS = """\
try {
    var presets = JSON.parse(msg.payload);
    flow.set('govee_presets', presets);
    node.status({fill:'green', shape:'dot', text: Object.keys(presets).length + ' presets loaded'});
} catch(e) {
    node.status({fill:'yellow', shape:'ring', text: 'no presets file yet'});
}
return null;"""

# ── Node definitions ───────────────────────────────────────────────────────────

NEW_NODES = [

    # ── Dashboard page ──────────────────────────────────────────────────────────
    {"id":"v2-page-govee","type":"ui-page","name":"Govee Lights",
     "ui":"v2-ui-base","path":"/govee","icon":"mdi-lightbulb",
     "layout":"notebook","theme":"8caffb684107c6b6","order":6},

    # Groups
    {"id":"v2-grp-govee-presets","type":"ui-group","name":"Presets",
     "page":"v2-page-govee","width":"12","height":"1","order":1,
     "showTitle":True,"className":"","visible":"true"},

    {"id":"v2-grp-govee-adjust","type":"ui-group","name":"Adjust",
     "page":"v2-page-govee","width":"12","height":"1","order":2,
     "showTitle":True,"className":"","visible":"true"},

    {"id":"v2-grp-govee-save","type":"ui-group","name":"Save Preset",
     "page":"v2-page-govee","width":"12","height":"1","order":3,
     "showTitle":True,"className":"","visible":"true"},

    # ── Preset buttons ──────────────────────────────────────────────────────────
    {"id":"v2-btn-evening","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-presets","name":"Evening","label":"Evening",
     "order":1,"width":"3","height":"2",
     "emitOnlyOnClick":True,"buttonColor":"#f5a623","textColor":"#000000","iconColor":"#000000",
     "enableClick":True,"enablePointerdown":False,
     "payload":"Evening","payloadType":"str","topic":"preset","topicType":"str",
     "x":200,"y":1100,"wires":[["gov-fn-apply-preset"]]},

    {"id":"v2-btn-bright","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-presets","name":"Bright","label":"Bright",
     "order":2,"width":"3","height":"2",
     "emitOnlyOnClick":True,"buttonColor":"#ffffff","textColor":"#000000","iconColor":"#000000",
     "enableClick":True,"enablePointerdown":False,
     "payload":"Bright","payloadType":"str","topic":"preset","topicType":"str",
     "x":200,"y":1160,"wires":[["gov-fn-apply-preset"]]},

    {"id":"v2-btn-movie","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-presets","name":"Movie","label":"Movie",
     "order":3,"width":"3","height":"2",
     "emitOnlyOnClick":True,"buttonColor":"#4a3580","textColor":"#ffffff","iconColor":"#ffffff",
     "enableClick":True,"enablePointerdown":False,
     "payload":"Movie","payloadType":"str","topic":"preset","topicType":"str",
     "x":200,"y":1220,"wires":[["gov-fn-apply-preset"]]},

    {"id":"v2-btn-alloff","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-presets","name":"All Off","label":"All Off",
     "order":4,"width":"3","height":"2",
     "emitOnlyOnClick":True,"buttonColor":"#333333","textColor":"#ffffff","iconColor":"#ffffff",
     "enableClick":True,"enablePointerdown":False,
     "payload":"All Off","payloadType":"str","topic":"preset","topicType":"str",
     "x":200,"y":1280,"wires":[["gov-fn-apply-preset"]]},

    # ── Apply preset function ───────────────────────────────────────────────────
    {"id":"gov-fn-apply-preset","type":"function","z":"gov-flow",
     "name":"apply preset","func":FN_APPLY_PRESET,"outputs":1,"noerr":0,
     "x":440,"y":1160,"wires":[["gov-udp-ctrl"]]},

    # ── Adjust sliders ──────────────────────────────────────────────────────────
    {"id":"v2-slider-brightness","type":"ui-slider","z":"gov-flow",
     "group":"v2-grp-govee-adjust","name":"Brightness","label":"Brightness  0 ─────────────── 100",
     "order":1,"width":"12","height":"1",
     "passthru":True,"outs":"end",
     "min":0,"max":100,"step":1,
     "topic":"brightness","topicType":"str",
     "x":210,"y":1340,"wires":[["gov-fn-all-brightness"]]},

    {"id":"v2-slider-colortemp","type":"ui-slider","z":"gov-flow",
     "group":"v2-grp-govee-adjust","name":"Color Temp","label":"Color Temp  Warm 2700K ──── Cool 6500K",
     "order":2,"width":"12","height":"1",
     "passthru":True,"outs":"end",
     "min":2700,"max":6500,"step":100,
     "topic":"colortemp","topicType":"str",
     "x":210,"y":1400,"wires":[["gov-fn-all-colortemp"]]},

    # Slider functions
    {"id":"gov-fn-all-brightness","type":"function","z":"gov-flow",
     "name":"brightness → all","func":FN_ALL_BRIGHTNESS,"outputs":1,"noerr":0,
     "x":450,"y":1340,"wires":[["gov-udp-ctrl"]]},

    {"id":"gov-fn-all-colortemp","type":"function","z":"gov-flow",
     "name":"colortemp → all","func":FN_ALL_COLORTEMP,"outputs":1,"noerr":0,
     "x":450,"y":1400,"wires":[["gov-udp-ctrl"]]},

    # ── Save preset buttons ─────────────────────────────────────────────────────
    {"id":"v2-btn-save-evening","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-save","name":"Save Evening","label":"Save Evening",
     "order":1,"width":"4","height":"1",
     "emitOnlyOnClick":True,"buttonColor":"#f5a623","textColor":"#000000","iconColor":"#000000",
     "enableClick":True,"enablePointerdown":False,
     "payload":"Evening","payloadType":"str","topic":"save","topicType":"str",
     "x":210,"y":1460,"wires":[["gov-fn-save-preset"]]},

    {"id":"v2-btn-save-bright","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-save","name":"Save Bright","label":"Save Bright",
     "order":2,"width":"4","height":"1",
     "emitOnlyOnClick":True,"buttonColor":"#ffffff","textColor":"#000000","iconColor":"#000000",
     "enableClick":True,"enablePointerdown":False,
     "payload":"Bright","payloadType":"str","topic":"save","topicType":"str",
     "x":210,"y":1520,"wires":[["gov-fn-save-preset"]]},

    {"id":"v2-btn-save-movie","type":"ui-button","z":"gov-flow",
     "group":"v2-grp-govee-save","name":"Save Movie","label":"Save Movie",
     "order":3,"width":"4","height":"1",
     "emitOnlyOnClick":True,"buttonColor":"#4a3580","textColor":"#ffffff","iconColor":"#ffffff",
     "enableClick":True,"enablePointerdown":False,
     "payload":"Movie","payloadType":"str","topic":"save","topicType":"str",
     "x":210,"y":1580,"wires":[["gov-fn-save-preset"]]},

    # Save preset logic + file write
    {"id":"gov-fn-save-preset","type":"function","z":"gov-flow",
     "name":"save preset","func":FN_SAVE_PRESET,"outputs":1,"noerr":0,
     "x":450,"y":1520,"wires":[["gov-file-write-presets"]]},

    {"id":"gov-file-write-presets","type":"file","z":"gov-flow",
     "name":"write presets.json","filename":PRESETS_FILE,"filenameType":"str",
     "appendNewline":False,"createDir":False,"overwriteFile":"true","encoding":"none",
     "x":680,"y":1520,"wires":[[]]},

    # ── Startup: load presets from file ────────────────────────────────────────
    {"id":"gov-inject-load-presets","type":"inject","z":"gov-flow",
     "name":"Load presets","props":[{"p":"payload"}],
     "repeat":"","crontab":"","once":True,"onceDelay":8,
     "payload":"","payloadType":"date",
     "x":200,"y":1640,"wires":[["gov-file-read-presets"]]},

    {"id":"gov-file-read-presets","type":"file in","z":"gov-flow",
     "name":"read presets.json","filename":PRESETS_FILE,"filenameType":"str",
     "format":"utf8","chunk":False,"sendError":False,"encoding":"none",
     "x":420,"y":1640,"wires":[["gov-fn-load-presets"]]},

    {"id":"gov-fn-load-presets","type":"function","z":"gov-flow",
     "name":"parse presets","func":FN_LOAD_PRESETS,"outputs":1,"noerr":0,
     "x":640,"y":1640,"wires":[[]]},
]

# ── Patch + save ───────────────────────────────────────────────────────────────
with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

flows.extend(NEW_NODES)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Added {len(NEW_NODES)} nodes. Total: {len(flows)}')
