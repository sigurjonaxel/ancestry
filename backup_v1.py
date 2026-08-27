import shutil, os, datetime

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"ancestry_v1_backup_{timestamp}.db"
shutil.copy2("ancestry.db", backup_file)
shutil.copy2("ancestry.db", "ancestry_v1.db")

print(f"✅ V1 GAGNAGRUNNURINN HEFUR VERIÐ VISTAÐUR OG TRYGGÐUR:")
print(f"   - {backup_file} ({os.path.getsize(backup_file)} bytes)")
print(f"   - ancestry_v1.db ({os.path.getsize('ancestry_v1.db')} bytes)")
