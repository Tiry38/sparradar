"""SparRadar: holt einmal am Tag alle Angebote rund um Wörth am Rhein
(Lebensmittel, Drogerie und Non-Food wie Haushalt, Technik, Mode, Garten).

Quellen (nur öffentliche Seiten, ohne Login, ein Abruf pro Seite und Tag):
  - Lidl:      lidl.de Suche, Kategorie "Essen & Trinken", nur Filialartikel mit Rabatt (Non-Food über kaufDA)
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
Shampoo Duschbad Deodorant Zahncreme Toilettenpapier Rasierer Seife Kosmetik
Waschmittel Spuelmittel Windeln Hundefutter Katzenstreu Werkzeug Fernseher Kopfhoerer Staubsauger
Bettwaesche Pfanne Spielzeug Fahrrad Jacke Schuhe Pflanzen""".split()

DROGERIE = (r"duschgel|schaumbad|haarentfern|epilier|duschbad|dusche\b|shampoo|sp[üu]lung|conditioner|\bdeo\b|deodorant|deospray|antitranspirant|"
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
    ("kaffee", r"kaffee|kr[öo]nung|l[ée]g[èe]re|tchibo|jacobs|dallmayr|lavazza|melitta|espresso|cappuccino|crema|kapseln|pads\b|\btee\b|teebeutel|kakao"),
    ("getraenke", r"getr[äa]nk|wasser\b|mineralwasser|saft\b|s[äa]fte\b|fruchtsaft|nektar|ouzo|amaro|kr[äa]uterlik|obstbrand|volvic|gerolsteiner|\bcola\b|limo\b|limonade|schorle|\bbier\b|pils|radler|weizenbier|hefeweizen|(?<![a-zäöüß])weine?\b|rotwein|wei[ßs]wein|ros[ée]wein|gl[üu]hwein|punsch|riesling|sekt|prosecco|secco|spirituos|lik[öo]r|whisk|wodka|vodka|\bgin\b|\brum\b|energy|eistee|smoothie|sprudel"),
    ("suess", r"s[üu][ßs]waren|oreo|schoko|praline|bonbon|gummi|fruchtgummi|chips|snack|keks|cookie|riegel|waffel|lebkuchen|spekulatius|stollen|n[üu]sse|nuss|erdn[üu]ss|popcorn|cracker|salzst"),
    ("fleisch", r"fleisch|wurst|w[üu]rstchen|schinken|h[äa]hnchen|huhn|gefl[üu]gel|pute|rind|schwein|hack|steak|schnitzel|gulasch|salami|aufschnitt|leberk[äa]se|lachs|fisch|forelle|thunfisch|garnele|shrimps|hering|kassler|filet|bacon|speck|saumagen|frikadell|braten\b|tafelspitz|nacken|kotelett|schweinehals|spareribs|ribs\b|leber\b|wade\b|ente\b|entenpfanne|gans\b|cordon bleu"),
    ("kuehl", r"milch|k[äa]se|gouda|emmentaler|camembert|mozzarella|feta|joghurt|jogurt|quark|skyr|sahne|butter|margarine|\beier?\b|pudding|dessert|frischk[äa]se|kefir|molke|ziegen|\brama\b|sanella|l[äa]tta|schmand|buttermilch"),
    ("vorrat", r"honig|marmelade|konfit|nudel|pasta\b|teigwaren|spaghetti|lasagne|ravioli|gnocchi|tortiglioni|basmati|\breis\b|mehl\b|type 405|zucker|dressing|senf|mayo|ketchup|gew[üu]rz|gemahlen|chilisalz|\bfix\b|br[üu]he|suppe|heisse tasse|p[üu]ree|fertiggericht|konserve|essig|m[üu]sli|cornflakes|aufstrich|streichcreme|pflanzenfett|cremefine"),
    ("brot", r"\bbrot|br[öo]tchen|toast|baguette|croissant|brezel|kuchen|backwaren|semmel|laugen|bagel|wrap"),
    ("obst", r"obst|gem[üu]se|tomate|apfel|[äa]pfel|banane|kartoffel|salat|gurke|paprika|zwiebel|beere|traube|orange|mandarine|clementine|zitrone|k[üu]rbis|pilz|champignon|avocado|m[öo]hre|karotte|birne|kiwi|ananas|mango|melone|kohl|brokkoli|lauch|porree|spinat|zucchini|aubergine|radieschen"),
]
# Alles außer Essen & Drogerie. Reihenfolge = Priorität, gilt nur für Artikel ohne Lebensmittel-Hinweis der Quelle
NF_CATS = [
    # Spielzeug zuerst, sonst landet z. B. ein Kinder-Werkzeugset unter Garten & Heimwerken
    ("freizeit", r"rollenspiel|spielzeug|spielset|spieltier|spielk[üu]che|kindersofa|activity|lego|playmobil|puppe|pl[üu]sch|ballzauber"),
    ("tier", r"\bhund|katzenstreu|streu\b|vogel|nager|aquarium|tierbedarf|kratzbaum|halsband|\bleine\b"),
    ("baby", r"baby|windel|kinderwagen|schnuller|feuchtt[üu]cher"),
    ("haushalt", r"waschmittel|weichsp[üu]l|reiniger|sp[üu]lmittel|geschirrsp[üu]l|putz|m[üu]llbeutel|frischhaltefolie|alufolie|backpapier|schw[äa]mm|wischmop|batterie|gl[üu]hbirne|leuchtmittel|haushalt"),
    ("garten", r"garten|pflanze(?!nfett)|blume|\berde\b|d[üu]nger|rasen|grillrost|holzkohle|gasgrill|kugelgrill|elektrogrill|grillzange|werkzeug|bohr|schrauber|s[äa]ge\b|schrauben|heimwerk|leiter\b|\bauto\b|kfz|fahrrad|e-bike"),
    ("technik", r"elektr|\btv\b|fernseher|laptop|notebook|tablet\b|smartphone|handy|kopfh[öo]rer|lautsprecher|kabel|ladeger|\bakku|powerbank|kamera|drucker|monitor|konsole|playstation|gaming|haartrockner|f[öo]hn\b|mixer|k[üu]chenmaschine|kaffeemaschine|wasserkocher|toaster|fritteuse|hei[ßs]luft|staubsauger|lampe|leuchte|\bled\b"),
    ("mode", r"kleid|hose\b|jacke|mantel|pullover|pulli|shirt|bluse|socke|strumpf|unterw[äa]sche|\bslip|schuh|stiefel|sneaker|m[üu]tze|\bschal\b|handschuh|pyjama|schlafanzug|bekleidung|jeans|leggings|weste\b"),
    ("wohnen", r"m[öo]bel|k[üu]chenutensil|\bkrug\b|glas\b|regal|tisch\b|stuhl|sofa|\bbett|kissen|decke\b|matratze|teppich|handtuch|gardine|vorhang|deko|weihnachtsbaum|kerze|vase|pfanne|\btopf|geschirr|besteck|gl[äa]ser\b|aufbewahrung|adventskalender"),
    ("freizeit", r"spielzeug|spiel\b|spiele\b|lego|puppe|pl[üu]sch|puzzle|sport|fitness|yoga|camping|zelt|koffer|rucksack|\breisen?\b|rundreise|kreuzfahrt|urlaub|\bhotel|netto-reisen|\bbuch\b|b[üu]cher|basteln"),
]


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


