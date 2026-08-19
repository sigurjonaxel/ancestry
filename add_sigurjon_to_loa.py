import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def update_loa_partner():
    blocks = parse_gedcom_blocks('loa.ged')
    
    loa_id = 'I272771958737' # Ólafía Rósbjörg
    
    new_id_counter = 100
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

    # Check if Sigurjon is already there
    sigurjon_id = None
    for b in blocks:
        if b.type == 'INDI' and 'Sigurjón Axel' in b.get_value(['NAME']):
            sigurjon_id = b.id
            break
            
    if not sigurjon_id:
        sigurjon_id = get_new_indi_id()
        new_block = GedcomBlock(f"0 @{sigurjon_id}@ INDI")
        new_block.add_tag(1, "NAME", "Sigurjón Axel /Guðjónsson/")
        new_block.add_tag(2, "GIVN", "Sigurjón Axel")
        new_block.add_tag(2, "SURN", "Guðjónsson")
        new_block.add_tag(1, "SEX", "M")
        new_block.add_tag(1, "BIRT")
        new_block.add_tag(2, "DATE", "4 Feb 1974")
        blocks.append(new_block)
        print(f"Added Sigurjón Axel as @{sigurjon_id}@")
        
    fam_id = get_new_fam_id()
    fam_block = GedcomBlock(f"0 @{fam_id}@ FAM")
    fam_block.add_tag(1, "HUSB", f"@{sigurjon_id}@")
    fam_block.add_tag(1, "WIFE", f"@{loa_id}@")
    fam_block.add_tag(1, "MARR")
    fam_block.add_tag(2, "DATE", "21 Feb 2026")
    fam_block.add_tag(2, "TYPE", "Kærustupar")
    blocks.append(fam_block)
    
    # Update individuals
    loa_block = next((b for b in blocks if b.id == loa_id), None)
    if loa_block:
        loa_block.add_tag(1, "FAMS", f"@{fam_id}@")
        
    sig_block = next((b for b in blocks if b.id == sigurjon_id), None)
    if sig_block:
        sig_block.add_tag(1, "FAMS", f"@{fam_id}@")

    # Move TRLR
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    save_gedcom_blocks(blocks, 'loa.ged')
    print("loa.ged updated with Kærustupar relationship!")

if __name__ == '__main__':
    update_loa_partner()
