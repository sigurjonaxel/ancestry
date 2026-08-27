log_file = "/home/sigurjonaxel/.gemini/antigravity-cli/brain/2ade16f4-7796-473f-b4fd-e73bf3c0ded8/.system_generated/tasks/task-8260.log"

with open(log_file, "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = re.findall(r"\[(\d+)/677\]\s*✓\s*\[([^\]]+)\]", text)

print(f"=== HEILDARKEYRSLA Á ÖLLUM 677 Í SIGURJÓNS TRÉ ===")
print(f"✅ Núverandi staða: {len(matches)} / 677 einstaklingar búnir")
print("\nSíðustu 10 einstaklingar sem voru að klárast:")
for idx, name in matches[-10:]:
    print(f" - [{idx}] {name}")
