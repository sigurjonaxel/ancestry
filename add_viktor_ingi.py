import sys
from edit_gedcom import parse_gedcom_blocks, save_gedcom_blocks, GedcomBlock

def add_loa_children():
    blocks = parse_gedcom_blocks('loa.ged')
    
    loa_id = 'I272771958737'
    
    # Find Jón Óskar's family ID
    jon_fam_id = None
    for b in blocks:
        if b.type == 'FAM' and b.get_value(['WIFE']) == f"@{loa_id}@" and b.get_value(['DIV']) == 'Y':
            jon_fam_id = b.id
            break
            
    if not jon_fam_id:
        print("Could not find family for Lóa and Jón Óskar.")
        return

    new_id_counter = 300
    def get_new_indi_id():
        nonlocal new_id_counter
        while f"I_ADD_{new_id_counter}" in [b.id for b in blocks if b.id]:
            new_id_counter += 1
        return f"I_ADD_{new_id_counter}"

    # Add Viktor Ingi Jónsson
    viktor_id = get_new_indi_id()
    new_block = GedcomBlock(f"0 @{viktor_id}@ INDI")
    new_block.add_tag(1, "NAME", "Viktor Ingi /Jónsson/")
    new_block.add_tag(2, "GIVN", "Viktor Ingi")
    new_block.add_tag(2, "SURN", "Jónsson")
    new_block.add_tag(1, "SEX", "M")
    new_block.add_tag(1, "FAMC", f"@{jon_fam_id}@")
    blocks.append(new_block)
    
    # Update family with child
    fam_block = next((b for b in blocks if b.id == jon_fam_id), None)
    if fam_block:
        fam_block.add_tag(1, "CHIL", f"@{viktor_id}@")

    # Add image to Loa's profile
    loa_block = next((b for b in blocks if b.id == loa_id), None)
    if loa_block:
        loa_block.add_tag(1, "OBJE")
        loa_block.add_tag(2, "FILE", "images/loa_profile.jpg")
        loa_block.add_tag(2, "TITL", "Ólafía Rósbjörg Ingólfsdóttir")

    # Move TRLR
    trailer = next((b for b in blocks if b.type == 'TRLR'), None)
    if trailer:
        blocks.remove(trailer)
        blocks.append(trailer)

    save_gedcom_blocks(blocks, 'loa.ged')
    print("loa.ged updated with son Viktor Ingi Jónsson and profile picture!")

if __name__ == '__main__':
    add_loa_children()
