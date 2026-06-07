"""
UPnP MediaRenderer discovery.
Sends SSDP M-SEARCH, fetches description XML, returns JSON array of renderers
with their AVTransport control URLs — ready for Node-RED exec node.
"""
import socket, time, urllib.request, xml.etree.ElementTree as ET, json, re, sys

SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
TIMEOUT    = 4   # seconds to wait for responses

def discover():
    msg = (
        'M-SEARCH * HTTP/1.1\r\n'
        f'HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n'
        'MAN: "ssdp:discover"\r\n'
        'MX: 3\r\n'
        'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n'
        '\r\n'
    ).encode()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.settimeout(TIMEOUT)

    locations = set()
    try:
        sock.sendto(msg, (SSDP_ADDR, SSDP_PORT))
        deadline = time.time() + TIMEOUT
        while time.time() < deadline:
            try:
                data = sock.recv(2048).decode('utf-8', errors='ignore')
                for line in data.splitlines():
                    if line.lower().startswith('location:'):
                        locations.add(line.split(':', 1)[1].strip())
            except socket.timeout:
                break
    finally:
        sock.close()

    renderers = []
    for loc in locations:
        try:
            r = parse_device(loc)
            if r:
                renderers.append(r)
        except Exception as e:
            print(f'[warn] {loc}: {e}', file=sys.stderr)

    renderers.sort(key=lambda r: r['name'])
    return renderers

def parse_device(location):
    base = re.match(r'(https?://[^/]+)', location).group(1)

    req = urllib.request.Request(location, headers={'User-Agent': 'NR-Discovery/1.0'})
    with urllib.request.urlopen(req, timeout=4) as resp:
        xml_bytes = resp.read()

    # strip namespace prefixes so ElementTree finds tags reliably
    xml_str = re.sub(r'\sxmlns[^"]*"[^"]*"', '', xml_bytes.decode('utf-8', errors='replace'))
    xml_str = re.sub(r'<[a-z]+:', '<', xml_str)
    xml_str = re.sub(r'</[a-z]+:', '</', xml_str)
    root = ET.fromstring(xml_str)

    device = root.find('.//device')
    if device is None:
        return None

    dtype = (device.findtext('deviceType') or '')
    if 'MediaRenderer' not in dtype:
        return None

    name  = (device.findtext('friendlyName') or location).strip()
    model = (device.findtext('modelName')    or '').strip()

    av_ctrl = None
    for svc in device.findall('.//service'):
        stype = svc.findtext('serviceType') or ''
        if 'AVTransport' in stype:
            ctrl = (svc.findtext('controlURL') or '').strip()
            av_ctrl = ctrl if ctrl.startswith('http') else base + ctrl
            break

    if not av_ctrl:
        return None

    ip = re.search(r'//([^:/]+)', base).group(1)
    return {'name': name, 'model': model, 'ip': ip,
            'avTransportUrl': av_ctrl, 'location': location}

if __name__ == '__main__':
    results = discover()
    print(json.dumps(results, indent=2))
