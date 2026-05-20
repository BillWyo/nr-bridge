#!/usr/bin/env python3
"""Migrate HIS flows from Node-RED Dashboard v1 to FlowFuse Dashboard v2."""
import json, copy

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# ── v1 node IDs to remove ─────────────────────────────────────────────────────
V1_REMOVE = {
    'd748b5591e098c6c',                          # ui_base
    'his-ui-tab-pth','his-ui-tab-overview','his-ui-tab-alarms',
    'his-ui-tab-frontdoor',
    'his-ui-grp-pressure','his-ui-grp-temp','his-ui-grp-faults',
    'his-ui-grp-doors','his-ui-grp-motion','his-ui-grp-gas',
    'his-ui-grp-visitor','his-ui-grp-status','his-ui-grp-photo',
    'his-chart-pressure','his-chart-temp',
    'his-template-rh','his-template-faults',
    'his-text-door','his-text-motion',
    'his-gauge-smoke','his-text-alarm-banner',
    'his-text-visitor','his-template-image',
    'his-template-node-status','his-template-display-photo',
    'pb-ui-tab','pb-ui-grp-cam','pb-btn-capture',
    'pb-template-image','pb-text-status',
}

# ── wire remap ────────────────────────────────────────────────────────────────
REMAP = {
    'his-chart-pressure':        'v2-tmpl-pressure',
    'his-chart-temp':            'v2-chart-temp',
    'his-template-rh':           'v2-tmpl-rh',
    'his-template-faults':       'v2-tmpl-faults',
    'his-text-door':             'v2-text-door',
    'his-text-motion':           'v2-text-motion',
    'his-gauge-smoke':           'v2-gauge-smoke',
    'his-text-alarm-banner':     'v2-text-alarm',
    'his-text-visitor':          'v2-text-visitor',
    'his-template-image':        'v2-tmpl-frontdoor',
    'his-template-node-status':  'v2-tmpl-status',
    'his-template-display-photo':'v2-tmpl-photo',
    'pb-template-image':         'v2-tmpl-pb',
    'pb-text-status':            'v2-text-pb-status',
}

def remap_wires(wires):
    return [[REMAP.get(nid, nid) for nid in out] for out in wires]

# ── Vue SFC templates ─────────────────────────────────────────────────────────
TMPL_PRESSURE = """\
<template>
  <div v-if="msg && msg.payload" class="ps">
    <div class="ps-val">{{ msg.payload.pressure }} PSI</div>
    <div class="ps-trend">{{ msg.payload.trend }}</div>
    <div class="ps-conf">Confidence: {{ msg.payload.conf }}</div>
    <div class="ps-src">Source: {{ msg.payload.source }}</div>
  </div>
</template>
<style scoped>
.ps { font-family: monospace; padding: 10px }
.ps-val { font-size: 2.8em; font-weight: bold; color: #0eb8c0 }
.ps-trend { font-size: 1.6em; color: #eeeeee; margin-top: 6px }
.ps-conf { font-size: 1.4em; color: #aaaaaa; margin-top: 4px }
.ps-src { font-size: 1.2em; color: #666; margin-top: 4px }
</style>"""

TMPL_RH = """\
<template>
  <div v-if="msg && msg.payload" class="rhs">
    <div v-for="r in msg.payload" :key="r.label" class="rhs-row">
      <span class="rhs-node">{{ r.label }}</span>
      <span class="rhs-val">{{ r.value }}</span>
    </div>
  </div>
</template>
<style scoped>
.rhs { font-family: monospace; padding: 10px }
.rhs-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #333 }
.rhs-node { font-size: 1.4em; color: #aaaaaa }
.rhs-val { font-size: 1.6em; font-weight: bold; color: #0eb8c0 }
</style>"""

