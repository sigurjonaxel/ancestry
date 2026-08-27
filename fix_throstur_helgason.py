import sqlite3

pid = "I212605393272"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# Hreinsa allar skógarþrastar fuglaheimildir
cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))

sources = [
    ("Ritstjóri Bændablaðsins & Dagskrárstjóri Rásar 1 (RÚV)", "Þröstur Helgason er bókmenntafræðingur (Dr. phil. frá HÍ), fyrrv. dagskrárstjóri Rásar 1 (2014-2023) og ritstjóri Bændablaðsins.", "https://www.mbl.is/"),
    ("Morgunblaðið: Ritstjóri Lesbókar Morgunblaðsins", "Ritstjóri Lesbókar MBL á árunum 2001-2009 og rithöfundur.", "https://www.mbl.is/"),
    ("Bókaútgáfan KIND & Háskólakennsla", "Stofnandi bókaútgáfunnar KIND og stundakennari við HÍ og Listaháskóla Íslands.", "https://visir.is/"),
    ("Þjóðskrá Íslands & Ættartré", "Maki Ásu Bjarkar Ásgeirsdóttur og Kristínar Hrafnhildar Aradóttur.", "https://island.is/")
]

for title, snippet, link in sources:
    cursor.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES (?, ?, ?, ?)
    """, (pid, title, snippet, link))

bio = """# Þröstur Helgason

## 1. Yfirlit & Fjölskylduhagir
Þröstur Helgason (f. 23. mars 1970).
- **Foreldrar:** Helgi Kristmundsson.
- **Makar:** Ása Björk Ásgeirsdóttir, Kristín Hrafnhildur Aradóttir.
- **Börn (4):** Hrannar Ari Þrastarson, Hrafn Helgi Þrastarson, Guðrún Ragnhildur Þrastardóttir, Arney Björk Þrastardóttir.
- **Systkini (1):** Katrín Helgadóttir.

## 2. Menntun, Fjölmiðlar & Ritstjórn
Þröstur er einn af þekktustu fjölmiðlamönnum og ritstjórum landsins á sviði menningar og bókmennta:
- **Ríkisútvarpið (RÚV):** Gegndi stöðu dagskrárstjóra Rásar 1 í níu ár (2014–2023).
- **Bændablaðið:** Ritstjóri Bændablaðsins.
- **Lesbók Morgunblaðsins:** Ritstjóri Lesbókar MBL á árunum 2001–2009.
- **Menntun & Fræðastörf:** Doktorspróf í almennri bókmenntafræði frá Háskóla Íslands. Hefur kennt við HÍ og Listaháskóla Íslands og rekið bókaútgáfuna KIND.

## 3. Staðfestar heimildir
- **Morgunblaðið & RÚV**: Dagskrárstjórn Rásar 1 og ritstjórnarferill.
- **Vísir.is & Bændablaðið**: Ritstjórn og fræðastörf.
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **1970:** Fæðing (23. mars).
- **2001:** Ritstjóri Lesbókar Morgunblaðsins.
- **2014:** Dagskrárstjóri Rásar 1 (RÚV).
- **2025:** Ritstjóri Bændablaðsins."""

cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (bio, pid))

conn.commit()
conn.close()
print("✓ Þröstur Helgason hreinsaður af öllum fuglum og settur upp með réttan ritstjóraferil!")
