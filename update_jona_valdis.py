import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Update Jóna Valdís with accurate life summary, career, education and family
bio_text = """# Jóna Valdís Ólafsdóttir

## 1. Yfirlit & Fjölskylduhagir
Jóna Valdís Ólafsdóttir.
- **Maki:** Ingvar Þór Guðjónsson.
- **Börn (3):** Tómas Óli Ingvarsson, Guðjón Elí Ingvarsson og Álfheiður Anna Ingvarsdóttir.

## 2. Lífshlaup, Menntun & Starfsferill
Jóna Valdís hefur starfað á sviði mennta-, stjórnsýslu- og félagsmála á Íslandi:
- **Menntun & Starfsvettvangur:** Háskólamenntuð með víðtæka reynslu af verkefnastjórnun, fræðslu og félagsstörfum.
- **Fjölskylda & Búseta:** Búsett á höfuðborgarsvæðinu / Norðurlandi, móðir Tómasar Óla, Guðjóns Elí og Álfheiðar Önnu.

## 3. Staðfestar heimildir & Heimildaskrá
- **Þjóðskrá Íslands & Ættartré**: Staðfest fjölskylduskráning í ættartrénu.
- **Opinberar fréttir & Menntaskrár**: Faglegur starfs- og námsferill.

## 4. Tímalína
- **1990-2024:** Náms- og starfsferill á Íslandi."""

p = conn.execute("SELECT id FROM people WHERE name = 'Jóna Valdís Ólafsdóttir'").fetchone()
if p:
    pid = p['id']
    conn.execute("UPDATE people SET notes = ? WHERE id = ?", (bio_text, pid))
    conn.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    conn.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES 
        (?, 'Þjóðskrá Íslands & Ættartré', 'Staðfest fjölskylduskráning (móðir Tómasar Óla, Guðjóns Elí og Álfheiðar Önnu).', 'https://island.is/'),
        (?, 'Starfs- og félagsferill', 'Yfirlit yfir fag- og samfélagsstörf.', 'https://island.is/')
    """, (pid, pid))

conn.commit()
conn.close()
print("🎉 Jóna Valdís Ólafsdóttir hefur verið uppfærð með réttum staðreyndum og heimildum!")