TMPL_FAULTS = """\
<template>
  <div v-if="msg && msg.payload" class="fc">
    <table>
      <thead><tr><th>Node</th><th>P</th><th>T</th><th>RH</th></tr></thead>
      <tbody>
        <tr v-if="msg.payload['bills-office']">
          <td class="name">Bills Office</td>
          <td :class="msg.payload['bills-office'].P > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['bills-office'].P }}</td>
          <td :class="msg.payload['bills-office'].T > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['bills-office'].T }}</td>
          <td :class="msg.payload['bills-office'].RH > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['bills-office'].RH }}</td>
        </tr>
        <tr v-if="msg.payload['mud-room']">
          <td class="name">Mud Room</td>
          <td :class="msg.payload['mud-room'].P > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['mud-room'].P }}</td>
          <td :class="msg.payload['mud-room'].T > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['mud-room'].T }}</td>
          <td :class="msg.payload['mud-room'].RH > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['mud-room'].RH }}</td>
        </tr>
        <tr v-if="msg.payload['garage']">
          <td class="name">Garage</td>
          <td :class="msg.payload['garage'].P > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['garage'].P }}</td>
          <td :class="msg.payload['garage'].T > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['garage'].T }}</td>
          <td :class="msg.payload['garage'].RH > 0 ? 'warn' : 'ok'" class="ctr">{{ msg.payload['garage'].RH }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<style scoped>
.fc { font-family: monospace; font-size: 13px }
.fc table { width: 100%; border-collapse: collapse }
.fc th, .fc td { padding: 4px 10px; border-bottom: 1px solid #444 }
.fc th { text-align: center; color: #aaa }
.name { text-align: left }
.ctr { text-align: center }
.ok { color: #2ca02c }
.warn { color: #ff7f0e }
</style>"""

TMPL_STATUS = """\
<template>
  <div v-if="msg && msg.payload" class="ns">
    <table>
      <thead><tr><th>Node</th><th>Last seen</th><th>Status</th></tr></thead>
      <tbody>
        <tr v-for="r in msg.payload" :key="r.node">
          <td>{{ r.node }}</td>
          <td>{{ r.age }}</td>
          <td><span class="dot" :style="{background: r.ok ? '#2ca02c' : '#d62728'}"></span>{{ r.ok ? 'OK' : 'DOWN' }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<style scoped>
.ns { font-family: monospace; font-size: 13px }
.ns table { width: 100%; border-collapse: collapse }
.ns th, .ns td { padding: 4px 12px; border-bottom: 1px solid #444 }
.ns th { color: #aaa; text-align: left }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px }
</style>"""

TMPL_IMAGE = """\
<template>
  <img v-if="msg && msg.payload"
       :src="'data:image/jpeg;base64,' + msg.payload"
       style="max-width:100%;border-radius:4px" />
</template>"""

TMPL_SMOKE = """\
<template>
  <div v-if="msg !== undefined" class="gw">
    <div class="gv" :style="{color: (msg.payload||0) > 2500 ? '#e60000' : (msg.payload||0) > 1500 ? '#e6e600' : '#00b500'}">
      {{ msg.payload || 0 }}
    </div>
    <div class="gl">Smoke ADC (0–4095)</div>
    <div class="gb">
      <div class="gf" :style="{width: Math.min(100,(msg.payload||0)/4095*100)+'%',
        background: (msg.payload||0) > 2500 ? '#e60000' : (msg.payload||0) > 1500 ? '#e6e600' : '#00b500'}"></div>
    </div>
  </div>
</template>
<style scoped>
.gw { font-family: monospace; padding: 10px }
.gv { font-size: 3em; font-weight: bold; text-align: center }
.gl { text-align: center; color: #aaa; font-size: 0.9em; margin: 4px 0 8px }
.gb { background: #333; border-radius: 4px; height: 20px; overflow: hidden }
.gf { height: 100%; transition: width 0.3s, background 0.3s }
</style>"""

