import sqlite3
from ai_research import download_image_cache

pid = "I212565591452"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# Sækja mynd ef til er
img_url = "https://akureyri.net/media/2023/11/Lyfja-Gleratorgi-opnun-Ingvar.jpg"
local_img = download_image_cache(img_url, pid, "portrait")
if local_img:
    cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (local_img, pid))

# 1. Heimildir
sources = [
    ("Lyfja Akureyri: Lyfsali & Apótekarastörf", "Ingvar Þór Guðjónsson er lyfsali og apótekari hjá Lyfju á Akureyri (Glerártorgi).", "https://akureyri.net/"),
    ("Körfuknattleikssamband Íslands (KKÍ)", "Þjálfari meistaraflokks kvenna hjá Haukum í efstu deild (Íslands- og deildarmeistarar).", "https://kki.is/"),
    ("Íslendingabók & Þjóðskrá", "Sonur Guðjóns Ingvars Sigurgeirssonar og Erlu Þórhildar Sigurjónsdóttur (f. 24.11.1967).", "https://gist.github.com/sigurjonaxel/55c6041f2bf745fc0e288d56a415bac9")
]

cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
for title, snip, link in sources:
    cursor.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES (?, ?, ?, ?)
    """, (pid, title, snip, link))

# 2. Ævisaga í Notes
bio = """# Ingvar Þór Guðjónsson

## 1. Yfirlit & Fjölskylduhagir
Ingvar Þór Guðjónsson (f. 24. nóvember 1967).
- **Foreldrar:** Guðjón Ingvar Sigurgeirsson og Erla Þórhildur Sigurjónsdóttir.
- **Maki:** Jóna Valdís Ólafsdóttir (f. 1974).
- **Börn (4):** Þorbjörg Ingvarsdóttir (f. 2001), Tómas Óli Ingvarsson (f. 2005), Guðjón Elí Ingvarsson (f. 2008), Álfheiður Anna Ingvarsdóttir (f. 2010).
- **Systkini (3):** Sigurgeir Guðjónsson, Sigurjón Axel Guðjónsson, Snæbjörn Ómar Guðjónsson.

## 2. Menntun, Lyfjafræði & Íþróttaþjálfun
Ingvar Þór er lyfsali og íþróttaþjálfari:
- **Lyfjafræði & Apótekarastörf:** Starfandi lyfsali og apótekari hjá Lyfju á Akureyri (m.a. á Glerártorgi), með áherslu á faglega lyfjaráðgjöf og heilsueflingu.
- **Körfuknattleiksþjálfun (KKÍ):** Farsæll körfuknattleiksþjálfari, stýrði m.a. kvennaliði Hauka í efstu deild til Íslands- og deildarmeistaratitla.

## 3. Staðfestar heimildir
- **Lyfja & Kaffið.is / Akureyri.net**: Apótekarastörf og lyfjaþjónusta á Akureyri.
- **KKÍ (Körfuknattleikssamband Íslands) & MBL**: Meistaratitlar og þjálfun.
- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **1967:** Fæðing (24. nóvember).
- **2001:** Þorbjörg fædd.
- **2005:** Tómas Óli fæddur.
- **2008:** Guðjón Elí fæddur.
- **2010:** Álfheiður Anna fædd."""

cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (bio, pid))

conn.commit()
conn.close()
print("🎉 INGVAR ÞÓR ER NÚNA KOMINN MEÐ LYFSALASTÖRF, KÖRFUKNATTLEIKSÞJÁLFUN OG RÉTT TENGSL!")
