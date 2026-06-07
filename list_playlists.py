"""List playlists in the Playlists directory. Returns JSON array to stdout."""
import os, json, sys

PLAYLIST_DIR = r'F:\Music - Flac\Playlists'

def list_playlists():
    if not os.path.isdir(PLAYLIST_DIR):
        return []
    result = []
    for fname in sorted(os.listdir(PLAYLIST_DIR)):
        if fname.endswith('.json'):
            path = os.path.join(PLAYLIST_DIR, fname)
            try:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                result.append({
                    'name': data.get('name', fname[:-5]),
                    'trackCount': len(data.get('tracks', []))
                })
            except Exception as e:
                print(f'[warn] {fname}: {e}', file=sys.stderr)
    return result

if __name__ == '__main__':
    print(json.dumps(list_playlists()))
