import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

# Add debug node after his-fn-grubbs output[1] (T values going to chart)
debug_t = {
    "id": "dbg-grubbs-t",
    "type": "debug",
    "z": "his-flow-main",
    "name": "Grubbs T out",
    "active": True,
    "tosidebar": True,
    "console": False,
    "tostatus": True,
    "complete": "true",
    "targetType": "full",
    "statusVal": "payload",
    "statusType": "auto",
    "x": 620,
    "y": 150,
    "wires": []
}

# Add debug node after his-fn-grubbs output[0] (P values going to p-diffs)
debug_p = {
    "id": "dbg-grubbs-p",
    "type": "debug",
    "z": "his-flow-main",
    "name": "Grubbs P out",
    "active": True,
    "tosidebar": True,
    "console": False,
    "tostatus": True,
    "complete": "true",
    "targetType": "full",
    "statusVal": "payload",
    "statusType": "auto",
    "x": 620,
    "y": 250,
    "wires": []
}

for n in flows:
    if n.get('id') == 'his-fn-grubbs':
        # output[0] = P, output[1] = T, output[2] = RH, output[3] = faults
        n['wires'][0].append('dbg-grubbs-p')
        n['wires'][1].append('dbg-grubbs-t')
        print('Wired his-fn-grubbs P -> dbg-grubbs-p')
        print('Wired his-fn-grubbs T -> dbg-grubbs-t')
        break

flows.append(debug_t)
flows.append(debug_p)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
print('Done.')
