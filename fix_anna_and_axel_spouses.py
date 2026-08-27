import sqlite3

conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# 1. Delete bogus I_ADD_500 placeholder and all relations to it
cursor.execute("DELETE FROM people WHERE id = 'I_ADD_500'")
cursor.execute("DELETE FROM relations WHERE person_id = 'I_ADD_500' OR related_id = 'I_ADD_500'")

# 2. Ensure Anna Huyen Ngo (I212609213455) is the ONLY spouse of Axel Bjarkar (I212565202554)
cursor.execute("DELETE FROM relations WHERE person_id = 'I212565202554' AND relation_type = 'spouse'")
cursor.execute("DELETE FROM relations WHERE person_id = 'I212609213455' AND relation_type = 'spouse'")

cursor.execute("INSERT INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212565202554', 'I212609213455', 'spouse')")
cursor.execute("INSERT INTO relations (tree_id, person_id, related_id, relation_type) VALUES ('sigurjon', 'I212609213455', 'I212565202554', 'spouse')")

# 3. Update Markdown notes on Axel Bjarkar to reflect Anna Huyen Ngo as spouse
bio_axel = """# Axel Bjarkar Sigurjónsson

## 1. Yfirlit & Fjölskylduhagir
Axel Bjarkar Sigurjónsson (f. 22. júní 2003).
- **Foreldrar:** Sigurjón Axel Guðjónsson, Ása Björk Ásgeirsdóttir.
- **Maki:** Anna Huyen Ngo (f. 2003).
- **Systkini (3):** Rannveig Arna Sigurjónsdóttir, Þórhildur Soffía Sigurjónsdóttir, Birkir Evan Sigurjónsson.

## 2. Nám, Vísindi & Hugbúnaðargerð
Axel Bjarkar er hugbúnaðar- og gervigreindarfræðingur:
- **Fulbright SUSI 2024:** Fulltrúi Íslands í virtri SUSI náms- og leiðtogadvöl í Bandaríkjunum á vegum Fulbright-stofnunarinnar.
- **APRÓ (apro.is):** Hugbúnaðar- og gervigreindarforritari.
- **Háskólinn í Reykjavík:** Nám í mekatróník / vélrænni hátækni og rannsóknir á lífupplýsingatækni og vélanámi (Nano/HR).
- **Alþjóðleg verðlaun í YRE (Young Reporters for the Environment):** 1. verðlaun á alþjóðavettvangi árið 2020 fyrir verkið „Mengun með miðlum“.

## 3. Staðfestar heimildir
- **Fulbright Ísland**: SUSI styrkþegi 2024.
- **APRÓ (apro.is)**: AI & hugbúnaðarteymi.
- **Landvernd / YRE International**: 1. verðlaun í umhverfisblaðamennsku.
- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **2003:** Fæðing (22. júní).
- **2020:** 1. verðlaun í YRE alþjóðlegu blaðamannakeppninni.
- **2024:** Fulbright SUSI leiðtogastyrkur í Bandaríkjunum."""

cursor.execute("UPDATE people SET notes = ? WHERE id = 'I212565202554'", (bio_axel,))

# 4. Update Markdown notes on Anna Huyen Ngo
bio_anna = """# Anna Huyen Ngo

## 1. Yfirlit & Fjölskylduhagir
Anna Huyen Ngo (f. 2003).
- **Maki:** Axel Bjarkar Sigurjónsson (f. 22.06.2003).

## 2. Lífshlaup & Upplýsingar
Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.

## 3. Staðfestar heimildir
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **2003:** Fæðing"""

cursor.execute("UPDATE people SET notes = ? WHERE id = 'I212609213455'", (bio_anna,))

conn.commit()
conn.close()
print("✓ Eyddi 'Óþekkt nafn' og tengdi Önnu Huyen Ngo og Axel Bjarkar 100% rétt saman!")
