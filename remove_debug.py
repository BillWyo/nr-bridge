import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

DEBUG_IDS = {'dbg-pth-raw', 'dbg-grubbs-t', 'dbg-grubbs-p'}

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

cleaned = []
for n in flows:
    if n['id'] in DEBUG_IDS:
        print('Removed:', n['id'])
        continue
    if 'wires' in n:
        n['wires'] = [[nid for nid in out if nid not in DEBUG_IDS] for out in n['wires']]
    cleaned.append(n)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, indent=2, ensure_ascii=False)
print(f'Done: {len(cleaned)} nodes')
