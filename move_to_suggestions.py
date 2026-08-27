import glob, os, sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Clear old suggestions for Sigurjón
conn.execute("DELETE FROM ai_suggestions WHERE person_id='I212097023483'")

# Add local cached photos as UNCONFIRMED SUGGESTIONS only (type='image', status='pending')
sig_imgs = sorted(glob.glob('images/cache/*I212097023483*'))

count = 0
for img_path in sig_imgs:
    filename = os.path.basename(img_path)
    conn.execute("""
        INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
        VALUES ('I212097023483', 'image', 'Vefgrein / Google leit', '', '', ?, 
                'Óstaðfest myndatillaga af netinu', 'Mynd sem fannst við leit á netinu. Smelltu á Staðfesta & Vista ef hún er rétt, eða Hafna ef hún er röng.', 60, 'pending')
    """, (img_path,))
    count += 1

conn.commit()
print(f"Færði allar {count} myndirnar yfir í 'Óstaðfestar uppástungur' (Pending suggestions)!")
conn.close()
