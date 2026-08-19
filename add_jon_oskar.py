import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def add_ex_husband():
    blocks = parse_gedcom_blocks('loa.ged')
    
    loa_id = 'I272771958737' # Ólafía Rósbjörg
    
    new_id_counter = 200
    def get_new_indi_id():
        nonlocal new_id_counter
        while f"I_ADD_{new_id_counter}" in [b.id for b in blocks if b.id]:
            new_id_counter += 1
        return f"I_ADD_{new_id_counter}"

    def get_new_fam_id():
        nonlocal new_id_counter
        while f"F_ADD_{new_id_counter}" in [b.id for b in blocks if b.id]:
            new_id_counter += 1
        return f"F_ADD_{new_id_counter}"

    # Create Jón Óskar
    jon_id = get_new_indi_id()
    new_block = GedcomBlock(f"0 @{jon_id}@ INDI")
    new_block.add_tag(1, "NAME", "Jón Óskar /Pétursson/")
    new_block.add_tag(2, "GIVN", "Jón Óskar")
    new_block.add_tag(2, "SURN", "Pétursson")
    new_block.add_tag(1, "SEX", "M")
    blocks.append(new_block)
    
    # Create Family (Divorced)
    fam_id = get_new_fam_id()
    fam_block = GedcomBlock(f"0 @{fam_id}@ FAM")
    fam_block.add_tag(1, "HUSB", f"@{jon_id}@")
    fam_block.add_tag(1, "WIFE", f"@{loa_id}@")
    fam_block.add_tag(1, "DIV", "Y") # Divorced
    blocks.append(fam_block)
    
    # Update individuals
    loa_block = next((b for b in blocks if b.id == loa_id), None)
    if loa_block:
        loa_block.add_tag(1, "FAMS", f"@{fam_id}@")
        
    jon_block = next((b for b in blocks if b.id == jon_id), None)
    if jon_block:
        jon_block.add_tag(1, "FAMS", f"@{fam_id}@")

    # Move TRLR
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    save_gedcom_blocks(blocks, 'loa.ged')
    print("loa.ged updated with ex-husband Jón Óskar Pétursson!")

if __name__ == '__main__':
    add_ex_husband()
