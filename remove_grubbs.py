import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

DELETE_IDS = {
    'his-fn-grubbs',
    'his-fn-fault-collect',
    'his-fn-grubbs-reset',
    'his-inject-reset-bo',
    'his-inject-reset-mr',
    'his-inject-reset-ga',
    'his-inject-reset-all',
    'v2-tmpl-faults',
}

NEW_SPLIT_NODE = {
    "id": "his-fn-split-pth",
    "type": "function",
    "z": "his-flow-main",
    "name": "Split P/T/RH",
    "func": (
        "var nodeId = msg.topic.split('/')[1];\n"
        "var d = msg.payload;\n"
        "function mk(v) { return { payload: v, _nodeId: nodeId, topic: nodeId }; }\n"
        "return [ mk(d.P), mk(d.T), mk(d.RH) ];"
    ),
    "outputs": 3,
    "noerr": 0,
    "x": 380,
    "y": 120,
    "wires": [
        ["his-fn-p-diffs"],
        ["v2-chart-temp"],
        ["his-fn-rh-summary"]
    ]
}

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

before = len(flows)

# Remove Grubbs nodes
flows = [n for n in flows if n.get('id') not in DELETE_IDS]

# Rewire his-mqtt-pth: replace his-fn-grubbs with his-fn-split-pth
for n in flows:
    if n.get('id') == 'his-mqtt-pth':
        wires = n.get('wires', [[]])
        new_wire = []
        for w in wires[0]:
            if w == 'his-fn-grubbs':
                new_wire.append('his-fn-split-pth')
            else:
                new_wire.append(w)
        n['wires'] = [new_wire]
        print('Rewired his-mqtt-pth:', n['wires'])

# Add the new split node
flows.append(NEW_SPLIT_NODE)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

after = len(flows)
print(f'Removed {before - after + 1} nodes (deleted {before - after + 1 - 1} Grubbs + added 1 split). Total: {after}')
