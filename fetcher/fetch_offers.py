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


def clean_text(t):
    """HTML-Reste entfernen, Leerraum zusammenfassen"""
    t = re.sub(r"<br\s*/?>|</li>|</p>", ". ", str(t or ""), flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    return re.sub(r"\s+", " ", t).strip(" .")


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
          app=None, extra=None, src="", url=None, cat_text="", food=True, app_only=None, bonus_only=None, img_large=None, info=None, cats=None, page=None, images=None, brochure=None):
    title = re.sub(r"\s+", " ", (title or "").strip())
    if not title or ((not price or price <= 0) and not bonus_only):
        return None
    price = price or 0
    up = unit_price(base) if isinstance(base, str) else base
    o = {
        "s": store,
        "n": title,
        "b": (brand or "").strip() or None,
        "d": re.sub(r"\s+", " ", (desc or "").strip())[:300],
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
    if img_large and img_large != img:
        o["il"] = img_large       # großes Bild für die Detailansicht
    ims = [u for u in dict.fromkeys(images or []) if isinstance(u, str) and u.startswith("http") and u not in (img, img_large)]
    if ims:
        o["ims"] = ims[:8]        # weitere Produktbilder
    inf = clean_text(info)
    if inf and inf != o["d"]:
        o["inf"] = inf[:900]      # vollständige Beschreibung / Produktmerkmale
    cl = [c for c in dict.fromkeys(cats or []) if isinstance(c, str) and c.strip()]
    if cl:
        o["cat"] = cl[:6]         # Kategorien laut Quelle
    if page:
        o["pg"] = page            # Seite im Prospekt
    if brochure:
        o["bid"] = brochure       # Prospekt-ID -> hochaufgelöste Prospektseite in der Detailansicht
    if app_only:
        o["ao"] = app_only        # Preis gilt nur mit dieser App/Karte
    if bonus_only:
        o["bo"] = bonus_only      # Bonus-Aktion: so viel Guthaben gibt es, Preis steht nicht im Prospekt
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
                      info=" ".join(v for v in (kf.values() if isinstance(kf, dict) else []) if isinstance(v, str)),
                      cats=[g.get("category")] if g.get("category") else None,
                      food=q == "&category.id=10068374")
            if o:
                # weitere Produktbilder (Lidl liefert oft mehrere Ansichten)
                more = []
                for im in (g.get("imageList") or [])[:8]:
                    u = im if isinstance(im, str) else (im or {}).get("image") or (im or {}).get("url") if isinstance(im, dict) else None
                    if isinstance(u, str) and u.startswith("http") and u != o.get("img") and u not in more:
                        more.append(u)
                if more:
                    o["ims"] = more
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
        img = img_l = None
        all_imgs = [a["url"].replace("{width}", "1200").replace("{slug}", it.get("urlSlugText") or "bild")
                    for a in it.get("assets") or [] if isinstance(a, dict) and a.get("url")]
        for a in it.get("assets") or []:
            if isinstance(a, dict) and a.get("url"):
                img = a["url"].replace("{width}", "1000").replace("{slug}", it.get("urlSlugText") or "bild")
                img_l = a["url"].replace("{width}", "1200").replace("{slug}", it.get("urlSlugText") or "bild")
                break
        brand = it.get("brandName")
        o = offer("aldi", it.get("name"), amount / 100, brand=None if brand in ("BIO", "no-brand") else brand,
                  desc=it.get("sellingSize") or "", old=old, base=pr.get("comparisonDisplay"), img=img,
                  start=it.get("onSaleDate"), src="aldi-sued.de", img_large=img_l if img else None, images=all_imgs,
                  info=" ".join(str(it.get(k)) for k in ("shortDescription", "description", "longDescription") if isinstance(it.get(k), str)),
                  cats=[c.get("name") for c in it.get("categories") or [] if isinstance(c, dict)],
                  url=f"https://www.aldi-sued.de/de/produkt/{it.get('urlSlugText')}-{it.get('sku')}.html", cat_text=cats,
                  food=food_hint)
        if o:
            out.append(o)
    log("Aldi Süd:", len(out))
    return out


