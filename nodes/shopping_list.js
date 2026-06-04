var list = global.get("shopping_list") || [];

if (msg.intent === "add" && msg.item) {
    list.push(msg.item);
    global.set("shopping_list", list);
    msg.telegram_text = "Added: " + msg.item + "\nList now has " + list.length + " item(s).";

} else if (msg.intent === "remove" && msg.item) {
    var before = list.length;
    list = list.filter(function(i) { return i !== msg.item; });
    global.set("shopping_list", list);
    msg.telegram_text = (list.length < before)
        ? "Removed: " + msg.item
        : "'" + msg.item + "' not found on list.";

} else if (msg.intent === "clear") {
    global.set("shopping_list", []);
    msg.telegram_text = "Shopping list cleared.";

} else if (msg.intent === "send") {
    msg.telegram_text = list.length === 0
        ? "Shopping list is empty."
        : "Shopping list:\n" + list.map(function(i, n) { return (n+1) + ". " + i; }).join("\n");

} else {
    msg.telegram_text = null;
}

if (!msg.telegram_text) return null;

msg.payload = {
    chatId: 8823231843,
    type: "message",
    content: msg.telegram_text
};
return msg;