def classify(title, text="", food=True):
    """Erst nur der Artikelname (zuverlässiger), dann der ganze Text inkl. Beschreibung und Kategorie.
    food=False: die Quelle sagt nicht "Lebensmittel" -> zuerst die Non-Food-Kategorien prüfen."""
    full = (text or "").lower()
    if "katz" in full and "streu" not in full and re.search(r"futter|nahrung|snack|sheba|felix|whiskas|gourmet|schale|beutel|multipack", full):
        return "katze"
    for t in (title, text):
        t = GENERIC.sub(" ", (t or "").lower())
        for key, rx in ([] if food else [("drogerie", DROGERIE)] + NF_CATS) + CATS:
            if re.search(rx, t):
                return key
    return "vorrat" if food else "sonstiges"



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
          app=None, extra=None, src="", url=None, cat_text="", food=True):
    title = re.sub(r"\s+", " ", (title or "").strip())
    if not title or not price or price <= 0:
        return None
    up = unit_price(base) if isinstance(base, str) else base
    o = {
        "s": store,
        "n": title,
        "b": (brand or "").strip() or None,
        "d": re.sub(r"\s+", " ", (desc or "").strip())[:140],
        "c": classify(title, " ".join([title, desc or "", cat_text, brand or ""]), food),
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


# Alle Artikelnamen, die beim Abruf vorbeikommen (auch ohne Rabatt): für die Vorschläge in Suche und Merkliste
SEEN_NAMES = set()


# ---------- Lidl ----------
def fetch_lidl():
    out = []
    base = "https://www.lidl.de/q/api/search?assortment=DE&locale=de_DE&version=2.1.0&store=1"

    def pages(q):
        """lidl.de liefert höchstens 60 Artikel pro Abruf -> mit offset weiterblättern bis numFound."""
        offset = 0
        while offset < 2000:
            raw = http(base + q + f"&fetchsize=60&offset={offset}")
            time.sleep(PAUSE)
            if not raw:
                return
            d = json.loads(raw)
            got = d.get("items") or []
            yield from got
            offset += len(got)
            if not got or offset >= int(d.get("numFound") or 0):
                return

    for q in ("&category.id=10068374", "&q=katzenfutter", "&q=katzennahrung", "&q=duschgel", "&q=deo",
              "&q=shampoo", "&q=zahncreme", "&q=toilettenpapier", "&q=kosmetik"):
        for it in pages(q):
            g = (it.get("gridbox") or {}).get("data") or {}
            pr = g.get("price") or {}
            p, old = pr.get("price"), pr.get("oldPrice")
            disc = (pr.get("discount") or {}).get("showDiscount")
            plus = None
            for lp in g.get("lidlPlus") or []:
                v = (lp.get("price") or {}).get("price") if isinstance(lp.get("price"), dict) else lp.get("price")
                if isinstance(v, (int, float)):
                    plus = v
            if g.get("fullTitle") or g.get("title"):
                SEEN_NAMES.add(re.sub(r"\s+", " ", (g.get("fullTitle") or g.get("title")).strip()))
            if not (disc or (old and p and old > p) or plus):
                continue  # nur Angebote
            kf = g.get("keyfacts") or {}
            text = " ".join([g.get("fullTitle") or "", g.get("category") or "", kf.get("wonCategoryPrimary") or ""])
            bp = pr.get("basePrice") or {}
            o = offer("lidl", g.get("fullTitle") or g.get("title"), p, old=old,
                      base=(bp.get("price"), (bp.get("unit") or "").lower()) if bp.get("price") else None,
                      img=g.get("image"), start=pr.get("startDate"), end=pr.get("endDate"), app=plus,
                      src="lidl.de", url="https://www.lidl.de" + (g.get("canonicalUrl") or ""), cat_text=text,
                      food=q == "&category.id=10068374")
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
        food_hint = bool(re.search(r"frisch|lebensmittel|getr[äa]nk|k[üu]hl|tiefk|s[üu][ßs]|fleisch|obst|gem[üu]se|feinkost|wein|spirit|backwaren|vorrat|fr[üu]hst", cats, re.I))
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
                  url=f"https://www.aldi-sued.de/de/produkt/{it.get('urlSlugText')}-{it.get('sku')}.html", cat_text=cats,
                  food=food_hint)
        if o:
            out.append(o)
    log("Aldi Süd:", len(out))
    return out


