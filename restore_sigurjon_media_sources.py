import sqlite3

conn_v1 = sqlite3.connect('ancestry_v1.db')
conn_v1.row_factory = sqlite3.Row

conn_curr = sqlite3.connect('ancestry.db')
conn_curr.row_factory = sqlite3.Row

# Get all real media sources for Sigurjón Axel from V1
srcs_v1 = conn_v1.execute("SELECT * FROM sources WHERE person_id = 'I212097023483' AND (image_url IS NOT NULL AND image_url != '')").fetchall()
print(f"Flyt yfir {len(srcs_v1)} ljósmyndir/heimildir fyrir Sigurjón Axel úr V1...")

for s in srcs_v1:
    conn_curr.execute("""
        INSERT OR IGNORE INTO sources (person_id, title, snippet, link, image_url, favicon)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (s['person_id'], s['title'], s['snippet'], s['link'], s['image_url'], s['favicon']))

# Also check if any suggestions should be preserved
sugs_v1 = conn_v1.execute("SELECT * FROM ai_suggestions WHERE person_id = 'I212097023483'").fetchall()
for sg in sugs_v1:
    conn_curr.execute("""
        INSERT OR IGNORE INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, relation_details, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sg['person_id'], sg['type'], sg['source'], sg['url'], sg['image_url'], sg['local_path'], sg['title'], sg['description'], sg['confidence'], sg['relation_details'], sg['status']))

conn_curr.commit()

# Staðfesta
srcs_new = conn_curr.execute("SELECT * FROM sources WHERE person_id = 'I212097023483'").fetchall()
sugs_new = conn_curr.execute("SELECT * FROM ai_suggestions WHERE person_id = 'I212097023483'").fetchall()
print(f"✓ Sigurjón Axel er núna með {len(srcs_new)} heimildir/myndir og {len(sugs_new)} uppástungur!")

conn_v1.close()
conn_curr.close()
