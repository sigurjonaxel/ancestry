with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

import time
ts = int(time.time())
html = html.replace('app.js?v=20260826_1021', f'app.js?v={ts}')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✓ Uppfærði útgáfunúmer á app.js í v={ts} svo vafrinn sæki strax nýjustu útgáfuna án skyndiminnistruflana!")
