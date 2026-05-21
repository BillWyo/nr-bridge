import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'
PRESETS_FILE = r'C:\Users\johan\.node-red\projects\Home_PTRH\govee_presets.json'

# Nodes to replace with updated versions
REPLACE_IDS = {
    'gov-fn-apply-preset', 'gov-fn-save-preset',
    'gov-fn-all-brightness', 'gov-fn-all-colortemp',
    'gov-fn-color-cmd', 'gov-fn-update-sliders',
    'v2-tmpl-color-picker',
}

# ── Function bodies ────────────────────────────────────────────────────────────

FN_APPLY_PRESET = """\
var name    = msg.payload;
var devs    = flow.get('govee_devices') || {};
var nameMap = flow.get('govee_names')   || {};
if (!Object.keys(devs).length) { node.warn('Run discovery first'); return null; }

if (name === 'All Off') {
    flow.set('govee_current', {onOff:0, brightness:0, colortemp:4000, color:{r:0,g:0,b:0}, mode:'white'});
    var msgs = Object.values(devs).map(function(d) {
        return {payload:JSON.stringify({msg:{cmd:'turn',data:{value:0}}}), ip:d.ip, port:4003};
    });
    return [[msgs], null];
}

var presets = flow.get('govee_presets') || {};
var preset  = presets[name];
if (!preset) { node.warn('Preset not found: ' + name); return null; }
flow.set('govee_current', preset);

var msgs = [];
Object.values(devs).forEach(function(d) {
    msgs.push({payload:JSON.stringify({msg:{cmd:'turn',      data:{value:preset.onOff}}}), ip:d.ip, port:4003});
    msgs.push({payload:JSON.stringify({msg:{cmd:'brightness', data:{value:preset.brightness}}}), ip:d.ip, port:4003});
    var colorData = preset.mode === 'color'
        ? {color: preset.color, colorTemInKelvin: 0}
        : {color: {r:0,g:0,b:0}, colorTemInKelvin: preset.colortemp || 4000};
    msgs.push({payload:JSON.stringify({msg:{cmd:'colorwc', data:colorData}}), ip:d.ip, port:4003});
});
return [[msgs], {payload: preset}];"""

FN_SAVE_PRESET = """\
var name    = msg.payload;
var current = flow.get('govee_current') || {};
if (!Object.keys(current).length) { node.warn('Apply a preset first to initialise state'); return null; }
var presets = flow.get('govee_presets') || {};
presets[name] = JSON.parse(JSON.stringify(current));
flow.set('govee_presets', presets);
node.status({fill:'green', shape:'dot', text: name + ' saved'});
msg.payload = JSON.stringify(presets, null, 2);
return msg;"""

FN_ALL_BRIGHTNESS = """\
var current = flow.get('govee_current') || {};
current.brightness = msg.payload;
flow.set('govee_current', current);
var devs = flow.get('govee_devices') || {};
var msgs = Object.values(devs).map(function(d) {
    return {payload:JSON.stringify({msg:{cmd:'brightness',data:{value:msg.payload}}}), ip:d.ip, port:4003};
});
return [msgs];"""

FN_ALL_COLORTEMP = """\
var current = flow.get('govee_current') || {};
current.colortemp = msg.payload;
current.mode = 'white';
flow.set('govee_current', current);
var devs = flow.get('govee_devices') || {};
var msgs = Object.values(devs).map(function(d) {
    return {payload:JSON.stringify({msg:{cmd:'colorwc',data:{color:{r:0,g:0,b:0},colorTemInKelvin:msg.payload}}}), ip:d.ip, port:4003};
});
return [msgs];"""

FN_COLOR_CMD = """\
var current = flow.get('govee_current') || {};
if (msg.payload.mode === 'color') {
    current.color = {r:msg.payload.r, g:msg.payload.g, b:msg.payload.b};
    current.mode  = 'color';
} else {
    current.mode     = 'white';
    current.colortemp = current.colortemp || 4000;
}
flow.set('govee_current', current);
var devs = flow.get('govee_devices') || {};
var data = current.mode === 'color'
    ? {color: current.color, colorTemInKelvin: 0}
    : {color: {r:0,g:0,b:0}, colorTemInKelvin: current.colortemp};
var msgs = Object.values(devs).map(function(d) {
    return {payload:JSON.stringify({msg:{cmd:'colorwc',data:data}}), ip:d.ip, port:4003};
});
return [msgs];"""

