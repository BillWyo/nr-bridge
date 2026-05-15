import requests
import os
import glob
import json
import subprocess
import sys
from datetime import datetime
from secrets import NR_URL

FLOWS_FILE = "flows/flows.json"
NODES_DIR = "nodes"


def get_flows():
    try:
        resp = requests.get(f"{NR_URL}/flows", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"ERROR: Could not reach Node-RED — {e}")
        sys.exit(1)


def post_flows(flows, deploy_type="nodes"):
    headers = {
        "Content-Type": "application/json",
        "Node-RED-Deployment-Type": deploy_type,
    }
    try:
        resp = requests.post(f"{NR_URL}/flows", json=flows, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Deploy failed — {e}")
        sys.exit(1)


def git_commit_and_push(message):
    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if result.returncode == 0:
        print("Nothing new to commit.")
        return
    subprocess.run(["git", "commit", "-m", message], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Committed and pushed to GitHub.")


def cmd_push():
    """Sync nodes/*.js files into matching Node-RED function nodes."""
    print(f"Connecting to Node-RED at {NR_URL} ...")
    flows = get_flows()

    node_files = glob.glob(f"{NODES_DIR}/*.js")
    if not node_files:
        print(f"No .js files found in {NODES_DIR}/")
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
        print("Node name in Node-RED must match the filename (without .js).")
        return

    post_flows(flows, deploy_type="nodes")
    print(f"Deployed {updated} node(s) to Node-RED.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_and_push(f"push: sync {updated} function node(s) [{timestamp}]")


def cmd_pull():
    """Export all Node-RED flows to flows/flows.json."""
    print(f"Pulling flows from Node-RED at {NR_URL} ...")
    flows = get_flows()

    os.makedirs("flows", exist_ok=True)
    with open(FLOWS_FILE, "w") as f:
        json.dump(flows, f, indent=2)

    print(f"Saved {len(flows)} nodes to {FLOWS_FILE}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_and_push(f"pull: snapshot from Node-RED [{timestamp}]")


def cmd_push_flows():
    """Import flows/flows.json into Node-RED (full replacement)."""
    if not os.path.exists(FLOWS_FILE):
        print(f"No {FLOWS_FILE} found. Run 'python nr_sync.py pull' first.")
        return

    with open(FLOWS_FILE, "r") as f:
        flows = json.load(f)

    print(f"Pushing {len(flows)} nodes from {FLOWS_FILE} to Node-RED ...")
    post_flows(flows, deploy_type="full")
    print("Full flow deployed to Node-RED.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_and_push(f"push-flows: full deploy [{timestamp}]")


COMMANDS = {
    "push": cmd_push,
    "pull": cmd_pull,
    "push-flows": cmd_push_flows,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python nr_sync.py <command>")
        print("Commands:")
        print("  push        — sync nodes/*.js to Node-RED function nodes")
        print("  pull        — export Node-RED flows to flows/flows.json")
        print("  push-flows  — import flows/flows.json to Node-RED (full replace)")
        sys.exit(1)

    COMMANDS[sys.argv[1]]()
