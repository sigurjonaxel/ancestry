import subprocess, time, os, re

os.system("pkill -f 'python.*server.py' || true")
os.system("pkill -f 'cloudflared' || true")
time.sleep(1)

# Start server
server_proc = subprocess.Popen([".venv/bin/python", "server.py"], start_new_session=True)

# Locate cloudflared binary
cf_bin = "/home/sigurjonaxel/.local/bin/cloudflared" if os.path.exists("/home/sigurjonaxel/.local/bin/cloudflared") else "/tmp/cloudflared"

# Start cloudflared
with open("/tmp/tunnel.log", "w") as f:
    tunnel_proc = subprocess.Popen([cf_bin, "tunnel", "--url", "http://localhost:8000"], stdout=f, stderr=f, start_new_session=True)

url = None
for _ in range(15):
    time.sleep(1)
    if os.path.exists("/tmp/tunnel.log"):
        with open("/tmp/tunnel.log", "r") as f:
            log = f.read()
        m = re.search(r'https://[-a-zA-Z0-9]+\.trycloudflare\.com', log)
        if m:
            url = m.group(0)
            break

if url:
    print("LIVE_URL:", url)
else:
    print("LOG:\n", log)
