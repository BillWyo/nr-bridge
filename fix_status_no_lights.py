import json

FLOWS_PATH = r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json'

NEW_FORMAT = (
    "<template>\n"
    "  <div v-if=\"msg && msg.payload\" class=\"ns\">\n"
    "    <table>\n"
    "      <thead><tr><th>Node</th><th>Last seen</th></tr></thead>\n"
    "      <tbody>\n"
    "        <tr v-for=\"r in msg.payload\" :key=\"r.node\">\n"
    "          <td>{{ r.node }}</td>\n"
    "          <td>{{ r.age }}</td>\n"
    "        </tr>\n"
    "      </tbody>\n"
    "    </table>\n"
    "  </div>\n"
    "</template>\n"
    "<style scoped>\n"
    ".ns { font-family: monospace; font-size: 13px }\n"
    ".ns table { width: 100%; border-collapse: collapse }\n"
    ".ns th, .ns td { padding: 4px 12px; border-bottom: 1px solid #444 }\n"
    ".ns th { color: #0d162b; text-align: left }\n"
    "</style>"
)

with open(FLOWS_PATH, encoding='utf-8') as f:
    flows = json.load(f)

for n in flows:
    if n.get('id') == 'v2-tmpl-status':
        n['format'] = NEW_FORMAT
        print('Patched v2-tmpl-status')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(flows, f, indent=2, ensure_ascii=False)
