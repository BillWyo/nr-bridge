import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

patched = []

for n in flows:
    nid = n.get('id')

    # ── Diagnostic warn() at top of each colorwc-capable function ─────────────

    if nid == 'gov-fn-mqtt-ctrl':
        n['func'] = (
            "node.warn('SRC:mqtt-ctrl retain=' + msg.retain + ' payload=' + JSON.stringify(msg.payload));\n"
            + n['func']
        )
        patched.append(nid)

    elif nid == 'gov-fn-visitor':
        n['func'] = (
            "node.warn('SRC:visitor retain=' + msg.retain);\n"
            + n['func']
        )
        patched.append(nid)

    elif nid == 'gov-fn-alarm':
        n['func'] = (
            "node.warn('SRC:alarm retain=' + msg.retain);\n"
            + n['func']
        )
        patched.append(nid)

    elif nid == 'gov-fn-all-colortemp':
        n['func'] = (
            "node.warn('SRC:colortemp-slider value=' + msg.payload);\n"
            + n['func']
        )
        patched.append(nid)

    elif nid == 'gov-fn-color-cmd':
        n['func'] = (
            "node.warn('SRC:color-cmd payload=' + JSON.stringify(msg.payload));\n"
            + n['func']
        )
        patched.append(nid)

    # ── Auto-clear retained MQTT messages 1 s after startup ───────────────────
    elif nid == 'gov-inject-clear-retained':
        n['once']      = True
        n['onceDelay'] = 1
        patched.append(nid + ' (auto-fire at 1s)')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print('Patched:', patched)
