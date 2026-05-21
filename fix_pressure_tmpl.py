import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

NEW_TMPL = """\
<template>
  <div class="ps">
    <div class="ps-val">{{ msg && msg.payload ? msg.payload.pressure + ' PSI' : '-- PSI' }}</div>
    <div class="ps-trend">{{ msg && msg.payload ? msg.payload.trend : 'waiting for sensors...' }}</div>
    <div class="ps-conf">{{ msg && msg.payload ? 'Confidence: ' + msg.payload.conf : '' }}</div>
    <div class="ps-src">{{ msg && msg.payload ? 'Source: ' + msg.payload.source : '' }}</div>
  </div>
</template>
<style scoped>
.ps { font-family: monospace; padding: 10px }
.ps-val { font-size: 2.8em; font-weight: bold; color: #0eb8c0 }
.ps-trend { font-size: 1.6em; color: var(--nrdb-widget-textColor, #eeeeee); margin-top: 6px }
.ps-conf { font-size: 1.4em; color: var(--nrdb-widget-textColor, #aaaaaa); margin-top: 4px }
.ps-src { font-size: 1.2em; color: var(--nrdb-widget-textColor, #aaaaaa); margin-top: 4px }
</style>"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'v2-tmpl-pressure':
        n['format'] = NEW_TMPL
        print('Updated v2-tmpl-pressure')
        break

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
print('Saved.')
