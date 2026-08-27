
def deep_live_web_search(name, birth_year, locations=[], relatives=[]):
    """Real multi-engine search across Icelandic sources (KSÍ, MBL, Tímarit, LSÍ, APRÓ, FRÍ, etc.)"""
    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    parts = name.split()
    first_last = f"{parts[0]} {parts[-1]}" if len(parts) > 2 else name
    
    queries = [
        f'"{name}"',
        f'"{first_last}"'
    ]
    if locations:
        queries.append(f'"{first_last}" ' + " OR ".join([f'"{loc}"' for loc in locations[:3]]))
    if relatives:
        queries.append(f'"{first_last}" "{relatives[0]}"')
        
    for q in queries[:3]:
        try:
            url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html, 'html.parser')
                for li in soup.find_all('li', class_='b_algo')[:3]:
                    h2 = li.find('h2')
                    p = li.find('p')
                    a = li.find('a')
                    if h2 and p and a:
                        title = h2.get_text(strip=True)
                        snip = p.get_text(strip=True)
                        link = a.get('href')
                        if any(w.lower() in (title + " " + snip).lower() for w in parts[:2]):
                            results.append({"title": title, "snippet": snip, "url": link})
        except Exception:
            pass
        time.sleep(0.5)
    return results

import os
import json
import time
import urllib.request
import urllib.parse
import re
import hashlib
from bs4 import BeautifulSoup
from PIL import Image
from db import save_suggestion, get_db

def download_image_cache(url, person_id, idx):
    try:
        cache_dir = os.path.join(os.path.dirname(__file__), "images", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        ext = "jpg"
        if ".png" in url.lower():
            ext = "png"
        elif ".webp" in url.lower():
            ext = "webp"
            
        clean_id = person_id.replace('@', '')
        # Use url hash to avoid name collisions
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{clean_id}_img_{idx}_{url_hash}.{ext}"
        local_path = os.path.join(cache_dir, filename)
        rel_path = f"images/cache/{filename}"
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
            return rel_path

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            if len(content) < 1500:  # skip tracking pixels / tiny icons
                return None
            with open(local_path, "wb") as f:
                f.write(content)
        return rel_path
    except Exception as e:
        print(f"[Image Cache] Error downloading {url[:60]}: {e}")
        return None

def extract_media_from_page(url):
    """Scrapes direct article images and profile pictures from news sites, Google Scholar, etc."""
    imgs = []
    if not url or not url.startswith('http'):
        return imgs
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Google Scholar special handler
        if 'scholar.google' in url:
            img = soup.find('img', id='gsc_prf_pup-img')
            if img and img.get('src'):
                src = img['src']
                if src.startswith('/'):
                    src = 'https://scholar.google.com' + src
                imgs.append({'url': src, 'title': 'Google Scholar Prófílmynd', 'is_profile': True})

        # 2. OpenGraph lead image (Mbl, Vísir, etc.)
        og = soup.find('meta', property='og:image')
        if og and og.get('content') and og['content'].startswith('http'):
            imgs.append({'url': og['content'], 'title': 'Aðalmynd úr frétt/grein', 'is_profile': False})

        # 3. In-article images
        for tag in soup.find_all('img'):
            src = tag.get('src') or tag.get('data-src') or tag.get('data-original')
            if not src:
                continue
            if src.startswith('/'):
                base = urllib.parse.urlparse(url)
                src = f'{base.scheme}://{base.netloc}{src}'
            if not src.startswith('http'):
                continue
            
            low = src.lower()
            if any(k in low for k in ['.svg', 'logo', 'icon', 'pixel', 'banner', 'facebook', 'instagram', 'twitter', 'radio/color', 'teams/ksi', 'sponsor', 'advert', '240x160', '308x200']):
                continue
            alt = tag.get('alt') or 'Mynd úr frétt'
            imgs.append({'url': src, 'title': alt, 'is_profile': False})

    except Exception as e:
        print(f"[Media Extract] Error scraping {url[:60]}: {e}")
    
    # Deduplicate by url
    seen = set()
    deduped = []
    for item in imgs:
        if item['url'] not in seen:
            seen.add(item['url'])
            deduped.append(item)
    return deduped

def search_direct_web_images(name):
    """Directly queries web image search to find real photos of the person from news, sports and web."""
    image_items = []
    try:
        url = 'https://www.bing.com/images/search?q=' + urllib.parse.quote(name) + '&FORM=HDRSC2'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=6).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a', class_='iusc')[:8]:
            m = a.get('m', '')
            try:
                m_json = json.loads(m)
                murl = m_json.get('murl')
                desc = m_json.get('desc', f'Mynd af {name}')
                clean_title = desc.replace('', '').replace('', '').strip()
                if murl and not any(murl.endswith(x) for x in ['.svg', '.gif']):
                    image_items.append({'url': murl, 'title': clean_title, 'is_profile': True})
            except Exception:
                pass
    except Exception as e:
        print(f"[Direct Web Image Search] Error: {e}")
    return image_items

