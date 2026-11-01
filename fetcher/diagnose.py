"""Diagnose: Wie stehen die Produkte auf den Aldi-Süd-Kategorieseiten? (Dauerpreise fanden 0 Artikel)"""
import json
import re

import fetch_dauerpreise as d
import fetch_offers as f

start = f.http(d.BASE + "/") or ""
cats = sorted(set(d.CAT.findall(start)))
print("Kategorien Startseite:", len(cats), cats[:8])
for path in [c for c in cats if "milch" in c.lower() or "molkerei" in c.lower()][:1] + cats[:2]:
    url = d.BASE + path
    h = f.http(url) or ""
    print(f"\n=== {url}: {len(h)} Zeichen")
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    print("NUXT_DATA:", bool(m), len(m.group(1)) if m else 0)
    if m:
        data = json.loads(m.group(1))
        withsku = [v for v in data if isinstance(v, dict) and "sku" in v]
        print("dicts mit sku:", len(withsku), "Beispiel-Schlüssel:", sorted(withsku[0].keys())[:40] if withsku else None)
        keys = {}
        for v in data:
            if isinstance(v, dict):
                for k in v:
                    keys[k] = keys.get(k, 0) + 1
        print("häufige Schlüssel:", sorted(keys.items(), key=lambda x: -x[1])[:60])
        if withsku:
            i = data.index(withsku[0])
            print("aufgelöst:", json.dumps(f.nuxt_resolve(data, i), ensure_ascii=False)[:1500])
    for pat in (r'"@type"\s*:\s*"Product"', r'data-sku', r'product-tile', r'/produkt/', r'amountRelevant', r'comparisonDisplay', r'\?page=\d+'):
        print(pat, len(re.findall(pat, h)))
    i = h.find("/produkt/")
    print("Ausschnitt:", h[max(0, i - 600):i + 600].replace("\n", " ") if i >= 0 else "-")
    print("aldi_items:", len(f.aldi_items(h)))
