import shutil, os

# Backup current active as v1 if not exists
if not os.path.exists("ancestry_v1.db"):
    shutil.copy2("ancestry.db", "ancestry_v1.db")

# Activate V2 by copying ancestry_v2.db -> ancestry.db
shutil.copy2("ancestry_v2.db", "ancestry.db")

print("==========================================================================")
print("🌟 V2 ER NÚNA VIRKI GAGNAGRUNNURINN Í KERFINU!")
print("   - ancestry_v1.db er varðveittur óbreyttur sem öryggisafrit.")
print("   - ancestry.db er núna byggður 100% á V2.")
print("==========================================================================")
