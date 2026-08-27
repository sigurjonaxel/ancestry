import sqlite3

gist_avatars = [
    ("I212565201805", "images/cache/gist_thorbjorg_sigurjon_brunnhol.jpg", "Sigurjón Einarsson á Brunnhóli"),
    ("I212565201806", "images/cache/gist_thorbjorg_sigurjon_brunnhol.jpg", "Þorbjörg Benediktsdóttir"),
    ("I212565201807", "images/cache/gist_einar_unnur_lambleiksstodum.jpg", "Einar Sigurjónsson (Lambleiksstöðum)"),
    ("I212565201809", "images/cache/gist_benedikt_sigridur.jpg", "Benedikt Sigurjónsson"),
    ("I212565201811", "images/cache/gist_ingunn_karl.jpg", "Ingunn Sigríður Sigurjónsdóttir"),
    ("I212565201813", "images/cache/gist_arnor_ragna.jpg", "Arnór Sigurjónsson (Brunnhóli)"),
    ("I212567429770", "images/cache/gist_adalheidur_gudmundur.jpg", "Aðalheiður Sigurjónsdóttir"),
    ("I212605401062", "images/cache/gist_sigurbjorg_sigurjon.jpg", "Sigurbjörg Sigurjónsdóttir"),
    ("I212565201500", "images/cache/gist_erla_gudjon.jpg", "Erla Þórhildur Sigurjónsdóttir"),
    ("I212565201202", "images/cache/gist_erla_gudjon.jpg", "Guðjón Ingvar Sigurgeirsson")
]

conn = sqlite3.connect("ancestry.db", timeout=30.0)
cursor = conn.cursor()

print("==========================================================================")
print("🖼️ STILLI ÆTTARMÓTSMYNDIR SEM PRÓFÍLMYNDIR FYRIR FORFEÐUR OG SYSTKINI:")
print("==========================================================================")

for pid, img_path, label in gist_avatars:
    cursor.execute("""
        UPDATE people 
        SET avatar_url = ?, avatar_verified = 1 
        WHERE id = ?
    """, (img_path, pid))
    print(f" ✓ [{label}] -> Prófílmynd stillt á: {img_path}")

conn.commit()

# Staðfesting
print("\n=== LOKASTAÐA PRÓFÍLMYNDA ===")
for pid, img_path, label in gist_avatars:
    p = cursor.execute("SELECT name, avatar_url, avatar_verified FROM people WHERE id = ?", (pid,)).fetchone()
    print(f" 👤 {p[0]}: Avatar = {p[1]} (Verified: {p[2]})")

conn.close()
print("\n🎉 ALLAR ÆTTARMÓTSMYNDIR HAFA VERIÐ SETTAR SEM PRÓFÍLMYNDIR!")
