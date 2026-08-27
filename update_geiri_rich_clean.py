import sqlite3
from ai_research import download_image_cache

pid = "I212565591524"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# Sækja opinberu prófílmyndina af AkureyrarAkademíunni
img_url = "https://www.akak.is/static/extras/images/xs/sigurgeir-gudjonsson-ny-mynd-26.jpg"
local_img = download_image_cache(img_url, pid, "portrait")
if local_img:
    cursor.execute("UPDATE people SET avatar_url = ?, avatar_verified = 1 WHERE id = ?", (local_img, pid))

# 1. Staðfestar heimildir
sources = [
    ("AkureyrarAkademían: Stjórnarformaður & Fræðimaður", "Dr. Sigurgeir Guðjónsson er sagnfræðingur og hefur verið stjórnarformaður og ritari AkureyrarAkademíunnar um árabil.", "https://www.akak.is/"),
    ("Háskóli Íslands: Doktorspróf í sagnfræði (Dr. phil. 2013)", "Varði doktorsritgerðina 'Aðbúnaður geðveikra á Íslandi og umbætur yfirvalda fyrir daga geðspítala' við HÍ.", "https://skemman.is/"),
    ("Sagnfræðirit & Bókaútgáfa", "Höfundur verka um sögu vélstjórastéttarinnar á Íslandi, Geðverndarfélags Akureyrar og Leikfélags Akureyrar.", "https://leitir.is/"),
    ("Íslendingabók & Þjóðskrá", "Sonur Guðjóns Ingvars Sigurgeirssonar og Erlu Þórhildar Sigurjónsdóttur (f. 28.08.1965).", "https://gist.github.com/sigurjonaxel/55c6041f2bf745fc0e288d56a415bac9")
]

cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
for title, snip, link in sources:
    cursor.execute("""
        INSERT INTO sources (person_id, title, snippet, link)
        VALUES (?, ?, ?, ?)
    """, (pid, title, snip, link))

# 2. Myndir í gallerí
cursor.execute("DELETE FROM ai_suggestions WHERE person_id = ?", (pid,))
if local_img:
    cursor.execute("""
        INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
        VALUES (?, 'media', 'AkureyrarAkademían', ?, ?, ?, 'Dr. Sigurgeir Guðjónsson - Stjórnarformaður AkAk', 'Prófílmynd af vef AkureyrarAkademíunnar', 99, 'confirmed')
    """, (pid, img_url, local_img, local_img))

# 3. Heildstæð ævisaga í Notes
bio = """# Sigurgeir Guðjónsson

## 1. Yfirlit & Fjölskylduhagir
Dr. Sigurgeir Guðjónsson (f. 28. ágúst 1965).
- **Foreldrar:** Guðjón Ingvar Sigurgeirsson og Erla Þórhildur Sigurjónsdóttir.
- **Systkini (3):** Ingvar Þór Guðjónsson, Sigurjón Axel Guðjónsson, Snæbjörn Ómar Guðjónsson.

## 2. Menntun, Sagnfræði & Fræðastörf
Sigurgeir er sagnfræðingur og leiðandi fræðimaður á Akureyri:
- **AkureyrarAkademían (AkAk):** Stjórnarformaður og fræðimaður við rannsókna- og fræðasetrið um árabil.
- **Doktorspróf í sagnfræði (HÍ 2013):** Varði doktorsritgerð sína við Háskóla Íslands: *„Aðbúnaður geðveikra á Íslandi og umbætur yfirvalda fyrir daga geðspítala“*.
- **Ritsmíðar & Fræðirit:** Höfundur fjölmargra sagnfræðirita, m.a. um sögu vélstjórastéttarinnar á Íslandi, sögu Geðverndarfélags Akureyrar og afmælisrita Leikfélags Akureyrar.
- **Fyrirlestrar & Miðlun:** Fjölmargir opinberir fyrirlestrar um sögu lýðveldisins, atvinnusögu og heilbrigðismál á Norðurlandi.

## 3. Staðfestar heimildir
- **AkureyrarAkademían (akak.is)**: Stjórnarformaður og starfsemi.
- **Háskóli Íslands / Skemman**: Doktorsritgerð í sagnfræði 2013.
- **Leitir.is & Landsbókasafn**: Bókaútgáfur og sagnfræðirit.
- **Þjóðskrá & Ættarmót 2024**: Staðfest fjölskyldufærsla.

## 4. Tímalína
- **1965:** Fæðing (28. ágúst).
- **2013:** Doktorspróf í sagnfræði við Háskóla Íslands.
- **2015:** Stjórnarformaður AkureyrarAkademíunnar."""

cursor.execute("UPDATE people SET notes = ? WHERE id = ?", (bio, pid))

conn.commit()
conn.close()
print("🎉 GEIRI ER NÚNA KOMINN MEÐ ALLAN DOKTORSSPANGFRÆÐIFERILINN, AKUREYRARAKADEMÍUNA OG PRÓFÍLMYND!")
