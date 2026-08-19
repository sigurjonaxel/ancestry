import json
import os
import argparse
import unicodedata
import time
import urllib.request
import urllib.parse
import re
from dotenv import load_dotenv

load_dotenv()

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        print("Vinsamlegast keyrðu: pip install ddgs")
        exit(1)

SUGGESTIONS_FILE = "suggestions.json"
IMAGE_CACHE_DIR = "images/cache"

def load_suggestions():
    if os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_suggestions(data):
    with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def remove_icelandic_chars(text):
    text = text.replace('ð', 'd').replace('Ð', 'D').replace('þ', 'th').replace('Þ', 'Th').replace('æ', 'ae').replace('Æ', 'Ae').replace('ö', 'o').replace('Ö', 'O')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_generation_search_strategies(name, birth_year_str):
    strategies = []
    try:
        birth_year = int(birth_year_str) if birth_year_str else None
    except ValueError:
        birth_year = None

    # Remove quotes so engines don't break or ignore Icelandic middle names
    queries = [name]
    
    for q in queries:
        strategies.append({"source": "Almenn vefleit", "query": q})
        if birth_year is None:
            pass # Keep it fast
        elif birth_year < 1960:
            strategies.append({"source": "Minningargreinar", "query": f"{q} minningargrein OR site:mbl.is/greinasafn"})
        else:
            strategies.append({"source": "Samfélag & Fréttir", "query": f"{q} (facebook OR linkedin OR visir.is OR mbl.is OR transfermarkt)"})
            strategies.append({"source": "Fréttir & Slys", "query": f"{q} tesla slys"})

    return strategies

def search_images_via_google_api(name, birth_year_str, max_images=8):
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CSE_CX")
    if not api_key or not cx:
        print("  [Google Search API] GOOGLE_API_KEY eða GOOGLE_CSE_CX vantar í .env (sleppir Google leit).")
        return None

    try:
        import socket
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(6)
        from googleapiclient.discovery import build
        service = build("customsearch", "v1", developerKey=api_key)
        
        # Build query
        query = f'"{name}"'
        try:
            birth_year = int(birth_year_str) if birth_year_str else 1950
        except ValueError:
            birth_year = 1950
            
        if birth_year >= 1960:
            query += " portrait"
            
        print(f"-> Leita að myndum á Google Search API: {query}")
        
        res = service.cse().list(
            q=query,
            cx=cx,
            searchType="image",
            num=min(max_images, 10)
        ).execute()
        
        results = []
        if "items" in res:
            for item in res["items"]:
                results.append({
                    "image": item.get("link"),
                    "url": item.get("image", {}).get("contextLink", item.get("link")),
                    "title": item.get("title", "Mynd")
                })
        print(f"  [Google Search API] Fundust {len(results)} myndir.")
    except Exception as e:
        err_str = str(e)
        if "403" in err_str or "not have the access to Custom Search JSON API" in err_str:
            print("  [Google Search API] Custom Search JSON API er ekki virkjað á þessu verkefni — skipti sjálfkrafa yfir í ókeypis leitarvélar (Bing / Raw Google).")
        else:
            print(f"  [Google Search API] Villa kom upp við fyrirspurn: {e}")
        return None
    finally:
        try:
            socket.setdefaulttimeout(old_timeout)
        except Exception:
            pass

