import os, json, urllib.request, re
from dotenv import load_dotenv

load_dotenv()

def search_with_perplexity(name, birth_year="", death_year="", family_context=""):
    """
    Direct ultra-fast real-time search with Perplexity API (Sonar model).
    Returns structured biography, timeline events and verified citations.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "PERPLEXITY_API_KEY vantar í .env skrána."
        }

    url = "https://api.perplexity.ai/chat/completions"
    
    prompt = f"""
    Þú ert sérfræðingur í íslenskri ættfræði og ævisögurannsóknum.
    Leitaðu á vefnum að öllum staðfestum upplýsingum, greinum, fréttum, menntun og starfsferli um:
    - Fullt nafn: {name}
    - Fæðingarár: {birth_year if birth_year else 'óþekkt'}
    - Dánarár: {death_year if death_year else 'Lifandi / óþekkt'}
    
    ÞEKKT FJÖLSKYLDUTENGSL ÚR ÆTTARTRÉI (TIL KROSSPRÓFUNAR):
    {family_context}
    
    STRÖNG SKILYRÐI:
    - KROSSPRÓFAÐU ALNAFNA: Ef annar einstaklingur með sama nafn er miklu yngri/eldri eða í öðru samhengi, hafnaðu þeim upplýsingum.
    - EKKI búa til skáldaðar staðreyndir.
    
    Skilaðu svarinu á íslensku sem JSON á eftirfarandi formi:
    {{
        "bio": "Nákvæm, samfelld ævisaga á íslensku...",
        "sources": [
            {{
                "title": "Titill greinar/vefsvæðis",
                "snippet": "1-2 setninga útdráttur um tengsl við {name}...",
                "url": "Bein vefslóð"
            }}
        ],
        "timeline": [
            {{
                "year": "Ártal",
                "title": "Viðburður",
                "description": "Lýsing..."
            }}
        ]
    }}
    """
    
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a professional Icelandic genealogy researcher. Return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if m:
                res_json = json.loads(m.group(1))
            else:
                s = content.find("{")
                e = content.rfind("}")
                res_json = json.loads(content[s:e+1]) if s != -1 and e != -1 else {"bio": content, "sources": []}
                
            return {
                "status": "success",
                "data": res_json
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Villa við tengingu við Perplexity: {e}"
        }
