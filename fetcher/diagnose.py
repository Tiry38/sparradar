"""Einmalige Diagnose: Sortiment-Seiten je Markt bei kaufDA (Nur von Hand, wenige Abrufe.)"""
import json
import re
import time

import fetch_offers as f


def page(url):
    h = f.http(url)
    time.sleep(2)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
    if not m:
        return None
    return json.loads(m.group(1))["props"]["pageProps"]


for u in ["https://www.kaufda.de/Lidl/Sortiment/Kaffee", "https://www.kaufda.de/Woerth-am-Rhein/Lidl/Sortiment/Kaffee",
          "https://www.kaufda.de/Lidl/Sortiment/Tassimo", "https://www.kaufda.de/Lidl/Sortiment/Butter",
          "https://www.kaufda.de/Netto-Marken-Discount/Sortiment/Butter", "https://www.kaufda.de/REWE/Sortiment/Butter",
          "https://www.kaufda.de/EDEKA/Sortiment/Butter", "https://www.kaufda.de/dm-drogerie-markt/Sortiment/Shampoo",
          "https://www.kaufda.de/ALDI-SUED/Sortiment/Butter"]:
    p = page(u)
    if not p:
        print("X", u)
        continue
    pi = p.get("pageInformation") or {}
    main = (pi.get("offers") or {}).get("main") or {}
    items = main.get("items") or []
    pubs, br = {}, set()
    for it in items:
        pubs[it.get("publisherName")] = pubs.get(it.get("publisherName"), 0) + 1
        br.add((it.get("parentContent") or {}).get("id"))
    print("OK", u, "->", len(items), "von", main.get("totalItems"), pubs, "Prospekte:", len(br))
    for it in items[:4]:
        print("     ", it.get("title"), "|", (it.get("prices") or {}).get("mainPrice"), "|", it.get("validFrom", "")[:10], "-", it.get("validUntil", "")[:10])
    tc = (pi.get("template") or {}).get("content") or {}
    links = ((tc.get("OfferLinkbox") or {}).get("PublisherOfferLinkbox") or {}).get("links") or []
    if links:
        print("      weitere Themen:", [l.get("link_text") for l in links][:20])