def search_images_via_raw_google(name, birth_year_str, max_images=8):
    import urllib.request
    import urllib.parse
    import re
    from bs4 import BeautifulSoup
    
    url = 'https://www.google.com/search?q=' + urllib.parse.quote(name) + '&tbm=isch'
    headers = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'
    }
    
    found_images = []
    print("  Sækir myndir gegnum raw Google Image Search...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')
        
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/imgres?imgurl=' in href:
                params = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                imgurl = params.get('imgurl')
                if imgurl:
                    img_data = {
                        "image": imgurl[0],
                        "url": "https://www.google.com",
                        "title": f"Mynd af {name} (frá Google)"
                    }
                    found_images.append(img_data)
                    if len(found_images) >= max_images:
                        break
    except Exception as e:
        print(f"  [Raw Google Image Search] Villa: {e}")
        
    return found_images

def search_images_via_bing(name, birth_year_str, max_images=8):
    """Use Bing Image Search directly via urllib to bypass blocks and captchas."""
    import urllib.request
    import urllib.parse
    from bs4 import BeautifulSoup
    
    print(f"  [Bing Search] Sækir myndir fyrir {name}...")
    try:
        # Hreinsa nafnið ef það inniheldur "OR" og gæsalappir
        clean_name = name.split(" OR ")[0].replace('"', '').strip()
        url = 'https://www.bing.com/images/search?q=' + urllib.parse.quote(clean_name)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        seen = set()
        
        # Bing image results store full image URLs in a JSON string inside the 'm' attribute of 'a.iusc' tags
        for a_tag in soup.find_all('a', class_='iusc'):
            if len(results) >= max_images:
                break
            m_attr = a_tag.get('m')
            if m_attr:
                try:
                    import json
                    m_data = json.loads(m_attr)
                    murl = m_data.get('murl')
                    purl = m_data.get('purl', murl)
                    title = m_data.get('t', name)
                    if murl and murl.startswith('http') and murl not in seen:
                        seen.add(murl)
                        results.append({
                            "url": purl,
                            "image": murl,
                            "title": title,
                            "source": "Bing Myndaleit (Almenn leit)",
                            "trusted": False
                        })
                except Exception:
                    pass
        print(f"  [Bing Search] Fann {len(results)} myndir.")
        return results
    except Exception as e:
        print(f"  [Bing Search] Villa: {e}")
        return None




def search_images_for_person(name, birth_year_str, max_images=15):
    """Search Bing, Google, and DuckDuckGo Images for photos of this person."""
    all_results = []
    
    # Sources that almost never have portrait photos of individuals
    SKIP_IMAGE_DOMAINS = [
        'youtube.com', 'youtu.be', 'vimeo.com', 'ytimg.com',
        'wikipedia.org', 'wikimedia.org', 'wikidata.org',
        'gstatic.com', 'google.com', 'bing.com',
        'squarespace.com',  # Often company logos
    ]
    
    # Known bad keyword patterns in image titles
    SKIP_TITLE_KEYWORDS = [
        'video', 'youtube', 'vimeo', 'logo', 'icon', 'banner',
        'yfirlit', 'office', 'building', 'map', 'flag'
    ]
    
    # 1. Google Custom Search API and Raw Google (Put Google first!)
    from concurrent.futures import ThreadPoolExecutor

    def run_google_api():
        try:
            return search_images_via_google_api(name, birth_year_str, max_images) or []
        except Exception as e:
            print(f"  [Google Search] Villa: {e}")
            return []

    def run_raw_google():
        try:
            return search_images_via_raw_google(name, birth_year_str, max_images) or []
        except Exception as e:
            print(f"  [Raw Google Search] Villa: {e}")
            return []

    def run_bing():
        try:
            return search_images_via_bing(name, birth_year_str, max_images) or []
        except Exception as e:
            print(f"  [Bing Search] Villa: {e}")
            return []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(run_google_api),
            executor.submit(run_raw_google),
            executor.submit(run_bing)
        ]
        for f in futures:
            all_results.extend(f.result())

    # 3. DuckDuckGo Image Search (Bara ef færar en 4 myndir fundust til að sleppa við 403 Ratelimit biðtíma!)
    if len(all_results) < 4:
        try:
            print("  Sækir myndir gegnum DuckDuckGo...")
            try:
                birth_year = int(birth_year_str) if birth_year_str else 1950
            except ValueError:
                birth_year = 1950

            # All meaningful name parts (skip short particles)
            name_parts = [p.lower() for p in name.split() if len(p) > 2]

            from duckduckgo_search import DDGS
            ddgs = DDGS()
            
            # Use very specific queries — name in quotes
            queries = [f'"{name}"']
            
            # If the name has middle names, add a query for just Firstname + Lastname
            if len(name_parts) > 2:
                simplified_name = f"{name.split()[0]} {name.split()[-1]}"
                queries.append(f'"{simplified_name}"')

            for i, query in enumerate(queries):
                try:
                    if i > 0:
                        time.sleep(2.0)
                    from duckduckgo_search import DDGS
                    ddgs = DDGS(timeout=3)
                    print(f"-> Leita að myndum á DDG: {query}")
                    imgs = list(ddgs.images(query, max_results=12))
                    for img in imgs:
                        # Normalize fields
                        img_data = {
                            "image": img.get("image"),
                            "url": img.get("url"),
                            "title": img.get("title")
                        }
                        all_results.append(img_data)
                    time.sleep(1.5)
                except Exception as e:
                    print(f"Villa við DDG myndaleit: {e}")
        except Exception as e:
            print(f"  [DuckDuckGo Search] Villa kom upp: {e}")

    # Unified validation, filtering and deduplication
    name_parts = [p.lower() for p in name.split() if len(p) > 2]
    name_parts_clean = [remove_icelandic_chars(p) for p in name_parts]
    
    unique_results = []
    seen_urls = set()
    
    for img in all_results:
        img_url = img.get("image") or img.get("url")
        if not img_url or img_url in seen_urls:
            continue
            
        title = img.get("title", "")
        title_lower = title.lower()
        
        # Determine if we should skip domain
        skip_domain = False
        page_url = img.get("url", "").lower()
        img_url_lower = img_url.lower()
        
        # Skip banned domains
        for d in SKIP_IMAGE_DOMAINS:
            if d in img_url_lower or d in page_url:
                # Do not skip YouTube if the channel/video title contains the person's full name!
                if 'youtube' in d or 'ytimg' in d:
                    first_clean = name_parts_clean[0]
                    last_clean = name_parts_clean[-1]
                    title_clean = remove_icelandic_chars(title_lower)
                    if first_clean in title_clean and last_clean in title_clean:
                        continue # Keep it!
                skip_domain = True
                break
                
        if skip_domain:
            continue
            
        # Skip bad title keywords
        skip_title = False
        for k in SKIP_TITLE_KEYWORDS:
            if k in title_lower:
                # Do not skip if it matches the person's name
                first_clean = name_parts_clean[0]
                last_clean = name_parts_clean[-1]
                title_clean = remove_icelandic_chars(title_lower)
                if first_clean in title_clean and last_clean in title_clean and k in ['video', 'youtube']:
                    continue # Keep it!
                skip_title = True
                break
                
        if skip_title:
            continue
            
        # Smart Name matching with word boundaries to avoid substring matching (e.g., Jonsson in Sigurjonsson)
        combined_clean = remove_icelandic_chars(title_lower + " " + page_url + " " + img_url_lower)
        first_clean = name_parts_clean[0] if len(name_parts_clean) > 0 else ""
        last_clean = name_parts_clean[-1] if len(name_parts_clean) > 1 else ""
        
        has_first = bool(re.search(r'\b' + re.escape(first_clean) + r'\b', combined_clean)) if first_clean else False
        has_last = bool(re.search(r'\b' + re.escape(last_clean) + r'\b', combined_clean)) if last_clean else False
        
        middle_ok = True
        middle_parts = name_parts_clean[1:-1]
        for m in middle_parts:
            initial = m[0]
            pattern = r'\b(' + re.escape(m) + r'|' + re.escape(initial) + r'(\.|\b))'
            if not re.search(pattern, combined_clean):
                middle_ok = False
                break

        if not (has_first and has_last and middle_ok):
            continue

        # Athuga hvort annað föðurnafn (t.d. Sigurjónsson eða Jóhannsson) sé í titli eða slóð
        title_words = remove_icelandic_chars(title_lower).replace('-', ' ').replace('_', ' ').split()
        other_last_name_found = False
        for w in title_words:
            if len(w) > 5 and (w.endswith('son') or w.endswith('dottir')):
                if last_clean and w != last_clean and not w in name_parts_clean:
                    other_last_name_found = True
                    break
                    
        if other_last_name_found:
            print(f"  Hafnað (annar föðurnafn í titli): {title[:50]}")
            continue
                    
        seen_urls.add(img_url)
        unique_results.append(img)
        print(f"  ✓ Samþykkt mynd: {title[:50]} ({img_url[:40]})")
            
    print(f"  [Myndaleit] Fann samtals {len(unique_results)} staðfestar myndir eftir vörun.")
    return unique_results[:max_images]

