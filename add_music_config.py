#!/usr/bin/env python3
"""Add music device config management to flows.json"""

import json
import uuid

FLOWS_FILE = "flows/flows.json"

def load_flows():
    with open(FLOWS_FILE, encoding='utf-8') as f:
        return json.load(f)

def save_flows(flows):
    with open(FLOWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(flows, f, indent=2)

def find_flow_tab(flows, tab_name):
    """Find tab by name"""
    for node in flows:
        if node.get("type") == "tab" and node.get("label") == tab_name:
            return node["id"]
    return None

def create_config_node(flow_id):
    """Create the config initialization function"""
    return {
        "id": "music-fn-config-init",
        "type": "function",
        "z": flow_id,
        "name": "Config - Initialize",
        "func": "if (!flow.get('musicConfig')) {\n    flow.set('musicConfig', {\n        fiioIp: '192.168.1.17',\n        fiioUuid: '460e4d1d-709d-44da-9532-ec9934249a07',\n        samsungIp: '192.168.1.12',\n        samsungPort: 9197\n    });\n    node.send({payload: 'Config initialized'});\n} else {\n    node.send({payload: 'Config already exists'});\n}",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "x": 100,
        "y": 40,
        "wires": [[]]
    }

def create_config_getter(flow_id):
    """Create function to get current config"""
    return {
        "id": "music-fn-config-get",
        "type": "function",
        "z": flow_id,
        "name": "Config - Get Current",
        "func": "const cfg = flow.get('musicConfig') || {};\nmsg.payload = cfg;\nreturn msg;",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "x": 280,
        "y": 40,
        "wires": [[]]
    }

def create_config_setter(flow_id):
    """Create function to save config"""
    return {
        "id": "music-fn-config-set",
        "type": "function",
        "z": flow_id,
        "name": "Config - Save",
        "func": "const cfg = msg.payload;\nflow.set('musicConfig', cfg);\nnode.send({payload: 'Config saved: ' + JSON.stringify(cfg)});",
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "x": 280,
        "y": 100,
        "wires": [[]]
    }

def main():
    flows = load_flows()
    music_flow_id = find_flow_tab(flows, "Music — Play")

    if not music_flow_id:
        print("ERROR: Could not find 'Music' tab")
        return

    print(f"Found Music tab: {music_flow_id}")

    # Check if config nodes already exist
    existing_ids = {node["id"] for node in flows}
    if "music-fn-config-init" in existing_ids:
        print("Config nodes already exist, skipping")
        return

    # Add config nodes
    flows.append(create_config_node(music_flow_id))
    flows.append(create_config_getter(music_flow_id))
    flows.append(create_config_setter(music_flow_id))

    save_flows(flows)
    print("[OK] Added 3 config management nodes")
    print("  - music-fn-config-init: initializes config with defaults")
    print("  - music-fn-config-get: retrieves current config")
    print("  - music-fn-config-set: saves updated config")
    print("\nNext steps:")
    print("1. Run: python nr_sync.py push")
    print("2. In Node-RED, wire the config nodes to dashboard inputs")
    print("3. Update music-fn-discover to read from flow.get('musicConfig')")

if __name__ == "__main__":
    main()
