import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# MQTT node IDs that need rap: true so msg.retain is correct for retained messages
FIX_RAP = {'gov-mqtt-ctrl', 'gov-mqtt-visitor', 'gov-mqtt-alarm'}

# Topics to clear in the auto-clear function
CLEAR_TOPICS = [
    'home/lights/set',
    'home/frontdoor/visitor',
    'home/frontdoor/alarm',
    'home/bills-office/alarm',
    'home/mud-room/alarm',
    'home/garage/alarm',
]

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

patched = []

for n in flows:
    nid = n.get('id')

    if nid in FIX_RAP:
        n['rap'] = True
        patched.append(nid + ' rap=true')

    if nid == 'gov-fn-clear-retained':
        n['func'] = (
            'var topics = ' + json.dumps(CLEAR_TOPICS) + ';\n'
            'return topics.map(function(t) {\n'
            '    return { topic: t, payload: \'\', retain: true };\n'
            '});'
        )
        patched.append(nid + ' (expanded topics)')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print('Patched:', patched)