def download_image_for_verification(url, cache_name):
    """Download an image to a temp file for Gemini Vision analysis."""
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    
    # Handle Base64 data URLs directly
    if url.startswith("data:image/"):
        try:
            import base64
            header, encoded = url.split(",", 1)
            ext = "jpg"
            if "png" in header:
                ext = "png"
            elif "webp" in header:
                ext = "webp"
            img_data = base64.b64decode(encoded)
            local_path = os.path.join(IMAGE_CACHE_DIR, f"{cache_name}.{ext}")
            with open(local_path, "wb") as f:
                f.write(img_data)
            return local_path
        except Exception as e:
            print(f"  Gat ekki afkóðað base64 mynd: {e}")
            return None

    ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp", "gif"]:
        ext = "jpg"
    local_path = os.path.join(IMAGE_CACHE_DIR, f"{cache_name}.{ext}")

    if os.path.exists(local_path):
        return local_path

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            content = resp.read()
        if len(content) < 2000:
            return None
        with open(local_path, "wb") as f:
            f.write(content)
        return local_path
    except Exception as e:
        print(f"  Gat ekki sótt mynd ({url[:60]}): {e}")
        return None

def verify_face_with_gemini(name, birth, image_path):
    """Use Gemini Vision to check if image contains a real human face of this person."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None  # None = unknown, not rejected

    try:
        from google import genai
        from PIL import Image

        google_key = os.environ.get("GOOGLE_API_KEY")
        try:
            if "GOOGLE_API_KEY" in os.environ:
                del os.environ["GOOGLE_API_KEY"]
                
            from google.genai import types
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(attempts=1),
                    timeout=8.0
                )
            )
            
            img = Image.open(image_path)
            width, height = img.size

            # Reject tiny icons (but accept portrait thumbnails from Google)
            if width < 40 or height < 40:
                print(f"  Of lítil mynd ({width}x{height}), sleppt.")
                return False

            # Reject banners (very wide)
            ratio = width / height
            if ratio > 3.0 or ratio < 0.2:
                print(f"  Hlutfall {ratio:.2f} hafnað (líklega borði/lógó).")
                return False

            prompt = (
                "Look at this image carefully. Does it show a clear human face (like a portrait or profile photo)? "
                "Ignore logos, banners, abstract art, icons, or group photos where the faces are too small. "
                "Answer with only one word: YES or NO."
            )
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt, img]
            )
            result = response.text.strip().upper()
            print(f"  Gemini Vision: {result} — {image_path}")
            return "YES" in result
        finally:
            if google_key:
                os.environ["GOOGLE_API_KEY"] = google_key

    except Exception as e:
        if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e) or 'quota' in str(e).lower():
            print(f"  Gemini Vision yfir kvóta (429) — hætti að reyna.")
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]
        else:
            print(f"  Gemini Vision villa: {e}")
        return None  # Unknown — don't reject, let through

def use_gemini_to_analyze_results(name, birth, raw_results):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return []

    from google import genai
    from google.genai import types
    
    google_key = os.environ.get("GOOGLE_API_KEY")
    try:
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
            
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1),
                timeout=8.0
            )
        )

        results_text = ""
        for idx, r in enumerate(raw_results):
            results_text += f"Result #{idx+1}:\nTitle: {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n\n"

        prompt = f"""
