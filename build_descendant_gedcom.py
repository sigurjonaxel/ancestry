import re

file_path = "/home/sigurjonaxel/.gemini/antigravity/brain/d5433bd9-cdaf-450e-94ba-be91aad354ce/.system_generated/steps/1119/content.md"
output_file = "aettarmot_new_people.ged"

def generate_id(prefix, num):
    # e.g. I_AETT_1_1
    safe_num = str(num).replace('.', '_')
    return f"@{prefix}_{safe_num}@"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

people = []
families = [] # list of dicts: {'husb': id, 'wife': id, 'chil': [ids], 'id': fam_id}
images = []

descendant_re = re.compile(r'(\d+(?:\.\d+)*)\.?\s+(.*?)\*\*\s+\(f\.\s*([\d\.]+)(?:\s*–\s*d\.\s*([\d\.]+))?\)')
spouse_re = re.compile(r'(?:Maki|Barnsfaðir|Barnsmóðir)(?:\s+\d+)?:?\s+(.*?)\s+\(f\.\s*([\d\.]+)(?:\s*(?:–|-)\s*d\.\s*([\d\.]+))?\)')
image_re = re.compile(r'!\[.*?\]\((.*?)\)')

current_descendant_num = ""

# Track the family ID keyed by descendant num
# Each descendant has a family where they are a parent, if they have spouses/children
fam_map = {}

# Parent mapping: e.g. 1.1's parent is 1
def get_parent_num(num):
    parts = str(num).split('.')
    if len(parts) > 1:
        return '.'.join(parts[:-1])
    return None

for line in lines:
    img_match = image_re.search(line)
    if img_match:
        images.append(img_match.group(1))
        continue

    clean_line = line.replace('**', '')
    d_match = re.search(r'(\d+(?:\.\d+)*)\.?\s+([^\(]+)\s*\(f\.\s*([\d\.]+)(?:\s*(?:–|-)\s*d\.\s*([\d\.]+))?\)', clean_line)
    
    if d_match:
        num = d_match.group(1)
        name = d_match.group(2).strip()
        birth = d_match.group(3)
        death = d_match.group(4)
        
        people.append({
            'id': generate_id('I', num),
            'name': name,
            'birth': birth,
            'death': death,
            'type': 'descendant',
            'num': num
        })
        current_descendant_num = num
        
        # Link to parent's family
        parent_num = get_parent_num(num)
        if parent_num:
            if parent_num not in fam_map:
                fam_map[parent_num] = {'id': generate_id('F', parent_num), 'husb': None, 'wife': None, 'chil': []}
            fam_map[parent_num]['chil'].append(generate_id('I', num))
            
        # Create my own family
        if num not in fam_map:
            fam_map[num] = {'id': generate_id('F', num), 'husb': generate_id('I', num), 'wife': None, 'chil': []}
        else:
            fam_map[num]['husb'] = generate_id('I', num)
            
        continue
        
    s_match = spouse_re.search(clean_line)
    if s_match and current_descendant_num:
        name = s_match.group(1).strip()
        birth = s_match.group(2)
        death = s_match.group(3)
        spouse_id = generate_id('S', current_descendant_num)
        
        people.append({
            'id': spouse_id,
            'name': name,
            'birth': birth,
            'death': death,
            'type': 'spouse',
            'partner_num': current_descendant_num
        })
        
        if current_descendant_num in fam_map:
            fam_map[current_descendant_num]['wife'] = spouse_id

# Búa til GEDCOM strenginn
gedcom_lines = ["0 HEAD", "1 CHAR UTF-8"]

for p in people:
    gedcom_lines.append(f"0 {p['id']} INDI")
    gedcom_lines.append(f"1 NAME {p['name']}")
    if p['birth']:
        gedcom_lines.append(f"1 BIRT\n2 DATE {p['birth']}")
    if p['death']:
        gedcom_lines.append(f"1 DEAT\n2 DATE {p['death']}")
        
    if p['type'] == 'descendant':
        # FamC
        parent_num = get_parent_num(p['num'])
        if parent_num and parent_num in fam_map:
            gedcom_lines.append(f"1 FAMC {fam_map[parent_num]['id']}")
        # FamS
        if p['num'] in fam_map and (fam_map[p['num']]['wife'] or fam_map[p['num']]['chil']):
            gedcom_lines.append(f"1 FAMS {fam_map[p['num']]['id']}")
            
    elif p['type'] == 'spouse':
        gedcom_lines.append(f"1 FAMS {fam_map[p['partner_num']]['id']}")

for num, fam in fam_map.items():
    if not fam['wife'] and not fam['chil']:
        continue # Empty family
    gedcom_lines.append(f"0 {fam['id']} FAM")
    if fam['husb']:
        gedcom_lines.append(f"1 HUSB {fam['husb']}")
    if fam['wife']:
        gedcom_lines.append(f"1 WIFE {fam['wife']}")
    for chil in fam['chil']:
        gedcom_lines.append(f"1 CHIL {chil}")

gedcom_lines.append("0 TRLR")

with open(output_file, "w", encoding="utf-8") as out:
    out.write("\n".join(gedcom_lines) + "\n")

print(f"Bjó til {output_file} með {len(people)} einstaklingum.")
