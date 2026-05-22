import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

TMPL_CLOCK = """\
<template>
  <div class="clk">
    <div class="clk-time">{{ time }}</div>
    <div class="clk-day">{{ day }}</div>
  </div>
</template>
<script>
  export default {
    data() { return { time: '', day: '' } },
    mounted()      { this.tick(); this._t = setInterval(this.tick, 10000); },
    beforeUnmount(){ clearInterval(this._t); },
    methods: {
      tick() {
        const d = new Date();
        const h = d.getHours(), m = String(d.getMinutes()).padStart(2, '0');
        this.time = (h % 12 || 12) + ':' + m + ' ' + (h >= 12 ? 'PM' : 'AM');
        const days   = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        this.day = days[d.getDay()] + '  ' + months[d.getMonth()] + ' ' + d.getDate();
      }
    }
  }
</script>
<style scoped>
.clk      { font-family: monospace; padding: 10px }
.clk-time { font-size: 2.8em; font-weight: bold; color: #0eb8c0 }
.clk-day  { font-size: 1.6em; color: var(--nrdb-widget-textColor, #eeeeee); margin-top: 6px }
</style>"""

NEW_NODES = [
    # Group — order 0 puts it above the existing Pressure group (order 1)
    {
        "id": "v2-grp-clock",
        "type": "ui-group",
        "name": "Clock",
        "page": "v2-page-pth",
        "width": "12",
        "height": "1",
        "order": 0,
        "showTitle": False,
        "className": "",
        "visible": "true"
    },
    # Self-updating clock template — no input wires needed
    {
        "id": "v2-tmpl-clock",
        "type": "ui-template",
        "z": "his-flow-main",
        "group": "v2-grp-clock",
        "name": "Clock",
        "order": 1,
        "width": "12",
        "height": "3",
        "format": TMPL_CLOCK,
        "storeOutMessages": False,
        "passthru": False,
        "resendOnRefresh": False,
        "templateScope": "local",
        "className": "",
        "x": 850,
        "y": 100,
        "wires": [[]]
    }
]

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

# Remove any previous clock nodes
flows = [n for n in flows if n.get('id') not in ('v2-grp-clock', 'v2-tmpl-clock')]
flows.extend(NEW_NODES)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Added clock. Total nodes: {len(flows)}')
