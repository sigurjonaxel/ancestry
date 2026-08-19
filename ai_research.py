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

def verify_portrait_image(client, name, birth_year, image_rel_path):
    try:
        abs_path = os.path.join(os.path.dirname(__file__), image_rel_path)
        img = Image.open(abs_path)
        width, height = img.size
        
        if width < 50 or height < 50:
            return False
            
        ratio = width / height
        if ratio > 3.5 or ratio < 0.2:
            return False
            
        prompt = (
            f"Skoðaðu þessa mynd. Er þetta persónumynd af manneskju (t.d. {name}) eða ljósmynd úr frétt/viðburði sem tengist manneskjunni? "
            "Hafnaðu auglýsingum, vefborðum, óskýrum táknum eða lógóum. "
            "Svaraðu aðeins með einu orði: YES eða NO."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        txt = response.text.strip().upper() if response.text else "YES"
        print(f"  [Vision Verification] {image_rel_path} -> {txt}")
        return "YES" in txt
    except Exception as e:
        print(f"  [Vision Verification] Error: {e}")
        return True

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
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("[AI Research] Missing GEMINI_API_KEY.")
        return {"status": "error", "message": "Vantar GEMINI_API_KEY í stillingar."}
        
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

        LEITARKRÖFUR:
        1. Vísir.is, Mbl.is, DV.is (fréttir, viðtöl, minningargreinar, myndefni).
        2. Tímarit.is, Landsbókasafn (sögulegar greinar, stúdentspróf, útskriftir).
        3. Menntun (stúdentspróf úr menntaskólum t.d. MA/MR/Kvennó, háskólagráður úr HÍ/HA/KHÍ).
        4. Störf, félagsmál, sveitarstjórn, íþróttir og opinber afrek.

        STRÖNG SKILYRÐI:
        - Allar heimildir og ljósmyndir VERÐA að eiga við réttan einstakling ({name}).
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
        for attempt in range(3):
            for model_name in ['gemini-3.5-flash', 'gemini-3.7-flash', 'gemini-2.5-flash', 'gemini-3-flash-preview']:
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
                    print(f"  [AI Research] Model {model_name} quota/error: {me}")
                    if 'RESOURCE_EXHAUSTED' in str(me) or '429' in str(me):
                        time.sleep(5)
            if response and (response.text or response.candidates):
                break
            print(f"  [AI Research] Retrying in 8 seconds (attempt {attempt+1}/3)...")
            time.sleep(8)

        if not response:
            return {"status": "error", "message": "Allir Gemini módelkandidatar uppteknir."}

        resp_text = None
        if response.text:
            resp_text = response.text.strip()
        elif response.candidates:
            parts = response.candidates[0].content.parts if response.candidates[0].content else []
            resp_text = ''.join(p.text for p in parts if hasattr(p, 'text') and p.text).strip()

        if not resp_text:
            print("[AI Research] Empty response from model.")
            return {"status": "error", "message": "Tómt svar frá Gemini."}

        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', resp_text, re.DOTALL)
        if json_match:
            resp_text = json_match.group(1)
        else:
            start = resp_text.find('{')
            end = resp_text.rfind('}')
            if start != -1 and end != -1:
                resp_text = resp_text[start:end+1]

        data = json.loads(resp_text)
        added_count = 0

        # Save Timeline / Events
        for item in data.get("timeline", []):
            raw_url = item.get("url", "")
            real_url = resolve_real_url(raw_url) if raw_url else ""
            
            # Check if source exists to enhance it
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

        # Save Family Relations
        for rel in data.get("relations", []):
            save_suggestion(
                person_id=clean_id,
                sug_type="relation",
                source="Google AI Search",
                url="",
                image_url="",
                local_path="",
                title=f"Mögulegur {rel.get('type')}: {rel.get('name')}",
                description=f"AI fann tengsl við {rel.get('name')} sem {rel.get('type')}.",
                confidence=80,
                relation_details={
                    "name": rel.get("name"),
                    "type": rel.get("type"),
                    "sex": rel.get("sex", "M")
                }
            )
            added_count += 1

        # Collect images from discovered articles & direct web image search
        discovered_image_items = []
        for u in data.get("image_urls", []):
            discovered_image_items.append({'url': u, 'title': f'Mynd tengd {name}', 'is_profile': False})

        # Add direct web image search results
        direct_web_imgs = search_direct_web_images(name)
        discovered_image_items.extend(direct_web_imgs)

        # Save Sources & Scrape Images
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
                added_count += 1

            if real_url and 'http' in real_url:
                page_imgs = extract_media_from_page(real_url)
                discovered_image_items.extend(page_imgs)

        # Download & Verify Discovered Images
        img_idx = 1
        seen_img_urls = set()
        for img_item in discovered_image_items[:15]:
            img_url = img_item['url']
            if img_url in seen_img_urls:
                continue
            seen_img_urls.add(img_url)

            rel_path = download_image_cache(img_url, clean_id, img_idx)
            if rel_path:
                is_valid = verify_portrait_image(client, name, birth_year, rel_path)
                if is_valid:
                    title_text = "Prófílmynd" if img_item.get('is_profile') else f"Mynd úr grein: {img_item.get('title', name)}"
                    save_suggestion(
                        person_id=clean_id,
                        sug_type="image",
                        source="Vefgrein / Google AI",
                        url=img_url,
                        image_url=img_url,
                        local_path=rel_path,
                        title=title_text,
                        description=f"Mynd sótt úr heimild sem tengist {name}.",
                        confidence=90
                    )
                    added_count += 1
                    img_idx += 1

        print(f"[AI Research] Completed! Processed research for {name}.")
        return {"status": "success", "added": added_count, "data": data}

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
