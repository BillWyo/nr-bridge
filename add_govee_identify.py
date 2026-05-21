import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

DEVICES = [
    ("23:99:5C:E7:53:E6:17:B2", "192.168.1.30", "gov-inject-id-1", "Bulb A  .30"),
    ("47:A7:5C:E7:53:F0:80:74", "192.168.1.29", "gov-inject-id-2", "Bulb B  .29"),
    ("15:A2:5C:E7:53:F2:38:D8", "192.168.1.32", "gov-inject-id-3", "Bulb C  .32"),
    ("10:31:5C:E7:53:ED:FA:78", "192.168.1.31", "gov-inject-id-4", "Bulb D  .31"),
]

new_nodes = []

for i, (device_id, ip, node_id, label) in enumerate(DEVICES):
    payload = json.dumps({"cmd": "turn", "value": 1, "devices": [device_id]})
    new_nodes.append({
        "id": node_id,
        "type": "inject",
        "z": "gov-flow",
        "name": label,
        "props": [{"p": "payload"}],
        "repeat": "",
        "crontab": "",
        "once": False,
        "payload": payload,
        "payloadType": "json",
        "x": 180,
        "y": 520 + i * 60,
        "wires": [["gov-fn-mqtt-ctrl"]]
    })

all_off_payload = json.dumps({"cmd": "turn", "value": 0, "devices": "all"})
new_nodes.append({
    "id": "gov-inject-all-off",
    "type": "inject",
    "z": "gov-flow",
    "name": "All OFF",
    "props": [{"p": "payload"}],
    "repeat": "",
    "crontab": "",
    "once": False,
    "payload": all_off_payload,
    "payloadType": "json",
    "x": 180,
    "y": 760,
    "wires": [["gov-fn-mqtt-ctrl"]]
})

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

flows.extend(new_nodes)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Added {len(new_nodes)} nodes. Total: {len(flows)}')
