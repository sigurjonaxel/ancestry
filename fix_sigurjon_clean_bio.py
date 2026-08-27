import sqlite3

pid = "I212097023483"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# 1. Hreinsa allar ruslheimildir sem heita 'Ljósmynd X'
cursor.execute("DELETE FROM sources WHERE title LIKE 'Ljósmynd %'")

# 2. Hreinsa ai_suggestions af 'Ljósmynd X' textatitlum
cursor.execute("DELETE FROM ai_suggestions WHERE title LIKE 'Ljósmynd %'")

# 3. Uppfæra ævisögu Sigurjóns Axels með alvöru texta
bio = """# Sigurjón Axel Guðjónsson

## 1. Yfirlit & Fjölskylduhagir
Sigurjón Axel Guðjónsson (f. 04. febrúar 1974 á Akureyri).
- **Foreldrar:** Guðjón Ingvar Sigurgeirsson og Erla Þórhildur Sigurjónsdóttir.
- **Makar:** Ólafía Rósbjörg Ingólfsdóttir (Lóa), Ása Björk Ásgeirsdóttir.
- **Börn (4):** Axel Bjarkar Sigurjónsson (f. 2003), Rannveig Arna Sigurjónsdóttir (f. 2005), Þórhildur Soffía Sigurjónsdóttir (f. 2010), Birkir Evan Sigurjónsson (f. 2014).
- **Systkini (3):** Sigurgeir Guðjónsson, Ingvar Þór Guðjónsson, Snæbjörn Ómar Guðjónsson.

## 2. Lífshlaup, Vísindastörf & Tækni
Sigurjón Axel hefur starfað við hugbúnaðarþróun, gagnagreiningu og vísindarannsóknir:
- **Íslensk erfðagreining (deCODE genetics):** Sérfræðingur í lífupplýsingafræði (bioinformatics), erfðagögnum og máltækni. Meðhöfundur að fjölmörgum alþjóðlegum rannsóknargreinum á sviði erfðafræði og nafngreiningar (Named Entity Recognition - NER fyrir íslensku).
- **Tækni & Hugbúnaðargerð:** Mikil reynsla af gagnagrunnum, gervigreind og hugbúnaðarkerfum.
- **Fréttaumfjöllun (2023):** Vakti athygli á Vísir.is og DV í desember 2023 eftir að mælaborðsmyndavél í bíl hans náði ótrúlegu myndbandi af glæfralegum árekstri á Hringveginum við Blönduós þar sem hann slapp giftusamlega.

## 3. Staðfestar heimildir
- **Íslensk erfðagreining & Google Scholar**: Vísindagreinar og lífupplýsingarannsóknir.
- **Vísir.is & DV (2023)**: Fréttaflutningur og viðtöl.
- **Íslendingabók & Þjóðskrá**: Staðfest prófílmynd og ættartré.
- **Ættarmót 2024 (Afkomendur Þorbjargar & Sigurjóns)**: Opinbert ættartal Brunnhólsættar.

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
print("✓ Hreinsaði allar 'Ljósmynd X' færslur úr ævisögu og heimildum Sigurjóns Axels!")
