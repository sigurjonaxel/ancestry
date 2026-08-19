import re
import json

file_path = "/home/sigurjonaxel/.gemini/antigravity/brain/d5433bd9-cdaf-450e-94ba-be91aad354ce/.system_generated/steps/1119/content.md"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

people = []
images = []

descendant_re = re.compile(r'(\d+(?:\.\d+)*)\.?\s+(.*?)\*\*\s+\(f\.\s*([\d\.]+)(?:\s*–\s*d\.\s*([\d\.]+))?\)')
# Maki / Barnsfaðir / Barnsmóðir
spouse_re = re.compile(r'(?:Maki|Barnsfaðir|Barnsmóðir)(?:\s+\d+)?:?\s+(.*?)\s+\(f\.\s*([\d\.]+)(?:\s*(?:–|-)\s*d\.\s*([\d\.]+))?\)')
image_re = re.compile(r'!\[.*?\]\((.*?)\)')

current_descendant_id = ""
for line in lines:
    img_match = image_re.search(line)
    if img_match:
        images.append(img_match.group(1))
        continue

    # Clean markdown bold
    clean_line = line.replace('**', '')
    
    # Try descendant
    d_match = re.search(r'(\d+(?:\.\d+)*)\.?\s+([^\(]+)\s*\(f\.\s*([\d\.]+)(?:\s*(?:–|-)\s*d\.\s*([\d\.]+))?\)', clean_line)
    if d_match:
        num = d_match.group(1)
        name = d_match.group(2).strip()
        birth = d_match.group(3)
        death = d_match.group(4)
        people.append({
            'type': 'descendant',
            'num': num,
            'name': name,
            'birth': birth,
            'death': death
        })
        current_descendant_id = num
        continue
        
    s_match = spouse_re.search(clean_line)
    if s_match and current_descendant_id:
        name = s_match.group(1).strip()
        birth = s_match.group(2)
        death = s_match.group(3)
        people.append({
            'type': 'spouse',
            'partner_num': current_descendant_id,
            'name': name,
            'birth': birth,
            'death': death
        })

print(f"Found {len(people)} people and {len(images)} images.")
for p in people[:10]:
    print(p)
