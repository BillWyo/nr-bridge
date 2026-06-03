var raw = (typeof msg.payload === "object") ? msg.payload.text : String(msg.payload);
raw = (raw || "").trim().toLowerCase();

node.warn("Voice input: " + raw);

if (raw.startsWith("add ")) {
    msg.intent = "add";
    msg.item = raw.slice(4).trim();
} else if (raw.startsWith("remove ") || raw.startsWith("delete ")) {
    msg.intent = "remove";
    msg.item = raw.replace(/^(remove|delete)\s+/, "").trim();
} else if (raw === "clear list" || raw === "clear") {
    msg.intent = "clear";
    msg.item = null;
} else if (raw === "list" || raw === "send list" || raw === "what's on the list") {
    msg.intent = "send";
    msg.item = null;
} else {
    msg.intent = "unknown";
    msg.item = raw;
}

msg.statusCode = 200;
msg.payload = { status: "received", intent: msg.intent, item: msg.item };
return msg;
