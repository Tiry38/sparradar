"""SparRadar: Prospekt-Wächter (läuft Do–So alle 2 Stunden, .github/workflows/prospekte.yml).

Schaut nur auf die 5 kaufDA-Händlerseiten, 2 kaufDA-Sortimentseiten, prospektewoche.de/rewe und die Aldi-Angebotsseite und meldet, ob dort
ein Prospekt bzw. Angebote mit Startdatum ab heute stehen (auch montags erscheinende Prospekte, die am selben Tag starten), die SparRadar noch nicht abgerufen hat.
Nur dann startet der Workflow den kompletten Abruf (fetch_offers.py). So stehen die Angebote der nächsten
Woche so früh wie möglich in der App, ohne die Quellen ständig komplett abzufragen.

Aufruf: python check_new.py          -> schreibt new=true/false nach $GITHUB_OUTPUT
        python check_new.py --save   -> merkt sich die aktuell sichtbaren künftigen Prospekte (nach dem Abruf)
"""
import datetime as dt
import json
import os
import re
import sys
import time

import fetch_offers as f

STATE = os.path.join(f.DATA, "prospekte.json")


def future_marks():
    """Alle künftigen Prospekte/Angebote, die gerade öffentlich sichtbar sind: {"rewe:2501...": "2026-11-02", ...}"""
    today = dt.date.today().isoformat()
    marks = {}
    for store, url in f.KD_STORES.items():
        h = f.http(url)
        time.sleep(f.PAUSE)
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
        if not m:
            continue
        pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
        for key in ("viewer", "publisher"):  # nur Prospekte dieses Händlers, nicht die „sector“-Werbung anderer
            lst = (pi.get("brochures") or {}).get(key)
            for b in lst if isinstance(lst, list) else []:
                start = str((b or {}).get("validFrom") or "")[:10]
                if start >= today:
                    marks[f"{store}:{b.get('id') or b.get('contentId')}"] = start
        for it in ((pi.get("offers") or {}).get("main") or {}).get("items") or []:
            start = str(it.get("validFrom") or "")[:10]
            if start >= today:
                pc = (it.get("parentContent") or {}).get("id")
                if pc:
                    marks[f"{store}:{pc}"] = start
    # Edeka/Rewe: Vorschau-Prospekte der nächsten Woche erscheinen zuerst auf den Sortiment-Seiten (gleiche Händler-Kennung)
    for store, slug, pub in (("edeka", "Edeka", "DE-220164"), ("rewe", "REWE", "DE-1062")):
        h = f.http(f"https://www.kaufda.de/{slug}/Sortiment/Kaffee")
        time.sleep(f.PAUSE)
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
        if not m:
            continue
        pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
        for it in ((pi.get("offers") or {}).get("main") or {}).get("items") or []:
            start = str(it.get("validFrom") or "")[:10]
            if start >= today and it.get("publisherId") == pub:
                marks[f"{store}:{(it.get('parentContent') or {}).get('id')}"] = start
    # Rewe-Vorschau: neue Woche bei prospektewoche.de (nur die Startseite mit den Wochen-Reitern)
    h = f.http(f"{f.PW}/rewe") or ""
    time.sleep(f.PAUSE)
    for t in re.findall(r'tab-dates">([^<]+)<', h):
        span = f.pw_dates(t, dt.date.today())
        if span and span[0] >= today:
            marks[f"rewe-pw:{span[0]}"] = span[0]
    h = f.http("https://www.aldi-sued.de/de/angebote.html") or ""
    for day, _ in f.aldi_days(h):  # Aldi-Tagesseiten der nächsten Woche (z. B. /angebote/2026-11-02)
        if day >= today:
            marks[f"aldi:{day}"] = day
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if m:
        data = json.loads(m.group(1))
        for i, v in enumerate(data):
            if isinstance(v, dict) and "onSaleDate" in v and "sku" in v:
                start = str(f.nuxt_resolve(data, i).get("onSaleDate") or "")[:10]
                if start >= today:
                    marks[f"aldi:{start}"] = start  # Aldi: je Starttag ein Merkmal
    return marks


def main():
    marks = future_marks()
    seen = f.load("prospekte.json", {})
    if "--save" in sys.argv:
        f.save("prospekte.json", {k: v for k, v in {**seen, **marks}.items() if v >= dt.date.today().isoformat()})
        f.log("Prospekt-Wächter: gemerkt", len(marks))
        return
    new = sorted(k for k in marks if k not in seen)
    f.log("Prospekt-Wächter: künftige Prospekte", len(marks), "davon neu:", new or "keine")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"new={'true' if new else 'false'}\n")


if __name__ == "__main__":
    main()
