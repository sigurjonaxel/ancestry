import json

try:
    with open("suggestions.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    count = 0
    for pid, sugs in data.items():
        for sug in sugs:
            if "rejected" in sug:
                del sug["rejected"]
                count += 1
                
    with open("suggestions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Cleared {count} rejected flags.")
except Exception as e:
    print(e)