# ---------- kaufDA (Rewe, Netto, Edeka, dm, Lidl) ----------
KD_INFO = {}  # je Händlerseite: gültige Prospekt-IDs und Themen-Links (für die Sortiment-Seiten)


def _ids(o, out):
    """alle 'id'-Werte (Prospekt-IDs) in den Prospekt-Listen einsammeln"""
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("id", "contentId", "legacyId") and isinstance(v, (str, int)):
                out.add(str(v))
            elif isinstance(v, (dict, list)) and k != "pages":
                _ids(v, out)
    elif isinstance(o, list):
        for v in o:
            _ids(v, out)
    return out


def kd_page(url):
    """Eine kaufDA-Seite: (Angebote, Gesamtzahl laut kaufDA). Merkt sich Prospekt-IDs und Themen-Links."""
    h = http(url)
    time.sleep(PAUSE)
    if not h:
        return [], 0
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S)
    if not m:
        return [], 0
    pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
    main = (pi.get("offers") or {}).get("main") or {}
    items = main.get("items") or []
    br = pi.get("brochures") or {}
    links = ((((pi.get("template") or {}).get("content") or {}).get("OfferLinkbox") or {}).get("PublisherOfferLinkbox") or {}).get("links") or []
    KD_INFO[url] = {
        "brochures": _ids([br.get("viewer"), br.get("publisher")], set()) | {str((it.get("parentContent") or {}).get("id")) for it in items},
        "links": [l.get("link_href") for l in links if isinstance(l, dict) and l.get("link_href")],
        "known": {(norm(it.get("title")), round(float((it.get("prices") or {}).get("mainPrice") or 0), 2)) for it in items},
    }
    return items, int(main.get("totalItems") or 0)


def kd_items(url):
    """Angebote einer kaufDA-Seite. Weiterblättern gibt es nicht (?page= liefert dieselben 16),
    deshalb kommen die übrigen Angebote über die Sortiment-Seiten (fetch_sortiment)."""
    items, total = kd_page(url)
    if total > len(items) and url in KD_STORES.values():
        log(f"  {url.split('/')[-2]}: {len(items)} von {total} Angeboten auf der Händlerseite")
    return items


APP_COND = re.compile(r"lidl\s*plus|app[- ]?preis|mit (der )?app|netto[- ]?app|payback|deutschlandcard|kundenkarte|coupon", re.I)
APP_LABEL = {"lidl": "Lidl Plus", "edeka": "Edeka-App", "netto": "Netto-App", "rewe": "Rewe-App", "dm": "dm-App", "aldi": "Aldi-App"}
APP_HINT = re.compile(r"(?:mit\s+(?:der\s+)?app|app[- ]preis|rewe\s+bonus|lidl\s+plus|netto[- ]app)[^0-9]{0,25}(\d+)[,.](\d\d)", re.I)


