"""SparRadar: Preisverlauf rückwirkend füllen (Kevins Wunsch 01.11.: ca. 2 Monate zurück, für jeden Artikel).

Quelle: das Internet-Archiv (web.archive.org, robots.txt erlaubt es, öffentliche CDX-Schnittstelle). Dort liegen
alte Schnappschüsse der öffentlichen kaufDA-Sortiment-Seiten von Lidl und Netto (bundesweit gleiche Prospektpreise)
und, falls vorhanden, der Aldi-Süd-Angebotsseiten. Gelesen wird mit denselben Auswertungen wie beim täglichen Abruf.
Nur echte, damals veröffentlichte Angebotspreise – nichts wird geschätzt. Rewe/Edeka bewusst nicht: deren Preise
sind regional und lassen sich auf alten Seiten nicht dem Markt in Wörth/Jockgrim zuordnen.

Ablauf (Workflow „Preisverlauf nachtragen“, nur von Hand):
  python backfill_history.py --collect rows.json   # Schnappschüsse lesen (setzt nach Abbruch fort, Stand in backfill-state.json)
  python backfill_history.py --merge rows.json     # Zeilen in docs/data/history.json einsortieren
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_offers as f  # noqa: E402

FROM, TO = os.environ.get("SR_BF_FROM", "20260901"), os.environ.get("SR_BF_TO", "20261031")
MAX_MIN = float(os.environ.get("SR_BF_MINUTES", "320"))
PAUSE = 2.0  # Sekunden zwischen zwei Abrufen beim Internet-Archiv
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backfill-state.json")
PATTERNS = [
    ("kd", "www.kaufda.de/Lidl/Sortiment/*"),
    ("kd", "www.kaufda.de/Netto-Marken-Discount/Sortiment/*"),
    ("kd", "www.kaufda.de/Woerth-am-Rhein/Lidl/p-r74"),
    ("kd", "www.kaufda.de/Woerth-am-Rhein/Netto-Marken-Discount/p-r9"),
    ("aldi", "www.aldi-sued.de/de/angebote*"),
    ("aldi", "aldi-sued.de/de/angebote*"),
]
KEEP = {"lidl", "netto", "aldi"}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def get(u, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": f.UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            wait = 60 if e.code == 429 else 10 * (i + 1)
            log("   ! HTTP", e.code, "warte", wait, "s")
            time.sleep(wait)
        except Exception as e:  # Zeitüberschreitung, Verbindungsabbruch
            log("   !", str(e)[:80])
            time.sleep(10 * (i + 1))
    return None


def cdx(pattern):
    """Alle Schnappschüsse (Status 200) im Zeitraum, seitenweise über den Fortsetzungs-Schlüssel."""
    out, key = [], None
    while True:
        q = {"url": pattern, "from": FROM, "to": TO, "output": "json", "fl": "timestamp,original,digest",
             "filter": "statuscode:200", "collapse": "digest", "limit": "5000", "showResumeKey": "true"}
        if key:
            q["resumeKey"] = key
        txt = get("https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(q))
        time.sleep(PAUSE)
        rows = json.loads(txt) if txt and txt.strip() else []
        rows = rows[1:] if rows else []
        key = None
        if len(rows) >= 2 and rows[-2] == []:  # [..., [], [resumeKey]]
            key = rows[-1][0]
            rows = rows[:-2]
        out += [r for r in rows if len(r) >= 2]
        if not key:
            return out


def offers_kd(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
    items = ((pi.get("offers") or {}).get("main") or {}).get("items") or []
    out = []
    for it in items:
        try:
            o = f.kd_offer(it)
        except Exception:
            o = None
        if o and o.get("s") in KEEP:
            out.append(o)
    return out


def offers_aldi(html, url):
    m = re.search(r"/angebote/(20\d\d-\d\d-\d\d)", url)
    out = []
    for it in f.aldi_items(html, m.group(1) if m else None):
        pr = it.get("price") or {}
        amount = pr.get("amountRelevant") or pr.get("amount")
        if not amount:
            continue
        brand = it.get("brandName")
        try:
            o = f.offer("aldi", it.get("name"), amount / 100, brand=None if brand in ("BIO", "no-brand") else brand,
                        desc=it.get("sellingSize") or "", start=it.get("onSaleDate"), src="aldi-sued.de")
        except Exception:
            o = None
        if o:
            out.append(o)
    return out


def day_of(o, snap):
    """Preis gilt ab Prospektstart; liegt der weit vor dem Schnappschuss (Dauerangebot), zählt der Schnappschuss-Tag."""
    fr = str(o.get("from") or "")[:10]
    s = f"{snap[:4]}-{snap[4:6]}-{snap[6:8]}"
    if fr and fr <= s and (int(s.replace("-", "")) - int(fr.replace("-", ""))) <= 14:
        return fr
    return s


def collect(path):
    t0 = time.time()
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"done": [], "snaps": None}
    done = set(st["done"])
    rows = json.load(open(path)) if os.path.exists(path) else {}
    if st.get("snaps") is None:
        snaps = []
        for kind, pat in PATTERNS:
            got = cdx(pat)
            log(f"{pat}: {len(got)} Schnappschüsse")
            snaps += [[kind, r[0], r[1]] for r in got]
        st["snaps"] = snaps
        json.dump(st, open(STATE, "w"))
    todo = [s for s in st["snaps"] if f"{s[1]}|{s[2]}" not in done]
    log(f"Offen: {len(todo)} von {len(st['snaps'])} Schnappschüssen")
    n_new = 0
    for i, (kind, ts, url) in enumerate(todo):
        if (time.time() - t0) / 60 > MAX_MIN:
            log("Zeit um – nächster Lauf macht weiter")
            break
        html = get(f"https://web.archive.org/web/{ts}id_/{url}")
        time.sleep(PAUSE)
        offs = (offers_kd(html) if kind == "kd" else offers_aldi(html, url)) if html else []
        for o in offs:
            k = f"{o['s']}|{f.norm(o['n'])[:40]}"
            d = day_of(o, ts)
            cur = rows.setdefault(k, {})
            if d not in cur or o["p"] < cur[d]:
                cur[d] = o["p"]; n_new += 1
        done.add(f"{ts}|{url}")
        if i % 100 == 99:
            st["done"] = sorted(done); json.dump(st, open(STATE, "w")); json.dump(rows, open(path, "w"))
            log(f"  {i + 1}/{len(todo)} · {len(rows)} Artikel · {n_new} Preise")
    st["done"] = sorted(done)
    json.dump(st, open(STATE, "w"))
    json.dump(rows, open(path, "w"))
    left = len(st["snaps"]) - len(done)
    log(f"Fertig: {len(rows)} Artikel, {n_new} neue Preise, noch offen: {left}")
    print(f"left={left}")


def merge(path):
    rows = json.load(open(path)) if os.path.exists(path) else {}
    hist = f.load("history.json", {})
    added = 0
    for k, days in rows.items():
        cur = {d: p for d, p in hist.get(k, [])}
        for d, p in days.items():
            if d not in cur:
                cur[d] = p; added += 1
            elif p < cur[d]:
                cur[d] = p
        hist[k] = [[d, cur[d]] for d in sorted(cur)][-60:]
    f.save("history.json", hist)
    log(f"history.json: {added} Preise nachgetragen, {len(hist)} Artikel")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--collect":
        collect(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--merge":
        merge(sys.argv[2])
    else:
        print(__doc__)
