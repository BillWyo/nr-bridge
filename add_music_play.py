"""
Replace Music -- Play tab with full UPnP playlist management + playback.
Adds v2-page-music + v2-grp-music-main UI config nodes.
Keeps Music -- Create tab unchanged, but refreshes playlist list after save.
"""
import json

FLOWS = r'flows\flows.json'

NRB = r'C:\\Users\\johan\\Documents\\PlatformIO\\Projects\\NR_Bridge'
DISCOVER_CMD = f'python "{NRB}\\\\discover_renderers.py"'
LIST_CMD     = f'python "{NRB}\\\\list_playlists.py"'
DELETE_CMD_PREFIX = f'python "{NRB}\\\\delete_playlist.py"'  # + " " + name appended in fn

TAB = 'music-flow-play'

# ── Vue SFC template ──────────────────────────────────────────────────────────
TMPL = """\
<template>
  <div class="music-panel">
    <div class="section">
      <div class="sec-title">Renderer
        <button class="icon-btn" @click="doAction('refresh')" title="Refresh">&#x21BB;</button>
      </div>
      <div v-if="!renderers.length" class="muted">Scanning&hellip;</div>
      <label v-for="r in renderers" :key="r.avTransportUrl" class="renderer-row">
        <input type="radio" :value="r.avTransportUrl" v-model="selectedUrl"
               @change="doAction('setRenderer', {renderer: r})"> {{ r.name }}
      </label>
    </div>

    <div class="section">
      <div class="sec-title">Playlists</div>
      <div v-if="!playlists.length" class="muted">No playlists saved</div>
      <div v-for="pl in playlists" :key="pl.name" class="pl-row">
        <span class="pl-name">{{ pl.name }}</span>
        <span class="muted">{{ pl.trackCount }}&thinsp;t</span>
        <button class="btn-play" @click="doPlay(pl.name)" :disabled="!selectedUrl">&#x25B6;</button>
        <button class="btn-del"  @click="doDel(pl.name)">&#x2715;</button>
      </div>
    </div>

    <div class="section now" v-if="nowPlaying">
      <div class="sec-title">Now Playing
        <button class="btn-stop" @click="doAction('stop')">&#x25A0; Stop</button>
      </div>
      <div class="np-title">{{ nowPlaying.title }}</div>
      <div class="muted">{{ nowPlaying.album }}</div>
      <div class="muted">Track {{ nowPlaying.index + 1 }} / {{ nowPlaying.total }} &mdash; {{ nowPlaying.playlist }}</div>
    </div>
  </div>
</template>
<script>
export default {
  data() {
    return { renderers: [], playlists: [], selectedUrl: null, nowPlaying: null };
  },
  watch: {
    msg(v) {
      if (!v || !v.payload) return;
      const p = v.payload;
      if (p.renderers  !== undefined) this.renderers  = p.renderers;
      if (p.playlists  !== undefined) this.playlists  = p.playlists;
      if (p.nowPlaying !== undefined) this.nowPlaying = p.nowPlaying;
      if (this.renderers.length && !this.selectedUrl)
        this.selectedUrl = this.renderers[0].avTransportUrl;
    }
  },
  methods: {
    doAction(action, extra) {
      const renderer = this.renderers.find(r => r.avTransportUrl === this.selectedUrl) || null;
      this.send({ payload: { action, renderer, ...(extra || {}) } });
    },
    doPlay(name) { this.doAction('play', { name }); },
    doDel(name)  {
      if (!confirm('Delete "' + name + '"?')) return;
      this.doAction('delete', { name });
    }
  }
}
</script>
<style scoped>
.music-panel { padding: 8px; font-size: 14px; }
.section { margin-bottom: 14px; }
.sec-title { font-weight: bold; border-bottom: 1px solid #444; padding-bottom: 3px; margin-bottom: 6px; }
.renderer-row { display: block; margin: 3px 0; cursor: pointer; }
.pl-row { display: flex; align-items: center; gap: 6px; padding: 3px 0; border-bottom: 1px solid #2a2a2a; }
.pl-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.btn-play { background: #1e5e1e; border: none; color: #ddd; padding: 2px 8px; border-radius: 3px; cursor: pointer; }
.btn-play:disabled { background: #333; color: #666; cursor: not-allowed; }
.btn-del  { background: #5e1e1e; border: none; color: #ddd; padding: 2px 6px; border-radius: 3px; cursor: pointer; }
.btn-stop { background: #5e1e1e; border: none; color: #ddd; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 12px; margin-left: 8px; }
.icon-btn { background: none; border: none; color: #888; cursor: pointer; font-size: 15px; margin-left: 6px; }
.now { background: #111d11; padding: 8px; border-radius: 4px; }
.np-title { font-size: 15px; font-weight: bold; margin-bottom: 2px; }
.muted { color: #888; font-size: 12px; }
</style>"""

