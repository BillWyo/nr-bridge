import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

# Apply preset: output 1 = UDP commands, output 2 = reference state for sliders
FN_APPLY_PRESET = """\
var name    = msg.payload;
var devs    = flow.get('govee_devices') || {};
var nameMap = flow.get('govee_names')   || {};
if (!Object.keys(devs).length) { node.warn('Run discovery first'); return null; }

if (name === 'All Off') {
    var msgs = Object.values(devs).map(function(d) {
        return {payload:JSON.stringify({msg:{cmd:'turn',data:{value:0}}}), ip:d.ip, port:4003};
    });
    return [[msgs], null];
}

var presets = flow.get('govee_presets') || {};
var preset  = presets[name];
if (!preset) { node.warn('Preset not found: ' + name); return null; }

var msgs = [];
Object.keys(preset).forEach(function(devName) {
    var state = preset[devName];
    var dev   = devs[nameMap[devName]];
    if (!dev) return;
    msgs.push({payload:JSON.stringify({msg:{cmd:'turn',      data:{value:state.onOff}}}),                                                            ip:dev.ip, port:4003});
    msgs.push({payload:JSON.stringify({msg:{cmd:'brightness', data:{value:state.brightness}}}),                                                       ip:dev.ip, port:4003});
    msgs.push({payload:JSON.stringify({msg:{cmd:'colorwc',    data:{color:state.color||{r:0,g:0,b:0}, colorTemInKelvin:state.colorTemInKelvin||0}}}), ip:dev.ip, port:4003});
});

var ref = preset['lvgrm_1'] || Object.values(preset)[0];
return [[msgs], {payload: ref}];"""

# Save preset: output 1 = JSON for file write, output 2 = reference state for sliders
FN_SAVE_PRESET = """\
var name     = msg.payload;
var snapshot = flow.get('govee_snapshot') || {};
if (!Object.keys(snapshot).length) { node.warn('No snapshot - click Read state first'); return null; }
var presets  = flow.get('govee_presets') || {};
presets[name] = JSON.parse(JSON.stringify(snapshot));
flow.set('govee_presets', presets);
node.status({fill:'green', shape:'dot', text: name + ' saved'});
var ref = snapshot['lvgrm_1'] || Object.values(snapshot)[0];
return [{payload: JSON.stringify(presets, null, 2)}, {payload: ref}];"""

# Extract reference values and send to sliders
FN_UPDATE_SLIDERS = """\
var ref = msg.payload;
if (!ref) return null;
var brightness = (ref.brightness !== undefined) ? ref.brightness : 50;
var colortemp  = ref.colorTemInKelvin || 3000;
return [{payload: brightness}, {payload: colortemp}];"""

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'gov-fn-apply-preset':
        n['func']    = FN_APPLY_PRESET
        n['outputs'] = 2
        n['wires']   = [['gov-udp-ctrl'], ['gov-fn-update-sliders']]
        print('Updated gov-fn-apply-preset')

    if n.get('id') == 'gov-fn-save-preset':
        n['func']    = FN_SAVE_PRESET
        n['outputs'] = 2
        n['wires']   = [['gov-file-write-presets'], ['gov-fn-update-sliders']]
        print('Updated gov-fn-save-preset')

# Add the slider-update function
flows.append({
    "id": "gov-fn-update-sliders",
    "type": "function",
    "z": "gov-flow",
    "name": "update sliders",
    "func": FN_UPDATE_SLIDERS,
    "outputs": 2,
    "noerr": 0,
    "x": 460,
    "y": 1700,
    "wires": [["v2-slider-brightness"], ["v2-slider-colortemp"]]
})
print('Added gov-fn-update-sliders')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Done. Total: {len(flows)}')
