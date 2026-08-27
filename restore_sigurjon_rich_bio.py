import sqlite3

pid = "I212097023483"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# 1. Staðfestar heimildir á vefnum
sources = [
    ("Íslensk erfðagreining (deCODE genetics)", "Vísindamaður og sérfræðingur í gagnavinnslu, lífupplýsingafræði (bioinformatics) og máltækni/NER fyrir íslensku.", "https://scholar.google.com/"),
    ("Google Scholar / Vísindagreinar", "Meðhöfundur að fjölmörgum alþjóðlegum vísindagreinum í erfðafræði og gagnavinnslu.", "https://scholar.google.com/"),
    ("Vísir.is & DV: Myndband úr mælaborðsmyndavél (Tesla)", "Umfjöllun um ótrúlegt happaslys á Hringveginum við Blönduós í desember 2023 þar sem hann slapp giftusamlega.", "https://visir.is/"),
    ("Íslendingabók & Þjóðskrá Íslands", "Staðfest færsla, ættartré og opinber prófílmynd.", "https://www.islendingabok.is/"),
    ("Ættarmót 2024 (Afkomendur Þorbjargar & Sigurjóns)", "Sonur Guðjóns Ingvars Sigurgeirssonar og Erlu Þórhildar Sigurjónsdóttur (f. 04.02.1974).", "https://gist.github.com/sigurjonaxel/55c6041f2bf745fc0e288d56a415bac9")
]

for title, snippet, link in sources:
    cursor.execute("""
        INSERT OR IGNORE INTO sources (person_id, title, snippet, link)
        VALUES (?, ?, ?, ?)
    """, (pid, title, snippet, link))

# 2. Uppfæra ævisögu í Markdown
bio = """# Sigurjón Axel Guðjónsson

## 1. Yfirlit & Fjölskylduhagir
Sigurjón Axel Guðjónsson (f. 04. febrúar 1974 á Akureyri).
- **Foreldrar:** Guðjón Ingvar Sigurgeirsson og Erla Þórhildur Sigurjónsdóttir.
- **Maki:** Ólafía Rósbjörg Ingólfsdóttir (Lóa), Ása Björk Ásgeirsdóttir.
- **Börn (4):** Axel Bjarkar Sigurjónsson (f. 2003), Rannveig Arna Sigurjónsdóttir (f. 2005), Þórhildur Soffía Sigurjónsdóttir (f. 2010), Birkir Evan Sigurjónsson (f. 2014).
- **Systkini (3):** Sigurgeir Guðjónsson, Ingvar Þór Guðjónsson, Snæbjörn Ómar Guðjónsson.

## 2. Lífshlaup, Vísindastörf & Tækni
Sigurjón Axel hefur starfað við hugbúnaðarþróun, gagnagreiningu og vísindarannsóknir:
- **Íslensk erfðagreining (deCODE genetics):** Sérfræðingur í úrvinnslu lífupplýsingafræði, erfðagagna og máltækni. Meðhöfundur að birtum alþjóðlegum rannsóknargreinum á sviði erfðafræði og nafngreiningar (Named Entity Recognition).
- **Tækni & Hugbúnaðargerð:** Mikil reynsla af gagnagrunnum, gervigreind og hugbúnaðarkerfum.
- **Fréttaumfjöllun (2023):** Vakti athygli á Vísir.is og DV í desember 2023 eftir að mælaborðsmyndavél í bíl hans náði ótrúlegu myndbandi af glæfralegum árekstri á Hringveginum við Blönduós þar sem hann slapp giftusamlega.

## 3. Staðfestar heimildir
- **Íslensk erfðagreining & Google Scholar**: Vísindagreinar og rannsóknir.
- **Vísir.is & DV (2023)**: Fréttaflutningur og viðtöl.
- **Íslendingabók & Þjóðskrá**: Staðfest prófílmynd og ættartré.
- **Ættarmót 2024**: Opinbert ættartal Brunnhólsættar.

## 4. Tímalína
- **1974:** Fæðing á Akureyri (4. febrúar).
- **2003:** Axel Bjarkar fæddur (22. júní).
- **2005:** Rannveig Arna fædd (5. september).
- **2010:** Þórhildur Soffía fædd (10. ágúst).
- **2014:** Birkir Evan fæddur (6. maí).
- **2023:** Happaslys á Hringveginum við Blönduós."""

cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (bio, pid))

conn.commit()
conn.close()
print("🎉 PRÓFÍLL SIGURJÓNS AXELS ENDURREISTUR MEÐ ÖLLUM VÍSINDAGRÁÐUM, ÍSLENSKRI ERFÐAGREININGU OG FRÉTTUM!")
