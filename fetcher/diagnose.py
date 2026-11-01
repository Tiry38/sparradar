"""Diagnose: Dauer- vs. Aktionsware auf den Aldi-Süd-Kategorieseiten (Verkaufsdatum, Abzeichen, Rabatt-Felder)"""
import collections
import time

import fetch_dauerpreise as d
import fetch_offers as f

start = f.http(d.BASE + "/") or ""
cats = sorted(set(d.CAT.findall(start)))
pick = [c for c in cats if any(w in c for w in ("milch", "butter", "brot", "kaffee", "nudeln", "hygiene", "wasch"))][:6]
print("Kategorien:", len(cats), pick)
dates = collections.Counter()
for path in pick:
    time.sleep(2)
    h = f.http(d.BASE + path) or ""
    its = f.aldi_items(h)
    print(f"\n=== {path}: {len(its)} Artikel")
    for it in its[:40]:
        pr = it.get("price") or {}
        od = str(it.get("onSaleDate") or "-")
        dates[od[:7]] += 1
        print(f"  {od} | {it.get('onSaleDateDisplay')} | nfs={it.get('notForSale')} | badges={[b.get('text') or b.get('name') or b for b in (it.get('badges') or [])][:3]}"
              f" | {pr.get('amountRelevantDisplay')} was={pr.get('wasPriceDisplay')} sav={pr.get('savingsDisplay')} | {it.get('brandName')} {it.get('name')}")
print("\nVerkaufsdatum (Monat):", dates.most_common(20))
