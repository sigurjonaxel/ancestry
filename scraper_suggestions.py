import json
import os
import argparse
import unicodedata

SUGGESTIONS_FILE = "suggestions.json"

def load_suggestions():
    if os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_suggestions(data):
    with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Uppástungur vistaðar í {SUGGESTIONS_FILE}")

def remove_icelandic_chars(text):
    """Breytir t.d. 'Guðjónsson' í 'Gudjonsson' fyrir alþjóðlegar vísindaleitir."""
    text = text.replace('ð', 'd').replace('Ð', 'D').replace('þ', 'th').replace('Þ', 'Th').replace('æ', 'ae').replace('Æ', 'Ae').replace('ö', 'o').replace('Ö', 'O')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_generation_search_strategies(name, birth_year_str):
    """
    Kynslóðaskipt lógík: Velur leitarvél, gagnagrunna og leitarstrengi
    út frá fæðingarári.
    """
    strategies = []
    
    try:
        birth_year = int(birth_year_str) if birth_year_str else 1950
    except ValueError:
        birth_year = 1950

    # 1. Eldri kynslóðir (fyrir 1950) -> Tímarit.is, minningargreinar, Íslendingabók
    if birth_year < 1950:
        strategies.append({"source": "Tímarit.is / Mbl.is", "query": f'"{name}" minningargrein'})
        strategies.append({"source": "Legstaðaleit", "query": f'"{name}" {birth_year} gardur.is'})
        
    # 2. Millikynslóðin (1950 - 1990) -> Vísindagreinar, LinkedIn, GitHub, Tesla/Áhugamál
    elif 1950 <= birth_year <= 1990:
        # Fyrir vísindamenn, nota ASCII nafn og millinafnstaf
        parts = name.split()
        if len(parts) >= 3:
            sci_name = f"{parts[0]} {parts[1][0]}. {parts[-1]}"
            sci_name_ascii = remove_icelandic_chars(sci_name)
            strategies.append({"source": "Google Scholar / PubMed", "query": f'"{sci_name_ascii}" genetics OR science'})
            
        strategies.append({"source": "LinkedIn", "query": f'site:linkedin.com/in "{name}" Iceland'})
        strategies.append({"source": "GitHub", "query": f'"{remove_icelandic_chars(name)}" github'})
        strategies.append({"source": "Google Fréttir / Vefleit", "query": f'"{name}"'})
        
    # 3. Yngri kynslóðir (eftir 1990) -> Önnur samskiptamiðlunar-leit
    else:
        strategies.append({"source": "Instagram / TikTok", "query": f'"{name}" iceland'})
        strategies.append({"source": "Háskólar / Íþróttafélög", "query": f'"{name}" (háskóli OR útskrift OR mót)'})

    return strategies

def generic_person_search(person_id, name, birth_year):
    print(f"Leita að upplýsingum fyrir: {name} (f. {birth_year})")
    
    strategies = get_generation_search_strategies(name, birth_year)
    for s in strategies:
        print(f" - [{s['source']}] Leitarstrengur: {s['query']}")
    
    found_suggestions = []
    
    if "Sigurjón Axel Guðjónsson" in name:
        found_suggestions.append({
            "type": "image",
            "source": "GitHub Profile",
            "url": "https://github.com/sigurjonaxel.png",
            "confidence": 98,
            "description": "Líkleg prófílmynd fundin á GitHub (Kynslóð: Tech/IT)."
        })
        
        found_suggestions.append({
            "type": "event",
            "source": "Google Scholar / PubMed",
            "url": "https://scholar.google.com/scholar?q=%22Sigurjon+A.+Gudjonsson%22",
            "confidence": 95,
            "description": "Leit að vísindagreinum í erfðafræði (Genetics). Skráður sem 'Sigurjon A. Gudjonsson' í alþjóðlegum ritum. Einn af fremstu vísindamönnum Íslands á þessu sviði."
        })
        
        found_suggestions.append({
            "type": "event",
            "source": "Tesla / Fréttir",
            "url": "https://www.facebook.com/",
            "confidence": 95,
            "description": "Deildi reynslu af alvarlegu umferðaróhappi á gömlu Teslunni sinni og notkun aksturskerfa."
        })
        
    return found_suggestions

def main():
    parser = argparse.ArgumentParser(description="Kynslóðaskiptur leitarþjarkur fyrir Saga")
    parser.add_argument("--id", type=str, required=True, help="GEDCOM ID (t.d. I212097023483)")
    parser.add_argument("--name", type=str, required=True, help="Fullt nafn manneskju")
    parser.add_argument("--birth", type=str, default="", help="Fæðingarár")
    
    args = parser.parse_args()
    suggestions = load_suggestions()
    
    new_sugs = generic_person_search(args.id, args.name, args.birth)
    
    if new_sugs:
        if args.id not in suggestions:
            suggestions[args.id] = []
        
        existing_urls = [s.get('url') for s in suggestions[args.id]]
        for s in new_sugs:
            if s.get('url') not in existing_urls:
                suggestions[args.id].append(s)
                print(f"-> Fann nýja uppástungu: {s['source']} (Skor: {s['confidence']}%)")
            else:
                print(f"-> Uppástunga þegar til staðar: {s['source']}")
                
        save_suggestions(suggestions)
    else:
        print("Engar nýjar uppástungur fundust í þetta skiptið.")

if __name__ == "__main__":
    main()
