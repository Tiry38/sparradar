"""Diagnose: Stehen auf den Aldi-Süd-Produktseiten (Sitemap) Normalpreise? Wie viele Seiten? Was erlaubt robots.txt?"""
import collections
import json
import re
import time

import fetch_offers as f
import fill_images as fi

print("=== robots.txt Aldi ===")
print((f.http("https://www.aldi-sued.de/robots.txt") or "")[:3000])
time.sleep(2)
urls = fi.sitemap_urls(fi.SITEMAPS["aldi"], r"/produkt/")
print("\nProduktseiten in der Sitemap:", len(urls))
c = collections.Counter(u.split("/")[3] if len(u.split("/")) > 3 else "" for u in urls)
print("Pfade:", c.most_common(5))
want = [u for u in urls if re.search(r"milch|butter|kaffee|katzen|joghurt|nudel|toilett", u)][:6] or urls[:6]
for u in want:
    time.sleep(2)
    t = time.time()
    h = f.http(u) or ""
    print(f"\n--- {u} ({time.time() - t:.1f}s, {len(h)} Zeichen)")
    items = f.aldi_items(h)
    print("NUXT-Artikel:", len(items))
    for it in items[:2]:
        pr = it.get("price") or {}
        print("  ", it.get("name"), "|", it.get("brandName"), "| sku", it.get("sku"), "|", json.dumps(pr, ensure_ascii=False)[:400])
        print("   keys:", sorted(it.keys())[:40])
        print("   onSale", it.get("onSaleDate"), "| cats", [c.get("name") for c in it.get("categories") or [] if isinstance(c, dict)][:6])
    for m in re.finditer(r'"@type"\s*:\s*"Offer".{0,300}', h):
        print("  JSON-LD:", m.group(0)[:300])
        break
    for m in list(re.finditer(r"\d+,\d\d\s*(?:€|&euro;)", h))[:3]:
        print("  €-Text:", re.sub(r"\s+", " ", h[max(0, m.start() - 120):m.end() + 40]))
# Kategorie-Seiten (viele Produkte auf einer Seite)?
time.sleep(2)
home = f.http("https://www.aldi-sued.de/") or ""
cats = sorted(set(re.findall(r'href="(/produkte/[^"#?]+)"', home)))
print("\nKategorie-Links auf der Startseite:", len(cats), cats[:30])
for p in cats[:3]:
    time.sleep(2)
    h = f.http("https://www.aldi-sued.de" + p) or ""
    items = f.aldi_items(h)
    print(f"  {p}: {len(h)} Zeichen, NUXT-Artikel {len(items)}",
          [(i.get("name"), (i.get("price") or {}).get("amount")) for i in items[:4]])
    print("   Seitenlinks:", sorted(set(re.findall(r'href="([^"]*(?:page|seite)=\d+[^"]*)"', h)))[:5])
