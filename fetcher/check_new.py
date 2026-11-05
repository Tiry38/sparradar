"""SparRadar: Prospekt-Wächter (läuft jeden Tag, Fr–So und Mo früh alle 5 min, sonst alle 15 min; Cloudflare-Taktgeber).

Schaut nur auf die 5 kaufDA-Händlerseiten, 2 kaufDA-Sortimentseiten, prospektewoche.de (Rewe, Edeka) und die Aldi-Angebotsseite und meldet, ob dort
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
# Händlerseiten zeigen je Aufruf andere 16 zufällige Angebote (Edeka 16 von ~230, dm 16 von ~150, Lidl 16 von ~1000).
# Der Wächter lädt sie sowieso (bis zu alle 5 min) -> was dabei auftaucht und in der App noch fehlt, übernimmt er gleich
# (add_seen), für alle Märkte und ganz ohne zusätzliche Seitenaufrufe. Dazu die Angebote der Aldi-Angebotsseite und
# einmal pro Stunde die Aldi-Tagesseiten (Kevin 02.11.: auch bei den anderen Märkten tagsüber nach Neuem schauen).
GROW = tuple(f.KD_STORES)
SEEN = []


def future_marks(grow=False):
    """Alle künftigen Prospekte/Angebote, die gerade öffentlich sichtbar sind: {"rewe:2501...": "2026-11-02", ...}
    grow=True: dabei gesehene Angebote nach SEEN sammeln (für add_seen)."""
    today = dt.date.today().isoformat()
    marks = {}
    home = {}  # je Markt: Prospekt-IDs der eigenen Händlerseite
    for store, url in f.KD_STORES.items():
        h = f.http(url)
        time.sleep(f.PAUSE)
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
        if not m:
            continue
        pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
        br = pi.get("brochures") or {}
        f.note_online(br)
        home[store] = f._ids([br.get("viewer"), br.get("publisher")], set()) | f.local_flyers(store)
        f.KD_INFO.setdefault(url, {})["brochures"] = home[store]  # für kd_store (Scheck-In = Prospekt-ID der Wörther „EDEKA“-Seite)
        for key in ("viewer", "publisher"):  # nur Prospekte dieses Händlers, nicht die „sector“-Werbung anderer
            lst = (pi.get("brochures") or {}).get(key)
            for b in lst if isinstance(lst, list) else []:
                start = str((b or {}).get("validFrom") or "")[:10]
                if start >= today and not re.search(r"online", str(b.get("title") or ""), re.I):
                    marks[f"{store}:{b.get('id') or b.get('contentId')}"] = start
        for it in ((pi.get("offers") or {}).get("main") or {}).get("items") or []:
            start = str(it.get("validFrom") or "")[:10]
            if start >= today:
                pc = (it.get("parentContent") or {}).get("id")
                if pc:
                    marks[f"{store}:{pc}"] = start
            if grow and store in GROW and f.kd_store(it) == store:
                home[store].add(str((it.get("parentContent") or {}).get("id")))
                o = f.kd_offer(it)
                if o:
                    SEEN.append(o)
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
            # bundesweite Seite: nur Angebote aus den eigenen Prospekten (Händlerseite bzw. flyers.json) übernehmen
            if grow and f.kd_store(it) == store \
                    and str((it.get("parentContent") or {}).get("id")) in home.get(store, set()):
                o = f.kd_offer(it)
                if o:
                    SEEN.append(o)
    # Rewe-/Edeka-Vorschau: neue Woche bei prospektewoche.de (nur die Startseiten mit den Wochen-Reitern;
    # ob der Edeka-Prospekt zu Jockgrim passt, prüft erst der Abruf)
    for shop in ("rewe", "edeka"):
        h = f.http(f"{f.PW}/{shop}") or ""
        time.sleep(f.PAUSE)
        for t in re.findall(r'tab-dates">([^<]+)<', h):
            span = f.pw_dates(t, dt.date.today())
            if span and span[0] >= today:
                marks[f"{shop}-pw:{span[0]}"] = span[0]
    h = f.http("https://www.aldi-sued.de/de/angebote.html") or ""
    days = [(day, path) for day, path in f.aldi_days(h) if day >= today]
    for day, _ in days:  # Aldi-Tagesseiten der nächsten Woche (z. B. /angebote/2026-11-02)
        marks[f"aldi:{day}"] = day
    if grow:
        items = f.aldi_items(h)
        if dt.datetime.now(dt.timezone.utc).minute < 15:  # Tagesseiten nur einmal pro Stunde (je Seite 1 Aufruf)
            for day, path in days:  # mit Folgeseiten (je Seite nur 30 Artikel) + Rubrik Wochenangebote
                items += f.aldi_pages(f"https://www.aldi-sued.de{path}", day)
            items += f.aldi_pages(f.ALDI_WEEK)
        SEEN.extend(o for o in map(f.aldi_offer, items) if o)
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if m:
        data = json.loads(m.group(1))
        for i, v in enumerate(data):
            if isinstance(v, dict) and "onSaleDate" in v and "sku" in v:
                start = str(f.nuxt_resolve(data, i).get("onSaleDate") or "")[:10]
                if start >= today:
                    marks[f"aldi:{start}"] = start  # Aldi: je Starttag ein Merkmal
    return marks


def add_seen():
    """Gesehene Angebote, die in offers.json fehlen, übernehmen. „generated“ (= letzter kompletter Abruf) bleibt, nur
    „upd“ ändert sich -> die App lädt neu. Frühestens 10 min nach der letzten Änderung (ab 10 neuen), sonst nach 15 min,
    1–2 Artikel erst nach 60 min: nicht jeder Durchgang soll einen Commit machen (GitHub Pages baut je Push neu,
    empfohlen höchstens 10× pro Stunde). Rückgabe: Anzahl übernommen."""
    data = f.load("offers.json", {})
    old = data.get("offers") or []
    if len(old) < 30 or not SEEN:
        return 0
    have = {(o["s"], f.norm(o["n"])[:30], o["p"]) for o in old}
    ids = {o.get("id") for o in old}
    cand = [o for o in SEEN if (o["s"], f.norm(o["n"])[:30], o["p"]) not in have and o.get("id") not in ids]
    if not cand:
        f.log("Eingesammelt: nichts Neues", f"({len(SEEN)} Angebote angesehen)")
        return 0
    f.OLD_OFFERS[:] = old
    offers = f.finalize([dict(o) for o in old] + cand)
    new_ids = {o.get("id") for o in cand}
    got = [o for o in offers if o.get("id") in new_ids and o.get("id") not in ids]
    n = len(got)
    now = dt.datetime.now(dt.timezone.utc)
    try:
        gap = (now - dt.datetime.fromisoformat(data.get("upd") or data.get("generated"))).total_seconds() / 60
    except (TypeError, ValueError):
        gap = 999
    if not n:  # nur Doppel bestehender Karten (anders aufgeteilter Name, Sorten-/App-Doppel) -> finalize führt zusammen
        f.log("Eingesammelt: nichts Neues", f"({len(SEEN)} Angebote angesehen, {len(cand)} davon Doppel)")
        return 0
    if gap < 10 or (n < 10 and gap < 15) or (n < 3 and gap < 60):
        f.log(f"Eingesammelt: {n} neue Angebote – warten auf mehr (letzte Änderung vor {gap:.0f} min)")
        return 0
    try:
        f.measure_images(offers)  # misst nur neue Bilder (bekannte Größen aus OLD_OFFERS)
    except Exception as e:
        f.log("  ! Bildprüfung fehlgeschlagen:", repr(e))
    counts = {}
    for o in offers:
        counts[o["s"]] = counts.get(o["s"], 0) + 1
    upd = now.isoformat(timespec="minutes")
    data.update({"upd": upd, "counts": counts, "offers": offers})
    f.save("offers.json", data)
    f.save("stand.json", {"generated": data.get("generated"), "upd": upd})
    by = {}
    for o in got:
        by[o["s"]] = by.get(o["s"], 0) + 1
    f.log(f"Eingesammelt: {n} neue Angebote übernommen {by} -> jetzt {counts}")
    return n


def main():
    marks = future_marks(grow="--snap" not in sys.argv and "--save" not in sys.argv)
    seen = f.load("prospekte.json", {})
    snap = os.path.join(os.environ.get("RUNNER_TEMP") or "/tmp", "sr-prospekte-start.json")
    if "--snap" in sys.argv:  # beim Start des Abrufs: was jetzt sichtbar ist, wird gleich abgerufen
        with open(snap, "w") as fh:
            json.dump(marks, fh)
        return
    if "--save" in sys.argv:
        if os.path.exists(snap):  # nur merken, was beim Start schon da war (später Erschienenes holt der nächste Abruf)
            with open(snap) as fh:
                marks = json.load(fh)
        f.save("prospekte.json", {k: v for k, v in {**seen, **marks}.items() if v >= dt.date.today().isoformat()})
        f.log("Prospekt-Wächter: gemerkt", len(marks))
        return
    new = sorted(k for k in marks if k not in seen)
    f.log("Prospekt-Wächter: künftige Prospekte", len(marks), "davon neu:", new or "keine")
    # Startet gleich der komplette Abruf (neuer Prospekt) oder läuft er schon (SR_ADD=0), nichts selbst schreiben
    added = add_seen() if not new and os.environ.get("SR_ADD") == "1" else 0
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as fh:
            fh.write(f"new={'true' if new else 'false'}\nadded={added}\n")


if __name__ == "__main__":
    main()
