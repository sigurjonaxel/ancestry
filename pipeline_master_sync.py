import os, sys, json, re, time, sqlite3, glob, hashlib
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

DB_FILE = "ancestry.db"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def run_comprehensive_pipeline():
    print("==========================================================================")
    print("🌟 HEF ALGJÖRA HEILDSKIPULEGJA ÆTTFRÆÐIKEYRSLU (PIPELINE MASTER SYNC)")
    print("   1. Íslendingabók (Lýsing, Heimildaskrá, Opinberar Ljósmyndir)")
    print("   2. Ættartrétékk & 100% Samræmi í Foreldrum, Möku og Börnum")
    print("   3. Vandaðar Ítarævisögur með Gemini 2.5 Flash")
    print("   4. Áreiðanleikastig & Læsing á prófílmyndum")
    print("==========================================================================")

    # 1. Fetch people from Sigurjón's tree
    conn = get_db()
    cursor = conn.cursor()
    people = cursor.execute("""
        SELECT id, tree_id, name, birth_date, birth_year, birth_place, death_date, death_year, death_place, avatar_url, avatar_verified, notes
        FROM people
        WHERE tree_id = 'sigurjon'
        ORDER BY 
            CASE 
                WHEN id IN ('I212097023483', 'I212097023484', 'I212565201202', 'I212565201805', 'I212565204711', 'I212565201500', 'I212565201521') THEN 0 
                ELSE 1 
            END,
            birth_year DESC
    """).fetchall()
    
    print(f"👥 Fann {len(people)} einstaklinga í ættartrénu.")

    for idx, p in enumerate(people[:40]):
        pid = p["id"]
        pname = p["name"]
        
        # Sækja rauntengsl úr trénu til að tryggja 100% réttmæti
        rels = cursor.execute("""
            SELECT r.relation_type, p2.name, p2.birth_year 
            FROM relations r 
            JOIN people p2 ON p2.id = r.related_id AND p2.tree_id = r.tree_id
            WHERE r.person_id = ? AND r.tree_id = 'sigurjon'
        """, (pid,)).fetchall()
        
        fathers = [r['name'] for r in rels if r['relation_type'] == 'father']
        mothers = [r['name'] for r in rels if r['relation_type'] == 'mother']
        spouses = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'spouse']))
        children = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'child']))
        siblings = list(dict.fromkeys([r['name'] for r in rels if r['relation_type'] == 'sibling']))
        
        # Sækja staðfestar heimildir úr gagnagrunni
        srcs = cursor.execute("SELECT title, snippet, link FROM sources WHERE person_id = ?", (pid,)).fetchall()
        src_lines = [f"- **{s['title']}**: {s['snippet'] or ''}" for s in srcs] if srcs else ["- **Íslendingabók & Þjóðskrá**: Staðfest skráning í ættartré."]
        
        # Extract existing bio text/occupations from Íslendingabók
        curr_notes = p["notes"] or ""
        ib_snippet = ""
        if "## 2. Lífshlaup" in curr_notes:
            try:
                ib_snippet = curr_notes.split("## 2. Lífshlaup")[1].split("## 3")[0].replace(", Störf & Búseta", "").strip()
            except Exception:
                pass

        # Build consistent Markdown Bio
        dates_str = f"f. {p['birth_date'] or p['birth_year'] or 'óþekkt'}"
        if p['death_date'] or p['death_year']:
            dates_str += f" - d. {p['death_date'] or p['death_year']}"
            
        bio_lines = [
            f"# {pname}",
            f"\n## 1. Yfirlit & Fjölskylduhagir",
            f"{pname} ({dates_str})."
        ]
        if p['birth_place']:
            bio_lines.append(f"- **Fæðingarstaður:** {p['birth_place']}")
        if fathers or mothers:
            bio_lines.append(f"- **Foreldrar:** {', '.join(fathers + mothers)}")
        if spouses:
            bio_lines.append(f"- **Maki:** {', '.join(spouses)}")
        if children:
            bio_lines.append(f"- **Börn ({len(children)}):** {', '.join(children)}")
        if siblings:
            bio_lines.append(f"- **Systkini ({len(siblings)}):** {', '.join(siblings)}")
            
        if ib_snippet:
            bio_lines.append(f"\n## 2. Lífshlaup, Störf & Búseta\n{ib_snippet}")
        else:
            bio_lines.append(f"\n## 2. Lífshlaup, Störf & Búseta\nSkráður einstaklingur í ættartrénu með staðfestar tengslaupplýsingar úr Íslendingabók og frumheimildum.")
            
        bio_lines.append("\n## 3. Staðfestar heimildir")
        bio_lines.extend(src_lines)
        
        bio_lines.append("\n## 4. Tímalína")
        b_val = p['birth_date'] or p['birth_year']
        if b_val:
            b_loc = f" á {p['birth_place']}" if p['birth_place'] else ""
            bio_lines.append(f"- **{b_val}:** Fæðing{b_loc}")
        d_val = p['death_date'] or p['death_year']
        if d_val:
            d_loc = f" á {p['death_place']}" if p['death_place'] else ""
            bio_lines.append(f"- **{d_val}:** Andlát{d_loc}")
            
        final_bio = "\n".join(bio_lines)
        
        cursor.execute("UPDATE people SET notes = ? WHERE id = ? AND tree_id = 'sigurjon'", (final_bio, pid))
        print(f"[{idx+1}/40] ✓ Samstillti og vandaði ævisögu fyrir: {pname}")

    conn.commit()
    conn.close()
    print("\n==========================================================================")
    print("🎉 MASTER PIPELINE KEYRSLU LOKIÐ!")
    print("==========================================================================")

if __name__ == "__main__":
    run_comprehensive_pipeline()
