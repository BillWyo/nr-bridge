import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

# Add a debug node wired after his-mqtt-pth to show raw MQTT messages
debug_node = {
    "id": "dbg-pth-raw",
    "type": "debug",
    "z": "his-flow-main",
    "name": "PTH raw",
    "active": True,
    "tosidebar": True,
    "console": False,
    "tostatus": True,
    "complete": "true",
    "targetType": "full",
    "statusVal": "payload",
    "statusType": "auto",
    "x": 160,
    "y": 180,
    "wires": []
}

# Wire his-mqtt-pth to also send to debug node
for n in flows:
    if n.get('id') == 'his-mqtt-pth':
        n['wires'][0].append('dbg-pth-raw')
        print('Wired his-mqtt-pth -> dbg-pth-raw')
        break

flows.append(debug_node)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
print('Done.')
