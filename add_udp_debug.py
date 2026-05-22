import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

# Add debug tap to every node that wires to gov-udp-ctrl
tapped = 0
for n in flows:
    for out in n.get('wires', []):
        if 'gov-udp-ctrl' in out and 'gov-debug-udp' not in out:
            out.append('gov-debug-udp')
            tapped += 1

# Add the debug node
flows.append({
    "id": "gov-debug-udp",
    "type": "debug",
    "z": "gov-flow",
    "name": "UDP out tap",
    "active": True,
    "tosidebar": True,
    "console": False,
    "tostatus": True,
    "complete": "true",
    "targetType": "full",
    "x": 960,
    "y": 300,
    "wires": []
})

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Tapped {tapped} wires. Total nodes: {len(flows)}')
