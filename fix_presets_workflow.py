import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# apply-preset: default onOff to 1 (on) when missing from saved preset
FN_APPLY_PRESET = """\
var name    = msg.payload;
var devs    = flow.get('govee_devices') || {};
var nameMap = flow.get('govee_names')   || {};
if (!Object.keys(devs).length) { node.warn('Run discovery first'); return null; }

if (name === 'All Off') {
    flow.set('govee_current', {onOff:0, brightness:0, colortemp:4000, color:{r:0,g:0,b:0}, mode:'white'});
    var msgs = Object.values(devs).map(function(d) {
        return {payload:JSON.stringify({msg:{cmd:'turn',data:{value:0}}}), ip:d.ip, port:4003};
    });
    return [msgs, null];
}

var presets = flow.get('govee_presets') || {};
var preset  = presets[name];
if (!preset) { node.warn('Preset not found: ' + name + ' (use sliders + Save to create it)'); return null; }
flow.set('govee_current', preset);

var msgs = [];
Object.values(devs).forEach(function(d) {
    var onOff = (preset.onOff !== undefined) ? preset.onOff : 1;
    msgs.push({payload:JSON.stringify({msg:{cmd:'turn',      data:{value:onOff}}}),                                    ip:d.ip, port:4003});
    msgs.push({payload:JSON.stringify({msg:{cmd:'brightness', data:{value:preset.brightness || 50}}}),                 ip:d.ip, port:4003});
    var colorData = preset.mode === 'color'
        ? {color: preset.color, colorTemInKelvin: 0}
        : {color: {r:0,g:0,b:0}, colorTemInKelvin: preset.colortemp || 4000};
    msgs.push({payload:JSON.stringify({msg:{cmd:'colorwc', data:colorData}}), ip:d.ip, port:4003});
});
return [msgs, {payload: preset}];"""

# save-preset: fill in any missing fields so the saved preset is always complete
FN_SAVE_PRESET = """\
var name    = msg.payload;
var current = flow.get('govee_current') || {};
if (!Object.keys(current).length) { node.warn('Use sliders first to set brightness/colortemp, then save'); return null; }

// Ensure all required fields are present
current.onOff      = (current.onOff !== undefined) ? current.onOff : 1;
current.brightness = (current.brightness !== undefined) ? current.brightness : 50;
current.colortemp  = current.colortemp  || 4000;
current.color      = current.color      || {r:255, g:136, b:0};
current.mode       = current.mode       || 'white';

var presets = flow.get('govee_presets') || {};
presets[name] = JSON.parse(JSON.stringify(current));
flow.set('govee_presets', presets);
node.status({fill:'green', shape:'dot', text: name + ' saved'});
msg.payload = JSON.stringify(presets, null, 2);
return msg;"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

patched = []
for n in flows:
    nid = n.get('id')
    if nid == 'gov-fn-apply-preset':
        n['func'] = FN_APPLY_PRESET
        patched.append(nid)
    elif nid == 'gov-fn-save-preset':
        n['func'] = FN_SAVE_PRESET
        patched.append(nid)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print('Patched:', patched)