# ---------- kaufDA (Rewe, Netto, Edeka, dm, Lidl) ----------
KD_PER_PAGE = 16   # kaufDA zeigt 16 Angebote pro Seite, weitere über ?page=2, 3, …
KD_MAX_PAGES = 70  # Sicherheitsgrenze (kaufDA meldet höchstens 1000 Angebote = 63 Seiten)


def kd_page(url):
    """Eine kaufDA-Seite: (Angebote, Gesamtzahl laut kaufDA)."""
    h = http(url)
    time.sleep(PAUSE)
    if not h:
        return [], 0
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        return [], 0
    pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
    main = (pi.get("offers") or {}).get("main") or {}
    return main.get("items") or [], int(main.get("totalItems") or 0)


def kd_items(url, all_pages=True):
    """Alle Angebote einer kaufDA-Seite, Seite für Seite (vorher fehlte alles ab Angebot 17!)."""
    items, total = kd_page(url)
    if not all_pages or total <= len(items):
        return items
    seen = {it.get("id") for it in items}
    pages = min(KD_MAX_PAGES, -(-total // KD_PER_PAGE))
    for page in range(2, pages + 1):
        more, _ = kd_page(f"{url}?page={page}")
        new = [it for it in more if it.get("id") not in seen]
        if not new:
            break  # keine neuen Angebote mehr
        seen.update(it.get("id") for it in new)
        items += new
    log(f"  {url.split('/')[-2]}: {len(items)} von {total} Angeboten")
    return items


APP_HINT = re.compile(r"(?:mit\s+(?:der\s+)?app|app[- ]preis|rewe\s+bonus|lidl\s+plus|netto[- ]app)[^0-9]{0,25}(\d+)[,.](\d\d)", re.I)


def kd_offer(it):
    store = KD_PUBLISHER.get(it.get("publisherName"))
    if not store:
        return None
    paths = it.get("categoryPaths") or []
    cat_names = " ".join(n.get("name", "") for p in paths for n in p if isinstance(n, dict))
    food_hint = any(p and isinstance(p[0], dict) and p[0].get("name") == "Lebensmittel und Getränke" for p in paths)
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
                 src="kaufda.de", cat_text=cat_names + " " + " ".join(it.get("categories") or []), food=food_hint)


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
    store_pages = set(KD_STORES.values())
    for n, url in enumerate(pages, 1):
        # Händlerseiten komplett durchblättern, Stichwortseiten (Karlsruhe) nur die erste Seite
        items = kd_items(url, all_pages=url in store_pages)
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


def update_names(offers, today):
    """Artikelnamen für die Vorschläge beim Tippen sammeln (auch wenn sie später nicht mehr im Angebot sind)."""
    names = load("names.json", {})
    for o in offers:
        n, b = o["n"], (o.get("b") or "").strip()
        text = n if not b or norm(b) in norm(n) else f"{b} {n}"
        names[text[:80]] = today
    for n in SEEN_NAMES:
        names[n[:80]] = today
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=400)).isoformat()
    names = {k: v for k, v in names.items() if v >= cutoff}
    names = dict(sorted(names.items(), key=lambda kv: kv[1], reverse=True)[:6000])
    save("names.json", names)


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
    update_names(offers, today)


if __name__ == "__main__":
    main()
