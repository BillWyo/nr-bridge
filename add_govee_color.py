import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

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
    methods: {
      onPick() {
        const h = this.color;
        const r = parseInt(h.slice(1,3), 16);
        const g = parseInt(h.slice(3,5), 16);
        const b = parseInt(h.slice(5,7), 16);
        this.send({ payload: { mode:'color', r, g, b } });
      },
      onWhite() {
        this.send({ payload: { mode:'white' } });
      }
    }
  }
</script>"""

FN_COLOR_CMD = """\
var devs = flow.get('govee_devices') || {};
if (!Object.keys(devs).length) { node.warn('Run discovery first'); return null; }
var data;
if (msg.payload.mode === 'color') {
    data = { color: {r: msg.payload.r, g: msg.payload.g, b: msg.payload.b}, colorTemInKelvin: 0 };
} else {
    data = { color: {r:0, g:0, b:0}, colorTemInKelvin: 4000 };
}
var msgs = Object.values(devs).map(function(d) {
    return { payload: JSON.stringify({msg:{cmd:'colorwc', data:data}}), ip:d.ip, port:4003 };
});
return [msgs];"""

NEW_NODES = [
    {"id":"v2-grp-govee-color","type":"ui-group","name":"Color",
     "page":"v2-page-govee","width":"12","height":"1","order":3,
     "showTitle":True,"className":"","visible":"true"},

    {"id":"v2-tmpl-color-picker","type":"ui-template","z":"gov-flow",
     "group":"v2-grp-govee-color","name":"Color Picker",
     "order":1,"width":"12","height":"4",
     "format":TMPL_COLOR_PICKER,"storeOutMessages":True,"passthru":True,
     "resendOnRefresh":True,"templateScope":"local","className":"",
     "x":210,"y":1720,"wires":[["gov-fn-color-cmd"]]},

    {"id":"gov-fn-color-cmd","type":"function","z":"gov-flow",
     "name":"color cmd","func":FN_COLOR_CMD,"outputs":1,"noerr":0,
     "x":440,"y":1720,"wires":[["gov-udp-ctrl"]]},
]

# Bump Save Preset group to order 4 so Color sits at 3
with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'v2-grp-govee-save':
        n['order'] = 4
        print('Bumped v2-grp-govee-save to order 4')

flows.extend(NEW_NODES)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Added {len(NEW_NODES)} nodes. Total: {len(flows)}')
