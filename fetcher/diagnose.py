"""Einmalige Diagnose: Wie blättert kaufDA weiter? (Nur von Hand starten, wenige Abrufe.)"""
import json
import re
import time

import fetch_offers as f

URL = f.KD_STORES["netto"]


def ids(h):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
    if not m:
        return set(), None, None
    d = json.loads(m.group(1))
    pi = d["props"]["pageProps"].get("pageInformation") or {}
    main = (pi.get("offers") or {}).get("main") or {}
    return {it.get("id") for it in main.get("items") or []}, main.get("totalItems"), d.get("buildId")


h1 = f.http(URL); time.sleep(2)
a, total, build = ids(h1)
h1b = f.http(URL); time.sleep(2)
b, _, _ = ids(h1b)
print("Seite 1 zweimal: gleiche Angebote?", a == b, len(a), "von", total, "buildId", build)
for m in sorted(set(re.findall(r'<link[^>]+rel="(?:next|prev|canonical)"[^>]*>', h1 or "")))[:10]:
    print("LINK", m)
for m in sorted(set(re.findall(r'href="([^"]*(?:page|seite|offset|p=)[^"]*)"', h1 or "", re.I)))[:20]:
    print("HREF", m)
for m in sorted(set(re.findall(r'"(/api/[^"]{3,120})"', h1 or "")))[:20]:
    print("API", m)
for m in sorted(set(re.findall(r'(https?://[a-z0-9.-]*(?:bonial|kaufda)[a-z0-9.-]*/[^"\s]{0,80})', h1 or "")))[:40]:
    if "content-media" not in m and ".jpg" not in m and ".png" not in m:
        print("URL", m)
for q in ("?page=2", "?offset=16", "?p=2", "?seite=2"):
    hh = f.http(URL + q); time.sleep(2)
    s, t, _ = ids(hh)
    print(q, "->", len(s), "Angebote, neu gegenüber Seite 1:", len(s - a - b))
if build:
    path = URL.split("kaufda.de")[1]
    for q in ("", "?page=2"):
        raw = f.http(f"https://www.kaufda.de/_next/data/{build}/de-DE{path}.json{q}"); time.sleep(2)
        try:
            d = json.loads(raw or "")
            main = d["pageProps"]["pageInformation"]["offers"]["main"]
            s = {it.get("id") for it in main.get("items") or []}
            print("_next/data", q, "->", len(s), "neu:", len(s - a - b), "Schlüssel:", [k for k in main if k != "items"])
        except Exception as e:
            print("_next/data", q, "->", repr(e)[:120])
