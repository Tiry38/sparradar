"""Einmalige Diagnose: Themen-Unterseiten je Markt bei kaufDA (Nur von Hand, wenige Abrufe.)"""
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


pp = page(f.KD_STORES["lidl"])
pi = pp.get("pageInformation") or {}
tc = (pi.get("template") or {}).get("content") or {}
links = ((tc.get("OfferLinkbox") or {}).get("PublisherOfferLinkbox") or {}).get("links") or []
print("Themen-Links auf der Lidl-Seite:", len(links))
for l in links[:20]:
    print("  ", json.dumps(l, ensure_ascii=False)[:200])
print("Produkte des Händlers:", json.dumps((pi.get("publisher") or {}).get("products", [])[:5], ensure_ascii=False)[:600])
tests = []
for l in links[:3]:
    u = l.get("url") or l.get("href") or l.get("link")
    if u:
        tests.append(u if u.startswith("http") else "https://www.kaufda.de" + u)
tests += ["https://www.kaufda.de/Woerth-am-Rhein/Lidl/Kaffee", "https://www.kaufda.de/Karlsruhe/Lidl/Kaffee",
          "https://www.kaufda.de/Woerth-am-Rhein/Angebote/Kaffee", "https://www.kaufda.de/Angebote/Tassimo"]
for u in tests:
    p = page(u)
    if not p:
        print("X", u, "-> keine Daten")
        continue
    main = ((p.get("pageInformation") or {}).get("offers") or {}).get("main") or {}
    pubs = {}
    for it in main.get("items") or []:
        pubs[it.get("publisherName")] = pubs.get(it.get("publisherName"), 0) + 1
    print("OK", u, "->", len(main.get("items") or []), "von", main.get("totalItems"), pubs)
