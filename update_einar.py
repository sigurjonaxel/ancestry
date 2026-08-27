import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

einar_bio = """# Einar Sigjón Þorvarðarson

## 1. Yfirlit & Fjölskylda
Einar Sigjón Þorvarðarson (f. 8. jan. 1867 í Kálfafellsstaðarsókn, A-Skaft. - d. 17. des. 1955).
- **Fæðingarstaður:** Kálfafellsstaðarsókn, A-Skaft.
- **Foreldrar:** Þorvarður Magnússon (1834–1868) og Snjófríður Einarsdóttir (1842–1934).
- **Maki:** Ingunn Jónsdóttir (28. sept. 1866 – 18. nóv. 1958).
- **Börn (8):** Drengur (1891), Guðný (1892–1990), Jón (1894), Sigurjón Einarsson (1895–1983), Þorbjörg (1898–1995), Sigurborg (1901–1996), Stefán (1905–1998), Guðleif (1911–2002).
- **Systkini:** Jón Þorvarðarson.

## 2. Lífshlaup, Störf & Búseta
Bóndi á Brunnhóli, Einholtssókn, Skaft. og hreppstjóri í Odda. Fjöldi afkomenda: 351 (319 á lífi, 32 látnir).

## 3. Staðfestar heimildir úr Íslendingabók
- **Manntal á Íslandi 1910**
- **Vélstjóra- og vélfræðingatal, 1997** (Höf. Ritstjóri Þorsteinn Jónsson, Útg. Þjóðsaga, Reykjavík 1996-1997)
- **Manntal á Íslandi 1930**
- **Almanak þjóðvinafélagsins 1875-1879(1916), 1880-1991** (Útg. Hið íslenzka Þjóðvinafélag, Kaupm./Rvík 1875)
- **Kirkjubók Bjarnanessóknar, A-Skaft.**

## 4. Tímalína
- **1867:** Fæddur 8. janúar í Kálfafellsstaðarsókn, A-Skaft.
- **1892:** Gifting við Ingunni Jónsdóttur.
- **1910:** Bóndi á Brunnhóli og hreppstjóri í Odda.
- **1955:** Látinn 17. desember."""

conn.execute("""
    UPDATE people 
    SET birth_date = '8. jan. 1867',
        birth_year = '1867',
        birth_place = 'Kálfafellsstaðarsókn, A-Skaft.',
        death_date = '17. des. 1955',
        death_year = '1955',
        notes = ?
    WHERE id = 'I212565204711'
""", (einar_bio,))

einar_sources = [
    ("Manntal á Íslandi 1910", "Bóndi á Brunnhóli, Einholtssókn, Skaft. og hreppstjóri í Odda.", "https://manntal.is/"),
    ("Vélstjóra- og vélfræðingatal, 1997", "Höf. Ritstjóri Þorsteinn Jónsson. Útg. Þjóðsaga, Reykjavík 1996-1997.", "https://timarit.is/"),
    ("Manntal á Íslandi 1930", "Bóndi á Brunnhóli 1930.", "https://manntal.is/"),
    ("Almanak þjóðvinafélagsins 1875-1879", "Útg. Hið íslenzka Þjóðvinafélag, Kaupm./Rvík 1875.", "https://timarit.is/"),
    ("Kirkjubók Bjarnanessóknar, A-Skaft.", "Opinber skráning úr kirkjubók.", "https://heimildir.is/")
]

for title, snip, link in einar_sources:
    conn.execute("INSERT OR IGNORE INTO sources (person_id, title, snippet, link) VALUES ('I212565204711', ?, ?, ?)", (title, snip, link))

conn.commit()
conn.close()
print("Uppfærði Einar Sigjón Þorvarðarson með öllum upplýsingum úr Íslendingabók!")
