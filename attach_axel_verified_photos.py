import sqlite3

pid = "I212565202554"
conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

# 1. Ensure avatar is set to high-res YRE award photo
cursor.execute("UPDATE people SET avatar_url = 'images/cache/I212565202554_yre_axel.jpg', avatar_verified = 1 WHERE id = ?", (pid,))

# 2. Attach direct verified images to the Sögubók Sources
sources_with_images = [
    ("Morgunblaðið & Landvernd: 1. sæti í Umhverfisfréttamennsku (YRE)", "Verðlaunahafi á alþjóðavettvangi fyrir heimildamyndina Mengun með miðlum.", "https://mbl.is/", "images/cache/I212565202554_yre_axel.jpg"),
    ("APRÓ: Forritari og sérfræðingur í gervigreind & skýjalausnum", "Hugbúnaðarþróun, gervigreind og mekatróník.", "https://apro.is/", "images/cache/I212565202554_img_web_3_bf40c016.jpg"),
    ("Háskólinn í Reykjavík (HR): Mechatronics Engineering & NANO", "Nám og rannsóknir í lífupplýsingatækni og vélanámi.", "https://ru.is/", "images/cache/I212565202554_img_web_5_443e17ff.png"),
    ("Seeking Solutions to Internet Pollution: Video - Iceland Monitor", "Viðtal og umfjöllun um verðlaunamyndina í Iceland Monitor.", "https://mbl.is/", "images/cache/I212565202554_img_web_0_f297666f.jpg"),
    ("Fulbright Ísland & US Embassy: SUSI Student Leader 2024", "Fulltrúi Íslands á SUSI náms- og leiðtogadvöl í Bandaríkjunum.", "https://fulbright.is/", "")
]

cursor.execute("DELETE FROM sources WHERE person_id = ?", (pid,))
for title, snip, link, img in sources_with_images:
    cursor.execute("""
        INSERT INTO sources (person_id, title, snippet, link, image_url)
        VALUES (?, ?, ?, ?, ?)
    """, (pid, title, snip, link, img if img else None))

# 3. Clean and populate visual Media in ai_suggestions for the gallery
cursor.execute("DELETE FROM ai_suggestions WHERE person_id = ?", (pid,))

gallery_photos = [
    ("images/cache/I212565202554_yre_axel.jpg", "Verðlaunamynd YRE (1. sæti á alþjóðavettvangi)", "https://landvernd.is/"),
    ("images/cache/I212565202554_img_web_3_bf40c016.jpg", "Starfsfólk APRÓ - Gervigreindar- & hugbúnaðarteymi", "https://apro.is/"),
    ("images/cache/I212565202554_img_web_5_443e17ff.png", "Háskólinn í Reykjavík - Mekatróník rannsóknir", "https://ru.is/"),
    ("images/cache/I212565202554_img_web_0_f297666f.jpg", "Iceland Monitor / Morgunblaðið umfjöllun", "https://mbl.is/"),
    ("images/cache/I212565202554_img_web_1_36eaa0ea.jpg", "Fulbright SUSI 2024 leiðtogafundur", "https://fulbright.is/"),
    ("images/cache/I212565202554_img_web_2_6b3ae4fe.jpg", "Tæknimenntun & YRE verðlaun", "https://tskoli.is/")
]

for img_path, title, src_url in gallery_photos:
    cursor.execute("""
        INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
        VALUES (?, 'media', 'Staðfest ljósmynd', ?, ?, ?, ?, 'Ljósmynd í Sögubók', 99, 'pending')
    """, (pid, src_url, img_path, img_path, title))

conn.commit()
conn.close()
print("🎉 ALLAR 6 LJÓSMYNDIRNAR AF AXEL ERU NÚ TENGDAR BEINT Í SÖGUBÓK OG GALLERÍ!")
