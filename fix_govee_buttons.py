import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

BUTTON_IDS = {
    'v2-btn-evening', 'v2-btn-bright', 'v2-btn-movie', 'v2-btn-alloff',
    'v2-btn-save-evening', 'v2-btn-save-bright', 'v2-btn-save-movie',
}

def btn(node_id, label, group, order, payload, color, text_color, wires, x, y, w=3, h=2):
    return {
        "id": node_id,
        "type": "ui-button",
        "z": "gov-flow",
        "group": group,
        "name": label,
        "label": label,
        "order": order,
        "width": str(w),
        "height": str(h),
        "icon": "",
        "iconPosition": "left",
        "payload": payload,
        "payloadType": "str",
        "topic": "preset",
        "topicType": "str",
        "buttonColor": color,
        "textColor": text_color,
        "iconColor": text_color,
        "className": "",
        "x": x,
        "y": y,
        "wires": [wires],
    }

FIXED_BUTTONS = [
    # Preset buttons
    btn("v2-btn-evening",    "Evening",     "v2-grp-govee-presets", 1, "Evening",  "#f5a623", "#000000", ["gov-fn-apply-preset"], 200, 1100),
    btn("v2-btn-bright",     "Bright",      "v2-grp-govee-presets", 2, "Bright",   "#fffde7", "#000000", ["gov-fn-apply-preset"], 200, 1160),
    btn("v2-btn-movie",      "Movie",       "v2-grp-govee-presets", 3, "Movie",    "#4a3580", "#ffffff", ["gov-fn-apply-preset"], 200, 1220),
    btn("v2-btn-alloff",     "All Off",     "v2-grp-govee-presets", 4, "All Off",  "#333333", "#ffffff", ["gov-fn-apply-preset"], 200, 1280),
    # Save buttons
    btn("v2-btn-save-evening", "Save Evening", "v2-grp-govee-save", 1, "Evening",  "#f5a623", "#000000", ["gov-fn-save-preset"],  210, 1460, w=4, h=1),
    btn("v2-btn-save-bright",  "Save Bright",  "v2-grp-govee-save", 2, "Bright",   "#fffde7", "#000000", ["gov-fn-save-preset"],  210, 1520, w=4, h=1),
    btn("v2-btn-save-movie",   "Save Movie",   "v2-grp-govee-save", 3, "Movie",    "#4a3580", "#ffffff", ["gov-fn-save-preset"],  210, 1580, w=4, h=1),
]

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

# Remove old button nodes
flows = [n for n in flows if n.get('id') not in BUTTON_IDS]

# Add fixed versions
flows.extend(FIXED_BUTTONS)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Replaced {len(FIXED_BUTTONS)} button nodes. Total: {len(flows)}')
