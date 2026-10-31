"""Einmalige Diagnose: Edeka Jockgrim und dm direkt bei edeka.de / dm.de (Nur von Hand, wenige Abrufe.)"""
import json
import re
import time
import urllib.parse

import fetch_offers as f


def get(url, n=600):
    raw = f.http(url)
    time.sleep(2)
    print(f"\n=== {url}\n    -> {'FEHLER' if raw is None else str(len(raw)) + ' Zeichen'}")
    if raw:
        print("    ", raw[:n].replace("\n", " | "))
    return raw


get("https://www.edeka.de/robots.txt", 1500)
get("https://www.dm.de/robots.txt", 1500)
# Edeka: Marktsuche (öffentlich, so findet die Website die Märkte)
for u in ["https://www.edeka.de/api/marketsearch/markets?searchstring=Jockgrim",
          "https://www.edeka.de/api/marketsearch/markets?searchstring=76751"]:
    raw = get(u, 1500)
    try:
        d = json.loads(raw or "")
        ms = d.get("markets") or d
        for m in (ms if isinstance(ms, list) else [])[:5]:
            print("    MARKT", json.dumps(m, ensure_ascii=False)[:400])
    except Exception as e:
        print("    kein JSON", repr(e)[:80])
raw = get("https://www.edeka.de/eh/suedwest/maerkte/index.jsp", 300)
# dm: Aktionsseite und öffentliche Produktsuche
get("https://www.dm.de/aktionen", 800)
get("https://product-search.services.dmtech.com/de/search?query=angebot&pageSize=5&currentPage=0", 1500)