def kd_offer(it):
    store = KD_PUBLISHER.get(it.get("publisherName"))
    if not store:
        return None
    paths = it.get("categoryPaths") or []
    cat_names = " ".join(n.get("name", "") for p in paths for n in p if isinstance(n, dict))
    food_hint = any(p and isinstance(p[0], dict) and p[0].get("name") == "Lebensmittel und Getränke" for p in paths)
    pr = it.get("prices") or {}
    p = pr.get("mainPrice") or 0
    old = pr.get("secondaryPrice") or None
    extra, app, app_only, bonus_only = [], None, None, None
    # kaufDA kennzeichnet App-Preise in prices.conditions, z. B. {"other": "Mit Lidl Plus"} oder "App-Preis"
    cond = " ".join(str(c.get("other") or "") for c in pr.get("conditions") or [] if isinstance(c, dict))
    if APP_COND.search(cond):
        label = "Payback" if re.search(r"payback", cond, re.I) else APP_LABEL.get(store, "App")
        if old and old > p:
            # „Mit Lidl Plus 1,49 statt 2,29“: ohne App zahlt man 2,29, mit App 1,49
            p, app, old = old, p, None
        else:
            app_only = label  # nur dieser Preis bekannt, gilt nur mit App
    # Rewe Bonus: prices.description „0,80 € Bonus“ = Guthaben in der Rewe-App
    mb = re.search(r"(\d+)[,.](\d\d)\s*€?\s*bonus", str(pr.get("description") or ""), re.I)
    if mb:
        v = float(f"{mb.group(1)}.{mb.group(2)}")
        if p:
            extra.append(["bonus", "Rewe Bonus Guthaben" if store == "rewe" else "Bonus-Guthaben", v])
        else:
            bonus_only = v  # Bonus-Aktion ohne Preis im Prospekt
    m = APP_HINT.search(" ".join([it.get("description") or "", cond]))
    if m and not app and not app_only:
        v = float(f"{m.group(1)}.{m.group(2)}")
        if store == "rewe" and v < (p or 0) * 0.6:
            extra.append(["bonus", "Rewe Bonus Guthaben", v])
        elif v < (p or 0):
            app = v
    imgs = ((it.get("offerImages") or {}).get("url") or {})
    return offer(store, it.get("title"), p, brand=it.get("brand"), desc=it.get("description") or "", old=old,
                 base=pr.get("priceByBaseUnit"), img=imgs.get("large") or imgs.get("normal"), img_large=imgs.get("large"),
                 start=it.get("validFrom"), end=it.get("validUntil"), app=app, extra=extra,
                 src="kaufda.de", cat_text=cat_names + " " + " ".join(it.get("categories") or []), food=food_hint,
                 app_only=app_only, bonus_only=bonus_only, info=it.get("description"),
                 cats=[n.get("name") for p in paths for n in p if isinstance(n, dict)][-3:] + list(it.get("categories") or []),
                 page=((it.get("parentContent") or {}).get("page") or {}).get("number"),
                 brochure=(it.get("parentContent") or {}).get("id"))