# ── v2 config nodes (no z) ────────────────────────────────────────────────────
V2_CFG = [
    {"id":"v2-ui-base","type":"ui-base","name":"HIS Dashboard",
     "path":"/dashboard","includeClientData":True,
     "acceptsClientConfig":["ui-notification","ui-control"],
     "navigationStyle":"default","showPathInSidebar":False},

    {"id":"v2-page-pth","type":"ui-page","name":"PTH Charts",
     "ui":"v2-ui-base","path":"/pth","icon":"show_chart",
     "layout":"notebook","theme":"","order":1,"groups":[]},
    {"id":"v2-page-overview","type":"ui-page","name":"Home Overview",
     "ui":"v2-ui-base","path":"/overview","icon":"home",
     "layout":"notebook","theme":"","order":2,"groups":[]},
    {"id":"v2-page-alarms","type":"ui-page","name":"Alarms",
     "ui":"v2-ui-base","path":"/alarms","icon":"warning",
     "layout":"notebook","theme":"","order":3,"groups":[]},
    {"id":"v2-page-frontdoor","type":"ui-page","name":"Front Door",
     "ui":"v2-ui-base","path":"/frontdoor","icon":"camera_alt",
     "layout":"notebook","theme":"","order":4,"groups":[]},
    {"id":"v2-page-pb","type":"ui-page","name":"Photo Booth",
     "ui":"v2-ui-base","path":"/photobooth","icon":"photo_camera",
     "layout":"notebook","theme":"","order":5,"groups":[]},

    # PTH groups
    {"id":"v2-grp-pressure","type":"ui-group","name":"Pressure (PSI)",
     "page":"v2-page-pth","width":"12","height":"1","order":1,
     "showTitle":True,"className":"","visible":"true"},
    {"id":"v2-grp-temp","type":"ui-group","name":"Temperature (°F)",
     "page":"v2-page-pth","width":"12","height":"1","order":2,
     "showTitle":True,"className":"","visible":"true"},
    {"id":"v2-grp-faults","type":"ui-group","name":"Sensor Fault Counts",
     "page":"v2-page-pth","width":"12","height":"1","order":3,
     "showTitle":True,"className":"","visible":"true"},
    {"id":"v2-grp-status","type":"ui-group","name":"Node Status",
     "page":"v2-page-pth","width":"12","height":"1","order":4,
     "showTitle":True,"className":"","visible":"true"},
    # Overview groups
    {"id":"v2-grp-doors","type":"ui-group","name":"Doors & Windows",
     "page":"v2-page-overview","width":"6","height":"1","order":1,
     "showTitle":True,"className":"","visible":"true"},
    {"id":"v2-grp-motion","type":"ui-group","name":"Motion",
     "page":"v2-page-overview","width":"6","height":"1","order":2,
     "showTitle":True,"className":"","visible":"true"},
    {"id":"v2-grp-photo","type":"ui-group","name":"Current Photo",
     "page":"v2-page-overview","width":"12","height":"1","order":3,
     "showTitle":True,"className":"","visible":"true"},
    # Alarms groups
    {"id":"v2-grp-gas","type":"ui-group","name":"Smoke / CO",
     "page":"v2-page-alarms","width":"12","height":"1","order":1,
     "showTitle":True,"className":"","visible":"true"},
    # Front Door groups
    {"id":"v2-grp-visitor","type":"ui-group","name":"Visitor",
     "page":"v2-page-frontdoor","width":"12","height":"1","order":1,
     "showTitle":True,"className":"","visible":"true"},
    # Photo Booth groups
    {"id":"v2-grp-pb-cam","type":"ui-group","name":"Camera",
     "page":"v2-page-pb","width":"12","height":"1","order":1,
     "showTitle":True,"className":"","visible":"true"},
]

