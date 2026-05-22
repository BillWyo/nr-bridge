import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# ── Strict alarm guard ─────────────────────────────────────────────────────────
# Only act if payload has alert:true (red) or alert:false (warm white restore).
# Anything else (junk, malformed, wrong topic) is silently discarded.
FN_ALARM = """\
node.warn('SRC:alarm topic=' + msg.topic + ' retain=' + msg.retain + ' payload=' + JSON.stringify(msg.payload));
if (msg.retain) return null;
if (!msg.payload || typeof msg.payload !== 'object') return null;
if (msg.payload.alert === true) {
    msg.govee_cmd = {cmd:'colorwc', data:{color:{r:255,g:0,b:0}, colorTemInKelvin:0}};
} else if (msg.payload.alert === false) {
    msg.govee_cmd = {cmd:'colorwc', data:{color:{r:0,g:0,b:0}, colorTemInKelvin:3000}};
} else {
    node.warn('alarm: no alert field - discarded');
    return null;
}
msg.govee_targets = 'all';
return msg;"""

# ── Strict visitor guard ───────────────────────────────────────────────────────
# Only act if payload has a 'trigger' field (from the camera firmware).
FN_VISITOR = """\
node.warn('SRC:visitor topic=' + msg.topic + ' retain=' + msg.retain + ' payload=' + JSON.stringify(msg.payload));
if (msg.retain) return null;
if (!msg.payload || !msg.payload.trigger) { node.warn('visitor: no trigger field - discarded'); return null; }
msg.govee_cmd     = {cmd:'colorwc', data:{color:{r:0,g:0,b:0}, colorTemInKelvin:3000}};
msg.govee_targets = 'all';
return msg;"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

patched = []

for n in flows:
    nid = n.get('id')
    if nid == 'gov-fn-alarm':
        n['func'] = FN_ALARM
        patched.append(nid)
    elif nid == 'gov-fn-visitor':
        n['func'] = FN_VISITOR
        patched.append(nid)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print('Patched:', patched)
