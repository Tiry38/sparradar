"""Diagnose (nur von Hand): dm-Aktionsseiten über den öffentlichen Inhalts-Dienst, den dm.de selbst lädt.
Kein Schlüssel, keine Anmeldung; robots.txt von content.services.dmtech.com existiert nicht (404 = keine Einschränkung)."""
import json
import re
import time
import urllib.request

import fetch_offers as f

CS = "https://content.services.dmtech.com/rootpage-dm-shop-de-de"


def get(path):
    try:
        req = urllib.request.Request(CS + path, headers={"User-Agent": f.UA, "Accept-Language": "de-DE", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"FEHLER {getattr(e, 'code', str(e)[:60])}"


t = get("/neu/aktionen")
print("Pfade:", sorted(set(re.findall(r'(?:https://www\.dm\.de)?(/neu/aktionen/[a-z0-9\-/]+)', t))))
d = json.loads(t)
for blk in d.get("mainData", []):
    if blk.get("type") in ("DMTeaserSlider", "DMBanner", "DMTeaserGroup"):
        print("\n---", blk["type"], json.dumps(blk)[:2500])
time.sleep(f.PAUSE)
for p in ("/ausverkauf", "/neu/limited-editions"):
    t = get(p)
    print(f"\n##### {p} {len(t)}")
    print(t[:200])
    for m in re.finditer(r'"type":"DMSearchProductGrid".{0,1500}', t):
        print("  Grid:", m.group(0)[:1500])
    time.sleep(f.PAUSE)
