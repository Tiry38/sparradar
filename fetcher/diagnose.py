"""Diagnose (nur von Hand): Preisfelder von lidl.de bei reduzierten Artikeln (UVP / 30-Tage-Preis?)."""
import json

import fetch_offers as f

n = 0
for q in ("butter", "eis", "kaffee", "kissen"):
    raw = f.http(f"https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1&q={q}&fetchsize=60&offset=0")
    for it in json.loads(raw).get("items") or []:
        g = ((it.get("gridbox") or {}).get("data")) or {}
        pr = g.get("price") or {}
        if pr.get("oldPrice") or pr.get("discount"):
            n += 1
            print("LIDL", g.get("fullTitle"), json.dumps({"price": pr, "lidlPlus": g.get("lidlPlus")}, ensure_ascii=False)[:1200])
        if n >= 8:
            break
    if n >= 8:
        break
print("gefunden:", n)
