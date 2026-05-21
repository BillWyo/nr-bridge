import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# Updated parse function: handles both scan and devStatus responses
FN_PARSE_SCAN = """\
try {
    var d = JSON.parse(msg.payload);
    if (!d.msg) return null;

    if (d.msg.cmd === 'scan') {
        var info = d.msg.data;
        var devs = flow.get('govee_devices') || {};
        devs[info.device] = { ip: info.ip, sku: info.sku, device: info.device };
        flow.set('govee_devices', devs);
        node.status({fill:'green', shape:'dot', text: info.sku + ' @ ' + info.ip});
        msg.payload = devs;
        return [msg, null];
    }

    if (d.msg.cmd === 'devStatus') {
        var nameMap  = flow.get('govee_names')   || {};
        var devs2    = flow.get('govee_devices')  || {};
        var idToName = {};
        Object.keys(nameMap).forEach(function(n) { idToName[nameMap[n]] = n; });
        var dev = Object.values(devs2).find(function(x) { return x.ip === msg.ip; });
        var label = dev ? (idToName[dev.device] || dev.device) : msg.ip;

        var snapshot = flow.get('govee_snapshot') || {};
        snapshot[label] = d.msg.data;
        flow.set('govee_snapshot', snapshot);
        var count = Object.keys(snapshot).length;
        node.status({fill:'blue', shape:'dot', text: 'status ' + count + '/4'});
        if (count >= 4) {
            node.status({fill:'green', shape:'ring', text: 'snapshot ready'});
            msg.payload = snapshot;
            return [null, msg];
        }
        return null;
    }

    return null;
} catch(e) {
    node.warn('parse error: ' + e.message);
    return null;
}"""

# Query devStatus from all discovered devices
FN_QUERY_STATUS = """\
flow.set('govee_snapshot', {});
var devs = flow.get('govee_devices') || {};
if (!Object.keys(devs).length) { node.warn('Run discovery first'); return null; }
var msgs = Object.values(devs).map(function(d) {
    return { payload: JSON.stringify({msg:{cmd:'devStatus',data:{}}}), ip: d.ip, port: 4003 };
});
return [msgs];"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'gov-fn-parse-scan':
        n['func']    = FN_PARSE_SCAN
        n['outputs'] = 2
        # second output wires to new debug node
        if len(n['wires']) < 2:
            n['wires'].append(['gov-debug-status'])
        else:
            n['wires'][1] = ['gov-debug-status']
        print('Updated gov-fn-parse-scan -> 2 outputs')

    # Remove existing debug-devices wire if present; it stays on output 0
    if n.get('id') == 'gov-debug-devices':
        print('gov-debug-devices retained on output 0')

new_nodes = [
    {
        "id": "gov-inject-read-state",
        "type": "inject",
        "z": "gov-flow",
        "name": "Read state",
        "props": [{"p": "payload"}],
        "repeat": "",
        "crontab": "",
        "once": False,
        "payload": "",
        "payloadType": "date",
        "x": 180,
        "y": 1000,
        "wires": [["gov-fn-query-status"]]
    },
    {
        "id": "gov-fn-query-status",
        "type": "function",
        "z": "gov-flow",
        "name": "query devStatus",
        "func": FN_QUERY_STATUS,
        "outputs": 1,
        "noerr": 0,
        "x": 390,
        "y": 1000,
        "wires": [["gov-udp-ctrl"]]
    },
    {
        "id": "gov-debug-status",
        "type": "debug",
        "z": "gov-flow",
        "name": "state snapshot",
        "active": True,
        "tosidebar": True,
        "console": False,
        "tostatus": True,
        "complete": "payload",
        "targetType": "msg",
        "x": 620,
        "y": 160,
        "wires": []
    }
]

flows.extend(new_nodes)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Done. Total: {len(flows)} nodes')
