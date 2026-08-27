import subprocess

log_file = "/home/sigurjonaxel/.gemini/antigravity-cli/brain/2ade16f4-7796-473f-b4fd-e73bf3c0ded8/.system_generated/tasks/task-8200.log"

with open(log_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

processed_names = []
for line in lines:
    if line.startswith("🔍 [SNJÖLL VEFRANNSÓKN]"):
        name = line.replace("🔍 [SNJÖLL VEFRANNSÓKN]", "").strip()
        processed_names.append(name)

print(f"=== STAÐAN Á NÝJU SNJÖLLU KEYRSLUNNI ===")
print(f"✅ Samtals búnir með NÝJU aðferðina: {len(processed_names)} / 677 einstaklingar")
print("\nSíðustu 10 einstaklingar sem voru að klárast rétt í þessu:")
for n in processed_names[-10:]:
    print(f" - ✓ {n}")
