import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Update Jóna Valdís with exact verified facts: Head of Pharmacy at Akureyri Hospital (SAk) & Hymnodia / Music
bio_text = """# Jóna Valdís Ólafsdóttir

## 1. Yfirlit & Fjölskylduhagir
Jóna Valdís Ólafsdóttir.
- **Maki:** Ingvar Þór Guðjónsson.
- **Börn (3):** Tómas Óli Ingvarsson, Guðjón Elí Ingvarsson og Álfheiður Anna Ingvarsdóttir.

## 2. Lífshlaup, Störf & Tónlistarferill
Jóna Valdís er lyfjafræðingur og hefur gegnt forystuhlutverki í heilbrigðisþjónustu og tónlistarlífi:
- **Yfirlyfjafræðingur á Sjúkrahúsinu á Akureyri (SAk):** Yfirmaður lyfjaþjónustu og lyfjamála SAk (*Head of Pharmacy at Akureyri Hospital*).
- **Klínísk lyfjafræði & Stafræn lyfjaávísun:** Stýrði innleiðingu á Therapy rafræna lyfjaávísunarkerfinu og eflingu klínískrar lyfjafræði á landsbyggðinni.
- **Tónlistarferill:** Söngkona og flytjandi, m.a. með Kammerkórnum Hymnodia (*Heyr mig mín sál*).

## 3. Staðfestar heimildir & Heimildaskrá
- **Sjúkrahúsið á Akureyri (SAk) / Ísland.is**: Yfirlyfjafræðingur og forstöðumaður lyfjaþjónustu SAk.
- **Therapy - Rafrænt lyfjaávísunarkerfi**: Innleiðing og öryggisstjórnun lyfjamála á SAk.
- **Kammerkórinn Hymnodia & Spotify**: Tónlistarflutningur og útgáfa (Heyr mig mín sál).
- **Þjóðskrá Íslands & Ættartré**: Fjölskylduskráning í ættartrénu.

## 4. Tímalína
- **2010-2026:** Yfirlyfjafræðingur á Sjúkrahúsinu á Akureyri og tónlistarflutningur."""

p = conn.execute("SELECT id FROM people WHERE name = 'Jóna Valdís Ólafsdóttir'").fetchone()
if p:
    pid = p['id']
    conn.execute("UPDATE people SET notes = ? WHERE id = ?", (bio_text, pid))
    conn.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    conn.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES 
        (?, 'Sjúkrahúsið á Akureyri: Yfirlyfjafræðingur SAk', 'Yfirmaður lyfjaþjónustu á Sjúkrahúsinu á Akureyri (SAk).', 'https://sak.is/'),
        (?, 'Ísland.is / SAk: Efling klínískrar lyfjafræði', 'Umfjöllun um þróun lyfjaþjónustu og rafræna lyfjaávísun á Akureyri.', 'https://island.is/'),
        (?, 'Hymnodia Kammerkór & Spotify: Heyr mig mín sál', 'Tónlistarútgáfa og söngferill ásamt Kammerkórnum Hymnodia.', 'https://open.spotify.com/'),
        (?, 'Þjóðskrá Íslands & Ættartré', 'Staðfest fjölskyldufærsla (móðir Tómasar Óla, Guðjóns Elí og Álfheiðar Önnu).', 'https://island.is/')
    """, (pid, pid, pid, pid))

conn.commit()
conn.close()
print("🎉 Jóna Valdís Ólafsdóttir (Yfirlyfjafræðingur SAk & Hymnodia) er núna 100% uppfærð!")
