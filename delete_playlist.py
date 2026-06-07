"""Delete a playlist file. Pass playlist name (without .json) as argument."""
import os, json, sys

PLAYLIST_DIR = r'F:\Music - Flac\Playlists'

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No name given'}), file=sys.stderr)
        sys.exit(1)
    name = sys.argv[1]
    path = os.path.join(PLAYLIST_DIR, f'{name}.json')
    if os.path.exists(path):
        os.remove(path)
        print(json.dumps({'deleted': name}))
    else:
        print(json.dumps({'error': f'Not found: {name}'}), file=sys.stderr)
        sys.exit(1)