FN_UPDATE_SLIDERS = """\
var p = msg.payload;
if (!p) return null;
var brightness = p.brightness !== undefined ? p.brightness : 50;
var colortemp  = p.colortemp  || 4000;
return [
    {payload: brightness},
    {payload: colortemp},
    {payload: {color: p.color || {r:255,g:136,b:0}}}
];"""

TMPL_COLOR_PICKER = """\
<template>
  <div style="padding:8px">
    <label style="display:block;margin-bottom:6px;font-size:14px">Color</label>
    <input type="color" v-model="color" @change="onPick"
           style="width:100%;height:64px;border:none;border-radius:6px;cursor:pointer;padding:2px"/>
    <button @click="onWhite"
            style="margin-top:8px;width:100%;height:40px;border:none;border-radius:6px;
                   background:#fffde7;color:#333;font-size:14px;cursor:pointer">
      Back to White Light
    </button>
  </div>
</template>
<script>
  export default {
    data() { return { color: '#ff8800' } },
    watch: {
      msg(v) {
        if (v && v.payload && v.payload.color) {
          const c = v.payload.color;
          this.color = '#'
            + (c.r||0).toString(16).padStart(2,'0')
            + (c.g||0).toString(16).padStart(2,'0')
            + (c.b||0).toString(16).padStart(2,'0');
        }
      }
    },
    methods: {
      onPick() {
        const h = this.color;
        const r = parseInt(h.slice(1,3),16);
        const g = parseInt(h.slice(3,5),16);
        const b = parseInt(h.slice(5,7),16);
        this.send({payload:{mode:'color',r,g,b}});
      },
      onWhite() { this.send({payload:{mode:'white'}}); }
    }
  }
</script>"""

# ── Replacement nodes ──────────────────────────────────────────────────────────
REPLACEMENTS = [
    {"id":"gov-fn-apply-preset","type":"function","z":"gov-flow",
     "name":"apply preset","func":FN_APPLY_PRESET,"outputs":2,"noerr":0,
     "x":440,"y":1160,"wires":[["gov-udp-ctrl"],["gov-fn-update-sliders"]]},

    {"id":"gov-fn-save-preset","type":"function","z":"gov-flow",
     "name":"save preset","func":FN_SAVE_PRESET,"outputs":1,"noerr":0,
     "x":450,"y":1520,"wires":[["gov-file-write-presets"]]},

    {"id":"gov-fn-all-brightness","type":"function","z":"gov-flow",
     "name":"brightness → all","func":FN_ALL_BRIGHTNESS,"outputs":1,"noerr":0,
     "x":450,"y":1340,"wires":[["gov-udp-ctrl"]]},

    {"id":"gov-fn-all-colortemp","type":"function","z":"gov-flow",
     "name":"colortemp → all","func":FN_ALL_COLORTEMP,"outputs":1,"noerr":0,
     "x":450,"y":1400,"wires":[["gov-udp-ctrl"]]},

    {"id":"gov-fn-color-cmd","type":"function","z":"gov-flow",
     "name":"color cmd","func":FN_COLOR_CMD,"outputs":1,"noerr":0,
     "x":440,"y":1720,"wires":[["gov-udp-ctrl"]]},

    {"id":"gov-fn-update-sliders","type":"function","z":"gov-flow",
     "name":"update sliders","func":FN_UPDATE_SLIDERS,"outputs":3,"noerr":0,
     "x":460,"y":1700,
     "wires":[["v2-slider-brightness"],["v2-slider-colortemp"],["v2-tmpl-color-picker"]]},

    {"id":"v2-tmpl-color-picker","type":"ui-template","z":"gov-flow",
     "group":"v2-grp-govee-color","name":"Color Picker",
     "order":1,"width":"12","height":"4",
     "format":TMPL_COLOR_PICKER,"storeOutMessages":True,"passthru":True,
     "resendOnRefresh":True,"templateScope":"local","className":"",
     "x":210,"y":1720,"wires":[["gov-fn-color-cmd"]]},
]

# ── Load, replace, save ────────────────────────────────────────────────────────
with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

flows = [n for n in flows if n.get('id') not in REPLACE_IDS]
flows.extend(REPLACEMENTS)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Replaced {len(REPLACEMENTS)} nodes. Total: {len(flows)}')
