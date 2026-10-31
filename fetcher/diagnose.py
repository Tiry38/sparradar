"""Einmalige Diagnose: Liefert kaufDA die Prospektseite unter /<Prospekt-ID>/zoomlarge_page_<Seite>.jpg?"""
import struct
import urllib.request

import fetch_offers as f


def size(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": f.UA}), timeout=30) as r:
            data = r.read()
    except Exception as e:
        return f"FEHLER {e}"
    i, w, h = 2, None, None
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        if data[i + 1] in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            break
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return f"OK {len(data) // 1024} KB, {w}x{h}"


import json
import re
h = f.http(f.KD_STORES["netto"])
d = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S).group(1))
pi = d["props"]["pageProps"]["pageInformation"]
for key in ("viewer", "publisher"):
    for b in (pi.get("brochures") or {}).get(key) or []:
        print("PROSPEKT", key, json.dumps({k: v for k, v in b.items() if k != "pages"}, ensure_ascii=False)[:500])
        for pg in (b.get("pages") or [])[:2]:
            print("   SEITE", json.dumps(pg, ensure_ascii=False)[:400])
        print("   Seiten in Liste:", len(b.get("pages") or []), "von", b.get("pageCount"))
it = pi["offers"]["main"]["items"][0]
pc = it["parentContent"]
print("ANGEBOT parentContent:", pc)
for q in ("?impolicy=SEO-BROCHURE-BOX-VIEWER", ""):
    for name in ("zoomlarge_page_%d.jpg", "page_%d.jpg"):
        u = f"https://content-media.bonial.biz/{pc['id']}/" + name % pc["page"]["number"] + q
        print(u, "->", size(u))