# ── v2 display widget nodes (have z) ─────────────────────────────────────────
V2_WIDGETS = [
    # PTH Charts
    {"id":"v2-tmpl-pressure","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-pressure","name":"Pressure Summary",
     "order":1,"width":"12","height":"7","format":TMPL_PRESSURE,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":620,"y":80,"wires":[[]]},
    {"id":"v2-tmpl-rh","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-pressure","name":"Humidity Summary",
     "order":2,"width":"12","height":"3","format":TMPL_RH,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":840,"y":160,"wires":[[]]},
    {"id":"v2-chart-temp","type":"ui-chart","z":"his-flow-main",
     "group":"v2-grp-temp","name":"Temperature",
     "label":"Temperature (°F)","order":1,"width":"12","height":"6",
     "chartType":"line","category":"topic","categoryType":"msg",
     "xAxisType":"time","xAxisFormat":"","removeOlder":"30",
     "removeOlderUnit":"60","removeOlderPoints":"",
     "colors":["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#aec7e8","#ffbb78","#98df8a"],
     "smooth":False,"interpolation":"linear","legend":"right",
     "action":"append","ymin":"55","ymax":"75",
     "x":620,"y":120,"wires":[[]]},
    {"id":"v2-tmpl-faults","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-faults","name":"Fault Counts",
     "order":1,"width":"12","height":"4","format":TMPL_FAULTS,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":840,"y":300,"wires":[[]]},
    {"id":"v2-tmpl-status","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-status","name":"Node Status",
     "order":1,"width":"12","height":"3","format":TMPL_STATUS,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":680,"y":1060,"wires":[[]]},
    # Overview
    {"id":"v2-text-door","type":"ui-text","z":"his-flow-main",
     "group":"v2-grp-doors","name":"Door Status","label":"",
     "format":"{{msg.payload}}","layout":"row-left","style":False,
     "className":"","order":1,"width":"6","height":"1",
     "x":600,"y":420,"wires":[]},
    {"id":"v2-text-motion","type":"ui-text","z":"his-flow-main",
     "group":"v2-grp-motion","name":"Motion Status","label":"",
     "format":"{{msg.payload}}","layout":"row-left","style":False,
     "className":"","order":1,"width":"6","height":"1",
     "x":600,"y":480,"wires":[]},
    {"id":"v2-tmpl-photo","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-photo","name":"Current Photo",
     "order":1,"width":"12","height":"9","format":TMPL_IMAGE,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":680,"y":840,"wires":[[]]},
    # Alarms
    {"id":"v2-gauge-smoke","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-gas","name":"Smoke Level",
     "order":1,"width":"6","height":"4","format":TMPL_SMOKE,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":600,"y":560,"wires":[[]]},
    {"id":"v2-text-alarm","type":"ui-text","z":"his-flow-main",
     "group":"v2-grp-gas","name":"Alarm Banner","label":"⚠ Alert",
     "format":"{{msg.payload}}","layout":"row-left","style":False,
     "className":"","order":2,"width":"12","height":"1",
     "x":600,"y":620,"wires":[]},
    # Front Door
    {"id":"v2-text-visitor","type":"ui-text","z":"his-flow-main",
     "group":"v2-grp-visitor","name":"Last Visitor","label":"Last event",
     "format":"{{msg.payload}}","layout":"row-left","style":False,
     "className":"","order":1,"width":"12","height":"1",
     "x":640,"y":720,"wires":[]},
    {"id":"v2-tmpl-frontdoor","type":"ui-template","z":"his-flow-main",
     "group":"v2-grp-visitor","name":"Visitor Snapshot",
     "order":2,"width":"12","height":"9","format":TMPL_IMAGE,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":680,"y":780,"wires":[[]]},
    # Photo Booth
    {"id":"v2-btn-capture","type":"ui-button","z":"pb-flow-main",
     "group":"v2-grp-pb-cam","name":"Capture","label":"Capture",
     "order":1,"width":"4","height":"1","passthru":False,
     "tooltip":"","color":"","bgcolor":"","className":"",
     "icon":"camera_alt","iconPosition":"left",
     "payload":"go","payloadType":"str","topic":"","topicType":"str",
     "x":160,"y":100,"wires":[["pb-mqtt-trigger"]]},
    {"id":"v2-text-pb-status","type":"ui-text","z":"pb-flow-main",
     "group":"v2-grp-pb-cam","name":"Capture Status","label":"",
     "format":"{{msg.payload}}","layout":"row-left","style":False,
     "className":"","order":2,"width":"8","height":"1",
     "x":580,"y":260,"wires":[]},
    {"id":"v2-tmpl-pb","type":"ui-template","z":"pb-flow-main",
     "group":"v2-grp-pb-cam","name":"Snapshot",
     "order":3,"width":"12","height":"9","format":TMPL_IMAGE,
     "storeOutMessages":True,"passthru":False,"resendOnRefresh":True,
     "templateScope":"local","className":"","x":620,"y":200,"wires":[[]]},
]

# ── Run ───────────────────────────────────────────────────────────────────────
with open(FLOWS_PATH, 'r', encoding='utf-8') as f:
    flows = json.load(f)

kept = []
removed = []
for node in flows:
    if node['id'] in V1_REMOVE:
        removed.append(node['id'])
        continue
    node = copy.deepcopy(node)
    if 'wires' in node:
        node['wires'] = remap_wires(node['wires'])
    kept.append(node)

result = V2_CFG + kept + V2_WIDGETS

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Removed {len(removed)} v1 nodes: {removed}")
print(f"Kept    {len(kept)} existing nodes")
print(f"Added   {len(V2_CFG)+len(V2_WIDGETS)} v2 nodes")
print(f"Total   {len(result)} nodes written")
