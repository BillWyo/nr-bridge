import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

FN_WATCHDOG = """\
var STALE_MS = 300000;
var nodes  = ['bills-office','mud-room','garage'];
var labels = {'bills-office':'Bills Office','mud-room':'Mud Room','garage':'Garage'};
var ls  = flow.get('node_lastseen') || {};
var now = Date.now();
var rows = nodes.map(function(n) {
    var t = ls[n];
    if (!t) return {node: labels[n], age: 'never', ok: false};
    var age = Math.floor((now - t) / 1000);
    var d  = new Date(t);
    var mo = d.getMonth() + 1;
    var dd = String(d.getDate()).padStart(2, '0');
    var hh = String(d.getHours()).padStart(2, '0');
    var mm = String(d.getMinutes()).padStart(2, '0');
    var stamp = mo + '/' + dd + ' ' + hh + ':' + mm;
    return {node: labels[n], age: stamp, ok: age < (STALE_MS / 1000)};
});
msg.payload = rows;
return msg;"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'his-fn-watchdog':
        n['func'] = FN_WATCHDOG
        print('Patched his-fn-watchdog')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
