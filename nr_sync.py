import requests
import os
import glob
from secrets import NR_URL


def sync_nodes():
    print(f"Connecting to Node-RED at {NR_URL} ...")

    try:
        resp = requests.get(f"{NR_URL}/flows", timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Could not reach Node-RED — {e}")
        return

    flows = resp.json()

    node_files = glob.glob("nodes/*.js")
    if not node_files:
        print("No .js files found in nodes/")
        return

    updated = 0
    for filepath in node_files:
        node_name = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, "r") as f:
            code = f.read()

        for node in flows:
            if node.get("type") == "function" and node.get("name") == node_name:
                node["func"] = code
                updated += 1
                print(f"  Matched: '{node_name}'  (id: {node['id']})")

    if updated == 0:
        print("No matching function nodes found.")
        print("Check that the function node name in Node-RED matches the filename (without .js).")
        return

    headers = {
        "Content-Type": "application/json",
        "Node-RED-Deployment-Type": "nodes",
    }
    try:
        resp = requests.post(f"{NR_URL}/flows", json=flows, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Deploy failed — {e}")
        return

    print(f"Done. {updated} node(s) deployed to Node-RED.")


if __name__ == "__main__":
    sync_nodes()
