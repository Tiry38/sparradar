"""SparRadar – Abruf auf dem eigenen PC (wird bei jedem Lauf frisch von GitHub geladen, start.py ruft main() auf).

Warum: prospektangebote.de lässt GitHub-Server nicht rein (03.11.: „202, leer“, Bot-Schutz für Rechenzentren).
Vom PC zu Hause klappt es. Dieses Programm holt dort
  - die Müller-Angebote (Liste /geschaefte/mueller/angebote?page=N, robots.txt erlaubt es) und
  - die Scheck-In-Prospekte (Gültigkeit + Seitenbilder, /anzeigen/angebote/…)
und lädt sie als docs/data/pc-pa.json ins Repo. Der Angebots-Abruf auf GitHub baut sie ein, liest neue
Scheck-In-Prospekte per Texterkennung und wirft Doppelte zu kaufDA raus. Nichts wird umgangen: normale Seitenaufrufe
mit ehrlichem Namen, 2 s Pause, höchstens alle 3 Stunden.

Der GitHub-Schlüssel liegt nur auf dem PC (%LOCALAPPDATA%\\SparRadar\\token.txt), nie im Repo.
"""
import base64
import datetime as dt
import html
import json
import os
import re
import time
import urllib.error
import urllib.request

REPO = "Tiry38/sparradar"
OUT = "docs/data/pc-pa.json"
PA = "https://www.prospektangebote.de"
UA = "SparRadar/1.0 (+https://github.com/Tiry38/sparradar; private Angebots-App, Abruf vom eigenen PC)"
PAUSE = 2.0
LOG = print


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "de-DE,de;q=0.9"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):  # Seite nach der letzten Seite
                return None
            LOG(f"  Seite {url}: Fehler {e.code}")
            if e.code == 403:
                return None
        except Exception as e:
            LOG(f"  Seite {url}: {e}")
        time.sleep(5 * (i + 1))
    return None


def money(v):
    m = re.search(r"(\d+(?:\.\d{3})*),(\d\d)", v or "")
    return float(m.group(1).replace(".", "") + "." + m.group(2)) if m else None


def until(txt, today):
    """Restlaufzeit („5 Tage“) -> letzter Tag; künftige („Gültig in …“) -> 'future'."""
    t = (txt or "").strip().lower()
    if not t or t.startswith("gültig in") or "bald" in t:
        return "future"
    m = re.match(r"(\d+)\s*(tag|tage|woche|wochen|monat|monate)\b", t)
    if m:
        n, u = int(m.group(1)), m.group(2)
        return (today + dt.timedelta(days=n * (30 if u.startswith("monat") else 7 if u.startswith("woche") else 1))).isoformat()
    if t in ("heute", "letzter tag", "endet heute"):
        return today.isoformat()
    return None


def shop_list(slug):
    today = dt.date.today()
    rows, seen = [], set()
    for page in range(1, 61):
        h = get(f"{PA}/geschaefte/{slug}/angebote" + (f"?page={page}" if page > 1 else ""))
        time.sleep(PAUSE)
        blocks = (h or "").split('<a class="js-offer-link-item')[1:]
        if not blocks:
            break
        new = 0
        for b in blocks:
            b = b.split("</a>")[0]
            mid = re.search(r'href="(/geschaefte/[^"]+-angebot-(\d+)/)"', b)
            if not mid or mid.group(2) in seen:
                continue
            seen.add(mid.group(2))
            new += 1
            name = re.search(r'product__name[^>]*>([^<]*)<', b)
            to = until((re.search(r'product-date[^>]*>([^<]*)<', b) or [None, ""])[1], today)
            p = money((re.search(r'product__price-offer[^>]*>([^<]*)<', b) or [None, ""])[1])
            if to == "future" or not name or not p:
                continue
            img = re.search(r'src="(https://img\.offers-cdn\.net/assets/uploads/offers/[^"]+?)-thumb[^"]*"', b)
            rows.append({"i": mid.group(2), "n": html.unescape(name.group(1)).strip(), "p": p,
                         "o": money((re.search(r'product__price-normal[^>]*>([^<]*)<', b) or [None, ""])[1]),
                         "t": to, "img": (img.group(1) + "-normal.jpeg") if img else None, "u": PA + mid.group(1)})
        if not new:
            break
    return rows


