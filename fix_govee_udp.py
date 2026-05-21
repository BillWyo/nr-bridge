import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'gov-udp-out':
        n['addr']      = '239.255.255.250'
        n['multicast'] = 'true'
        print('Fixed gov-udp-out: multicast 239.255.255.250')
    # scan message also needs to target the multicast address
    if n.get('id') == 'gov-fn-scan-msg':
        n['func'] = (
            'msg.payload = JSON.stringify({"msg":{"cmd":"scan","data":{"account_topic":"reserve"}}});\n'
            'msg.ip   = "239.255.255.250";\n'
            'msg.port = 4001;\n'
            'return msg;'
        )
        print('Fixed gov-fn-scan-msg: multicast address')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
print('Done.')
