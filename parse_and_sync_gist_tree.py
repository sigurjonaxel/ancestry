import re, sqlite3, os

GIST_PATH = "/home/sigurjonaxel/.gemini/antigravity-cli/brain/2ade16f4-7796-473f-b4fd-e73bf3c0ded8/.system_generated/steps/8060/content.md"

with open(GIST_PATH, "r", encoding="utf-8") as f:
    text = f.read()

conn = sqlite3.connect("ancestry.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("==========================================================================")
print("🌳 LES ÚR ÆTTARMÓTI 2024 (AFKOMENDUR ÞORBJARGAR & SIGURJÓNS Á BRUNNHÓLI):")
print("==========================================================================")

# Update Key Ancestors
# Sigurjón Einarsson (f. 17.10.1895 - d. 28.02.1983)
cursor.execute("""
    UPDATE people SET 
        birth_date = '17. október 1895', birth_year = '1895', birth_place = 'Oddi á Mýrum',
        death_date = '28. febrúar 1983', death_year = '1983', death_place = 'Höfn / Brunnhóll'
    WHERE id = 'I212565201805'
""")

# Þorbjörg Benediktsdóttir (f. 04.08.1898 - d. 27.02.1992)
cursor.execute("""
    UPDATE people SET 
        birth_date = '04. ágúst 1898', birth_year = '1898', birth_place = 'Einholt á Mýrum',
        death_date = '27. febrúar 1992', death_year = '1992', death_place = 'Höfn / Brunnhóll'
    WHERE id = 'I212565201806'
""")

# Parse all lines with name & dates
# Example: **1.1.1. Einar Hjalti Steinþórsson** (f. 26.04.1969)
# Example: * Maki: Sigríður Lucia Þórarinsdóttir (f. 09.07.1971)
lines = text.split("\n")
updated_count = 0

for line in lines:
    m = re.search(r"\*{0,2}(?:(?:\d+\.)+\s*)?([A-ZÁÐÉÍÓÚÝÞÆÖ][a-záðéíóúýþæöA-ZÁÐÉÍÓÚÝÞÆÖ\s]+?)\*{0,2}\s*\(\s*f\.\s*(\d{2}\.\d{2}\.\d{4})(?:\s*[-–]\s*d\.\s*(\d{2}\.\d{2}\.\d{4}))?\s*\)", line)
    if m:
        name = m.group(1).strip()
        # Clean title words like "Maki:" or "Barnsfaðir:"
        name = re.sub(r"^(?:Maki\s*\d*:|Barnsfaðir:|Barnsmóðir:)\s*", "", name).strip()
        b_date = m.group(2).strip()
        b_year = b_date.split(".")[-1]
        d_date = m.group(3).strip() if m.group(3) else None
        d_year = d_date.split(".")[-1] if d_date else None
        
        # Check if person exists in DB
        p = cursor.execute("SELECT id, name FROM people WHERE tree_id = 'sigurjon' AND name = ?", (name,)).fetchone()
        if p:
            if d_date:
                cursor.execute("UPDATE people SET birth_date = ?, birth_year = ?, death_date = ?, death_year = ? WHERE id = ?", (b_date, b_year, d_date, d_year, p['id']))
            else:
                cursor.execute("UPDATE people SET birth_date = ?, birth_year = ? WHERE id = ?", (b_date, b_year, p['id']))
            updated_count += 1
            print(f" ✓ Uppfærði dagsetningar fyrir: {name} (f. {b_date}{' - d. ' + d_date if d_date else ''})")

conn.commit()
print(f"\n🎉 Samtals uppfærði {updated_count} einstaklinga nákvæmlega samkvæmt Gist skránni!")
conn.close()
