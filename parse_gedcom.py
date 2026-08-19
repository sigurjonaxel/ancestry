import sys

def parse_gedcom(file_path):
    print(f"Parsing {file_path}...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    indis = {}
    current_indi = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(' ', 2)
        level = parts[0]
        tag = parts[1]
        val = parts[2] if len(parts) > 2 else ''
        
        # Check for new INDI record
        if len(parts) > 2 and parts[2] == 'INDI':
            current_indi = parts[1].replace('@', '')
            indis[current_indi] = {'name': '', 'birth': '', 'death': '', 'sex': '', 'fams': [], 'famc': []}
        elif current_indi:
            if tag == 'NAME':
                indis[current_indi]['name'] = val.replace('/', '').strip()
            elif tag == 'SEX':
                indis[current_indi]['sex'] = val
            elif tag == 'FAMS':
                indis[current_indi]['fams'].append(val.replace('@', ''))
            elif tag == 'FAMC':
                indis[current_indi]['famc'].append(val.replace('@', ''))
            elif tag == 'BIRT':
                # we will catch DATE in subsequent lines
                indis[current_indi]['last_event'] = 'BIRT'
            elif tag == 'DEAT':
                indis[current_indi]['last_event'] = 'DEAT'
            elif tag == 'DATE':
                last_event = indis[current_indi].get('last_event')
                if last_event == 'BIRT':
                    indis[current_indi]['birth'] = val
                    indis[current_indi]['last_event'] = None
                elif last_event == 'DEAT':
                    indis[current_indi]['death'] = val
                    indis[current_indi]['last_event'] = None
            elif level == '1': # reset event context
                indis[current_indi]['last_event'] = None

    print(f"Total individuals found: {len(indis)}")
    # Print the first 20 individuals
    for i, (k, v) in enumerate(list(indis.items())[:30]):
        print(f"  {k}: {v['name']} (B: {v['birth']}, D: {v['death']}) - FAMC: {v['famc']}, FAMS: {v['fams']}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        parse_gedcom(sys.argv[1])
    else:
        print("Usage: python parse_gedcom.py <ged_file>")
