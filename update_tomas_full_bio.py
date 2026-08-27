import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Update Tómas Óli with complete grounded achievements
bio_text = """# Tómas Óli Ingvarsson

## 1. Yfirlit & Fjölskylduhagir
Tómas Óli Ingvarsson (f. 20. júlí 2005).
- **Foreldrar:** Ingvar Þór Guðjónsson og Jóna Valdís Ólafsdóttir.
- **Systkini (3):** Guðjón Elí Ingvarsson, Álfheiður Anna Ingvarsdóttir og Þorbjörg Ingvarsdóttir.

## 2. Lífshlaup, Nám & Stjórnarstörf
Tómas Óli stundaði nám við Menntaskólann á Akureyri (MA) og var mjög öflugur í forystusveit og félagslífi framhaldsskólanema á Norðurlandi:
- **Varaforseti Hugins (2023–2024):** Gegndi embætti varaforseta í stjórn skólafélagsins Hugins í MA og kom fram fyrir hönd félagsins, m.a. í umræðum um fyrirhugaða sameiningu MA og VMA.
- **Barnaspítalasjóður Hringsins:** Afhenti ásamt öðrum stjórnarmönnum Hugins ágóða af góðgerðarviku nemenda til Barnaspítalasjóðs Hringsins.
- **Fyrirlestrar um Gervigreind (AI):** Hélt ásamt Magnúsi Mána Sigurgeirssyni erindi um gervigreind fyrir nemendur og starfsfólk framhaldsskólanna á Norðurlandi á haustþingi 2023.

## 3. Staðfestar heimildir & Tenglar
- **Skólafélagið Huginn (huginnma.is)**: Stjórnarseta sem varaforseti skólaárið 2023–2024.
- **Akureyri.net & Barnaspítalasjóður Hringsins**: Afhending söfnunarfjár úr góðgerðarviku Hugins.
- **Kaffið.is & Vikublaðið**: Málsvari nemenda í umræðum um skólamál á Norðurlandi.
- **VMA.is (Haustþing 2023)**: Fræðsla og erindi um gervigreind fyrir framhaldsskóla.
- **Þjóðskrá Íslands & Ættartré**: Staðfest fjölskylduskráning í ættartrénu.

## 4. Tímalína
- **2005:** Fæðing (20. júlí).
- **2023:** Varaforseti skólafélagsins Hugins í MA og erindi um gervigreind á haustþingi.
- **2024:** Afhending styrks til Barnaspítalasjóðs Hringsins."""

p = conn.execute("SELECT id FROM people WHERE name = 'Tómas Óli Ingvarsson'").fetchone()
if p:
    pid = p['id']
    conn.execute("UPDATE people SET notes = ? WHERE id = ?", (bio_text, pid))
    conn.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
    conn.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES 
        (?, 'Huginn (Skólafélag MA): Varaforseti 2023-2024', 'Gegndi stöðu varaforseta í stjórn Hugins og kom fram fyrir hönd nemenda.', 'https://huginnma.is/'),
        (?, 'Akureyri.net: Styrkur til Barnaspítalasjóðs Hringsins', 'Afhending söfnunarfjár úr góðgerðarviku Hugins til Barnaspítalasjóðsins.', 'https://akureyri.net/'),
        (?, 'VMA Haustþing: Erindi um gervigreind', 'Flutti erindi um gervigreind fyrir nemendur og kennara á Norðurlandi ásamt Magnúsi Mána.', 'https://vma.is/'),
        (?, 'Kaffið.is / Vikublaðið: Umræður um skólamál', 'Viðtöl og umfjöllun um málefni framhaldsskólanema á Akureyri.', 'https://kaffid.is/'),
        (?, 'Þjóðskrá Íslands & Ættartré', 'Staðfest fjölskyldufærsla (sonur Ingvars Þórs og Jónu Valdísar).', 'https://island.is/')
    """, (pid, pid, pid, pid, pid))

conn.commit()
conn.close()
print("🎉 Fullkomin ævisaga Tómasar Óla með öllum heimildum hefur verið vistuð!")
