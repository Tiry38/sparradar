"""Diagnose (nur von Hand): Welche alten Angebotsseiten (ab Aug. 2026) hat das Internet-Archiv?
Prüft robots.txt von web.archive.org und zählt Schnappschüsse über die öffentliche CDX-Schnittstelle."""
import json
import time
import urllib.parse
import urllib.request
import urllib.robotparser

import fetch_offers as f

PATS = [
    "aldi-sued.de/de/angebote*",
    "www.kaufda.de/Woerth-am-Rhein/REWE/p-r101",
    "www.kaufda.de/Woerth-am-Rhein/Netto-Marken-Discount/p-r9",
    "www.kaufda.de/Jockgrim/EDEKA/p-r107",
    "www.kaufda.de/Woerth-am-Rhein/Lidl/p-r74",
    "www.kaufda.de/Woerth-am-Rhein/dm-drogerie-markt/p-r104",
    "www.kaufda.de/Lidl/Sortiment/*",
    "www.kaufda.de/REWE/Sortiment/*",
    "www.kaufda.de/Netto-Marken-Discount/Sortiment/*",
    "www.kaufda.de/Karlsruhe/Angebote/*",
    "www.lidl.de/c/billiger-montag/*",
    "www.lidl.de/q/api/search*",
    "www.lidl.de/*",
    "prospektewoche.de/images/prospekte/rewe/*",
    "www.prospektewoche.de/*",
]


def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": f.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def robots(host, path):
    try:
        txt = get(f"https://{host}/robots.txt")
    except Exception as e:
        print(host, "robots.txt:", str(e)[:60], "-> keine Regeln"); return True
    rp = urllib.robotparser.RobotFileParser(); rp.parse(txt.splitlines())
    ok = rp.can_fetch(f.UA, f"https://{host}{path}"); print(host, path, "erlaubt:", ok)
    lines = [l for l in txt.splitlines() if l.lower().startswith(("disallow", "user-agent", "crawl"))]
    print("   ", " | ".join(lines[:30])); return ok


robots("web.archive.org", "/cdx/search/cdx?url=x")
robots("world.openfoodfacts.org", "/cgi/search.pl?search_terms=x&json=1")
robots("world.openfoodfacts.org", "/api/v2/search?brands_tags=x")
robots("search.openfoodfacts.org", "/search?q=x")
for u in ["https://search.openfoodfacts.org/search?q=IronMaxx%20SqueeBarista%20Caramel&page_size=5&fields=product_name,brands,code,image_front_small_url,image_small_url,images,lang",
          "https://world.openfoodfacts.org/cgi/search.pl?search_terms=IronMaxx%20SqueeBarista&json=1&page_size=5&fields=product_name,brands,code,image_front_small_url"]:
    try:
        print("\nOFF", u[:60], get(u)[:1500])
    except Exception as e:
        print("OFF FEHLER", u[:60], str(e)[:80])
    time.sleep(3)

for p in PATS:
    q = urllib.parse.urlencode({"url": p, "from": "20260801", "output": "json",
                                "fl": "timestamp,original,statuscode", "filter": "statuscode:200", "limit": "5000"})
    try:
        rows = json.loads(get("https://web.archive.org/cdx/search/cdx?" + q) or "[]")[1:]
    except Exception as e:
        print(p, "FEHLER", str(e)[:80]); time.sleep(5); continue
    days = sorted({r[0][:8] for r in rows})
    urls = {r[1] for r in rows}
    print(f"\n== {p}: {len(rows)} Schnappschüsse, {len(urls)} Adressen, {len(days)} Tage")
    print("   Tage:", " ".join(days[:80]))
    for u in sorted(urls)[:25]:
        print("   ", u[:150])
    time.sleep(5)
