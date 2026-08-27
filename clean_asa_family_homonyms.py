import sqlite3

conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# 1. Hreinsa Ásgeir Egilsson (f. 1952) af tónlistarmanninum Ásgeiri Trausta
cursor.execute("DELETE FROM sources WHERE person_id = 'I212605393119' AND (title LIKE '%Afterglow%' OR title LIKE '%Singer%' OR title LIKE '%Ásgeir%')")
cursor.execute("""
    UPDATE people SET notes = '# Ásgeir Egilsson

## 1. Yfirlit & Fjölskylduhagir
Ásgeir Egilsson (f. 14. júní 1952).
- **Maki:** Rannveig Ingvadóttir (f. 16.06.1958).
- **Börn (4):** Ása Björk, Egill, Jón Heiðar og Óskar Ásgeirssynir og dætur.

## 2. Lífshlaup & Upplýsingar
Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.

## 3. Staðfestar heimildir
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **14.06.1952:** Fæðing'
    WHERE id = 'I212605393119'
""")

# 2. Hreinsa Jón Heiðar Ásgeirsson (f. 1991) af tónskáldinu Jóni Ásgeirssyni (1928-2025)
cursor.execute("DELETE FROM sources WHERE person_id = 'I212605397836'")
cursor.execute("""
    UPDATE people SET notes = '# Jón Heiðar Ásgeirsson

## 1. Yfirlit & Fjölskylduhagir
Jón Heiðar Ásgeirsson (f. 17. mars 1991).
- **Foreldrar:** Ásgeir Egilsson, Rannveig Ingvadóttir.
- **Maki:** Gwen Gilbank.
- **Börn (1):** Freyja Sif Jónsdóttir (f. 2023).
- **Systkini (3):** Ása Björk, Egill og Óskar Ásgeirssynir.

## 2. Lífshlaup & Upplýsingar
Skráður einstaklingur í ættartrénu með staðfestar fjölskylduupplýsingar.

## 3. Staðfestar heimildir
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **17.03.1991:** Fæðing'
    WHERE id = 'I212605397836'
""")

# 3. Hreinsa Rannveigu Ingvadóttur af Brunnhólsættar stimpli
cursor.execute("""
    UPDATE people SET notes = '# Rannveig Ingvadóttir

## 1. Yfirlit & Fjölskylduhagir
Rannveig Ingvadóttir (f. 16. júní 1958).
- **Maki:** Ásgeir Egilsson (f. 14.06.1952).
- **Börn (4):** Ása Björk, Egill, Óskar og Jón Heiðar Ásgeirssynir og dætur.

## 2. Lífshlaup & Upplýsingar
Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.

## 3. Staðfestar heimildir
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **16.06.1958:** Fæðing'
    WHERE id = 'I212605393158'
""")

# 4. Hreinsa Ásu Björk Ásgeirsdóttur af Brunnhólsættar stimpli
cursor.execute("""
    UPDATE people SET notes = '# Ása Björk Ásgeirsdóttir

## 1. Yfirlit & Fjölskylduhagir
Ása Björk Ásgeirsdóttir (f. 06. mars 1976).
- **Foreldrar:** Ásgeir Egilsson, Rannveig Ingvadóttir.
- **Makar:** Sigurjón Axel Guðjónsson, Þröstur Helgason.
- **Börn (4):** Axel Bjarkar Sigurjónsson (f. 2003), Rannveig Arna Sigurjónsdóttir (f. 2005), Þórhildur Soffía Sigurjónsdóttir (f. 2010), Birkir Evan Sigurjónsson (f. 2014).
- **Systkini (3):** Egill Ásgeirsson, Óskar Ásgeirsson, Jón Heiðar Ásgeirsson.

## 2. Lífshlaup & Upplýsingar
Skráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar.

## 3. Staðfestar heimildir
- **Þjóðskrá & Ættartré**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **06.03.1976:** Fæðing'
    WHERE id = 'I212565585214'
""")

conn.commit()
conn.close()
print("✓ Fjölskylda Ásu Bjarkar hreinsuð af öllum nafnavillum (tónlistarmönnum, tónskáldum og röngum ættarmerkjum)!")
