"""
Fix duplicate family records in sigurjon.ged.

Problems identified:
1. FADD5 is a duplicate of F17 (Guðjón + Erla family) but missing HUSB.
   Children point to FADD5 as FAMC instead of F17 → father missing.
2. FADD26 is a duplicate of F18 (Sigurjón Axel + Ása Björk).
   Children point to both → duplicate spouse entries.
3. Similar FADD duplicates for other siblings (FADD25, FADD27 etc.)

Fix strategy:
- For each FADD family that duplicates a real F## family:
  - Repoint all FAMC references from FADD## to F##
  - Remove FAMS @FADD##@ from individuals
  - Delete the FADD## family record
"""
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks

def find_duplicate_families(blocks):
    """Find FADD families that are duplicates of F## families."""
    fams = {}
    for b in blocks:
        if b.type == 'FAM':
            husb = None
            wife = None
            children = []
            for line in b.lines:
                if line.startswith('1 HUSB'):
                    husb = line.split()[-1].replace('@', '')
                elif line.startswith('1 WIFE'):
                    wife = line.split()[-1].replace('@', '')
                elif line.startswith('1 CHIL'):
                    children.append(line.split()[-1].replace('@', ''))
            fams[b.id] = {
                'husb': husb,
                'wife': wife,
                'children': set(children),
                'block': b
            }
    
    duplicates = {}  # FADD_id -> original F_id
    
    for fid, fdata in fams.items():
        if not fid.startswith('FADD'):
            continue
        # Look for a matching F## family
        for oid, odata in fams.items():
            if oid.startswith('FADD'):
                continue
            # Check if children overlap significantly
            if not fdata['children'] or not odata['children']:
                continue
            overlap = fdata['children'] & odata['children']
            if len(overlap) >= 2 or (len(overlap) >= 1 and len(fdata['children']) <= 2):
                # Strong match
                duplicates[fid] = oid
                print(f"  DUPLICATE: {fid} -> {oid}")
                print(f"    FADD: husb={fdata['husb']}, wife={fdata['wife']}, children={fdata['children']}")
                print(f"    Orig: husb={odata['husb']}, wife={odata['wife']}, children={odata['children']}")
                break
    
    return duplicates

def fix_gedcom(filename):
    print(f"\n=== Fixing {filename} ===")
    blocks = parse_gedcom_blocks(filename)
    
    duplicates = find_duplicate_families(blocks)
    
    if not duplicates:
        print("No duplicate families found.")
        return
    
    print(f"\nFound {len(duplicates)} duplicate families to fix.")
    
    # Fix FAMC references on individuals
    for b in blocks:
        if b.type != 'INDI':
            continue
        new_lines = []
        changed = False
        for line in b.lines:
            if line.startswith('1 FAMC'):
                fam_ref = line.split()[-1].replace('@', '')
                if fam_ref in duplicates:
                    original = duplicates[fam_ref]
                    new_line = f"1 FAMC @{original}@"
                    # Only add if not already there
                    if f"1 FAMC @{original}@" not in [l for l in new_lines]:
                        new_lines.append(new_line)
                        changed = True
                        name = b.get_value(['NAME']) or b.id
                        print(f"  Fixed FAMC: {name}: {fam_ref} -> {original}")
                    else:
                        changed = True  # Skip duplicate
                    continue
            if line.startswith('1 FAMS'):
                fam_ref = line.split()[-1].replace('@', '')
                if fam_ref in duplicates:
                    changed = True
                    name = b.get_value(['NAME']) or b.id
                    print(f"  Removed FAMS: {name}: {fam_ref}")
                    continue  # Skip this line entirely
            new_lines.append(line)
        if changed:
            b.lines = new_lines
    
    # Remove duplicate family blocks
    blocks_to_remove = []
    for b in blocks:
        if b.type == 'FAM' and b.id in duplicates:
            blocks_to_remove.append(b)
            print(f"  Deleted family record: {b.id}")
    
    for b in blocks_to_remove:
        blocks.remove(b)
    
    save_gedcom_blocks(blocks, filename)
    print(f"\n{filename} fixed! Removed {len(blocks_to_remove)} duplicate families.")

if __name__ == '__main__':
    fix_gedcom('sigurjon.ged')
    fix_gedcom('loa.ged')
