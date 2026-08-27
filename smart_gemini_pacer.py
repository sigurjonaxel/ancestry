import time, os, json, re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_grounded_ai_summary(name, birth_year="", death_year="", family_context=""):
    """
    Calls Google Search Grounding with Gemini, with a built-in 3.5s cooldown
    to strictly stay below the 20 RPM Free Tier limit and prevent 429 errors.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "Vantar GEMINI_API_KEY"}
        
    client = genai.Client(api_key=api_key)
    
    # 3.5s cooldown ensures maximum 17 RPM (well below 20 RPM limit)
    time.sleep(3.5)
    
    prompt = f"""
    Þú ert íslenskur ættfræðingur og rannsóknarmaður.
    Leitaðu á Google að nákvæmum, staðfestum upplýsingum, starfsferli, námi, íþróttum eða afrekum um:
    - Fullt nafn: {name}
    - Fæðingarár: {birth_year if birth_year else 'ótilgreint'}
    - Dánarár: {death_year if death_year else 'Lifandi / ótilgreint'}
    
    ÞEKKT FJÖLSKYLDUTENGSL:
    {family_context}
    
    KROSSPRÓFAÐU ALNAFNA: Hafnaðu upplýsingum sem eiga við aðra alnafna sem passa ekki við aldur eða fjölskyldu.
    
    Skilaðu samantekt á íslensku sem JSON:
    {{
        "bio": "Samantekt á starfs- og lífshlaupi...",
        "sources": [
            {{
                "title": "Nafn vefs/fréttar",
                "snippet": "Útdráttur um {name}...",
                "url": "Slóð"
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
    
    for attempt in range(4):
        try:
            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            if resp and resp.text:
                txt = resp.text.strip()
                m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.DOTALL)
                if m:
                    res_json = json.loads(m.group(1))
                else:
                    s = txt.find("{")
                    e = txt.rfind("}")
                    res_json = json.loads(txt[s:e+1]) if s != -1 and e != -1 else {"bio": txt, "sources": []}
                return {"status": "success", "data": res_json}
        except Exception as e:
            err_str = str(e)
            print(f"  ⏳ [Pacer] Google er að endurstilla kvóta ({err_str[:60]}), bíð í 15s...")
            time.sleep(15)
            
    return {"status": "error", "message": "Google Search Grounding svaraði ekki eftir 4 tilraunir."}

if __name__ == "__main__":
    test_res = generate_grounded_ai_summary("Sara Kristín Jónsdóttir", "2004", "", "Móðir: Ólafía Rósbjörg Ingólfsdóttir")
    print("Niðurstaða:", test_res)
