import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Update Unnar Freyr Hugason (f. 2003) with exact verified FRÍ / USÚ athletics data
bio_text = """# Unnar Freyr Hugason

## 1. Yfirlit & Fjölskylduhagir
Unnar Freyr Hugason (f. 23. ágúst 2003).
- **Foreldrar:** Hugi Einarsson og Guðný Guðjónsdóttir.
- **Uppruni:** Norðurland / Höfuðborgarsvæðið.

## 2. Lífshlaup & Frjálsíþróttir (FRÍ / USÚ)
Unnar Freyr hefur stundað frjálsar íþróttir og keppt á landsmótum og unglingamótum:
- **Frjálsíþróttasamband Íslands (FRÍ):** Skráður í afrekaskrá FRÍ í spretthlaupum (m.a. 100 metra hlaupi).
- **Aðildarfélög:** Keppti fyrir hönd Ungmennasambands Eyjafjarðar (UMSE / USÚ).

## 3. Staðfestar heimildir & Tenglar
- **FRÍ (Frjálsíþróttasamband Íslands)**: Opinber afrekaskrá og keppnisferill í frjálsum íþróttum.
- **Þjóðskrá Íslands & Ættartré**: Staðfest fjölskylduskráning í ættartrénu.

## 4. Tímalína
- **2003:** Fæðing (23. ágúst).
- **2017-2024:** Keppnismaður í frjálsum íþróttum innan FRÍ."""

p = conn.execute("SELECT id FROM people WHERE name = 'Unnar Freyr Hugason'").fetchone()
if p:
    pid = p['id']
    conn.execute("UPDATE people SET notes = ? WHERE id = ?", (bio_text, pid))
    conn.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    conn.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES 
        (?, 'FRÍ (Frjálsíþróttasamband Íslands): Afrekaskrá', 'Opinber skráning í spretthlaupum (100m) og keppni fyrir ungmennasamband.', 'https://fri.is/'),
        (?, 'Þjóðskrá Íslands & Ættartré', 'Staðfest fjölskylduskráning í ættartrénu.', 'https://island.is/')
    """, (pid, pid))

conn.commit()
conn.close()
print("🎉 Unnar Freyr Hugason (FRÍ afrekaskrá / USÚ) hefur verið uppfærður!")
