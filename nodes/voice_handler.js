// Receives spoken text from Android phone via HTTP POST
// Payload can be raw string or JSON {"text": "..."}
var text = (typeof msg.payload === "object") ? msg.payload.text : String(msg.payload);
text = (text || "").trim();

node.warn("Voice input: " + text);

msg.statusCode = 200;
msg.payload = { status: "received", text: text };
return msg;
