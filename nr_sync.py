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


def filter_by_tab(flows, tab_name):
    """Return only nodes belonging to the named tab (plus the tab node itself)."""
    tab = next(
        (n for n in flows if n.get("type") == "tab" and n.get("label") == tab_name),
        None,
    )
    if not tab:
        labels = [n.get("label") for n in flows if n.get("type") == "tab"]
        print(f"ERROR: Tab '{tab_name}' not found.")
        print(f"Available tabs: {labels}")
        sys.exit(1)
    return [n for n in flows if n.get("id") == tab["id"] or n.get("z") == tab["id"]]


def safe_filename(name):
    """Strip characters that are invalid in filenames."""
    return "".join(c if c.isalnum() or c in "._- " else "_" for c in name).strip()


def cmd_push(args):
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


def cmd_pull(args):
    """Export Node-RED flows to flows/flows.json. Use --tab <name> to filter."""
    tab_name = args[0] if args else None
    print(f"Pulling flows from Node-RED at {NR_URL} ...")
    flows = get_flows()

    if tab_name:
        flows = filter_by_tab(flows, tab_name)
        print(f"  Filtered to tab '{tab_name}': {len(flows)} nodes")

    os.makedirs("flows", exist_ok=True)
    with open(FLOWS_FILE, "w") as f:
        json.dump(flows, f, indent=2)

    print(f"Saved {len(flows)} nodes to {FLOWS_FILE}")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    label = f"tab:{tab_name}" if tab_name else "all"
    git_commit_and_push(f"pull: snapshot [{label}] [{timestamp}]")


def cmd_extract(args):
    """Extract every function node from flows.json into nodes/<name>.js"""
    if not os.path.exists(FLOWS_FILE):
        print(f"No {FLOWS_FILE} found. Run 'python nr_sync.py pull' first.")
        return

    with open(FLOWS_FILE, "r", encoding="utf-8") as f:
        flows = json.load(f)

    os.makedirs(NODES_DIR, exist_ok=True)
    count = 0
    for node in flows:
        if node.get("type") != "function":
            continue
        name = node.get("name", "").strip()
        if not name:
            name = node.get("id", "unnamed")
        filename = safe_filename(name) + ".js"
        filepath = os.path.join(NODES_DIR, filename)
        with open(filepath, "w") as f:
            f.write(node.get("func", ""))
        print(f"  Extracted: '{name}' → {filepath}")
        count += 1

    if count == 0:
        print("No function nodes found in flows.json.")
        return

    print(f"Extracted {count} function node(s) to {NODES_DIR}/")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_and_push(f"extract: {count} function node(s) from flows [{timestamp}]")


def cmd_push_flows(args):
    """Import flows/flows.json into Node-RED (full replacement)."""
    if not os.path.exists(FLOWS_FILE):
        print(f"No {FLOWS_FILE} found. Run 'python nr_sync.py pull' first.")
        return

    with open(FLOWS_FILE, "r", encoding="utf-8") as f:
        flows = json.load(f)

    print(f"Pushing {len(flows)} nodes from {FLOWS_FILE} to Node-RED ...")
    post_flows(flows, deploy_type="full")
    print("Full flow deployed to Node-RED.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_commit_and_push(f"push-flows: full deploy [{timestamp}]")


def cmd_tabs(args):
    """List all tab names in Node-RED."""
    print(f"Connecting to Node-RED at {NR_URL} ...")
    flows = get_flows()
    tabs = [n for n in flows if n.get("type") == "tab"]
    if not tabs:
        print("No tabs found.")
        return
    print(f"Found {len(tabs)} tab(s):")
    for t in tabs:
        print(f"  '{t.get('label', '(unnamed)')}' — id: {t['id']}")


COMMANDS = {
    "push":        (cmd_push,       "sync nodes/*.js to Node-RED function nodes"),
    "pull":        (cmd_pull,       "export Node-RED flows to flows/flows.json  [--tab <name>]"),
    "extract":     (cmd_extract,    "extract function nodes from flows.json into nodes/"),
    "push-flows":  (cmd_push_flows, "import flows/flows.json to Node-RED (full replace)"),
    "tabs":        (cmd_tabs,       "list all tab names in Node-RED"),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python nr_sync.py <command> [options]")
        print("Commands:")
        for name, (_, desc) in COMMANDS.items():
            print(f"  {name:<14} — {desc}")
        sys.exit(1)

    cmd_name = sys.argv[1]
    cmd_args = sys.argv[2:]
    COMMANDS[cmd_name][0](cmd_args)