# ── helper: build a SOAP envelope ─────────────────────────────────────────────
def _soap_js(action, body_inner):
    """Return a JS expression string for a SOAP envelope."""
    return (
        "'<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\">"
        f"<s:Body><u:{action} xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">"
        + body_inner +
        f"</u:{action}></s:Body></s:Envelope>'"
    )

# ── JS function bodies ─────────────────────────────────────────────────────────

FN_STORE_RENDERERS = """\
try { var list = JSON.parse(msg.payload); } catch(e) { return null; }
flow.set('renderers', list);
if (!flow.get('selectedRenderer') && list.length)
    flow.set('selectedRenderer', list[0]);
msg.payload = { renderers: list };
return msg;"""

FN_STORE_PLAYLISTS = """\
try { var list = JSON.parse(msg.payload); } catch(e) { return null; }
flow.set('playlists', list);
msg.payload = { playlists: list };
return msg;"""

FN_DISPATCH = """\
var a = msg.payload.action;
if (a === 'play')        return [msg, null, null, null, null];
if (a === 'delete')      return [null, msg, null, null, null];
if (a === 'stop')        return [null, null, msg, null, null];
if (a === 'refresh')     return [null, null, null, msg, null];
if (a === 'setRenderer') return [null, null, null, null, msg];
return null;"""

FN_BUILD_PLAY = """\
var renderer = msg.payload.renderer || flow.get('selectedRenderer');
flow.set('selectedRenderer', renderer);
msg._renderer = renderer;
msg.filename = 'F:\\\\Music - Flac\\\\Playlists\\\\' + msg.payload.name + '.json';
return msg;"""

FN_START_PLAYBACK = """\
var data = JSON.parse(msg.payload);
var renderer = msg._renderer || flow.get('selectedRenderer');
flow.set('queue', { playlist: data.name, tracks: data.tracks, index: 0, renderer: renderer });
var t = data.tracks[0];
msg.url     = renderer.avTransportUrl;
msg.method  = 'POST';
msg.headers = { 'Content-Type': 'text/xml; charset=utf-8',
                'SOAPACTION': '"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"' };
msg.payload = '<?xml version="1.0" encoding="utf-8"?>'
  + '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
  + '<s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">'
  + '<InstanceID>0</InstanceID>'
  + '<CurrentURI>' + t.uri + '</CurrentURI>'
  + '<CurrentURIMetaData></CurrentURIMetaData>'
  + '</u:SetAVTransportURI></s:Body></s:Envelope>';
return msg;"""

FN_AFTER_SET = """\
var q = flow.get('queue');
if (!q) return null;
msg.url     = q.renderer.avTransportUrl;
msg.method  = 'POST';
msg.headers = { 'Content-Type': 'text/xml; charset=utf-8',
                'SOAPACTION': '"urn:schemas-upnp-org:service:AVTransport:1#Play"' };
msg.payload = '<?xml version="1.0" encoding="utf-8"?>'
  + '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
  + '<s:Body><u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">'
  + '<InstanceID>0</InstanceID><Speed>1</Speed>'
  + '</u:Play></s:Body></s:Envelope>';
return msg;"""

FN_AFTER_PLAY = """\
var q = flow.get('queue');
if (!q) return null;
var t = q.tracks[q.index];
msg.payload = { nowPlaying: { title: t.title, album: t.album || '',
    index: q.index, total: q.tracks.length, playlist: q.playlist } };
return msg;"""

