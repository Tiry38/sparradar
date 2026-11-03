"""Diagnose (03.11.): Hat das Internet-Archiv Schnappschüsse aus Oktober 2026 von Seiten mit Angebotspreisen?
(Kevin: Preisverlauf der letzten 2-3 Wochen nachtragen. Die kaufDA-Sortiment-Seiten Lidl/Netto gibt es nur vom September.)"""
import collections
import json
import time
import urllib.parse
import urllib.request

UA = "SparRadar/1.0 (+https://github.com/Tiry38/sparradar; private Angebots-App)"
PATTERNS = [
    "www.kaufda.de/Lidl/Sortiment/*", "www.kaufda.de/Netto-Marken-Discount/Sortiment/*", "www.kaufda.de/REWE/Sortiment/*",
    "www.kaufda.de/Edeka/Sortiment/*", "www.kaufda.de/DM/Sortiment/*", "www.kaufda.de/Mueller/Sortiment/*",
    "www.kaufda.de/Karlsruhe/*", "www.kaufda.de/Woerth-am-Rhein/*", "www.kaufda.de/Jockgrim/*", "www.kaufda.de/Angebote/*",
    "www.kaufda.de/Lidl", "www.kaufda.de/Aldi-Sued*", "www.meinprospekt.de/angebote/*", "www.meinprospekt.de/karlsruhe/*",
    "www.meinprospekt.de/jockgrim/*", "www.aldi-sued.de/de/angebote*", "www.aldi-sued.de/produkt/*", "www.lidl.de/p/*",
    "www.lidl.de/c/*", "www.lidl.de/q/*", "www.netto-online.de/*", "www.rewe.de/angebote/*", "www.prospektangebote.de/*",
    "www.prospektewoche.de/*", "www.marktguru.de/*", "www.discounto.de/*", "www.wogibtswas.de/*",
]
for pat in PATTERNS:
    q = urllib.parse.urlencode({"url": pat, "from": "20261005", "to": "20261031", "output": "json",
                                "fl": "timestamp,original,statuscode", "filter": "statuscode:200", "limit": "20000"})
    rows = None
    for i in range(3):
        try:
            req = urllib.request.Request("https://web.archive.org/cdx/search/cdx?" + q, headers={"User-Agent": UA})
            rows = json.loads(urllib.request.urlopen(req, timeout=120).read().decode() or "[]")[1:]
            break
        except Exception as e:
            print("  Fehler", pat, e)
            time.sleep(15 * (i + 1))
    if rows is None:
        print(f"=== {pat}: keine Antwort")
        continue
    days = collections.Counter(r[0][:8] for r in rows)
    print(f"=== {pat}: {len(rows)} Schnappschüsse, {len({r[1] for r in rows})} Seiten")
    print("   Tage:", " ".join(f"{d[6:8]}.{d[4:6]}:{n}" for d, n in sorted(days.items())))
    for r in rows[:4]:
        print("   z. B.", r[0], r[1][:120])
    time.sleep(3)
