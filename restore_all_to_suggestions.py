import glob, os, sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# 1. Clear any artificial sources for Sigurjón
conn.execute("DELETE FROM sources WHERE person_id='I212097023483' AND (title LIKE 'Fréttamynd%' OR title LIKE 'Mynd úr%' OR title LIKE 'Viðburðamynd%')")

# 2. Find EVERY SINGLE image file on disk for Sigurjón
all_files = sorted(glob.glob('images/cache/*I212097023483*'))
print(f"Fann {len(all_files)} upprunalegar myndir á diski!")

# 3. Clear old suggestions and put ALL of them into ai_suggestions so the user can easily see, confirm, or delete every single one
conn.execute("DELETE FROM ai_suggestions WHERE person_id='I212097023483'")

idx = 1
for img_path in all_files:
    fname = os.path.basename(img_path)
    title = f"Mynd {idx}: {fname}"
    conn.execute("""
        INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
        VALUES ('I212097023483', 'image', 'Sótt af netinu / Vefgrein', '', '', ?, ?, 'Smelltu á „Staðfesta & Vista“ til að vista eða „Hafna“ til að henda.', 75, 'pending')
    """, (img_path, title))
    idx += 1

conn.commit()
print(f"🎉 Allar {idx-1} myndirnar eru nú komnar í 'Uppástungur af vefnum' þar sem þú hefur 100% stjórn á að vista eða henda hverri einustu!")
conn.close()
