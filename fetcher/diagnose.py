"""Diagnose (nur von Hand): dm – wer steckt hinter den Prospekten ab 02.11., was bietet dm.de selbst (Sitemaps, Content-Dienste)?"""
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
        print(f"\n##### {base}/robots.txt {st}\n" + "\n".join(l for l in txt.splitlines() if l.strip())[:800])
    return RP[base].can_fetch(f.UA, url)


# 1) kaufDA dm-Seite: Prospekte mit Herausgeber
st, h = get("https://www.kaufda.de/Woerth-am-Rhein/dm-drogerie-markt/p-r104")
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
pi = ((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {} if m else {}
for key, lst in (pi.get("brochures") or {}).items():
    for b in lst if isinstance(lst, list) else []:
        if isinstance(b, dict):
            print("KAUFDA", key, "|", b.get("title"), "|", str(b.get("validFrom"))[:10], "-", str(b.get("validUntil"))[:10], "|",
                  b.get("publisherName") or (b.get("publisher") or {}).get("name") if isinstance(b.get("publisher"), dict) else b.get("publisherName"),
                  b.get("publisherId"), b.get("type"))

# 2) dm.de Sitemaps
st, sm = get("https://www.dm.de/sitemap.xml")
print("\nDM SITEMAP", st, sm[:600])
subs = re.findall(r"<loc>([^<]+)</loc>", sm)
for u in subs[:12]:
    st, x = get(u)
    locs = re.findall(r"<loc>([^<]+)</loc>", x)
    hit = [l for l in locs if re.search(r"angebot|aktion|prospekt|coupon|rabatt|sale|neu|deal|spar", l, re.I)]
    print("  SUB", u, st, len(locs), hit[:25])

# 3) dm-Content-Dienste (laden die Inhalte von dm.de) – nur wenn robots.txt es erlaubt
for u in ("https://content.services.dmtech.com/rootpage-dm-shop-de-de/angebote",
          "https://content.services.dmtech.com/rootpage-dm-shop-de-de/aktionen",
          "https://content.services.dmtech.com/rootpage-dm-shop-de-de/",
          "https://product-search.services.dmtech.com/de/search/static?query=angebot",
          "https://www.dm.de/content/angebote"):
    ok = allowed(u)
    st, x = get(u) if ok else ("robots-verboten", "")
    print(f"\n--- {u} erlaubt={ok} {st} {len(x)}")
    if x:
        print("   ", x[:700].replace("\n", " "))
