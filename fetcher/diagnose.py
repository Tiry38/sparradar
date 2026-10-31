"""Diagnose (nur von Hand): Wo stehen dm-Angebote für nächste Woche? (meinprospekt, kaufDA, dm.de, Portale)"""
import collections
import json
import re
import urllib.parse
import urllib.request
import urllib.robotparser

import fetch_offers as f


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", str(e)[:60]), ""


RP = {}


def allowed(url):
    p = urllib.parse.urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in RP:
        st, txt = get(base + "/robots.txt")
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(txt.splitlines())
        RP[base] = rp
        print(f"\n##### {base}/robots.txt {st}\n" + "\n".join(l for l in txt.splitlines() if l.strip() and not l.startswith("#"))[:1500])
    return RP[base].can_fetch(f.UA, url)


def nd(h):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
    return json.loads(m.group(1)) if m else {}


def walk(o, found, path=""):
    if isinstance(o, dict):
        if ("validFrom" in o or "validUntil" in o or "validTo" in o) and ("title" in o or "name" in o or "productName" in o):
            found.append(o)
        for k, v in o.items():
            walk(v, found, path + "." + k)
    elif isinstance(o, list):
        for v in o:
            walk(v, found, path)


def show(label, url):
    ok = allowed(url)
    st, h = get(url) if ok else ("robots-verboten", "")
    print(f"\n=== {label} {url} erlaubt={ok} status={st} len={len(h)}")
    if not h:
        return
    found = []
    walk(nd(h), found)
    c = collections.Counter((str(x.get("validFrom"))[:10], str(x.get("validUntil") or x.get("validTo"))[:10],
                             x.get("publisherName") or x.get("type")) for x in found)
    print("  Zeiträume:", c.most_common(15))
    for x in found[:6]:
        print("   ·", {k: x.get(k) for k in ("title", "name", "brandName", "publisherName", "validFrom", "validUntil", "type") if k in x})
    print("  Datumsangaben im Text:", collections.Counter(re.findall(r"\d\d\.\d\d\.20\d\d", h)).most_common(10))


show("meinprospekt dm", "https://www.meinprospekt.de/dm-de")
show("meinprospekt dm Karlsruhe", "https://www.meinprospekt.de/karlsruhe/dm-de")
show("kaufDA dm Wörth", f.KD_STORES.get("dm", "https://www.kaufda.de/Woerth-am-Rhein/dm-drogerie-markt/p-r104"))
show("kaufDA dm Karlsruhe", "https://www.kaufda.de/Karlsruhe/dm-drogerie-markt/p-r104")
show("kaufDA dm Geschäfte", "https://www.kaufda.de/Geschaefte/DM")
for u in ("https://www.dm.de/", "https://www.dm.de/angebote", "https://www.dm.de/aktionen", "https://www.dm.de/prospekt",
          "https://www.dm.de/services/services-im-markt/prospekt", "https://www.dm.de/tipps-und-trends", "https://www.dm.de/sitemap.xml",
          "https://www.prospektguru.de/prospekt/dm", "https://www.marktguru.de/rp/dm-drogerie-markt-prospekte",
          "https://www.kimbino.de/dm-drogerie/", "https://www.prospektangebote.de/geschaefte/dm-prospekte.html",
          "https://onlineprospekt.com/prospekte/dm/", "https://www.wogibtswas.de/dm-drogerie-markt"):
    ok = allowed(u)
    st, h = get(u) if ok else ("robots-verboten", "")
    print(f"\n--- {u} erlaubt={ok} {st} {len(h)}")
    if h:
        print("  Daten:", collections.Counter(re.findall(r"\d\d\.\d\d\.(?:20)?\d\d", h)).most_common(10))
        print("  Links:", sorted(set(re.findall(r'href="([^"]*(?:angebot|aktion|prospekt|leaflet|brochure)[^"]*)"', h, re.I)))[:25])
        print("  JSON-LD:", [m[:300] for m in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S)][:3])
