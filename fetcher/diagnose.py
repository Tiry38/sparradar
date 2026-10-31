"""Diagnose (nur von Hand): Welche Preisfelder liefert Aldi Süd bei reduzierten Artikeln (UVP / 30-Tage-Preis?)."""
import json
import re

import fetch_offers as f

h = f.http("https://www.aldi-sued.de/de/angebote.html")
data = json.loads(re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S).group(1))
n = 0
for i, v in enumerate(data):
    if not (isinstance(v, dict) and "price" in v and "name" in v and "sku" in v):
        continue
    it = f.nuxt_resolve(data, i)
    pr = it.get("price") or {}
    if pr.get("wasPriceDisplay") or n < 2:
        n += 1
        print("ALDI", it.get("name"), json.dumps(pr, ensure_ascii=False)[:800])
        print("   weitere Felder:", sorted(k for k in it.keys()))
        for k, val in it.items():
            if isinstance(val, str) and re.search(r"uvp|30 tage|niedrigst|statt|streich", val, re.I):
                print("   TEXT", k, val[:200])
    if n >= 10:
        break
# Texte auf der Seite zu UVP / 30-Tage-Preis
for m in re.finditer(r"[^<>\"]{0,80}(?:UVP|30 Tage|niedrigste[rn]? Preis)[^<>\"]{0,80}", h):
    print("SEITE", m.group(0)[:200])
    n += 1
    if n > 25:
        break
