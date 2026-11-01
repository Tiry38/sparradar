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
import gzip
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
MAX_MIN = float(os.environ.get("SR_BF_MINUTES", "40"))  # kurze Etappen: alle ~45 min landet etwas in der App
PAUSE = 2.0  # Sekunden zwischen zwei Abrufen beim Internet-Archiv
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backfill-state.json")
PATTERNS = [
    ("kd", "www.kaufda.de/Lidl/Sortiment/*"),
    ("kd", "www.kaufda.de/Netto-Marken-Discount/Sortiment/*"),
]  # Händlerseiten Wörth und Aldi-Angebotsseiten: im Archiv nicht vorhanden (geprüft 01.11.)
KEEP = {"lidl", "netto", "aldi"}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def get(u, tries=2, timeout=25):
    """Kurze Wartezeit, wenige Versuche: Das Archiv antwortet entweder in Sekunden oder gar nicht (dann nächste Seite)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": f.UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            if raw[:2] == b"\x1f\x8b":  # Archiv liefert die Seite so, wie kaufDA sie damals gepackt geschickt hat
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            wait = 60 if e.code == 429 else 5
            log("   ! HTTP", e.code, "warte", wait, "s")
            time.sleep(wait)
        except Exception as e:  # Zeitüberschreitung, Verbindungsabbruch, kaputte Daten
            log("   !", str(e)[:80])
            time.sleep(3)
    return None


def thin(snaps):
    """Übersichtsseiten (ohne Angebote) weg; je Seite höchstens ein Schnappschuss pro Halbwoche (Mo–Mi, Do–So),
    das reicht: Prospektpreise wechseln montags und donnerstags."""
    seen, out = set(), []
    for kind, ts, url in sorted(snaps, key=lambda s: (s[2], s[1])):
        if kind == "kd" and re.search(r"/Sortiment/?$", url.split("?")[0]):
            continue
        d = time.strptime(ts[:8], "%Y%m%d")
        half = f"{time.strftime('%G-%V', d)}-{0 if d.tm_wday < 3 else 1}"
        key = (url.split("?")[0].rstrip("/").lower(), half)
        if key in seen:
            continue
        seen.add(key)
        out.append([kind, ts, url])
    return out


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
    if st.get("v") != 2:  # alte Liste (mit Übersichtsseiten, ungepackt gelesen = 0 Preise) neu aufbauen
        st = {"v": 2, "done": [], "snaps": None}
    done = set(st["done"])
    rows = json.load(open(path)) if os.path.exists(path) else {}
    if st.get("snaps") is None:
        snaps = []
        for kind, pat in PATTERNS:
            got = cdx(pat)
            log(f"{pat}: {len(got)} Schnappschüsse")
            snaps += [[kind, r[0], r[1]] for r in got]
        st["snaps"] = thin(snaps)
        log(f"Davon nötig (ohne Übersichtsseiten, je Seite 2× pro Woche): {len(st['snaps'])}")
        json.dump(st, open(STATE, "w"))
    todo = [s for s in st["snaps"] if f"{s[1]}|{s[2]}" not in done]
    log(f"Offen: {len(todo)} von {len(st['snaps'])} Schnappschüssen")
    n_new, ok, miss = 0, 0, 0
    fail = st.setdefault("fail", {})
    for i, (kind, ts, url) in enumerate(todo):
        if (time.time() - t0) / 60 > MAX_MIN:
            log("Zeit um – nächster Lauf macht weiter")
            break
        # 1 Versuch, 15 s: Antwortet das Archiv, dann in Sekunden; sonst kostete jede Seite ~1 min (Etappe 1: 34 von 40 min Warten)
        html = get(f"https://web.archive.org/web/{ts}id_/{url}", tries=1, timeout=15)
        time.sleep(PAUSE)
        key = f"{ts}|{url}"
        if not html:  # Archiv hat nicht geantwortet: in der nächsten Etappe noch einmal, danach aufgeben
            miss += 1
            fail[key] = fail.get(key, 0) + 1
            if fail[key] < 2:
                if miss >= 30 and ok == 0:
                    log("Internet-Archiv antwortet gerade nicht – Etappe beendet")
                    break
                continue
        else:
            ok += 1
        offs = (offers_kd(html) if kind == "kd" else offers_aldi(html, url)) if html else []
        for o in offs:
            k = f"{o['s']}|{f.norm(o['n'])[:40]}"
            d = day_of(o, ts)
            bk, q = f.hist_tag(o)
            dk = json.dumps([d, bk, q])  # Tag + Marke + Menge (gleicher Artikel)
            cur = rows.setdefault(k, {})
            if dk not in cur or o["p"] < cur[dk]:
                cur[dk] = o["p"]; n_new += 1
        done.add(key)
        fail.pop(key, None)
        if i % 100 == 99:
            st["done"] = sorted(done); json.dump(st, open(STATE, "w")); json.dump(rows, open(path, "w"))
            log(f"  {i + 1}/{len(todo)} · {len(rows)} Artikel · {n_new} Preise")
    st["done"] = sorted(done)
    json.dump(st, open(STATE, "w"))
    json.dump(rows, open(path, "w"))
    left = len(st["snaps"]) - len(done)
    log(f"Etappe fertig: {ok} Seiten gelesen, {miss} ohne Antwort, {len(rows)} Artikel, {n_new} neue Preise, noch offen: {left}")
    # Kam gar nichts an (Archiv gestört), nicht endlos neu starten – dann von Hand später wieder anstoßen
    print(f"left={left if ok else 0}")


def merge(path):
    rows = json.load(open(path)) if os.path.exists(path) else {}
    hist = f.load("history.json", {})
    added = 0
    for k, days in rows.items():
        old = [r for r in hist.get(k, []) if len(r) < 4]  # alte Zeilen ohne Marke/Menge bleiben (ordnet update_history zu)
        cur = {json.dumps([r[0], r[2], r[3]]): r[1] for r in hist.get(k, []) if len(r) >= 4}
        for dk, p in days.items():
            if not dk.startswith("["):
                continue
            if dk not in cur:
                cur[dk] = p; added += 1
            elif p < cur[dk]:
                cur[dk] = p
        new = [[*json.loads(dk)[:1], p, *json.loads(dk)[1:]] for dk, p in cur.items()]
        hist[k] = sorted(old + new, key=lambda r: r[0])[-150:]
    f.save("history.json", hist)
    log(f"history.json: {added} Preise nachgetragen, {len(hist)} Artikel")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--collect":
        collect(sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--merge":
        merge(sys.argv[2])
    else:
        print(__doc__)
