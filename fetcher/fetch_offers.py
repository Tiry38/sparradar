"""SparRadar: holt einmal am Tag die Lebensmittel-Angebote rund um Wörth am Rhein.

Quellen (nur öffentliche Seiten, ohne Login, ein Abruf pro Seite und Tag):
  - Lidl:      lidl.de Suche, Kategorie "Essen & Trinken", nur Filialartikel mit Rabatt
  - Aldi Süd:  aldi-sued.de/de/angebote.html (Daten stecken in der Seite)
  - kaufDA:    öffentliche Prospekt-Seiten für Wörth/Karlsruhe -> Rewe, Netto, Edeka, dm (+ Lidl/Aldi als Ergänzung)

Ergebnis: docs/data/offers.json und docs/data/history.json (Preisverlauf).
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "SparRadar/1.0 (private Angebotsuebersicht; 1 Abruf pro Tag)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "docs", "data")
PAUSE = 1.5  # Sekunden zwischen zwei Abrufen bei kaufDA

KD_STORES = {  # kaufDA-Händlerseiten für Wörth am Rhein
    "rewe": "https://www.kaufda.de/Woerth-am-Rhein/REWE/p-r101",
    "netto": "https://www.kaufda.de/Woerth-am-Rhein/Netto-Marken-Discount/p-r9",
    "edeka": "https://www.kaufda.de/Jockgrim/EDEKA/p-r107",
    "lidl": "https://www.kaufda.de/Woerth-am-Rhein/Lidl/p-r74",
    "dm": "https://www.kaufda.de/Woerth-am-Rhein/dm-drogerie-markt/p-r104",
}
KD_PUBLISHER = {"REWE": "rewe", "Netto Marken-Discount": "netto", "EDEKA": "edeka", "Lidl": "lidl",
                "ALDI SÜD": "aldi", "dm-drogerie markt": "dm", "dm": "dm", "DM": "dm"}
KD_CITY = "Karlsruhe"  # Stichwort-Seiten gibt es nicht für Wörth; Karlsruhe ist 10 km entfernt, gleiche Prospekt-Region
KEYWORDS = """Butter Milch Käse Joghurt Quark Sahne Eier Mozzarella Margarine Pudding
Hackfleisch Hähnchen Putenbrust Schweinefleisch Rindfleisch Steak Bratwurst Würstchen Salami Schinken Aufschnitt Lachs Fisch Garnelen
Tomaten Äpfel Bananen Kartoffeln Gurken Paprika Zwiebeln Salat Trauben Erdbeeren Mandarinen Avocado Pilze Möhren
Brot Brötchen Kuchen
Nudeln Reis Mehl Zucker Thunfisch Marmelade Honig Nutella
Pizza Eis
Schokolade Chips Kekse Pralinen
Kaffee Espresso Tee
Cola Mineralwasser Saft Bier Wein Sekt Energydrink
Katzenfutter
Shampoo Duschbad Deodorant Zahncreme Toilettenpapier Rasierer Seife Kosmetik""".split()

DROGERIE = (r"duschgel|duschbad|dusche\b|shampoo|sp[üu]lung|conditioner|\bdeo\b|deodorant|deospray|antitranspirant|"
            r"zahncreme|zahnpasta|zahnb[üu]rste|zahnseide|mundsp[üu]l|seife|bodylotion|k[öo]rperlotion|k[öo]rpermilch|body ?butter|"
            r"gesichtscreme|gesichtspflege|tagescreme|nachtcreme|handcreme|hautcreme|hautpflege|pflegecreme|sonnencreme|sonnenspray|lippenpflege|"
            r"make-?up|mascara|lippenstift|nagellack|parfum|parf[üu]m|eau de|kosmetik|rasier|damenbinde|\bbinden\b|tampon|slipeinlage|"
            r"toilettenpapier|klopapier|toilettent[üu]cher|taschent[üu]cher|kosmetikt[üu]cher|k[üu]chenrolle|k[üu]chent[üu]cher|wattepad|wattest[äa]bchen|"
            r"haargel|haarspray|haarfarbe|haarpflege|styling|nivea|balea|isana|labello|elmex|colgate|blend-a-med|odol|gillette|wilkinson|"
            r"schauma|head ?& ?shoulders|garnier|l'or[ée]al|rexona|\baxe\b|zewa|hakle|tempo\b|always|o\.b\.")

CATS = [  # Reihenfolge = Priorität
    ("katze", r"katzen|\bkatze|sheba|whiskas|felix|kitekat|gourmet gold|perfect fit|catessy|cat'?s? ?(?:food|snack)"),
    ("drogerie", DROGERIE),
    ("tk", r"tiefk[üu]hl|\btk\b|tk-|gefroren|fischst[äa]bchen|pommes|eiscreme|\beis\b|speiseeis|pizza"),
    ("kaffee", r"kaffee|espresso|cappuccino|crema|kapseln|pads\b|\btee\b|teebeutel|kakao"),
    ("getraenke", r"getr[äa]nk|wasser|saft|nektar|\bcola\b|limo|schorle|\bbier\b|pils|radler|weizenbier|hefeweizen|(?<![a-zäöüß])weine?\b|rotwein|wei[ßs]wein|ros[ée]wein|gl[üu]hwein|punsch|riesling|sekt|prosecco|secco|spirituos|lik[öo]r|whisk|wodka|vodka|\bgin\b|\brum\b|energy|eistee|smoothie|sprudel"),
    ("suess", r"s[üu][ßs]waren|schoko|praline|bonbon|gummi|fruchtgummi|chips|snack|keks|cookie|riegel|waffel|lebkuchen|spekulatius|stollen|n[üu]sse|nuss|erdn[üu]ss|popcorn|cracker|salzst"),
    ("fleisch", r"fleisch|wurst|w[üu]rstchen|schinken|h[äa]hnchen|huhn|gefl[üu]gel|pute|rind|schwein|hack|steak|schnitzel|gulasch|salami|aufschnitt|leberk[äa]se|lachs|fisch|forelle|thunfisch|garnele|shrimps|hering|kassler|filet|bacon|speck|saumagen"),
    ("kuehl", r"milch|k[äa]se|gouda|emmentaler|camembert|mozzarella|feta|joghurt|jogurt|quark|skyr|sahne|butter|margarine|\beier?\b|pudding|dessert|frischk[äa]se|kefir|molke"),
    ("brot", r"\bbrot|br[öo]tchen|toast|baguette|croissant|brezel|kuchen|backwaren|semmel|laugen|bagel|wrap"),
    ("obst", r"obst|gem[üu]se|tomate|apfel|[äa]pfel|banane|kartoffel|salat|gurke|paprika|zwiebel|beere|traube|orange|mandarine|clementine|zitrone|k[üu]rbis|pilz|champignon|avocado|m[öo]hre|karotte|birne|kiwi|ananas|mango|melone|kohl|brokkoli|lauch|porree|spinat|zucchini|aubergine|radieschen"),
]
# Was nie rein soll (Drogerie & Pflege ist erwünscht und wird vorher erkannt)
NONFOOD = re.compile(r"streu\b|katzenstreu|hygienestreu|waschmittel|weichsp[üu]ler|windel|reiniger|sp[üu]lmittel|geschirrsp[üu]l|batterie|kerze|blumenstrau|schnittblume|topfblume|zimmerpflanze|dekoration|adventskalender|socke|kleid\b|\bhose\b|jacke|werkzeug|lampe|kabel|spielzeug|bratpfanne|kochtopf|hundefutter|hundesnack|vogelfutter|pflaster|nahrungserg[äa]nzung|tabletten", re.I)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def http(url, cookie=None):
    headers = {"User-Agent": UA, "Accept-Language": "de-DE,de;q=0.9"}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as e:
        log("  ! Abruf fehlgeschlagen:", url, e)
        return None


def norm(s):
    s = (s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


GENERIC = re.compile(r"lebensmittel\s*(?:und|&)\s*getr[äa]nke|essen\s*(?:und|&)\s*trinken|wochenangebote|im angebot|kategorien/|bed[üu]rfniswelten/", re.I)


def classify(text):
    t = GENERIC.sub(" ", (text or "").lower())
    for key, rx in CATS:
        if re.search(rx, t):
            return key
    return "vorrat"


def is_food(text, food_hint):
    t = (text or "").lower()
    if "katz" in t and "streu" not in t and re.search(r"futter|nahrung|snack|sheba|felix|whiskas|gourmet|schale|beutel|multipack", t):
        return True  # Katzenfutter ja, Katzenstreu nein
    if NONFOOD.search(t):
        return False
    if re.search(DROGERIE, t):
        return True  # Drogerie & Pflege: Duschgel, Deo, Kosmetik, Klopapier …
    if re.search(r"drogerie|k[öo]rperpflege|hygiene", t) and not food_hint:
        return False  # sonstiger Drogeriekram (z. B. Haushalt) bleibt draußen
    if NONFOOD.search(t):
        return False
    if food_hint:
        return True
    return any(re.search(rx, t) for _, rx in CATS)


def unit_price(text):
    """'(1 kg = 6.63)' / '(14.95 / kg)' / '1 l = 1,98' / '2,58 €/1 kg' -> (6.63, 'kg')"""
    if not text:
        return None
    t = text.replace(",", ".")
    m = re.search(r"1\s*(kg|l|stk|st[üu]ck)\s*=\s*(\d+(?:\.\d+)?)", t, re.I)
    if m:
        return round(float(m.group(2)), 2), m.group(1).lower()[:2] if m.group(1).lower() != "kg" else "kg"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:€|eur)?\s*/\s*1?\s*(kg|l)\b", t, re.I)
    if m:
        return round(float(m.group(1)), 2), m.group(2).lower()
    return None


def offer(store, title, price, *, brand=None, desc="", old=None, base=None, img=None, start=None, end=None,
          app=None, extra=None, src="", url=None, cat_text=""):
    title = re.sub(r"\s+", " ", (title or "").strip())
    if not title or not price or price <= 0:
        return None
    up = unit_price(base) if isinstance(base, str) else base
    o = {
        "s": store,
        "n": title,
        "b": (brand or "").strip() or None,
        "d": re.sub(r"\s+", " ", (desc or "").strip())[:140],
        "c": classify(" ".join([title, desc or "", cat_text, brand or ""])),
        "p": round(float(price), 2),
        "o": round(float(old), 2) if old and old > price else None,
        "gp": {"v": up[0], "u": up[1]} if up else None,
        "img": img,
        "from": (start or "")[:10] or None,
        "to": (end or "")[:10] or None,
        "ap": round(float(app), 2) if app and app < price else None,
        "x": extra or [],
        "src": src,
        "url": url,
    }
    o["id"] = f"{store}-{norm(title)[:40]}-{int(o['p'] * 100)}"
    return o


# ---------- Lidl ----------
def fetch_lidl():
    out = []
    base = "https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1"
    for q in ("&category.id=10068374", "&q=katzenfutter", "&q=katzennahrung", "&q=duschgel", "&q=deo",
              "&q=shampoo", "&q=zahncreme", "&q=toilettenpapier", "&q=kosmetik"):
        raw = http(base + q + "&fetchsize=500&offset=0")
        time.sleep(PAUSE)
        if not raw:
            continue
        for it in json.loads(raw).get("items", []):
            g = (it.get("gridbox") or {}).get("data") or {}
            pr = g.get("price") or {}
            p, old = pr.get("price"), pr.get("oldPrice")
            disc = (pr.get("discount") or {}).get("showDiscount")
            plus = None
            for lp in g.get("lidlPlus") or []:
                v = (lp.get("price") or {}).get("price") if isinstance(lp.get("price"), dict) else lp.get("price")
                if isinstance(v, (int, float)):
                    plus = v
            if not (disc or (old and p and old > p) or plus):
                continue  # nur Angebote
            kf = g.get("keyfacts") or {}
            text = " ".join([g.get("fullTitle") or "", g.get("category") or "", kf.get("wonCategoryPrimary") or ""])
            if q != "&category.id=10068374" and not is_food(text, False):
                continue
            bp = pr.get("basePrice") or {}
            o = offer("lidl", g.get("fullTitle") or g.get("title"), p, old=old,
                      base=(bp.get("price"), (bp.get("unit") or "").lower()) if bp.get("price") else None,
                      img=g.get("image"), start=pr.get("startDate"), end=pr.get("endDate"), app=plus,
                      src="lidl.de", url="https://www.lidl.de" + (g.get("canonicalUrl") or ""), cat_text=text)
            if o:
                out.append(o)
    log("Lidl:", len(out))
    return out


# ---------- Aldi Süd ----------
def nuxt_resolve(data, i, depth=0):
    if depth > 14 or not isinstance(i, int) or i < 0 or i >= len(data):
        return None
    v = data[i]
    if isinstance(v, list):
        if v and isinstance(v[0], str) and v[0] in ("Reactive", "ShallowReactive", "Ref", "ShallowRef", "EmptyRef", "Set", "Map"):
            return nuxt_resolve(data, v[1], depth + 1) if len(v) > 1 else None
        return [nuxt_resolve(data, x, depth + 1) for x in v]
    if isinstance(v, dict):
        return {k: nuxt_resolve(data, x, depth + 1) for k, x in v.items()}
    return v


def fetch_aldi():
    out = []
    h = http("https://www.aldi-sued.de/de/angebote.html")
    if not h:
        return out
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        log("  ! Aldi: keine Daten in der Seite gefunden")
        return out
    data = json.loads(m.group(1))
    for i, v in enumerate(data):
        if not (isinstance(v, dict) and "price" in v and "name" in v and "sku" in v):
            continue
        it = nuxt_resolve(data, i)
        pr = it.get("price") or {}
        amount = pr.get("amountRelevant") or pr.get("amount")
        if not amount:
            continue
        cats = " ".join(c.get("name", "") for c in it.get("categories") or [] if isinstance(c, dict))
        text = " ".join([it.get("name") or "", it.get("brandName") or "", cats])
        food_hint = bool(re.search(r"frisch|lebensmittel|getr[äa]nk|k[üu]hl|tiefk|s[üu][ßs]|fleisch|obst|gem[üu]se|feinkost|wein|spirit|backwaren|vorrat|fr[üu]hst", cats, re.I))
        if not is_food(text, food_hint):
            continue
        old = None
        if pr.get("wasPriceDisplay"):
            mm = re.search(r"(\d+),(\d\d)", pr["wasPriceDisplay"])
            old = float(f"{mm.group(1)}.{mm.group(2)}") if mm else None
        img = None
        for a in it.get("assets") or []:
            if isinstance(a, dict) and a.get("url"):
                img = a["url"].replace("{width}", "500").replace("{slug}", it.get("urlSlugText") or "bild")
                break
        brand = it.get("brandName")
        o = offer("aldi", it.get("name"), amount / 100, brand=None if brand in ("BIO", "no-brand") else brand,
                  desc=it.get("sellingSize") or "", old=old, base=pr.get("comparisonDisplay"), img=img,
                  start=it.get("onSaleDate"), src="aldi-sued.de",
                  url=f"https://www.aldi-sued.de/de/produkt/{it.get('urlSlugText')}-{it.get('sku')}.html", cat_text=cats)
        if o:
            out.append(o)
    log("Aldi Süd:", len(out))
    return out


# ---------- kaufDA (Rewe, Netto, Edeka, dm, Lidl) ----------
def kd_items(url):
    h = http(url)
    time.sleep(PAUSE)
    if not h:
        return []
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        return []
    pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
    return ((pi.get("offers") or {}).get("main") or {}).get("items") or []


APP_HINT = re.compile(r"(?:mit\s+(?:der\s+)?app|app[- ]preis|rewe\s+bonus|lidl\s+plus|netto[- ]app)[^0-9]{0,25}(\d+)[,.](\d\d)", re.I)


def kd_offer(it):
    store = KD_PUBLISHER.get(it.get("publisherName"))
    if not store:
        return None
    paths = it.get("categoryPaths") or []
    cat_names = " ".join(n.get("name", "") for p in paths for n in p if isinstance(n, dict))
    food_hint = any(p and isinstance(p[0], dict) and p[0].get("name") == "Lebensmittel und Getränke" for p in paths)
    text = " ".join([it.get("title") or "", it.get("description") or "", it.get("brand") or "", cat_names, " ".join(it.get("categories") or [])])
    if not is_food(text, food_hint):
        return None
    pr = it.get("prices") or {}
    p = pr.get("mainPrice")
    old = pr.get("secondaryPrice") or None
    extra, app = [], None
    m = APP_HINT.search(" ".join([it.get("description") or "", " ".join(str(c) for c in pr.get("conditions") or [])]))
    if m:
        v = float(f"{m.group(1)}.{m.group(2)}")
        if store == "rewe" and v < (p or 0) * 0.6:
            extra.append(["bonus", "Rewe Bonus Guthaben", v])
        elif v < (p or 0):
            app = v
    imgs = ((it.get("offerImages") or {}).get("url") or {})
    return offer(store, it.get("title"), p, brand=it.get("brand"), desc=it.get("description") or "", old=old,
                 base=pr.get("priceByBaseUnit"), img=imgs.get("normal") or imgs.get("large"),
                 start=it.get("validFrom"), end=it.get("validUntil"), app=app, extra=extra,
                 src="kaufda.de", cat_text=cat_names)


def fetch_kaufda():
    out = []
    pages = list(KD_STORES.values())
    seen_kw = set()
    for kw in KEYWORDS:
        k = kw.strip()
        if not k or norm(k) in seen_kw:
            continue
        seen_kw.add(norm(k))
        slug = k[0].upper() + k[1:]
        for a, b in (("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
            slug = slug.replace(a, b)  # kaufDA schreibt Umlaute aus: Käse -> Kaese
        pages.append(f"https://www.kaufda.de/{KD_CITY}/Angebote/{urllib.parse.quote(slug)}")
    for n, url in enumerate(pages, 1):
        items = kd_items(url)
        for it in items:
            o = kd_offer(it)
            if o:
                out.append(o)
        if n % 20 == 0:
            log(f"  kaufDA: {n}/{len(pages)} Seiten")
    log("kaufDA:", len(out), "(vor Duplikat-Bereinigung)")
    return out


# ---------- Zusammenführen und Preisverlauf ----------
def load(name, default):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save(name, obj):
    os.makedirs(DATA, exist_ok=True)
    tmp = os.path.join(DATA, name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(DATA, name))


def merge(offers):
    by = {}
    for o in offers:
        k = (o["s"], norm(o["n"])[:30], o["p"])
        cur = by.get(k)
        if not cur:
            by[k] = o
            continue
        # das vollständigere Angebot behalten, fehlende Felder ergänzen
        for f in ("b", "o", "gp", "img", "from", "to", "ap", "url"):
            if not cur.get(f) and o.get(f):
                cur[f] = o[f]
        if o.get("x") and not cur.get("x"):
            cur["x"] = o["x"]
    return list(by.values())


def update_history(offers, today):
    hist = load("history.json", {})
    for o in offers:
        k = f"{o['s']}|{norm(o['n'])[:40]}"
        rows = hist.setdefault(k, [])
        if rows and rows[-1][0] == today:
            rows[-1][1] = min(rows[-1][1], o["p"])
        else:
            rows.append([today, o["p"]])
        del rows[:-40]
    # Einträge, die seit 120 Tagen nicht mehr auftauchen, löschen
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=120)).isoformat()
    hist = {k: v for k, v in hist.items() if v and v[-1][0] >= cutoff}
    save("history.json", hist)


def main():
    today = dt.date.today().isoformat()
    offers = []
    for name, fn in (("Lidl", fetch_lidl), ("Aldi", fetch_aldi), ("kaufDA", fetch_kaufda)):
        try:
            offers += fn()
        except Exception as e:  # eine kaputte Quelle soll die anderen nicht stoppen
            log(f"  ! {name} fehlgeschlagen: {e!r}")
    offers = merge(offers)
    # abgelaufene Angebote raus
    offers = [o for o in offers if not o.get("to") or o["to"] >= today]
    offers.sort(key=lambda o: (o["s"], o["c"], o["n"]))
    counts = {}
    for o in offers:
        counts[o["s"]] = counts.get(o["s"], 0) + 1
    log("Gesamt:", len(offers), counts)
    if len(offers) < 30:
        log("! Zu wenige Angebote, alte Daten bleiben stehen.")
        sys.exit(1)
    save("offers.json", {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                         "region": "Wörth am Rhein", "counts": counts, "offers": offers})
    update_history(offers, today)


if __name__ == "__main__":
    main()
