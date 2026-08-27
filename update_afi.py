import sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

afi_bio = """# Sigurjón Einarsson

## 1. Yfirlit & Fjölskylda
Sigurjón Einarsson (f. 17. okt. 1895 í Odda, Mýrahr., A-Skaft. - d. 28. feb. 1983).
- **Fæðingarstaður:** Odda, Mýrahr., A-Skaft.
- **Foreldrar:** Einar Sigjón Þorvarðarson og Ingunn Jónsdóttir.
- **Maki:** Þorbjörg Benediktsdóttir (4. ágúst 1898 – 27. feb. 1992).
- **Börn (7):** Einar Sigurjónsson (1920–2004), Benedikt Sigurjónsson (1922–2009), Ingunn Sigríður Sigurjónsdóttir (1924–2000), Arnór Sigurjónsson (1926–1979), Aðalheiður Sigurjónsdóttir (1928–2022), Sigurbjörg Sigurjónsdóttir (1938–2025), Erla Þórhildur Sigurjónsdóttir (f. 1944).
- **Systkini (7):** Drengur (1891), Guðný (1892–1990), Jón (1894), Þorbjörg (1898–1995), Sigurborg (1901–1996), Stefán (1905–1998), Guðleif (1911–2002).

## 2. Lífshlaup, Störf & Búseta
Bóndi og símstöðvarstjóri. Vinnumaður á Brunnhóli, Einholtssókn, Skaft. 1910. Var þar 1930. Búsettur lengst af á Brunnhóli á Mýrum í Austur-Skaftafellssýslu. Fjöldi afkomenda: 161 (152 á lífi, 9 látnir).

## 3. Staðfestar heimildir úr Íslendingabók
- **Þjóðskrá**
- **Manntal á Íslandi 1910**
- **Krossaætt**: Niðjar Gunnlaugs Þorvaldssonar og Þóru Jónsdóttur á Hellu á Árskógsströnd (Höf. Björn Pétursson, Útg. Mál og mynd, Reykjavík 1998)
- **Sveitir og jarðir í Múlaþingi** (Höf. Ritstjórn Ármann Halldórsson, Útg. Búnaðarsamband Austurlands, Egilsstaðir 1974-1995)
- **Vélstjóra- og vélfræðingatal, 1997** (Höf. Ritstjóri Þorsteinn Jónsson, Útg. Þjóðsaga, Reykjavík 1996-1997)
- **Manntal á Íslandi 1930**
- **Morgunblaðið** (23/07/2004, Útg. Árvakur, Reykjavík)
- **Kirkjubók Bjarnanessóknar**, A-Skaft.

## 4. Tímalína
- **1895:** Fæddur 17. október í Odda, Mýrahreppi, A-Skaftafellssýslu.
- **1910:** Vinnumaður á Brunnhóli, Einholtssókn.
- **1930:** Bóndi og símstöðvarstjóri á Brunnhóli.
- **1983:** Látinn 28. febrúar."""

conn.execute("""
    UPDATE people 
    SET birth_date = '17. okt. 1895',
        birth_year = '1895',
        birth_place = 'Odda, Mýrahr., A-Skaft.',
        death_date = '28. feb. 1983',
        death_year = '1983',
        notes = ?
    WHERE id = 'I212565201805'
""", (afi_bio,))

afi_sources = [
    ("Íslendingabók: Þjóðskrá", "Þjóðskrá Íslands.", "https://www.islendingabok.is/"),
    ("Manntal á Íslandi 1910", "Vinnumaður á Brunnhóli, Einholtssókn, Skaft. 1910.", "https://manntal.is/"),
    ("Krossaætt: Niðjar Gunnlaugs og Þóru", "Höf. Björn Pétursson. Útg. Mál og mynd, Reykjavík 1998.", "https://www.islendingabok.is/"),
    ("Sveitir og jarðir í Múlaþingi", "Höf. Ritstjórn Ármann Halldórsson. Búnaðarsamband Austurlands, 1974-1995.", "https://timarit.is/"),
    ("Vélstjóra- og vélfræðingatal, 1997", "Höf. Ritstjóri Þorsteinn Jónsson. Útg. Þjóðsaga, Reykjavík 1996-1997.", "https://timarit.is/"),
    ("Manntal á Íslandi 1930", "Bóndi og símstöðvarstjóri á Brunnhóli 1930.", "https://manntal.is/"),
    ("Kirkjubók Bjarnanessóknar, A-Skaft.", "Opinber skráning úr kirkjubók.", "https://heimildir.is/"),
    ("Morgunblaðið 23/07/2004", "Útg. Árvakur, Reykjavík.", "https://timarit.is/")
]

for title, snip, link in afi_sources:
    conn.execute("INSERT OR IGNORE INTO sources (person_id, title, snippet, link) VALUES ('I212565201805', ?, ?, ?)", (title, snip, link))

conn.commit()
conn.close()
print("Uppfærði afa Sigurjón Einarsson með öllum upplýsingum úr Íslendingabók!")
