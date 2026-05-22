import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# Only restore lights to warm-white when transitioning FROM alarm-red back to clear.
# Routine "alert:false" sensor readings are ignored if lights were never set to red.
FN_ALARM = """\
if (msg.retain) return null;
if (!msg.payload || typeof msg.payload !== 'object') return null;

if (msg.payload.alert === true) {
    flow.set('govee_alarm_active', true);
    msg.govee_cmd     = {cmd:'colorwc', data:{color:{r:255,g:0,b:0}, colorTemInKelvin:0}};
    msg.govee_targets = 'all';
    return msg;
}

if (msg.payload.alert === false) {
    if (!flow.get('govee_alarm_active')) return null;  // not in alarm - ignore routine sensor readings
    flow.set('govee_alarm_active', false);
    msg.govee_cmd     = {cmd:'colorwc', data:{color:{r:0,g:0,b:0}, colorTemInKelvin:3000}};
    msg.govee_targets = 'all';
    return msg;
}

return null;  // no alert field - discard"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'gov-fn-alarm':
        n['func'] = FN_ALARM
        print('Patched gov-fn-alarm')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
