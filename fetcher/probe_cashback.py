"""Einmaliger Test: Aufbau der Geld-zurück-Liste auf mystipendium.de (robots.txt erlaubt, Crawl-delay 10)."""
import urllib.request, re
UA = "SparRadar/1.0 (+https://tiry38.github.io/sparradar/)"
u = "https://www.mystipendium.de/geld/cashback-geld-zurueck-aktionen"
b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "replace")
i = b.find("Dove Refill")
print("POS", i, "LEN", len(b))
print(b[max(0, i - 3000): i + 5000])
print("\n\n=====KATEGORIEN=====")
for m in re.finditer(r"Tiernahrung", b): print(b[m.start() - 600: m.start() + 200].replace("\n", " ")[:800]); break
print("\n=====ANZAHL Einträge:", b.count("Einsendeschluss"), "| Zum Angebot:", b.count("Zum Angebot"))
for m in re.finditer(r'href="([^"]+)"[^>]*>\s*Zum Angebot', b): print("LINK", m.group(1)[:150])
