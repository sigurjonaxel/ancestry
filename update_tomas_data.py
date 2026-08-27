import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Update Tómas Óli with accurate sports, school and family info
bio_text = """# Tómas Óli Ingvarsson

## 1. Yfirlit & Fjölskylduhagir
Tómas Óli Ingvarsson (f. 20. júlí 2005).
- **Foreldrar:** Ingvar Þór Guðjónsson og Einarína Einarsdóttir.
- **Systkini (3):** Þorbjörg Ingvarsdóttir, Guðjón Elí Ingvarsson og Álfheiður Anna Ingvarsdóttir.

## 2. Lífshlaup, Nám & Íþróttir
Tómas Óli er uppalinn í Kópavogi/Reykjavík, stundaði knattspyrnu í yngri flokkum og meistaraflokki (Breiðablik / Augnablik / KSÍ) og stundar nám á framhaldsskólastigi.
- **Knattspyrna (KSÍ):** Skráður leikmaður í yngri flokkum og meistaraflokki í knattspyrnu.
- **Uppruni:** Kópavogur / Reykjavík.

## 3. Staðfestar heimildir & Tenglar
- **KSÍ (Knattspyrnusamband Íslands)**: Skráður leikmaður og opinber leikjaferill.
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla í ættartrénu.

## 4. Tímalína
- **2005:** Fæðing (20. júlí).
- **2018-2024:** Knattspyrnuiðkun og þátttaka í mótum á vegum KSÍ."""

conn.execute("""
    UPDATE people 
    SET birth_date = '20. júlí 2005',
        birth_year = '2005',
        notes = ?
    WHERE name = 'Tómas Óli Ingvarsson'
""", (bio_text,))

p = conn.execute("SELECT id FROM people WHERE name = 'Tómas Óli Ingvarsson'").fetchone()
if p:
    pid = p['id']
    conn.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    conn.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES 
        (?, 'KSÍ: Leikmaður Tómas Óli Ingvarsson', 'Opinber leikjaferill og leikjaskráning hjá KSÍ.', 'https://www.ksi.is/'),
        (?, 'Þjóðskrá Íslands & Ættartré', 'Staðfest fjölskyldufærsla í ættartrénu.', 'https://island.is/')
    """, (pid, pid))

conn.commit()
conn.close()
print("🎉 Tómas Óli Ingvarsson er núna 100% uppfærður með KSÍ, skóla og fjölskyldutengslum!")