Þú ert sérfræðingur í íslenskri ættfræði. Greindu eftirfarandi leitarniðurstöður fyrir manneskjuna "{name}" (fædd/ur {birth}).
Búðu til lista af uppástungum um fjölskyldutengsl (börn, maka, foreldra) eða myndir ef þú finnur þær í leitarniðurstöðunum.

Gakktu úr skugga um að:
1. Greina hvort upplýsingarnar eiga örugglega við þessa tilteknu manneskju.
2. Gefa hverri uppástungu "confidence" (líkindi á bilinu 0-100). Ef þú finnur mynd (t.d. af LinkedIn, mbl.is, eða háskólasíðu) og ert mjög viss um að hún sé af viðkomandi, skráðu hana sem "type": "image" með hátt confidence.
3. Fyrir skyldmenni (type: "relation"), tilgreindu:
   - relation_details: {{ "type": "child" | "spouse" | "father" | "mother", "name": "Fullt nafn", "sex": "M" | "F" }}
   - Stafsetning nafna íslenskra barna skal fylgja föðurnafni (t.d. Jónsdóttir eða Jónsson eftir kyni).

Skilaðu svarinu eingöngu sem JSON fylki (Array) á eftirfarandi formi:
[
  {{
    "type": "relation" | "image" | "event",
    "source": "Heiti heimildar (t.d. Morgunblaðið, LinkedIn)",
    "url": "Slóð á síðuna",
    "confidence": 95,
    "description": "Stutt lýsing á íslensku (t.d. 'Dóttir: Vala Björk Jónsdóttir')",
    "relation_details": {{
      "type": "child",
      "name": "Vala Björk Jónsdóttir",
      "sex": "F"
    }}
  }}
]