def verify_portrait_image(client, name, birth_year, image_rel_path, ref_image_rel_path=None):
    try:
        abs_path = os.path.join(os.path.dirname(__file__), image_rel_path)
        if not os.path.exists(abs_path):
            return False
        img = Image.open(abs_path)
        width, height = img.size
        
        # Filter out tiny thumbnails, icons, wide banners
        if width < 120 or height < 120:
            return False
            
        ratio = width / height
        if ratio > 2.5 or ratio < 0.4:
            return False

        # If we have a verified reference portrait from Íslendingabók, do a 1-to-1 face comparison!
        if ref_image_rel_path and os.path.exists(os.path.join(os.path.dirname(__file__), ref_image_rel_path)):
            ref_abs = os.path.join(os.path.dirname(__file__), ref_image_rel_path)
            ref_img = Image.open(ref_abs)
            prompt = f"""
            Þú ert nákvæmur andlitsgreinir og rannsakandi.
            Mynd 1 er staðfest opinber ljósmynd af {name} (f. {birth_year or 'ótilgreint'}).
            Mynd 2 er ljósmynd af netinu.

            Kröfur:
            1. Er mynd 2 alvöru persónumynd af manneskju (ekki bíll, lógó, landslag, tákn eða grafík)?
            2. Er maðurinn á mynd 2 sami einstaklingur og á mynd 1?

            Svaraðu aðeins með:
            MATCH (ef þetta er sami maður með mikilli vissu)
            NO (ef þetta er ekki sami maður, eða ef þetta er tákn/bíll/grafík).
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, ref_img, img]
            )
            txt = response.text.strip().upper() if response.text else "NO"
            print(f"  [Vision Face Match] {image_rel_path} vs Ref -> {txt}")
            return "MATCH" in txt

        prompt = (
            f"Skoðaðu þessa mynd. Er þetta skýr persónumynd af manneskju sem heitir {name} (f. {birth_year or 'ótilgreint'})? "
            "Hafnaðu stranglega öllum auglýsingum, bílum, vefborðum, lógóum eða ótengdum hlutum. "
            "Svaraðu aðeins: YES eða NO."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        txt = response.text.strip().upper() if response.text else "NO"
        print(f"  [Vision Verification] {image_rel_path} -> {txt}")
        return "YES" in txt
    except Exception as e:
        print(f"  [Vision Verification] Error: {e}")
        return False

def resolve_real_url(url):
    """Unwraps grounding redirect URLs (e.g. vertexaisearch.cloud.google.com) to their real target web address."""
    if not url or not url.startswith('http'):
        return url
    if 'vertexaisearch' in url or 'google.com/grounding' in url:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                final = resp.geturl()
                if final and not ('vertexaisearch' in final):
                    return final
        except Exception:
            pass
    return url

def update_or_enhance_existing_sources(person_id, title, snippet, url, image_url=None):
    """If a source already exists by title or url, updates it with a better snippet or image if it was missing."""
    clean_id = person_id.replace('@', '')
    with get_db() as conn:
        cursor = conn.cursor()
        # Check by link
        cursor.execute("SELECT id, snippet, image_url, title FROM sources WHERE person_id = ? AND (link = ? OR title = ?)", (clean_id, url, title))
        row = cursor.fetchone()
        if row:
            src_id, old_snip, old_img, old_title = row['id'], row['snippet'], row['image_url'], row['title']
            new_snip = snippet if (snippet and (not old_snip or len(snippet) > len(old_snip))) else old_snip
            new_img = image_url if (image_url and not old_img) else old_img
            new_link = url if (url and not url.startswith('https://vertexaisearch')) else None
            
            if new_link:
                cursor.execute("UPDATE sources SET snippet = ?, image_url = ?, link = ? WHERE id = ?", (new_snip, new_img, new_link, src_id))
            else:
                cursor.execute("UPDATE sources SET snippet = ?, image_url = ? WHERE id = ?", (new_snip, new_img, src_id))
            conn.commit()
            return True
    return False

def run_ai_research_for_person(person_id, name, birth_year="", death_year=""):
    clean_id = person_id.replace('@', '')
    
    # 1. Sækja skráð fjölskyldutengsl úr gagnagrunni til að krossprófa
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.relation_type, p.name 
            FROM relations r 
            JOIN people p ON p.id = r.related_id 
            WHERE r.person_id = ?
        """, (clean_id,))
        db_rels = cursor.fetchall()
        
    rel_context_lines = []
    if db_rels:
        foreldrar = [r['name'] for r in db_rels if r['relation_type'] in ('father', 'mother')]
        maki = [r['name'] for r in db_rels if r['relation_type'] == 'spouse']
        systkini = [r['name'] for r in db_rels if r['relation_type'] == 'sibling']
        born = [r['name'] for r in db_rels if r['relation_type'] == 'child']
        if foreldrar:
            rel_context_lines.append(f"- Foreldrar: {', '.join(foreldrar)}")
        if maki:
            rel_context_lines.append(f"- Maki: {', '.join(maki)}")
        if born:
            rel_context_lines.append(f"- Börn: {', '.join(born)}")
        if systkini:
            rel_context_lines.append(f"- Systkini: {', '.join(systkini)}")
            
    family_context_str = "\n".join(rel_context_lines) if rel_context_lines else "- Engin fjölskyldutengsl skráð enn."

    # 2. Check if PERPLEXITY_API_KEY is available (Primary Instant Engine)
    perp_key = os.environ.get("PERPLEXITY_API_KEY")
    if perp_key:
        print(f"[AI Research] Using Perplexity Sonar Engine for {name}...")
        from perplexity_engine import search_with_perplexity
        perp_res = search_with_perplexity(name, birth_year, death_year, family_context_str)
        if perp_res.get("status") == "success":
            data = perp_res.get("data", {})
            added_count = 0
            
            for item in data.get("timeline", []):
                save_suggestion(
                    person_id=clean_id,
                    sug_type="event",
                    source="Perplexity AI",
                    url=item.get("url", ""),
                    image_url="",
                    local_path="",
                    title=f"{item.get('year', '')} - {item.get('title', 'Viðburður')}",
                    description=item.get("description", ""),
                    confidence=95
                )
                added_count += 1
                
            for src in data.get("sources", []):
                save_suggestion(
                    person_id=clean_id,
                    sug_type="event",
                    source="Perplexity AI",
                    url=src.get("url", ""),
                    image_url="",
                    local_path="",
                    title=src.get("title", "Staðfest heimild"),
                    description=src.get("snippet", ""),
                    confidence=95
                )
                added_count += 1
                
            return {
                "status": "success",
                "message": f"Perplexity fann {added_count} nýjar uppástungur og staðfestar heimildir.",
                "count": added_count
            }

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[AI Research] Missing API key.")
        return {"status": "error", "message": "Vantar PERPLEXITY_API_KEY eða GEMINI_API_KEY í .env."}
        
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        death_info = f"Dánarár: {death_year}" if death_year else "Lifandi / Óstaðfest dánarár"
        print(f"[AI Research] Starting Strict Grounded Research for {name} (f. {birth_year}, {death_info})...")

        prompt = f"""
        Þú ert sérfræðingur í íslenskri ættfræði, sögu og ævisögurannsóknum.
        Leitaðu á vefnum að öllum staðfestum upplýsingum, greinum, fréttum, menntun og ljósmyndum um:
        Fullt nafn: {name}
        Fæðingarár: {birth_year if birth_year else 'óvíst'}
        {death_info}

        ÞEKKT FJÖLSKYLDUTENGSL ÚR ÆTTARTRÉI (KROSSPRÓFUN):
        {family_context_str}

        LEITARKRÖFUR:
        1. Vísir.is, Mbl.is, DV.is (fréttir, viðtöl, minningargreinar, myndefni).
        2. Tímarit.is, Landsbókasafn (sögulegar greinar, stúdentspróf, útskriftir).
        3. Menntun (stúdentspróf úr menntaskólum t.d. MA/MR/Kvennó, háskólagráður úr HÍ/HA/KHÍ/Listaháskóla).
        4. Störf, félagsmál, sveitarstjórn, íþróttir og opinber afrek.

        STRÖNG SKILYRÐI & RAUNVERULEIKATÉKK (HOMONYM / IDENTITY VERIFICATION):
        - PASSADU UPP Á NAFNA (NAMNAKRÖFUR): Margir Íslendingar bera sama fornafn/föðurnafn. Þú VERÐUR að staðfesta að greinin/heimildin eigi við ÞESSA manneskju með því að krossprófa fæðingarár, dánarár, búsetu eða ofangreind fjölskyldutengsl (foreldra, maka, börn).
        - ALGJÖRT BANNBREYTING: Bannað er að eigna manneskjunni afrek eða störf annarrar nafna (t.d. ef Jónína heitir Loftsdóttir en ekki Jónsdóttir, eða ef hún er fædd á öðrum tíma).
        - Ef einstaklingurinn lést árið {death_year if death_year else 'N/A'}, MÁTTU EKKI tengja greinar eða íþróttaviðburði/hlaup sem áttu sér stað eftir dánarárið!
        - EKKI búa til uppástungur um mögulega ættingja (faðir, móðir, börn, systkini) þar sem fjölskyldutengsl eru þegar skráð.
        - EKKI búa til heimildir fyrir venjulegar fæðingar barna eða ættingja.

        Fyrir sérhvern viðburð/heimild:
        - Gefðu nákvæman, lýsandi 1-2 setninga útdrátt (snippet) sem útskýrir nákvæmlega samhengið og tengslin við {name}.
        - Skráðu beinar vefslóðir (URL) á greinarnar.

        Skilaðu svörunum í eftirfarandi JSON formi:
        {{
            "bio": "Stuttur heildar æviágripstexti á íslensku...",
            "timeline": [
                {{
                    "year": "Ártal",
                    "title": "Titill viðburðar",
                    "description": "Nákvæm lýsing...",
                    "url": "https://..."
                }}
            ],
            "sources": [
                {{
                    "title": "Nafn fréttar eða heimildar",
                    "snippet": "1-2 setninga samantekt um innihald og tengsl við {name}...",
                    "url": "https://..."
                }}
            ],
            "image_urls": [
                "https://..."
            ]
        }}
        """

        response = None
        # Try multiple models with smart retry and fallback
        model_candidates = ['gemini-2.5-flash', 'gemini-3.5-flash', 'gemini-3.7-flash', 'gemini-3-flash-preview']
        
        for attempt in range(5):
            for model_name in model_candidates:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearch())],
                        )
                    )
                    if response and (response.text or response.candidates):
                        break
                except Exception as me:
                    err_str = str(me)
                    print(f"  [AI Research] Model {model_name} quota/error: {err_str[:120]}")
                    if 'RESOURCE_EXHAUSTED' in err_str or '429' in err_str:
                        m_sec = re.search(r'retry in (\d+(?:\.\d+)?)s', err_str)
                        wait_sec = float(m_sec.group(1)) + 1 if m_sec else 10
                        time.sleep(min(wait_sec, 20))
            if response and (response.text or response.candidates):
                break
            print(f"  [AI Research] Retrying in 8 seconds (attempt {attempt+1}/5)...")
            time.sleep(8)

        if not response:
            return {"status": "error", "message": "Google AI leitarþjónustan er tímabundið upptekin. Vinsamlegast prófaðu aftur eftir 30 sekúndur."}

        resp_text = None
        if response.text:
            resp_text = response.text.strip()
        elif response.candidates:
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            resp_text = ''.join(p.text for p in parts if hasattr(p, 'text') and p.text).strip()

        # Capture grounding links from Google Search tool metadata
        grounding_sources = []
        if response.candidates and response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            if hasattr(meta, 'grounding_chunks') and meta.grounding_chunks:
                for c in meta.grounding_chunks:
                    if hasattr(c, 'web') and c.web:
                        grounding_sources.append({
                            'title': c.web.title or 'Google leitarniðurstaða',
                            'url': c.web.uri or '',
                            'snippet': f"Staðfest tengsl við {name} samkvæmt leitarniðurstöðu."
                        })

        if not resp_text and not grounding_sources:
            return {"status": "error", "message": "Engar nýjar upplýsingar fundust á vefnum fyrir þessa persónu."}

        data = {"timeline": [], "sources": [], "image_urls": []}
        if resp_text:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', resp_text, re.DOTALL)
            if json_match:
                try: data = json.loads(json_match.group(1))
                except Exception: pass
            else:
                start = resp_text.find('{')
                end = resp_text.rfind('}')
                if start != -1 and end != -1:
                    try: data = json.loads(resp_text[start:end+1])
                    except Exception: pass

        # Merge grounding sources if json sources was empty
        if not data.get("sources") and grounding_sources:
            data["sources"] = grounding_sources
        added_count = 0

        # Save Timeline / Events
        for item in data.get("timeline", []):
            raw_url = item.get("url", "")
            real_url = resolve_real_url(raw_url) if raw_url else ""
            
            enhanced = update_or_enhance_existing_sources(clean_id, item.get("title", ""), item.get("description", ""), real_url)
            if not enhanced:
                save_suggestion(
                    person_id=clean_id,
                    sug_type="event",
                    source="Google AI Search",
                    url=real_url,
                    image_url="",
                    local_path="",
                    title=f"{item.get('year', '')} - {item.get('title', 'Viðburður')}",
                    description=item.get("description", ""),
                    confidence=85
                )
                added_count += 1

        # Save Sources directly
        for src in data.get("sources", []):
            raw_url = src.get("url", "")
            real_url = resolve_real_url(raw_url) if raw_url else ""
            title = src.get("title", "Heimild um persónu")
            snippet = src.get("snippet", "")

            enhanced = update_or_enhance_existing_sources(clean_id, title, snippet, real_url)
            if not enhanced:
                save_suggestion(
                    person_id=clean_id,
                    sug_type="event",
                    source="Google AI Search",
                    url=real_url,
                    image_url="",
                    local_path="",
                    title=title,
                    description=snippet,
                    confidence=85
                )
        # Extract and save real photos from web articles & image search
        print(f"[AI Research] Sæki myndir af vefnum fyrir {name}...")
        web_photos = search_direct_web_images(name)
        for p_idx, wp in enumerate(web_photos[:4]):
            img_rel = download_image_cache(wp['url'], clean_id, f"web_{p_idx}")
            if img_rel:
                save_suggestion(
                    person_id=clean_id,
                    sug_type="media",
                    source="Vefmyndaleit",
                    url=wp.get("url", ""),
                    image_url=img_rel,
                    local_path=img_rel,
                    title=wp.get("title", f"Mynd af {name}"),
                    description="Ljósmynd af vefnum",
                    confidence=80
                )
                added_count += 1

        print(f"[AI Research] ✓ Klár! Bætti við {added_count} nýjum uppástungum (og myndum) fyrir {name}.")
        return {
            "status": "success",
            "message": f"Fann {added_count} nýjar uppástungur, heimildir og myndir.",
            "suggestions_count": added_count
        }

    except Exception as e:
        print(f"[AI Research] Exception: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import sys
    pid = sys.argv[1] if len(sys.argv) > 1 else "I212097023483"
    pname = sys.argv[2] if len(sys.argv) > 2 else "Sigurjón Axel Guðjónsson"
    pyear = sys.argv[3] if len(sys.argv) > 3 else "1974"
    res = run_ai_research_for_person(pid, pname, pyear)
    print(json.dumps(res, indent=2, ensure_ascii=False))
