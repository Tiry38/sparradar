"""Diagnose: Aldi-Dauerpreise – fehlen Kategorien (Obst & Gemüse) oder Folgeseiten (?page=)?"""
import re
import time

import fetch_dauerpreise as d
import fetch_offers as f

start = f.http(d.BASE + "/") or ""
time.sleep(2)
more = f.http(d.BASE + "/produkte") or ""
cats = sorted(set(d.CAT.findall(start)) | set(d.CAT.findall(more)))
print("Kategorien:", len(cats))
for c in cats:
    if re.search(r"obst|gemuese|frisch|milch|butter|brot|backwaren", c):
        print("  ", c)
# Obst/Gemüse-Links überhaupt auf der Seite?
print("obst-Links:", sorted(set(re.findall(r'href="([^"]*obst[^"]*)"', start + more)))[:15])

pick = [c for c in cats if re.search(r"obst|gemuese", c)][:2] + [c for c in cats if re.search(r"milchprodukte|kuehlregal", c)][:1] \
    + [c for c in cats if re.search(r"butter", c)][:1]
for path in pick:
    time.sleep(2)
    h = f.http(d.BASE + path) or ""
    its = f.aldi_items(h)
    print(f"\n=== {path}: {len(its)} Artikel, HTML {len(h)} Zeichen")
    print("  PAGE-Links:", d.PAGE.findall(h)[:8])
    print("  page= im HTML:", [h[max(0, m.start() - 80):m.end() + 20].replace("\n", " ") for m in re.finditer(r"page=\d", h)][:4])
    for k in ("totalCount", "total", "numFound", "pageCount", "totalPages", "hits"):
        mm = re.search(r'"' + k + r'"\s*[:,]\s*(\d+)', h)
        if mm:
            print(f"  {k}: {mm.group(1)}")
    for it in its[:25]:
        pr = it.get("price") or {}
        print(f"  {str(it.get('onSaleDate') or '-')[:10]} disc={it.get('discontinued')} | {pr.get('amountRelevantDisplay')} was={pr.get('wasPriceDisplay')}"
              f" sav={pr.get('savingsDisplay')} | {it.get('brandName')} {it.get('name')}")