FN_BUILD_STOP = """\
var q = flow.get('queue');
var url = q ? q.renderer.avTransportUrl : (flow.get('selectedRenderer') || {}).avTransportUrl;
if (!url) return null;
flow.set('queue', null);
msg.url     = url;
msg.method  = 'POST';
msg.headers = { 'Content-Type': 'text/xml; charset=utf-8',
                'SOAPACTION': '"urn:schemas-upnp-org:service:AVTransport:1#Stop"' };
msg.payload = '<?xml version="1.0" encoding="utf-8"?>'
  + '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
  + '<s:Body><u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">'
  + '<InstanceID>0</InstanceID>'
  + '</u:Stop></s:Body></s:Envelope>';
return msg;"""

FN_AFTER_STOP = """\
msg.payload = { nowPlaying: null };
return msg;"""

FN_BUILD_DELETE = f"""\
var name = msg.payload.name;
msg.kill = false;
msg.payload = '{DELETE_CMD_PREFIX} "' + name.replace(/"/g, '') + '"';
return msg;"""

FN_SET_RENDERER = """\
var r = msg.payload.renderer;
if (r) flow.set('selectedRenderer', r);
return null;"""

FN_POLL_CHECK = """\
var q = flow.get('queue');
if (!q) return null;
msg.url     = q.renderer.avTransportUrl;
msg.method  = 'POST';
msg.headers = { 'Content-Type': 'text/xml; charset=utf-8',
                'SOAPACTION': '"urn:schemas-upnp-org:service:AVTransport:1#GetTransportInfo"' };
msg.payload = '<?xml version="1.0" encoding="utf-8"?>'
  + '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
  + '<s:Body><u:GetTransportInfo xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">'
  + '<InstanceID>0</InstanceID>'
  + '</u:GetTransportInfo></s:Body></s:Envelope>';
return msg;"""

FN_PARSE_TRANSPORT = """\
var q = flow.get('queue');
if (!q) return [null, null];
var xml = typeof msg.payload === 'string' ? msg.payload : JSON.stringify(msg.payload);
var m = xml.match(/<CurrentTransportState[^>]*>([^<]+)<\\/CurrentTransportState>/);
var state = m ? m[1].trim() : '';
if (state !== 'STOPPED') return [null, null];
// track ended — advance
var nextIdx = q.index + 1;
if (nextIdx >= q.tracks.length) {
    flow.set('queue', null);
    msg.payload = { nowPlaying: null };
    return [null, msg];
}
q.index = nextIdx;
flow.set('queue', q);
var t = q.tracks[nextIdx];
// update display first, then trigger set-uri
var displayMsg = { payload: { nowPlaying: { title: t.title, album: t.album || '',
    index: q.index, total: q.tracks.length, playlist: q.playlist } } };
msg.url     = q.renderer.avTransportUrl;
msg.method  = 'POST';
msg.headers = { 'Content-Type': 'text/xml; charset=utf-8',
                'SOAPACTION': '"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"' };
msg.payload = '<?xml version="1.0" encoding="utf-8"?>'
  + '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
  + '<s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">'
  + '<InstanceID>0</InstanceID>'
  + '<CurrentURI>' + t.uri + '</CurrentURI>'
  + '<CurrentURIMetaData></CurrentURIMetaData>'
  + '</u:SetAVTransportURI></s:Body></s:Envelope>';
return [msg, displayMsg];"""

# ── Node definitions ──────────────────────────────────────────────────────────
def n(id_, type_, name, x, y, z=TAB, **kw):
    node = {'id': id_, 'type': type_, 'z': z, 'name': name, 'x': x, 'y': y, 'wires': [[]]}
    node.update(kw)
    return node

def fn(id_, name, x, y, func, outputs=1, **kw):
    node = n(id_, 'function', name, x, y, func=func, outputs=outputs,
             noerr=0, initialize='', finalize='')
    node.update(kw)
    return node

def http_req(id_, name, x, y, **kw):
    node = n(id_, 'http request', name, x, y,
             method='use', ret='txt', paytoqs='ignore', url='')
    node.update(kw)
    return node

