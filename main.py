
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
import threading

messages = []
lock = threading.Lock()

PAGE = r"""<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Offline Wi-Fi Chat</title>
<style>
body { font: 16px Arial; max-width: 600px; margin: 25px auto;
       padding: 0 12px; background: #f3f5f7; }
h2 { text-align: center; }
#chat { height: 55vh; overflow-y: auto; background: white;
        padding: 12px; border-radius: 10px; }
.msg { padding: 9px; margin: 7px 0; background: #e0efff;
       border-radius: 8px; overflow-wrap: anywhere; }
form { display: flex; gap: 8px; margin-top: 12px; }
input { min-width: 0; flex: 1; padding: 12px; }
button { padding: 12px 16px; }
</style>
</head>
<body>
<h2>Offline Wi-Fi Chat</h2>
<div id="chat"></div>
<form id="form">
  <input id="name" placeholder="Your name" value="Phone" maxlength="30">
  <input id="message" placeholder="Type a message..." maxlength="2000" required>
  <button>Send</button>
</form>
<script>
const chat = document.getElementById('chat');
const input = document.getElementById('message');
let last = 0;

async function refresh() {
  try {
    const r = await fetch('/messages?after=' + last);
    const data = await r.json();
    for (const m of data) {
      const div = document.createElement('div');
      div.className = 'msg';
      const time = new Date(m.time).toLocaleTimeString();
      div.textContent = time + ' | ' + m.name + ': ' + m.text;
      chat.appendChild(div);
      last = Math.max(last, m.id);
    }
    if (data.length) chat.scrollTop = chat.scrollHeight;
  } catch (e) {
    // Retry on the next polling cycle.
  }
}

document.getElementById('form').addEventListener('submit', async e => {
  e.preventDefault();
  const text = input.value.trim();
  const name = document.getElementById('name').value.trim() || 'Guest';
  if (!text) return;
  input.value = '';
  try {
    const r = await fetch('/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, text})
    });
    if (!r.ok) alert('Message could not be sent.');
    await refresh();
  } catch (e) {
    alert('Cannot reach the computer. Check Wi-Fi.');
  }
  input.focus();
});

refresh();
setInterval(refresh, 700);
</script>
</body>
</html>
"""


class ChatHandler(BaseHTTPRequestHandler):
    def send_data(self, status, data, content_type):
        body = data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path)

        if path.path == "/":
            self.send_data(200, PAGE, "text/html; charset=utf-8")

        elif path.path == "/messages":
            from urllib.parse import parse_qs
            query = parse_qs(path.query)
            try:
                after = int(query.get("after", ["0"])[0])
            except ValueError:
                after = 0

            with lock:
                result = [m for m in messages if m["id"] > after]

            self.send_data(
                200, json.dumps(result), "application/json; charset=utf-8"
            )
        else:
            self.send_data(404, "Not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/send":
            self.send_data(404, "Not found", "text/plain")
            return

        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 10000:
                raise ValueError()
            data = json.loads(self.rfile.read(size))
            name = str(data.get("name", "Guest")).strip()[:30] or "Guest"
            text = str(data.get("text", "")).strip()[:2000]
            if not text:
                raise ValueError()
        except (ValueError, TypeError, json.JSONDecodeError):
            self.send_data(400, "Invalid message", "text/plain")
            return

        with lock:
            item = {
                "id": (messages[-1]["id"] + 1) if messages else 1,
                "name": name,
                "text": text,
                "time": __import__("time").time() * 1000
            }
            messages.append(item)
            if len(messages) > 500:
                del messages[:-500]

        self.send_data(200, '{"ok":true}', "application/json")

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.client_address[0], fmt % args))


server = ThreadingHTTPServer(("0.0.0.0", 8000), ChatHandler)
print("Offline chat server running on port 8000")
print("Keep this window open. Press Ctrl+C to stop.")
server.serve_forever()
