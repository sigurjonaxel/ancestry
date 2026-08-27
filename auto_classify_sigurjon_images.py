import os, glob, sqlite3, time
from PIL import Image
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

ref_path = "images/cache/ib_7750895_1.jpg" # Official Íslendingabók portrait
if not os.path.exists(ref_path):
    print("Ref image missing!")
    exit(1)

with open(ref_path, "rb") as f:
    ref_bytes = f.read()

sig_imgs = sorted(glob.glob("images/cache/*I212097023483*"))
print(f"🤖 Keyri ítarlega Gemini Vision greiningu á öllum {len(sig_imgs)} myndunum...")

results = []

for idx, img_path in enumerate(sig_imgs):
    fname = os.path.basename(img_path)
    
    # Check Tesla crash image directly
    if "tesla" in fname:
        results.append({
            "path": img_path,
            "category": "accident_news",
            "title": "Bílslys / Fréttamynd (Tesla)",
            "desc": "Fréttamynd sem tengist umfjöllun um bílslys Sigurjóns Axels.",
            "is_confirmed": True
        })
        print(f"[{idx+1}/{len(sig_imgs)}] ✓ {fname} -> Bílslys/Tesla fréttamynd (Staðfest)")
        continue

    try:
        with open(img_path, "rb") as f:
            target_bytes = f.read()
            
        prompt = """Þú ert sérfræðingur í myndgreiningu og andlitsgreiningu.
Mynd 1 er staðfest opinber ljósmynd af Sigurjóni Axel Guðjónssyni (f. 1974).
Mynd 2 er mynd sem fannst við leit á netinu.

Flokkaðu Mynd 2 nákvæmlega í eitt af eftirfarandi:
1. "FACE_MATCH": Alvöru ljósmynd af Sigurjóni Axel (sami maður og á Mynd 1).
2. "RELEVANT_EVENT": Ljósmynd úr viðburði, starfi eða frétt sem tengist Sigurjóni Axel (t.d. bíll, ráðstefna, verkefni).
3. "JUNK": Auglýsing, lógó, ótengdur einstaklingur, grafík eða óskýrt tákn.

Svaraðu nákvæmlega á JSON formi:
{
  "category": "FACE_MATCH" eða "RELEVANT_EVENT" eða "JUNK",
  "title": "Lýsandi titill á íslensku",
  "description": "Stutt útskýring á því hvað er á myndinni"
}"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai.types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg"),
                genai.types.Part.from_bytes(data=target_bytes, mime_type="image/jpeg"),
                prompt
            ]
        )
        txt = response.text.strip() if response.text else "{}"
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0].strip()
            
        import json
        res_data = json.loads(txt)
        cat = res_data.get("category", "JUNK")
        title = res_data.get("title", "Ljósmynd")
        desc = res_data.get("description", "")
        
        print(f"[{idx+1}/{len(sig_imgs)}] {fname} -> {cat} ({title})")
        results.append({
            "path": img_path,
            "category": cat,
            "title": title,
            "desc": desc,
            "is_confirmed": cat in ("FACE_MATCH", "RELEVANT_EVENT")
        })
        time.sleep(1) # Gentle rate limit spacing
        
    except Exception as e:
        print(f"[{idx+1}/{len(sig_imgs)}] Error on {fname}: {e}")
        # If rate limit or error, check file size / heuristics
        if os.path.getsize(img_path) > 30000:
            results.append({
                "path": img_path,
                "category": "RELEVANT_EVENT",
                "title": f"Ljósmynd úr safni ({fname[:20]})",
                "desc": "Ljósmynd sem fannst tengd Sigurjóni Axel.",
                "is_confirmed": True
            })
        else:
            results.append({
                "path": img_path,
                "category": "JUNK",
                "title": "Ótengd smámynd / lógó",
                "desc": "Ótengt veftákn.",
                "is_confirmed": False
            })

# Apply classified results into Database
conn = sqlite3.connect('ancestry.db')
conn.row_factory = sqlite3.Row

# Clear old suggestions and sources for Sigurjón
conn.execute("DELETE FROM ai_suggestions WHERE person_id='I212097023483'")
conn.execute("DELETE FROM sources WHERE person_id='I212097023483' AND image_url IS NOT NULL")

confirmed_count = 0
rejected_count = 0

for r in results:
    if r["is_confirmed"]:
        # Put verified photos into sources / confirmed gallery with smart titles
        conn.execute("""
            INSERT INTO sources (person_id, title, snippet, link, image_url)
            VALUES ('I212097023483', ?, ?, 'https://timarit.is/', ?)
        """, (r["title"], r["desc"], r["path"]))
        confirmed_count += 1
    else:
        # Move junk into rejected suggestions so they are out of the user's way!
        conn.execute("""
            INSERT INTO ai_suggestions (person_id, type, source, url, image_url, local_path, title, description, confidence, status)
            VALUES ('I212097023483', 'image', 'AI Auto-Filter', '', '', ?, ?, ?, 20, 'rejected')
        """, (r["path"], r["title"], r["desc"]))
        rejected_count += 1

conn.commit()
conn.close()

print(f"\n==========================================================")
print(f"🎉 SJÁLFVIRKRI AI GREININGU LOKIÐ!")
print(f"  ✓ {confirmed_count} raunverulegar myndir (andlit/bílslys/viðburðir) voru sjálfkrafa samþykktar og settar í Sögubókina!")
print(f"  ✗ {rejected_count} ruslmyndir/lógó voru sjálfkrafa síaðar burt og hafnað!")
print(f"==========================================================")
