import httpx
from datetime import datetime
d = datetime.now().strftime("%Y%m%d")
r = httpx.get(f"http://mis.nyiso.com/public/csv/pal/{d}pal.csv", timeout=15)
lines = r.text.strip().split("\n")
zones = set()
for line in lines[1:]:
    parts = line.replace('"', "").split(",")
    if len(parts) >= 5:
        zones.add(parts[2])
print("zones:", sorted(zones))
for line in lines[-30:]:
    if "Y.C" in line or "CAPITL" in line:
        print(line)
