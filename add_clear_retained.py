import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

FN_CLEAR = """\
var topics = [
    'home/lights/set',
    'home/frontdoor/visitor',
    'home/frontdoor/alarm'
];
return topics.map(function(t) {
    return { topic: t, payload: '', retain: true };
});"""

new_nodes = [
    {
        "id": "gov-inject-clear-retained",
        "type": "inject",
        "z": "gov-flow",
        "name": "Clear retained MQTT",
        "props": [{"p": "payload"}],
        "repeat": "",
        "crontab": "",
        "once": False,
        "payload": "",
        "payloadType": "date",
        "x": 180,
        "y": 840,
        "wires": [["gov-fn-clear-retained"]]
    },
    {
        "id": "gov-fn-clear-retained",
        "type": "function",
        "z": "gov-flow",
        "name": "build clear msgs",
        "func": FN_CLEAR,
        "outputs": 1,
        "noerr": 0,
        "x": 400,
        "y": 840,
        "wires": [["gov-mqtt-clear-out"]]
    },
    {
        "id": "gov-mqtt-clear-out",
        "type": "mqtt out",
        "z": "gov-flow",
        "name": "clear retained",
        "topic": "",
        "qos": "0",
        "retain": "true",
        "broker": "his-broker",
        "x": 620,
        "y": 840,
        "wires": []
    }
]

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

flows.extend(new_nodes)

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)

print(f'Added {len(new_nodes)} nodes. Total: {len(flows)}')
