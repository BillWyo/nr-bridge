import json, re

src = r"C:\Users\johan\Documents\PlatformIO\Projects\HIS_NodeRed_Hub\flows.json"
dst = r"C:\Users\johan\Documents\PlatformIO\Projects\NR_Bridge\flows\flows.json"

with open(src, "r", encoding="utf-8") as fh:
    content = fh.read()

# Fix double-encoded sequences (UTF-8 bytes mis-read as cp1252, then re-encoded)
fixes = [
    ("Â°", "°"),   # Â° → °
    ("â†’", "→"),  # â†' (right sq quote) → →
    ("â†‘", "↑"),  # â†' (left sq quote)  → ↑
    ("â†“", "↓"),  # â†" (left dbl quote) → ↓
]
for bad, good in fixes:
    content = content.replace(bad, good)

# Escape all non-ASCII as \uXXXX (JSON-safe, encoding-proof)
def escape_char(m):
    return "\\u{:04x}".format(ord(m.group()))

content = re.sub(r"[^\x00-\x7f]", escape_char, content)

# Validate
json.loads(content)
remaining = len(re.findall(r"[^\x00-\x7f]", content))
print(f"JSON valid. Non-ASCII remaining: {remaining}")

for path in [src, dst]:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print(f"Written: {path}")
