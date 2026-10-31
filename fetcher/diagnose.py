"""Diagnose (nur von Hand): Weitere öffentliche Quellen für die Prospekte der NÄCHSTEN Woche
(Rewe, Edeka, dm, Aldi Süd). Prüft robots.txt und listet gefundene Prospekte mit Datum."""
import re
import urllib.request

import fetch_offers as f


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", "FEHLER " + str(e)[:80]), ""


def robots(host):
    st, t = get(f"https://{host}/robots.txt")
    print(f"\n=== robots.txt {host} ({st})")
    block, show = [], False
    for line in t.splitlines():
        l = line.strip()
        if l.lower().startswith("user-agent"):
            show = l.split(":", 1)[1].strip() in ("*",)
        if show and l:
            block.append(l)
    print("\n".join(block[:40]) or "(keine Regeln für *)")


for host in ("www.discounto.de", "www.prospektangebote.de", "www.aldi-sued.de", "www.meinprospekt.de", "www.wogibtswas.de"):
    robots(host)

DATE = r"(20\d\d-\d\d-\d\d)"
for name, url in [
    ("discounto ALDI", "https://www.discounto.de/Prospekte/Anbieter:aldi_sued/"),
    ("discounto REWE", "https://www.discounto.de/Prospekte/Anbieter:REWE/"),
    ("discounto dm", "https://www.discounto.de/Prospekte/Anbieter:dm/"),
    ("discounto EDEKA", "https://www.discounto.de/Prospekte/Anbieter:EDEKA/"),
    ("prospektangebote ALDI", "https://www.prospektangebote.de/geschaefte/aldi-sud/prospekte-angebote"),
    ("prospektangebote REWE", "https://www.prospektangebote.de/geschaefte/rewe/prospekte-angebote"),
    ("prospektangebote dm", "https://www.prospektangebote.de/geschaefte/dm/prospekte-angebote"),
    ("prospektangebote EDEKA", "https://www.prospektangebote.de/geschaefte/edeka/prospekte-angebote"),
    ("aldi-sued Startseite", "https://www.aldi-sued.de/de/homepage.html"),
    ("aldi-sued Prospekte", "https://www.aldi-sued.de/de/prospekte.html"),
    ("aldi-sued Angebote", "https://www.aldi-sued.de/de/angebote.html"),
]:
    st, h = get(url)
    links = sorted(set(re.findall(r'href="([^"]*(?:rospekt|andzettel|angebote)[^"]*)"', h)))
    dated = sorted(set(re.findall(r'href="([^"]*' + DATE + r'[^"]*)"', h)))
    print(f"\n=== {name} ({st}) {url}  Größe {len(h)}")
    for l in dated[:15]:
        print("  DATUM-LINK", l[0][:160])
    for l in links[:25]:
        print("  LINK", l[:160])
    for m in re.finditer(r"(?:gültig|Gültig|ab|vom)[^<>]{0,40}?(\d{1,2}\.\d{1,2}\.(?:20\d\d)?)[^<>]{0,30}", h):
        print("  TEXT", m.group(0)[:100])
        break
