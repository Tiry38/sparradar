"""Diagnose (nur von Hand): dm.de-Aktionsseiten (/neu/aktionen) über den öffentlichen Inhalts-Dienst, den dm.de selbst lädt.
Kein Schlüssel, keine Anmeldung; robots.txt von content.services.dmtech.com existiert nicht (404 = keine Einschränkung)."""
import json
import re
import urllib.request

import fetch_offers as f


def get(url, accept="application/json"):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f.UA, "Accept-Language": "de-DE", "Accept": accept})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", str(e)[:60]), ""


for path in ("/neu/aktionen", "/neu", "/neu/aktionen/lego-duplo-3547552"):
    for url in (f"https://content.services.dmtech.com/rootpage-dm-shop-de-de{path}",
                f"https://content.services.dmtech.com/rootpage-dm-shop-de-de{path}?json",
                f"https://content.services.dmtech.com/rootpage-dm-shop-de-de{path}/?view=json"):
        st, t = get(url)
        print(f"\n=== {url} {st} {len(t)}")
        if t:
            print("  ", t[:1500].replace("\n", " "))
            print("  Daten:", sorted(set(re.findall(r"20\d\d-\d\d-\d\d|\d\d\.\d\d\.20\d\d", t)))[:20])
            print("  Preise:", re.findall(r'"(?:price|value|formattedPrice)"\s*:\s*"?[\d.,]+', t)[:10])
            break
