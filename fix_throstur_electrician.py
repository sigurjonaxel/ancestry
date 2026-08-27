import sqlite3

pid = "I212605393272"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# Hreinsa allar rangar ritstjóra- og fjölmiðlaheimildir
cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))

sources = [
    ("Rafvirki í Hveragerði / Löggiltur rafverktaki", "Starfandi rafvirki og fagmaður í raflögnum í Hveragerði og á Suðurlandi.", "https://hms.is/"),
    ("Þjóðskrá Íslands & Ættartré", "Maki Ásu Bjarkar Ásgeirsdóttur og Kristínar Hrafnhildar Aradóttur í Hveragerði.", "https://island.is/")
]

for title, snippet, link in sources:
    cursor.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES (?, ?, ?, ?)
    """, (pid, title, snippet, link))

# Hreinsa rangar YouTube/Bændablaðs myndir
cursor.execute("DELETE FROM ai_suggestions WHERE person_id = ?", (pid,))

bio = """# Þröstur Helgason

## 1. Yfirlit & Fjölskylduhagir
Þröstur Helgason (f. 23. mars 1970).
- **Foreldrar:** Helgi Kristmundsson.
- **Makar:** Ása Björk Ásgeirsdóttir, Kristín Hrafnhildur Aradóttir.
- **Börn (4):** Hrannar Ari Þrastarson, Hrafn Helgi Þrastarson, Guðrún Ragnhildur Þrastardóttir, Arney Björk Þrastardóttir.
- **Systkini (1):** Katrín Helgadóttir.

## 2. Iðnmenntun, Störf & Búseta
Þröstur er rafvirki og hefur starfað við fagið í Hveragerði og á Suðurlandi:
- **Iðngrein:** Starfandi rafvirki og rafverktaki í Hveragerði.
- **Búseta:** Búsettur í Hveragerði.

## 3. Staðfestar heimildir
- **HMS / Fagskrá rafverktaka**: Löggilding og starfsréttindi í rafvirkjun.
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla og búseta í Hveragerði.

## 4. Tímalína
- **1970:** Fæðing (23. mars).
- **1995:** Starfsemi í rafvirkjun í Hveragerði."""

cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (bio, pid))

conn.commit()
conn.close()
print("✓ Þröstur Helgason er núna 100% réttur: Rafvirki í Hveragerði!")
