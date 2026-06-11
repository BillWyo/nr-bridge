"""
Replace all Python exec nodes in Music -- Play with pure Node.js:
  - Renderer discovery: dgram SSDP + http fetch (async function node)
  - Playlist listing:   require('fs') sync read
  - Playlist delete:    require('fs') sync unlink
"""
import json

FLOWS = r'flows\flows.json'
TAB   = 'music-flow-play'

# ── Node.js function bodies ────────────────────────────────────────────────────

FN_DISCOVER = """\
const dgram = require('dgram');
const http  = require('http');

const SSDP_ADDR = '239.255.255.250';
const SSDP_PORT = 1900;
const TIMEOUT   = 4000;

const searchBuf = Buffer.from(
    'M-SEARCH * HTTP/1.1\\r\\n' +
    'HOST: 239.255.255.250:1900\\r\\n' +
    'MAN: "ssdp:discover"\\r\\n' +
    'MX: 3\\r\\n' +
    'ST: urn:schemas-upnp-org:device:MediaRenderer:1\\r\\n\\r\\n'
);

const sock = dgram.createSocket('udp4');
const locations = new Set();

sock.on('message', buf => {
    buf.toString().split('\\r\\n').forEach(line => {
        if (line.toLowerCase().startsWith('location:'))
            locations.add(line.slice(line.indexOf(':') + 1).trim());
    });
});

sock.on('error', err => { node.warn('SSDP socket: ' + err.message); sock.close(); });

sock.bind(0, () => {
    try { sock.setMulticastTTL(2); } catch(e) {}
    sock.send(searchBuf, SSDP_PORT, SSDP_ADDR);
});

function fetchUrl(url) {
    return new Promise((resolve, reject) => {
        const req = http.get(url, { timeout: 4000 }, res => {
            let body = '';
            res.on('data', d => body += d);
            res.on('end', () => resolve(body));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    });
}

function tag(xml, name) {
    const m = xml.match(new RegExp('<' + name + '[^>]*>([^<]*)</' + name + '>', 'i'));
    return m ? m[1].trim() : '';
}

function stripNs(xml) {
    return xml.replace(/<[a-z][a-z0-9]*:/gi, '<').replace(/<\\/[a-z][a-z0-9]*:/gi, '</');
}

setTimeout(async () => {
    try { sock.close(); } catch(e) {}
    const baseRe = /^(https?:\\/\\/[^\\/]+)/;
    const renderers = [];
    for (const loc of locations) {
        try {
            const base = (loc.match(baseRe) || [])[1] || '';
            const raw  = await fetchUrl(loc);
            const xml  = stripNs(raw);
            if (!tag(xml, 'deviceType').includes('MediaRenderer')) continue;
            const name  = tag(xml, 'friendlyName') || loc;
            const model = tag(xml, 'modelName');
            let avUrl = null;
            const svcs = xml.match(/<service>[\\s\\S]*?<\\/service>/g) || [];
            for (const s of svcs) {
                if (!s.includes('AVTransport')) continue;
                const ctrl = tag(s, 'controlURL');
                avUrl = ctrl.startsWith('http') ? ctrl : base + ctrl;
                break;
            }
            if (!avUrl) continue;
            const ip = (base.match(/\\/\\/([^:\\/]+)/) || [])[1] || '';
            renderers.push({ name, model, ip, avTransportUrl: avUrl, location: loc });
        } catch(e) { node.warn('describe ' + loc + ': ' + e.message); }
    }
    renderers.sort((a, b) => a.name.localeCompare(b.name));
    flow.set('renderers', renderers);
    if (!flow.get('selectedRenderer') && renderers.length)
        flow.set('selectedRenderer', renderers[0]);
    node.send({ payload: { renderers } });
}, TIMEOUT);

return null;"""

FN_LIST_PLAYLISTS = """\
const fs   = require('fs');
const path = require('path');
const dir  = 'F:\\\\Music - Flac\\\\Playlists';
try {
    if (!fs.existsSync(dir)) { msg.payload = { playlists: [] }; return msg; }
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort();
    const result = [];
    for (const f of files) {
        try {
            const data = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
            result.push({ name: data.name || f.slice(0, -5),
                          trackCount: (data.tracks || []).length });
        } catch(e) {}
    }
    flow.set('playlists', result);
    msg.payload = { playlists: result };
    return msg;
} catch(e) {
    node.error(e.message);
    return null;
}"""

FN_DELETE_PLAYLIST = """\
const fs   = require('fs');
const path = require('path');
const dir  = 'F:\\\\Music - Flac\\\\Playlists';
const name = msg.payload.name;
try { fs.unlinkSync(path.join(dir, name + '.json')); }
catch(e) { node.warn('delete: ' + e.message); }
return msg;"""

# ── IDs to remove (old exec + helper fn pairs + debug nodes) ──────────────────
REMOVE_IDS = {
    'music-exec-discover', 'music-fn-renderers',
    'music-exec-list',     'music-fn-playlists',
    'music-fn-build-delete', 'music-exec-delete',
    'music-dbg-discover-out', 'music-dbg-discover-err', 'music-dbg-list-err',
}

# ── New replacement nodes ──────────────────────────────────────────────────────
def fn_node(id_, name, x, y, func, outputs=1, wires=None):
    return {
        'id': id_, 'type': 'function', 'z': TAB,
        'name': name, 'func': func,
        'outputs': outputs, 'noerr': 0,
        'initialize': '', 'finalize': '',
        'x': x, 'y': y,
        'wires': wires or [[]]
    }

NEW_NODES = [
    fn_node('music-fn-discover',       'Discover Renderers', 320, 60,  FN_DISCOVER,
            wires=[['music-tmpl']]),
    fn_node('music-fn-list-playlists', 'List Playlists',     320, 120, FN_LIST_PLAYLISTS,
            wires=[['music-tmpl']]),
    fn_node('music-fn-delete',         'Delete Playlist',    320, 460, FN_DELETE_PLAYLIST,
            wires=[['music-fn-list-playlists']]),
]

# ── Patch flows ────────────────────────────────────────────────────────────────
with open(FLOWS, encoding='utf-8') as f:
    flows = json.load(f)

# Remove old nodes
kept = [n for n in flows if n['id'] not in REMOVE_IDS and n['id'] not in {nd['id'] for nd in NEW_NODES}]

# Fix wiring on nodes that pointed to removed nodes
for n in kept:
    if n.get('id') == 'music-inject-startup':
        n['wires'] = [['music-fn-discover', 'music-fn-list-playlists']]
    elif n.get('id') == 'music-inject-list-refresh':
        n['wires'] = [['music-fn-list-playlists']]
    elif n.get('id') == 'music-fn-dispatch':
        n['wires'] = [
            ['music-fn-build-play'],   # 0 play
            ['music-fn-delete'],       # 1 delete
            ['music-fn-build-stop'],   # 2 stop
            ['music-fn-discover'],     # 3 refresh
            ['music-fn-set-renderer'], # 4 setRenderer
        ]

merged = kept + NEW_NODES

# Sanity
ids = [n['id'] for n in merged]
dupes = [i for i in set(ids) if ids.count(i) > 1]
print('Dupes:', dupes if dupes else 'none')
from collections import Counter
tab_map = {n['id']: n.get('label', n.get('name', '?')) for n in merged if not n.get('z')}
for tab_id, cnt in sorted(Counter(n.get('z','(cfg)') for n in merged).items()):
    print(f'  {cnt:3d}  {tab_map.get(tab_id, tab_id)}')
print('Total:', len(merged))

with open(FLOWS, 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
print('Written.')