def fetch_kaufda():
    out = []
    pages = list(KD_STORES.values())
    seen_kw = set()
    # Stichwortseiten (Karlsruhe): wichtig vor allem für Edeka und dm, für die es keine Sortiment-Seiten gibt
    for kw in KEYWORDS + SORTIMENT:
        k = kw.strip()
        if not k or norm(k) in seen_kw:
            continue
        seen_kw.add(norm(k))
        slug = k[0].upper() + k[1:]
        for a, b in (("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
            slug = slug.replace(a, b)  # kaufDA schreibt Umlaute aus: Käse -> Kaese
        pages.append(f"https://www.kaufda.de/{KD_CITY}/Angebote/{urllib.parse.quote(slug)}")
    regional = {"rewe": [], "edeka": []}  # Angebote regionaler Händler aus Karlsruhe: erst prüfen, ob gleicher Prospekt
    for n, url in enumerate(pages, 1):
        items = kd_items(url)
        for it in items:
            st = KD_PUBLISHER.get(it.get("publisherName"))
            if url not in KD_STORES.values() and st in regional:
                regional[st].append(it)
                continue
            o = kd_offer(it)
            if o:
                out.append(o)
        if n % 20 == 0:
            log(f"  kaufDA: {n}/{len(pages)} Seiten")
    more, accepted = fetch_sortiment(regional)
    out += more
    log("kaufDA:", len(out), "(vor Duplikat-Bereinigung)")
    return out


# kaufDA zeigt auf der Händlerseite nur 16 Angebote. Die öffentlichen Sortiment-Seiten
# (kaufda.de/<Händler>/Sortiment/<Begriff>) zeigen je Begriff alle passenden Angebote des Händlers.
# Sie sind bundesweit -> nur Angebote aus Prospekten behalten, die auch für Wörth/Jockgrim gelten.
KD_SLUGS = {"lidl": ["Lidl"], "netto": ["Netto-Marken-Discount"], "rewe": ["REWE"], "edeka": ["Edeka"],
            "dm": ["dm-drogerie-markt", "Dm"]}
SORTIMENT = """Butter Milch Kaese Joghurt Quark Sahne Eier Mozzarella Margarine Pudding Skyr Frischkaese Gouda
Hackfleisch Haehnchen Putenbrust Schweinefleisch Rindfleisch Steak Schnitzel Bratwurst Wuerstchen Salami Schinken Wurst Lachs Fisch Garnelen Thunfisch
Obst Gemuese Tomaten Aepfel Bananen Kartoffeln Paprika Zwiebeln Salat Trauben Mandarinen Beeren Pilze
Brot Broetchen Kuchen Toast Nudeln Reis Mehl Zucker Oel Konserven Suppe Muesli Cornflakes Marmelade Honig Nutella Ketchup Gewuerze
Pizza Eis Pommes Tiefkuehlkost Schokolade Chips Kekse Pralinen Suessigkeiten Gummibaerchen Nuesse
Kaffee Kaffeekapseln Kaffeepads Espresso Tee Kakao Tassimo Senseo Jacobs Tchibo Dallmayr Lavazza
Cola Coca-Cola Pepsi Fanta Limonade Mineralwasser Wasser Saft Bier Wein Sekt Prosecco Spirituosen Whisky Wodka Energy-Drink Red-Bull Monster-Energy
Katzenfutter Hundefutter Katzenstreu Tierfutter
Shampoo Duschgel Deo Zahnpasta Zahnbuerste Rasierer Toilettenpapier Kuechenrolle Taschentuecher Windeln Kosmetik Creme
Waschmittel Persil Ariel Weichspueler Spuelmittel Reiniger Muellbeutel Batterien
Kleidung Schuhe Jacke Socken Unterwaesche Bettwaesche Handtuch Kissen Decke Pfanne Topf Geschirr Lampe Kerzen
Werkzeug Akkuschrauber Garten Pflanzen Blumen Grill Fahrrad Spielzeug Lego Fernseher Kopfhoerer Staubsauger Kaffeemaschine Kuechengeraete""".split()


def same_flyer(items, known, base_ids):
    """Welche Prospekte entsprechen dem lokalen Prospekt? Jeder Edeka-/Rewe-Markt hat eine eigene Prospekt-ID,
    der Inhalt ist in der Region aber gleich. Ein Prospekt zählt als „unserer“, wenn er mindestens 2 Angebote
    mit gleichem Artikel und gleichem Preis wie die lokale Händlerseite enthält."""
    hits = {}
    for it in items:
        b = str((it.get("parentContent") or {}).get("id"))
        key = (norm(it.get("title")), round(float((it.get("prices") or {}).get("mainPrice") or 0), 2))
        if key in known:
            hits[b] = hits.get(b, 0) + 1
    return set(base_ids) | {b for b, n in hits.items() if n >= 2}


def fetch_sortiment(regional=None):
    regional = regional or {}
    out, accepted = [], {}
    for store, slugs in KD_SLUGS.items():
        local = KD_INFO.get(KD_STORES.get(store), {})
        terms = list(dict.fromkeys(SORTIMENT + [l.rstrip("/").split("/")[-1] for l in local.get("links", [])]))
        slug = None
        for sl in slugs:  # gibt es für diesen Händler Sortiment-Seiten?
            items, total = kd_page(f"https://www.kaufda.de/{sl}/Sortiment/Butter" if store != "dm" else f"https://www.kaufda.de/{sl}/Sortiment/Shampoo")
            if items or total:
                slug = sl
                break
        found, seen = list(regional.get(store, [])), set()
        if slug:
            for t in terms:
                items, _ = kd_page(f"https://www.kaufda.de/{slug}/Sortiment/{urllib.parse.quote(t)}")
                found += items
        found = [it for it in found if not (it.get("id") in seen or seen.add(it.get("id")))]
        if store in ("rewe", "edeka"):
            # regionale Händler: nur Prospekte mit gleichem Inhalt wie die lokale Händlerseite
            base = {b for b in local.get("brochures", set()) if b and b != "None"}
            ok = same_flyer(found, local.get("known", set()), base)
            accepted[store] = ok
            kept_items = [it for it in found if str((it.get("parentContent") or {}).get("id")) in ok]
        else:
            kept_items = found
        n0 = len(out)
        for it in kept_items:
            o = kd_offer(it)
            if o:
                out.append(o)
        log(f"  Sortiment {store}: {len(out) - n0} Angebote übernommen von {len(found)} gefundenen"
            f" ({'keine Sortiment-Seiten, nur Stichwortseiten' if not slug else str(len(terms)) + ' Begriffe'})")
    return out, accepted


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
        for f in ("b", "o", "gp", "img", "il", "ims", "inf", "cat", "pg", "bid", "from", "to", "ap", "ao", "url"):
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
