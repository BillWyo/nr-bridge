"""
Restore HIS Main + Photo Booth to current flows (Govee + Music).

Sources:
  HIS Main   — git f8816dc  (June 3, most recent HIS state, 50 nodes)
  Photo Booth — git 98a1640  (May 22, unchanged since)
  UI config   — git 98a1640  (ui-base, ui-theme, ui-pages, ui-groups)
  his-broker  — git 98a1640
  Govee       — current flows/flows.json
  Music       — current flows/flows.json  (deduplicated; nis-broker → mqtt-broker-music)
"""
import json, subprocess

FLOWS_PATH = r'flows\flows.json'

def git_load(ref):
    out = subprocess.check_output(
        ['git', 'show', f'{ref}:flows/flows.json'],
        cwd=r'C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge'
    )
    return json.loads(out)

# ── load sources ───────────────────────────────────────────────────────────────
his_snap  = git_load('f8816dc')   # June 3 — HIS Main only
full_may  = git_load('98a1640')   # May 22  — full state

with open(FLOWS_PATH, encoding='utf-8') as f:
    current = json.load(f)

# ── helper: nodes belonging to a tab ──────────────────────────────────────────
def tab_nodes(flows, tab_id):
    return [n for n in flows if n.get('id') == tab_id or n.get('z') == tab_id]

# ── 1. UI config nodes from May 22 (ui-base, ui-theme, ui-pages, ui-groups) ──
ui_types = {'ui-base', 'ui-theme', 'ui-page', 'ui-group'}
ui_cfg = [n for n in full_may if n.get('type') in ui_types]

# ── 2. his-broker from May 22 ─────────────────────────────────────────────────
his_broker = [n for n in full_may if n.get('id') == 'his-broker']

# ── 3. HIS Main from June 3 ───────────────────────────────────────────────────
his_nodes = tab_nodes(his_snap, 'his-flow-main')

# ── 4. Photo Booth from May 22 ───────────────────────────────────────────────
pb_nodes = tab_nodes(full_may, 'pb-flow-main')

# ── 5. Govee from current (deduplicate by id) ─────────────────────────────────
gov_nodes_raw = tab_nodes(current, 'gov-flow')
seen = set()
gov_nodes = []
for n in gov_nodes_raw:
    if n['id'] not in seen:
        seen.add(n['id'])
        gov_nodes.append(n)

# ── 6. Music from current (deduplicate by id, fix nis-broker) ─────────────────
music_tabs = {'music-flow-create', 'music-flow-play'}
music_nodes_raw = [n for n in current
                   if n.get('id') in music_tabs or n.get('z') in music_tabs]
seen = set()
music_nodes = []
for n in music_nodes_raw:
    if n['id'] not in seen:
        seen.add(n['id'])
        n2 = dict(n)
        if n2.get('broker') == 'nis-broker':
            n2['broker'] = 'mqtt-broker-music'
        music_nodes.append(n2)

# ── 7. Music broker ───────────────────────────────────────────────────────────
music_broker = [n for n in current if n.get('id') == 'mqtt-broker-music']

# ── assemble ──────────────────────────────────────────────────────────────────
merged = (ui_cfg + his_broker + music_broker +
          his_nodes + pb_nodes + gov_nodes + music_nodes)

# sanity: no duplicate IDs
ids = [n['id'] for n in merged]
dupes = [i for i in ids if ids.count(i) > 1]
if dupes:
    print('WARNING — duplicate IDs:', set(dupes))
else:
    print('No duplicate IDs')

# count by tab
from collections import Counter
tab_map = {n['id']: n.get('label', n.get('name', n['id']))
           for n in merged if not n.get('z')}
counts = Counter(n.get('z', '(config)') for n in merged)
for tab_id, cnt in sorted(counts.items()):
    label = tab_map.get(tab_id, tab_id)
    print(f'  {cnt:3d}  {label}')
print(f'Total: {len(merged)}')

with open(FLOWS_PATH, 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
print('Written flows/flows.json')
