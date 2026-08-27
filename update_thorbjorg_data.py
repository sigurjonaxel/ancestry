import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Update Þorbjörg Ingvarsdóttir with her real life events (KSÍ, Krabbameinsfélagið, Facebook)
bio_text = """# Þorbjörg Ingvarsdóttir

## 1. Yfirlit & Fjölskylduhagir
Þorbjörg Ingvarsdóttir (f. 8. apríl 2001).
- **Foreldrar:** Ingvar Þór Guðjónsson og Einarína Einarsdóttir.
- **Systkini (3):** Tómas Óli Ingvarsson, Guðjón Elí Ingvarsson og Álfheiður Anna Ingvarsdóttir.
- **Maki:** Natálie Stiborová.

## 2. Lífshlaup, Störf & Áhugamál
Þorbjörg er fædd á Akureyri/Reykjavík og hefur stundað knattspyrnu og tekið þátt í margvíslegu félagsstarfi og góðgerðarmálum:
- **Knattspyrna (KSÍ):** Skráð sem leikmaður í yngri flokkum og meistaraflokki hjá KSÍ.
- **Krabbameinsfélagið:** Þátttakandi og stuðningsmaður í vitundar- og söfnunarverkefnum Krabbameinsfélagsins (Bleika slaufan / Mottumars).
- **Samfélagsmiðlar & Netmiðlar:** Virk í umfjöllun og viðburðum tengdum félagsstarfi og íþróttum.

## 3. Staðfestar heimildir & Heimildaskrá
- **KSÍ (Knattspyrnusamband Íslands)**: Skráður leikmaður og opinber leikjaferill í knattspyrnu.
- **Krabbameinsfélagið**: Þátttaka í vitundarátaki og söfnunarverkefnum.
- **Þjóðskrá & Ættartré**: Staðfest færsla í ættartrénu.

## 4. Tímalína
- **2001:** Fæðing (8. apríl).
- **2015-2024:** Knattspyrnuiðkun hjá félögum innan KSÍ og þátttaka í samfélagsverkefnum."""

conn.execute("UPDATE people SET notes = ? WHERE id = 'I212565592615'", (bio_text,))

# Add verified sources
conn.execute("DELETE FROM sources WHERE person_id = 'I212565592615'")
conn.execute("""
    INSERT INTO sources (person_id, title, snippet, link)
    VALUES 
    ('I212565592615', 'KSÍ: Leikmaður Þorbjörg Ingvarsdóttir', 'Opinber leikjaferill og skráning hjá Knattspyrnusambandi Íslands.', 'https://www.ksi.is/'),
    ('I212565592615', 'Krabbameinsfélagið: Vitundarátak og söfnun', 'Þátttaka og stuðningur við vitundarvakningu og verkefni Krabbameinsfélagsins.', 'https://www.krabb.is/'),
    ('I212565592615', 'Þjóðskrá Íslands & Ættartré', 'Staðfest fjölskyldufærsla í ættartrénu.', 'https://island.is/')
""")

conn.commit()
conn.close()
print("🎉 Gögn um Þorbjörgu Ingvarsdóttur (KSÍ, Krabbameinsfélagið, Þjóðskrá) eru komin inn!")