def flyers(slug):
    h = get(f"{PA}/geschaefte/{slug}/prospekte-angebote") or ""
    out = []
    for path, fid in dict.fromkeys(re.findall(rf"/anzeigen/angebote/({re.escape(slug)}-prospekt-(\d+))", h)):
        time.sleep(PAUSE)
        f = get(f"{PA}/anzeigen/angebote/{path}") or ""
        m = re.search(r"Gültig von (\d\d)/(\d\d)/(\d{4}) bis (\d\d)/(\d\d)/(\d{4})", f)
        pg = re.search(r"let flyerPages = (\[.*?\]);", f)
        if not m or not pg:
            continue
        try:
            pages = [x["page"] for x in json.loads(pg.group(1))]
        except Exception:
            continue
        out.append({"id": fid, "from": f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "to": f"{m.group(6)}-{m.group(5)}-{m.group(4)}",
                    "pages": pages, "url": f"{PA}/anzeigen/angebote/{path}"})
    return out


def api(token, method, path, body=None):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode()
            return r.status, (json.loads(t) if t.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, {}


def main(base, log=print):
    global LOG
    LOG = log
    tok_f = os.path.join(base, "token.txt")
    token = open(tok_f, encoding="utf-8").read().strip() if os.path.exists(tok_f) else ""
    if not token:
        log("Kein GitHub-Schlüssel gefunden – bitte SparRadar-PC-einrichten.bat nochmal starten.")
        return False
    today = dt.date.today().isoformat()

    log("Müller-Angebote holen …")
    mu = shop_list("mueller")
    log(f"  Müller: {len(mu)} Angebote")
    log("Scheck-In-Prospekte holen …")
    sc = [f for f in flyers("scheck-in-center") if f["to"] >= today]
    log(f"  Scheck-In: {len(sc)} gültige Prospekte ({', '.join(f['from'] + ' bis ' + f['to'] for f in sc) or '-'})")
    if len(mu) < 50 and not sc:
        log("Fast nichts bekommen (Seite gestört?) – nichts hochgeladen, nächster Versuch später.")
        return False

    data = {"mueller": mu, "scheck": sc}
    st, cur = api(token, "GET", f"contents/{OUT}?ref=main")
    if st == 401:
        log("GitHub lehnt den Schlüssel ab (abgelaufen oder falsch) – SparRadar-PC-einrichten.bat starten und neuen Schlüssel eintragen.")
        return False
    old = {}
    if st == 200 and cur.get("content"):
        try:
            old = json.loads(base64.b64decode(cur["content"]).decode())
        except Exception:
            old = {}
    age = 99
    try:
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(old.get("at"))).total_seconds() / 3600
    except Exception:
        pass
    if old.get("mueller") == mu and old.get("scheck") == sc and age < 20:
        log("Unverändert – nichts hochgeladen.")
    else:
        data = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                "src": "prospektangebote.de, abgerufen vom eigenen PC (GitHub-Server werden dort blockiert)", **data}
        content = base64.b64encode(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()).decode()
        for _ in range(3):
            body = {"message": f"PC-Abruf: Müller {len(mu)} Angebote, Scheck-In {len(sc)} Prospekt(e)",
                    "content": content, "branch": "main"}
            if cur.get("sha"):
                body["sha"] = cur["sha"]
            st, res = api(token, "PUT", f"contents/{OUT}", body)
            if st in (200, 201):
                log("Hochgeladen ✓")
                break
            if st in (409, 422):  # inzwischen neuer Stand (Bot hat committet) -> neu lesen, nochmal
                time.sleep(5)
                _, cur = api(token, "GET", f"contents/{OUT}?ref=main")
                continue
            log(f"Hochladen fehlgeschlagen (Fehler {st})" + (" – Schlüssel braucht „Contents: Read and write“." if st in (403, 404) else ""))
            return False
        else:
            log("Hochladen fehlgeschlagen (Konflikt) – nächster Versuch später.")
            return False

    # Neuer Scheck-In-Prospekt, den GitHub noch nicht gelesen hat -> Angebots-Abruf gleich starten (einmal je Prospekt)
    known = set()
    try:
        known = set(json.loads(get(f"https://raw.githubusercontent.com/{REPO}/main/docs/data/scheck-ocr.json") or "{}").get("flyers", {}))
    except Exception:
        pass
    done_f = os.path.join(base, "gestartet.json")
    try:
        done = set(json.load(open(done_f, encoding="utf-8")))
    except Exception:
        done = set()
    new = [f["id"] for f in sc if f["id"] not in known and f["id"] not in done]
    if new:
        st, _ = api(token, "POST", "actions/workflows/angebote.yml/dispatches", {"ref": "main"})
        if st == 204:
            log(f"Neuer Scheck-In-Prospekt {', '.join(new)} -> Angebots-Abruf auf GitHub gestartet ✓")
            json.dump(sorted(done | set(new)), open(done_f, "w", encoding="utf-8"))
        else:
            log(f"Abruf starten ging nicht (Fehler {st}) – Schlüssel braucht „Actions: Read and write“. Er läuft sonst morgen früh.")
    return True
