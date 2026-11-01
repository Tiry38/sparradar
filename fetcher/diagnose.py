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


rp = urllib.robotparser.RobotFileParser()
rp.parse(get("https://web.archive.org/robots.txt").splitlines())
print("robots cdx erlaubt:", rp.can_fetch(f.UA, "https://web.archive.org/cdx/search/cdx?url=x"))
print("robots web erlaubt:", rp.can_fetch(f.UA, "https://web.archive.org/web/2026id_/https://www.aldi-sued.de/"))

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