NEW_NODES = [
    # UI config — Music page + group
    {
        'id': 'v2-page-music', 'type': 'ui-page', 'name': 'Music',
        'ui': 'v2-ui-base', 'path': '/music', 'icon': 'mdi-music',
        'layout': 'flex', 'theme': '8caffb684107c6b6', 'order': 6,
        'groups': ['v2-grp-music-main'], 'disabled': False, 'info': ''
    },
    {
        'id': 'v2-grp-music-main', 'type': 'ui-group', 'name': 'Music Player',
        'page': 'v2-page-music', 'width': '12', 'height': '1',
        'order': 1, 'showTitle': False, 'disabled': False, 'info': ''
    },

    # Startup inject — fires once after 1 s
    {**n('music-inject-startup', 'inject', 'Startup', 100, 60),
     'props': [{'p': 'payload'}, {'p': 'topic', 'vt': 'str'}],
     'repeat': '', 'crontab': '', 'once': True, 'onceDelay': 1,
     'topic': '', 'payload': '', 'payloadType': 'date',
     'wires': [['music-exec-discover', 'music-exec-list']]},

    # Periodic playlist refresh (30 s)
    {**n('music-inject-list-refresh', 'inject', 'Refresh Playlists', 100, 120),
     'props': [{'p': 'payload'}],
     'repeat': '30', 'crontab': '', 'once': False, 'onceDelay': 0,
     'topic': '', 'payload': '', 'payloadType': 'date',
     'wires': [['music-exec-list']]},

    # Playback poll — every 5 s
    {**n('music-inject-poll', 'inject', 'Poll Playback', 100, 180),
     'props': [{'p': 'payload'}],
     'repeat': '5', 'crontab': '', 'once': False, 'onceDelay': 0,
     'topic': '', 'payload': '', 'payloadType': 'date',
     'wires': [['music-fn-poll-check']]},

    # Renderer discovery
    {**n('music-exec-discover', 'exec', 'Discover Renderers', 320, 60),
     'command': DISCOVER_CMD, 'addpay': False, 'append': '',
     'useSpawn': False, 'timer': '10', 'winHide': False, 'oldrc': False,
     'wires': [['music-fn-renderers'], [], []]},

    fn('music-fn-renderers', 'Store Renderers', 540, 60, FN_STORE_RENDERERS,
       wires=[['music-tmpl']]),

    # Playlist listing
    {**n('music-exec-list', 'exec', 'List Playlists', 320, 120),
     'command': LIST_CMD, 'addpay': False, 'append': '',
     'useSpawn': False, 'timer': '10', 'winHide': False, 'oldrc': False,
     'wires': [['music-fn-playlists'], [], []]},

    fn('music-fn-playlists', 'Store Playlists', 540, 120, FN_STORE_PLAYLISTS,
       wires=[['music-tmpl']]),

    # Dashboard template (bidirectional)
    {
        'id': 'music-tmpl', 'type': 'ui-template', 'z': TAB,
        'group': 'v2-grp-music-main', 'page': '', 'ui': '',
        'name': 'Music Dashboard', 'order': 1,
        'width': '12', 'height': '10',
        'format': TMPL,
        'storeOutMessages': True, 'passthru': False,
        'resendOnRefresh': True, 'templateScope': 'local',
        'className': '', 'x': 760, 'y': 120,
        'wires': [['music-fn-dispatch']]
    },

    # Action dispatcher (5 outputs)
    fn('music-fn-dispatch', 'Dispatch Action', 980, 120, FN_DISPATCH, outputs=5,
       wires=[['music-fn-build-play'],    # 0 play
              ['music-fn-build-delete'],  # 1 delete
              ['music-fn-build-stop'],    # 2 stop
              ['music-exec-discover'],    # 3 refresh
              ['music-fn-set-renderer']]),# 4 setRenderer

    # ── Play path ─────────────────────────────────────────────────────────────
    fn('music-fn-build-play', 'Build Load Path', 320, 280, FN_BUILD_PLAY,
       wires=[['music-file-read-play']]),

    {**n('music-file-read-play', 'file in', 'Load Playlist', 540, 280),
     'filename': '', 'format': 'utf8', 'chunk': False,
     'sendError': True, 'encoding': 'none',
     'wires': [['music-fn-start-playback']]},

    fn('music-fn-start-playback', 'Start Playback', 760, 280, FN_START_PLAYBACK,
       wires=[['music-http-set-uri']]),

    # ── SetAVTransportURI → Play (shared by start and advance) ────────────────
    {**http_req('music-http-set-uri', 'SetAVTransportURI', 980, 280),
     'wires': [['music-fn-after-set']]},

    fn('music-fn-after-set', 'Build Play SOAP', 1200, 280, FN_AFTER_SET,
       wires=[['music-http-play']]),

    {**http_req('music-http-play', 'Play', 1420, 280),
     'wires': [['music-fn-after-play']]},

    fn('music-fn-after-play', 'Update Now Playing', 1620, 280, FN_AFTER_PLAY,
       wires=[['music-tmpl']]),

    # ── Stop path ─────────────────────────────────────────────────────────────
    fn('music-fn-build-stop', 'Build Stop SOAP', 320, 380, FN_BUILD_STOP,
       wires=[['music-http-stop']]),

    {**http_req('music-http-stop', 'Stop', 540, 380),
     'wires': [['music-fn-after-stop']]},

    fn('music-fn-after-stop', 'Clear Now Playing', 760, 380, FN_AFTER_STOP,
       wires=[['music-tmpl']]),

    # ── Delete path ───────────────────────────────────────────────────────────
    fn('music-fn-build-delete', 'Build Delete Cmd', 320, 460, FN_BUILD_DELETE,
       wires=[['music-exec-delete']]),

    {**n('music-exec-delete', 'exec', 'Delete Playlist', 540, 460),
     'command': '', 'addpay': True, 'append': '',
     'useSpawn': False, 'timer': '10', 'winHide': False, 'oldrc': False,
     'wires': [['music-exec-list'], [], []]},

    # ── Set renderer ──────────────────────────────────────────────────────────
    fn('music-fn-set-renderer', 'Store Renderer', 320, 540, FN_SET_RENDERER,
       wires=[[]]),

    # ── Poll path ─────────────────────────────────────────────────────────────
    fn('music-fn-poll-check', 'Build GetTransportInfo', 320, 620, FN_POLL_CHECK,
       wires=[['music-http-getpos']]),

    {**http_req('music-http-getpos', 'GetTransportInfo', 540, 620),
     'wires': [['music-fn-parse-transport']]},

    fn('music-fn-parse-transport', 'Parse Transport', 760, 620, FN_PARSE_TRANSPORT,
       outputs=2,
       wires=[['music-http-set-uri'],  # advance to next track
              ['music-tmpl']]),        # playlist done — clear display
]

