import sqlite3

conn = sqlite3.connect("ancestry.db", timeout=60.0)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("🧹 HEF AFMAKS- OG TVÍVERKNAÐARHREINSUN (DEDUPLICATION) Á ÖLLUM GAGNATÖFLUM...")

# 1. Deduplicate sources table (keep only unique (person_id, title) or (person_id, image_url))
cursor.execute("""
    DELETE FROM sources
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM sources
        GROUP BY person_id, title
    )
""")
sources_deduped = cursor.rowcount

cursor.execute("""
    DELETE FROM sources
    WHERE image_url IS NOT NULL AND image_url != '' AND id NOT IN (
        SELECT MIN(id)
        FROM sources
        GROUP BY person_id, image_url
    )
""")

# 2. Deduplicate ai_suggestions table (keep only unique (person_id, title, image_url))
cursor.execute("""
    DELETE FROM ai_suggestions
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM ai_suggestions
        GROUP BY person_id, title, local_path
    )
""")
sugs_deduped = cursor.rowcount

# Also deduplicate if same image_url
cursor.execute("""
    DELETE FROM ai_suggestions
    WHERE local_path IS NOT NULL AND local_path != '' AND id NOT IN (
        SELECT MIN(id)
        FROM ai_suggestions
        GROUP BY person_id, local_path
    )
""")

# 3. Deduplicate relations table
cursor.execute("""
    DELETE FROM relations
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM relations
        GROUP BY tree_id, person_id, related_id, relation_type
    )
""")
rels_deduped = cursor.rowcount

conn.commit()

# Athuga stöðuna hjá Axel Bjarkar
axel_srcs = cursor.execute("SELECT id, title, image_url FROM sources WHERE person_id = 'I212565202554'").fetchall()
axel_sugs = cursor.execute("SELECT id, title, local_path FROM ai_suggestions WHERE person_id = 'I212565202554'").fetchall()

print(f"\n✓ Hreinsaði samtals:")
print(f"  - {sources_deduped} tvítekningar úr Heimildum (sources)")
print(f"  - {sugs_deduped} tvítekningar úr Uppástungum/Myndum (ai_suggestions)")
print(f"  - {rels_deduped} tvítekningar úr Fjölskyldutengslum (relations)")

print(f"\n📋 Staðan hjá Axel Bjarkar núna:")
print(f"  - Heimildir ({len(axel_srcs)} einstakar):")
for s in axel_srcs:
    print(f"    • {s['title']}")
print(f"  - Ljósmyndir í galleríi ({len(axel_sugs)} einstakar):")
for su in axel_sugs:
    print(f"    • {su['title']} ({su['local_path']})")

conn.close()
print("\n🎉 ALLAR TVÍTEKNINGAR HAFA VERIÐ HREINSAÐAR ÚR ÖLLUM GAGNATÖFLUNUM!")
