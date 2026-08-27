import glob, os, sqlite3

conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# All local photos of Sigurjón Axel
sig_imgs = sorted(glob.glob('images/cache/*I212097023483*'))

print(f"Fann {len(sig_imgs)} ljósmyndir á diski fyrir Sigurjón Axel!")

# Register each photo as a source/photo in the gallery
idx = 1
for img_path in sig_imgs:
    filename = os.path.basename(img_path)
    title = f"Ljósmynd {idx}: Sigurjón Axel"
    snippet = f"Ljósmynd úr safni ({filename})"
    conn.execute("""
        INSERT INTO sources (person_id, title, snippet, link, image_url)
        VALUES ('I212097023483', ?, ?, ?, ?)
    """, (title, snippet, "", img_path))
    idx += 1

conn.commit()
print(f"🎉 Tengdi {idx-1} ljósmyndir beint í Sögubók & Ljósmyndasafn Sigurjóns!")
conn.close()