# ── Load and patch flows ──────────────────────────────────────────────────────
with open(FLOWS, encoding='utf-8') as f:
    flows = json.load(f)

# IDs to remove from play tab (old stub nodes)
OLD_PLAY_IDS = {
    'music-in-select', 'music-fn-load', 'music-file-read',
    'music-fn-format', 'music-out-tracks'
}
# Also remove any stale new nodes if re-running
NEW_IDS = {nd['id'] for nd in NEW_NODES}

kept = [n for n in flows
        if n['id'] not in OLD_PLAY_IDS and n['id'] not in NEW_IDS]

merged = kept + NEW_NODES

# Sanity check
ids = [n['id'] for n in merged]
dupes = [i for i in set(ids) if ids.count(i) > 1]
if dupes:
    print('WARNING — duplicate IDs:', dupes)
else:
    print('No duplicate IDs')

from collections import Counter
tab_map = {n['id']: n.get('label', n.get('name', n['id']))
           for n in merged if not n.get('z')}
counts = Counter(n.get('z', '(config)') for n in merged)
for tab_id, cnt in sorted(counts.items()):
    label = tab_map.get(tab_id, tab_id)
    print(f'  {cnt:3d}  {label}')
print(f'Total: {len(merged)}')

with open(FLOWS, 'w', encoding='utf-8') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
print('Written flows/flows.json')