Hér eru leitarniðurstöðurnar:
{results_text}
"""
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return data
        except Exception as e:
            if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e) or 'quota' in str(e).lower():
                print(f"Gemini API kvóti uppurinn (429) við textagreiningu.")
                if "GEMINI_API_KEY" in os.environ:
                    del os.environ["GEMINI_API_KEY"]
            else:
                print(f"Error calling Gemini API: {e}")
            return []
    finally:
        if google_key:
            os.environ["GOOGLE_API_KEY"] = google_key

def resolve_og_image(url):
    if not url:
        return None
    if any(url.lower().split("?")[0].endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        return url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    try:
        parsed = urllib.parse.urlparse(url)
        quoted_path = urllib.parse.quote(parsed.path)
        quoted_query = urllib.parse.quote(parsed.query, safe='=&')
        url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            quoted_path,
            parsed.params,
            quoted_query,
            parsed.fragment
        ))
    except Exception:
        pass

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            html = response.read().decode('utf-8', errors='ignore')
            match = re.search(r'<meta\s+property=["\'`]og:image["\'`]\s+content=["\'`]([^"\'`]+)["\'`]', html)
            if not match:
                match = re.search(r'<meta\s+content=["\'`]([^"\'`]+)["\'`]\s+property=["\'`]og:image["\'`]', html)
            if not match:
                match = re.search(r'<meta\s+name=["\'`]twitter:image["\'`]\s+content=["\'`]([^"\'`]+)["\'`]', html)

            if match:
                img_url = match.group(1)
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/') and not img_url.startswith('//'):
                    parsed_base = urllib.parse.urlparse(url)
                    img_url = f"{parsed_base.scheme}://{parsed_base.netloc}{img_url}"
                return img_url
    except Exception as e:
        print(f"Error fetching og:image for {url}: {e}")
    return None

def find_verified_photos(name, birth, person_id, raw_results=None):
    """
    Search for and save images of this person.
    Uses Gemini Vision if available; otherwise trusts Google Image Search results directly.
    """
    print(f"\n=== Leita að myndum af {name} ===")
    image_results = search_images_for_person(name, birth)
    if not image_results:
        image_results = []

    # Try to extract og:image from the text results as a fallback if we need more photos
    if raw_results and len(image_results) < 3:
        print("  Sækir og:image úr vefleitarniðurstöðum sem bakvara...")
        for r in raw_results[:2]:
            href = r.get("href")
            if href:
                # Do not download from social sites that block standard crawlers
                if any(x in href.lower() for x in ['facebook.com', 'linkedin.com', 'instagram.com', 'twitter.com', 'x.com']):
                    continue
                try:
                    og_img = resolve_og_image(href)
                    if og_img:
                        if any(logo in og_img.lower() for logo in ['soccerway.png', 'flashscore.png', 'sofascore.png', 'default', 'placeholder', 'logo', 'favicon', 'sprite', 'badge']):
                            continue
                        if not any(img.get("image") == og_img for img in image_results):
                            image_results.append({
                                "image": og_img,
                                "url": href,
                                "title": r.get("title", name)
                            })
                            print(f"  ✓ Fann og:image á síðu: {og_img[:60]}")
                except Exception as e:
                    print(f"  Gat ekki sótt og:image fyrir {href}: {e}")

    if not image_results:
        print("Engar myndir fundust í myndaleit eða úr vefsíðum.")
        return []

    verified = []
    api_key = os.environ.get("GEMINI_API_KEY")
    gemini_quota_ok = bool(api_key)  # Start optimistic; will flip to False on first 429

    from concurrent.futures import ThreadPoolExecutor
    api_key = os.environ.get("GEMINI_API_KEY")

    def process_image(idx_and_data):
        i, img_data = idx_and_data
        img_url = img_data.get("image", "")
        page_url = img_data.get("url", img_url)
        source_domain = urllib.parse.urlparse(page_url).netloc.replace("www.", "")
        title = img_data.get("title", "Mynd")

        # Skip known logo/icon sources
        skip_domains = ["wikipedia.org", "wikimedia.org", "gstatic.com", "googlelogo", "apple.com/favicon"]
        if any(sd in img_url for sd in skip_domains):
            return None
        if any(x in img_url for x in ["icon", "logo", "favicon", "sprite", "badge"]):
            return None

        # Verify name (must have first name and last name, or be present on the page)
        name_parts = [p.lower() for p in name.split() if len(p) > 2]
        name_parts_clean = [remove_icelandic_chars(p) for p in name_parts]
        first_clean = name_parts_clean[0] if len(name_parts_clean) > 0 else ""
        last_clean = name_parts_clean[-1] if len(name_parts_clean) > 1 else ""

        title_lower = title.lower()
        combined_clean = remove_icelandic_chars(title_lower + " " + page_url + " " + img_url.lower())

        has_first = bool(re.search(r'\b' + re.escape(first_clean) + r'\b', combined_clean)) if first_clean else False
        has_last = bool(re.search(r'\b' + re.escape(last_clean) + r'\b', combined_clean)) if last_clean else False

        middle_ok = True
        middle_parts = name_parts_clean[1:-1]
        for m in middle_parts:
            # allow matching the full middle name, or its first letter as an initial (e.g. 'axel' or 'a')
            initial = m[0]
            pattern = r'\b(' + re.escape(m) + r'|' + re.escape(initial) + r'(\.|\b))'
            if not re.search(pattern, combined_clean):
                middle_ok = False
                break

        is_match = (has_first and has_last and middle_ok)

        # If not matched in title/URL, fetch the page content and check if the full name is mentioned on the page!
        if not is_match and page_url and page_url.startswith('http'):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                }
                req = urllib.request.Request(page_url, headers=headers)
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    page_html = resp.read().decode('utf-8', errors='ignore').lower()
                clean_page_html = remove_icelandic_chars(page_html)
                if first_clean in clean_page_html and last_clean in clean_page_html:
                    is_match = True
            except Exception:
                pass

        if not is_match:
            print(f"  Hafnað (nafn fannst hvorki í titli/slóð né á síðunni): {title[:50]}")
            return None

        cache_name = f"{person_id}_photo_{i}"
        local_path = download_image_for_verification(img_url, cache_name)
        if not local_path:
            return None

        # Trust the image — Gemini Vision disabled to avoid quota drain
        # (rule-based webpage name verification above is sufficient)
        confidence = 75
        is_trusted = img_data.get('trusted', False)
        # Gemini Vision disabled — rule-based name matching above is sufficient

        stored_img_url = img_url if img_url.startswith('http') else None
        return {
            "type": "image",
            "source": source_domain or "google.com",
            "url": page_url,
            **({"image_url": stored_img_url} if stored_img_url else {}),
            "local_path": local_path,
            "confidence": confidence,
            "description": f"Mynd fundin á Google myndaleit: {title}"
        }

    # Process up to 12 candidates in parallel
    candidates = list(enumerate(image_results[:12]))
    verified = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = executor.map(process_image, candidates)
        for res in results:
            if res:
                verified.append(res)
                print(f"  ✓ Mynd vistuð: {res['url'][:50]} (confidence: {res['confidence']}%)")
                if len(verified) >= 8:
                    break

    print(f"\n=== Myndaleit lokið: {len(verified)} myndir samþykktar ===")
    return verified

def search_web_via_ddg_lite(query, max_results=8):
    import urllib.request
    import urllib.parse
    from bs4 import BeautifulSoup
    results = []
    try:
        url = 'https://lite.duckduckgo.com/lite/'
        data = urllib.parse.urlencode({'q': query}).encode('utf-8')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a'):
            if len(results) >= max_results:
                break
            href = a.get('href')
            if href and href.startswith('http') and 'duckduckgo' not in href:
                title = a.text.strip()
                parent = a.find_parent('tr')
                snippet = ""
                if parent:
                    snippet_tr = parent.find_next_sibling('tr')
                    if snippet_tr:
                        snippet = snippet_tr.text.strip()
                results.append({
                    "title": title,
                    "href": href,
                    "body": snippet
                })
        print(f"  [DDG Lite Vefleit] Fann {len(results)} heimildir.")
    except Exception as e:
        print(f"  [DDG Lite Vefleit] Villa: {e}")
    return results

def search_web_via_bing(query, max_results=8):
    import urllib.request
    import urllib.parse
    import base64
    from bs4 import BeautifulSoup
    results = []
    try:
        url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for li in soup.find_all('li', class_='b_algo'):
            if len(results) >= max_results: break
            h2 = li.find('h2')
            if not h2 or not h2.find('a'): continue
            a = h2.find('a')
            href = a.get('href', '')
            title = a.text.strip()
            if 'bing.com/ck/a' in href and 'u=' in href:
                try:
                    u_param = href.split('u=')[1].split('&')[0]
                    if u_param.startswith('a1'): href = base64.b64decode(u_param[2:] + '==').decode('utf-8', errors='ignore')
                except Exception: pass
            p = li.find('p')
            snippet = p.text.strip() if p else ""
            if href.startswith('http') and not 'bing.com' in href and not 'microsoft.com' in href:
                results.append({"title": title, "href": href, "body": snippet})
        print(f"  [Bing Vefleit] Fann {len(results)} heimildir.")
    except Exception as e:
        print(f"  [Bing Vefleit] Villa: {e}")
    return results

def perform_search(name, birth, strategies, person_id):
    raw_results = []
    
    from concurrent.futures import ThreadPoolExecutor
    
    # Run searches sequentially to avoid DDG rate-limiting
    import time
    for idx, s in enumerate(strategies):
        if idx > 0:
            time.sleep(1.0)
        print(f"-> Leita að: {s['query']} ({s['source']})")
        try:
            ddg_res = search_web_via_ddg_lite(s['query'], max_results=8)
            if not ddg_res:
                print(f"  [DDG Lite] Skilaði engu (líklega varið/rate-limited), reyni Bing sem bakvara...")
                ddg_res = search_web_via_bing(s['query'], max_results=8)
            raw_results.extend(ddg_res)
        except Exception as e:
            print(f"  [Vefleit] Villa við leit: {e}")
    
    # Always also try Bing for the main query as backup
    if len(raw_results) < 4:
        try:
            bing_res = search_web_via_bing(name, max_results=8)
            raw_results.extend(bing_res)
        except Exception as e:
            print(f"  [Bing Vefleit] Villa: {e}")

    # Sía burt allt sem er ekki tengt nafni eða er tölvuleikir/erlent rusl
    name_parts = [p.lower() for p in name.split() if len(p) > 2]
    norm_parts = set(name_parts + [remove_icelandic_chars(p) for p in name_parts])
    blacklist_words = ['lol', 'league of legends', 'champion', 'mobafire', 'u.gg', 'op.gg', 'metasrc', 'fandom', 'riot', 'gameplay', 'runes', 'builds', 'esports', 'viktor.ai', 'viktor.com', 'star citizen', 'theimpound']
    
    filtered_results = []
    for r in raw_results:
        text_comb = remove_icelandic_chars((r.get("title", "") + " " + r.get("body", "") + " " + r.get("href", "")).lower())
        if any(bw in text_comb for bw in blacklist_words):
            continue
        matches = sum(1 for p in norm_parts if p in text_comb)
        if len(name_parts) >= 2 and matches < 2:
            continue
        filtered_results.append(r)
    raw_results = filtered_results
    print(f"  [Scraper] Eftir síun standa eftir {len(raw_results)} viðeigandi vefheimildir.")

    text_sugs = []
    gemini_success = False
    if os.environ.get("GEMINI_API_KEY"):  # Single Gemini call to analyze text results (Vision is disabled separately)
        print("Notar Gemini til að greina leitarniðurstöður...")
        gemini_sugs = use_gemini_to_analyze_results(name, birth, raw_results)
        if gemini_sugs:
            for sug in gemini_sugs:
                if sug.get("type") == "image":
                    direct_img = resolve_og_image(sug.get("url"))
                    if direct_img:
                        sug["image_url"] = direct_img
                    else:
                        sug["image_url"] = sug.get("url")
            text_sugs = gemini_sugs
            gemini_success = True

    if not gemini_success:
        print("  [Scraper] Notar reglumiðaðan bakvara fyrir greiningu (API óvirkt/yfir kvóta).")
        # Fallback rule-based
        for r in raw_results:
            confidence = 75
            title_lower = r.get("title", "").lower()
            if "minningargreinar" in title_lower or "andlát" in title_lower:
                confidence += 20
            if "scholar" in r.get("href", "") or "pubmed" in r.get("href", ""):
                confidence += 20
            if "linkedin.com/in/" in r.get("href", ""):
                confidence += 15
            confidence = min(confidence, 99)
            text_sugs.append({
                "type": "event",
                "source": "Vefleit",
                "url": r.get("href", ""),
                "confidence": confidence,
                "description": f"**{r.get('title', '')}**\n{r.get('body', '')}"
            })
        text_sugs.sort(key=lambda x: x['confidence'], reverse=True)

    # Search for verified photos
    photo_sugs = find_verified_photos(name, birth, person_id, raw_results)

    return photo_sugs + text_sugs

def main():
    parser = argparse.ArgumentParser(description="Raunverulegur leitarþjarkur (DDG) byggður á kynslóðalógík")
    parser.add_argument("--id", type=str, required=True, help="GEDCOM ID")
    parser.add_argument("--name", type=str, required=True, help="Nafn manneskju")
    parser.add_argument("--birth", type=str, default="", help="Fæðingarár")

    args = parser.parse_args()

    suggestions = load_suggestions()

    strategies = get_generation_search_strategies(args.name, args.birth)
    print(f"Byrja greiningu og leit fyrir {args.name} (f. {args.birth})...")

    new_sugs = perform_search(args.name, args.birth, strategies, args.id)

    if new_sugs:
        if args.id not in suggestions:
            suggestions[args.id] = []

        existing_urls = set(s.get('url') for s in suggestions[args.id])

        added_count = 0
        for s in new_sugs:
            is_dup = False
            img_src = s.get('image') or s.get('image_url') or s.get('local_path')
            for exist_sug in suggestions[args.id]:
                exist_img = exist_sug.get('image') or exist_sug.get('image_url') or exist_sug.get('local_path')
                if s.get('type') == 'image' and img_src and exist_img and img_src == exist_img:
                    is_dup = True
                    if 'rejected' in exist_sug:
                        del exist_sug['rejected']
                        added_count += 1
                    break
                elif s.get('url') and exist_sug.get('url') and s.get('url') == exist_sug.get('url'):
                    is_dup = True
                    if 'rejected' in exist_sug:
                        del exist_sug['rejected']
                        added_count += 1
                    break
            
            if not is_dup:
                suggestions[args.id].append(s)
                if s.get('url'):
                    existing_urls.add(s.get('url'))
                added_count += 1

        save_suggestions(suggestions)
        print(f"Tókst! Bætti við {added_count} raunverulegum uppástungum af vefnum fyrir {args.name}.")
    else:
        print("Engar nýjar uppástungur fundust eða leit brást.")

if __name__ == "__main__":
    main()
