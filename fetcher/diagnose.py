"""Diagnose (nur von Hand): Wo stehen die Prospekte der NÄCHSTEN Woche von Rewe, Edeka und dm schon öffentlich?
Prüft robots.txt vieler Quellen und sucht auf Kandidaten-Seiten nach dem nächsten Wochenstart."""
import datetime as dt
import json
import re
import urllib.request

import fetch_offers as f

today = dt.date.today()
mon = today + dt.timedelta(days=(7 - today.weekday()) % 7 or 7)  # nächster Montag
iso, de1, de2 = mon.isoformat(), mon.strftime("%d.%m."), f"{mon.day}.{mon.month}."
print("Nächster Montag:", iso)


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", "FEHLER " + str(e)[:70]), url, ""


def robots(host):
    st, _, t = get(f"https://{host}/robots.txt")
    rules, on = [], False
    for line in t.splitlines():
        l = line.strip()
        if l.lower().startswith("user-agent"):
            on = l.split(":", 1)[1].strip() == "*"
        elif on and l.lower().startswith(("disallow", "allow")):
            rules.append(l)
    print(f"ROBOTS {host} ({st}): " + " | ".join(rules[:25]))


for host in ("www.rewe.de", "www.edeka.de", "www.dm.de", "www.marktguru.de", "www.kimbino.de", "www.wogibtswas.de",
             "wogibtswas.de", "www.prospektmaschine.de", "www.prospekte.de", "www.meinprospekt.de", "www.kaufda.de"):
    robots(host)


def scan(name, url):
    st, final, h = get(url)
    hits = sorted(set(m.group(0) for m in re.finditer(r".{0,60}(?:" + re.escape(iso) + "|" + re.escape(de1) + r")(?:20\d\d)?.{0,60}", h)))
    print(f"\n=== {name} ({st}) {final} Größe {len(h)} Treffer {len(hits)}")
    for x in hits[:6]:
        print("   ", re.sub(r"\s+", " ", x)[:150])
    return h


# kaufDA: Rewe/Edeka/dm in anderen Städten (vielleicht früher freigeschaltet) + Händlerübersicht
for city in ("Karlsruhe", "Landau-in-der-Pfalz", "Kandel", "Woerth-am-Rhein", "Mannheim", "Stuttgart", "Berlin"):
    for slug, code in (("REWE", "p-r101"), ("EDEKA", "p-r107"), ("dm-drogerie-markt", "p-r104")):
        h = get(f"https://www.kaufda.de/{city}/{slug}/{code}")[2]
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
        if not m:
            continue
        pi = json.loads(m.group(1))["props"]["pageProps"].get("pageInformation") or {}
        fut = []
        for key in ("viewer", "publisher"):
            lst = (pi.get("brochures") or {}).get(key)
            for b in lst if isinstance(lst, list) else []:
                if str(b.get("validFrom") or "")[:10] >= (today + dt.timedelta(days=1)).isoformat():
                    fut.append((b.get("title"), str(b.get("validFrom"))[:10]))
        print(f"KAUFDA {city}/{slug}: künftige Prospekte {fut}")

for name, url in [
    ("kaufDA REWE Sortiment Kaffee", "https://www.kaufda.de/REWE/Sortiment/Kaffee"),
    ("kaufDA Edeka Sortiment Kaffee", "https://www.kaufda.de/Edeka/Sortiment/Kaffee"),
    ("kaufDA DM Sortiment Aktionen", "https://www.kaufda.de/DM/Sortiment/Aktionen"),
    ("meinprospekt Wörth REWE", "https://www.meinprospekt.de/woerth-am-rhein/rewe"),
    ("meinprospekt Jockgrim EDEKA", "https://www.meinprospekt.de/jockgrim/edeka"),
    ("meinprospekt Wörth dm", "https://www.meinprospekt.de/woerth-am-rhein/dm-drogerie-markt"),
    ("marktguru REWE", "https://www.marktguru.de/r/rewe"),
    ("marktguru EDEKA", "https://www.marktguru.de/r/edeka"),
    ("marktguru dm", "https://www.marktguru.de/r/dm"),
    ("kimbino REWE", "https://www.kimbino.de/rewe/"),
    ("kimbino EDEKA", "https://www.kimbino.de/edeka/"),
    ("kimbino dm", "https://www.kimbino.de/dm/"),
    ("wogibtswas REWE", "https://wogibtswas.de/rewe"),
    ("prospektmaschine REWE", "https://www.prospektmaschine.de/rewe/"),
    ("dm Aktionen", "https://www.dm.de/aktionen"),
    ("rewe Angebote", "https://www.rewe.de/angebote/"),
]:
    scan(name, url)
