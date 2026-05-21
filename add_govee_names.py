import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

NAMES = {
    'lvgrm_1': '47:A7:5C:E7:53:F0:80:74',
    'lvgrm_2': '23:99:5C:E7:53:E6:17:B2',
    'lvgrm_3': '10:31:5C:E7:53:ED:FA:78',
    'lvgrm_4': '15:A2:5C:E7:53:F2:38:D8',
}

FN_SET_NAMES = (
    "flow.set('govee_names', {\n" +
    "".join(f"    '{k}': '{v}',\n" for k, v in NAMES.items()) +
    "});\nreturn null;"
)

# Updated gov-fn-send: resolves names before device ID lookup
FN_SEND = """\
// Expects: msg.govee_cmd     = {cmd:'...', data:{...}}
//          msg.govee_targets = 'all' | ['name-or-device-id', ...]
var devs     = flow.get('govee_devices') || {};
var nameMap  = flow.get('govee_names')   || {};
if (!Object.keys(devs).length) { node.warn('No Govee devices found - run discovery first'); return null; }

var targets;
if (!msg.govee_targets || msg.govee_targets === 'all') {
    targets = Object.values(devs);
} else {
    var ids = Array.isArray(msg.govee_targets) ? msg.govee_targets : [msg.govee_targets];
    ids = ids.map(function(t) { return nameMap[t] || t; });
    targets = ids.map(function(id) { return devs[id]; }).filter(Boolean);
}
if (!targets.length) { node.warn('No matching Govee devices'); return null; }

var msgs = targets.map(function(d) {
    return { payload: JSON.stringify({msg: msg.govee_cmd}), ip: d.ip, port: 4003 };
});
return [msgs];"""

# Identify inject node updates: name → lvgrm label + name-based device targeting
IDENTIFY_UPDATES = {
    'gov-inject-id-1': ('lvgrm_2', json.dumps({"cmd":"turn","value":1,"devices":["lvgrm_2"]})),
    'gov-inject-id-2': ('lvgrm_1', json.dumps({"cmd":"turn","value":1,"devices":["lvgrm_1"]})),
    'gov-inject-id-3': ('lvgrm_4', json.dumps({"cmd":"turn","value":1,"devices":["lvgrm_4"]})),
    'gov-inject-id-4': ('lvgrm_3', json.dumps({"cmd":"turn","value":1,"devices":["lvgrm_3"]})),
}

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    # Update gov-fn-send
    if n.get('id') == 'gov-fn-send':
        n['func'] = FN_SEND
        print('Updated gov-fn-send')

    # Update identify inject nodes
    if n.get('id') in IDENTIFY_UPDATES:
        label, payload = IDENTIFY_UPDATES[n['id']]
        n['name'] = label
        n['payload'] = payload
        print(f"Updated {n['id']} -> {label}")

# Add startup name-assignment nodes
flows.extend([
    {
        "id": "gov-inject-names",
        "type": "inject",
        "z": "gov-flow",
        "name": "Set bulb names",
        "props": [{"p": "payload"}],
        "repeat": "",
        "crontab": "",
        "once": True,
        "onceDelay": 5,
        "payload": "",
        "payloadType": "date",
        "x": 180,
        "y": 920,
        "wires": [["gov-fn-set-names"]]
    },
    {
        "id": "gov-fn-set-names",
        "type": "function",
        "z": "gov-flow",
        "name": "store name map",
        "func": FN_SET_NAMES,
        "outputs": 1,
        "noerr": 0,
        "x": 400,
        "y": 920,
        "wires": [[]]
    }
])

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Done. Total: {len(flows)} nodes')
