// Edit this file in VSCode, then run: python nr_sync.py
// The node name in Node-RED must be exactly: hello_world

msg.payload = "Hello from VSCode! " + new Date().toLocaleTimeString();
return msg;
