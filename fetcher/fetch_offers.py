"""SparRadar: holt einmal am Tag alle Angebote rund um Wörth am Rhein
(Lebensmittel, Drogerie und Non-Food wie Haushalt, Technik, Mode, Garten).

Quellen (nur öffentliche Seiten, ohne Login, ein Abruf pro Seite und Tag):
  - Lidl:      lidl.de Suche, Kategorie "Essen & Trinken", nur Filialartikel mit Rabatt (Non-Food über kaufDA)
  - Aldi Süd:  aldi-sued.de/de/angebote.html (Daten stecken in der Seite)
  - kaufDA:    öffentliche Prospekt-Seiten für Wörth/Karlsruhe -> Rewe, Netto, Edeka, dm (+ Lidl/Aldi als Ergänzung)

Ergebnis: docs/data/offers.json und docs/data/history.json (Preisverlauf).
"""
import datetime as dt
import html as _html
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.client import HTTPException

UA = "SparRadar/1.0 (private Angebotsuebersicht; 1 Abruf pro Tag)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "docs", "data")
PAUSE = 2.0  # Sekunden zwischen zwei Abrufen bei kaufDA (robots.txt: crawl-delay 2)

KD_STORES = {  # kaufDA-Händlerseiten für Wörth am Rhein
    "rewe": "https://www.kaufda.de/Woerth-am-Rhein/REWE/p-r101",
    "netto": "https://www.kaufda.de/Woerth-am-Rhein/Netto-Marken-Discount/p-r9",
    "edeka": "https://www.kaufda.de/Jockgrim/EDEKA/p-r107",
    "lidl": "https://www.kaufda.de/Woerth-am-Rhein/Lidl/p-r74",
    "dm": "https://www.kaufda.de/Woerth-am-Rhein/dm-drogerie-markt/p-r104",
    "mueller": "https://www.kaufda.de/Woerth-am-Rhein/Mueller/p-r85",  # Müller im Maximilian-Center (Diagnose 02.11.)
    # „EDEKA Wörth“ bei kaufDA = Marktkauf/Scheck-in im Maximilian-Center (eigener Prospekt, ~420 Angebote, Händler „EDEKA“).
    # Welche Angebote zu Scheck-In gehören, entscheidet die Prospekt-ID dieser Seite (kd_store); scheck-in-center.de
    # selbst verbietet Abrufe (robots.txt Disallow: /).
    "scheck": "https://www.kaufda.de/Woerth-am-Rhein/EDEKA/p-r107",
}
# Händlerseiten der Nachbarorte zeigen je Ort andere 16 Angebote aus DEMSELBEN Prospekt (Diagnose 01.11.:
# Edeka 16 -> 48, dm 16 -> 32). Übernommen wird nur, was aus dem Prospekt der eigenen Händlerseite stammt.
KD_NEAR = {"edeka": ["Kandel", "Hagenbach", "Bellheim", "Herxheim", "Bad-Bergzabern"],
           "dm": ["Karlsruhe", "Ettlingen", "Rastatt"]}
KD_PUBLISHER = {"REWE": "rewe", "Netto Marken-Discount": "netto", "EDEKA": "edeka", "Lidl": "lidl",
                "ALDI SÜD": "aldi", "dm-drogerie markt": "dm", "dm": "dm", "DM": "dm", "Müller": "mueller"}
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

DROGERIE = (r"eyeliner|augenpads|augen-pads|augenpflege|kajal|concealer|gesichtsmaske|lippenbalsam|wimpern|lidschatten|foundation|duschgel|schaumbad|haarentfern|epilier|duschbad|dusche\b|shampoo|sp[üu]lung|conditioner|\bdeo\b|deodorant|deospray|antitranspirant|"
            r"zahncreme|zahnpasta|zahnb[üu]rste|zahnseide|mundsp[üu]l|(?<![a-zäöü])seife|fl[üu]ssigseife|handseife|cremeseife|bodylotion|k[öo]rperlotion|k[öo]rpermilch|body ?butter|"
            r"gesichtscreme|gesichtspflege|tagescreme|nachtcreme|handcreme|hautcreme|hautpflege|pflegecreme|sonnencreme|sonnenspray|lippenpflege|"
            r"massage(?:tool|roller|ball|b[üu]rste)|make-?up|mascara|lippenstift|nagellack|parfum|parf[üu]m|eau de|kosmetik|rasier|damenbinde|\bbinden\b|tampon|slipeinlage|"
            r"toilettenpapier|klopapier|toilettent[üu]cher|taschent[üu]cher|kosmetikt[üu]cher|k[üu]chenrolle|k[üu]chent[üu]cher|wattepad|wattest[äa]bchen|"
            r"haargel|haarspray|haarfarbe|haarpflege|styling|nivea|balea|isana|labello|elmex|colgate|blend-a-med|odol|gillette|wilkinson|"
            r"schauma|head ?& ?shoulders|garnier|l'or[ée]al|rexona|\baxe\b|zewa|hakle|tempo\b|always|o\.b\.")

CATS = [  # Reihenfolge = Priorität
    ("katze", r"katzen|\bkatze|sheba|whiskas|felix|kitekat|gourmet gold|perfect fit|catessy|cat'?s? ?(?:food|snack)"),
    ("drogerie", DROGERIE),
    ("tk", r"tiefk[üu]hl|eisbecher|ice cream|magnum|langnese|cremissimo|h[äa]+gen[ -]?dazs|nuggets|vanilleeis|die ofenfrische|pizzeria|iglo\b|coppenrath|fischst|\btk\b|tk-|gefroren|fischst[äa]bchen|pommes|eiscreme|\beis\b|speiseeis|pizza|kroketten|gyoza|dumplings|bibigo|ristorante|bistro baguette"),
    ("kaffee", r"kaffee|matcha|caf[eéè] latte|caff[eèé] latte|kamille|pfefferminztee|kr[äa]utertee|fr[üu]chtetee|(?<!eis)tee\b|kr[öo]nung|tchibo|jacobs|dallmayr|lavazza|melitta|espresso|cappuccino|crema|kapseln|kaffee-?pads|senseo|dolce gusto|nespresso|tassimo|\btee\b|teebeutel|kakao"),
    ("getraenke", r"getr[äa]nk|(?<!-)bier\b|(?<!trauben )\bhell\b|mixery|rockstar|granini|trinkgenuss|mocktail|black tower|biermarken|biersorten|helles\b|lager\b|export\b|krombacher|bitburger|veltins|paulaner|erdinger|beck'?s\b|radeberger|k[öo]nig pilsener|\blicher\b|jever|hasseröder|flensburger|franziskaner|hofbr[äa]u|warsteiner|pils\b|pilsener|radler\b|stubbi|weizenbier|weissbier|wei[ßs]bier|warsteiner|spaten|rothaus|tannenz[äa]pfle|m[öo]nchshof|budweiser|tyskie|corona|guinness|desperados|heineken|sternburg|br[äa]u\b|brauspezial|aperitif|aperol|lillet|bacardi|tequila|\bkorn\b|doppelkorn|kornmarken|edelbrand|obstbrand|destillat|schnaps|pastis|brandy|weinbrand|berentzen|wilthener|goldkrone|piccolo|henkell|zweigelt|m[üu]ller-thurgau|cuv[ée]e|rebsorten|7 ?up|pepsi|schwip schwap|fassbrause|hohes c|capri-sun|saftmarken|softdrink|adelholzener|spreequell|shots?\b|wasser\b|mineralwasser|saft\b|s[äa]fte\b|fruchtsaft|nektar|ouzo|amaro|kr[äa]uterlik|obstbrand|volvic|gerolsteiner|\bcola\b|limo\b|limonade|schorle|\bbier\b|pils|radler|weizenbier|hefeweizen|(?<![a-zäöüß])weine?\b|rotwein\b|wei[ßs]wein\b|ros[ée]wein\b|gl[üu]hwein\b|punsch\b|riesling\b|sekt\b|prosecco\b|secco|spirituos|lik[öo]r|whisk|wodka|vodka|\bgin\b|\brum\b|energy|eistee|smoothie|sprudel"),
    ("suess", r"s[üu][ßs]waren|s[üu][ßs]igkeiten|geb[äa]ck|knusperflocken|cashew|mandeln|macadamia|pistazie|pinienkern|studentenfutter|maronen|nougat|toffifee|[üu]berraschungs ?ei|marzipan|pl[äa]tzchen|kipferl|soft cake|jaffa|kinder country|kinder bueno|oreo|schoko|praline|bonbon|gummi|fruchtgummi|chips|snack|keks|cookie|riegel|waffel|lebkuchen|spekulatius|stollen|n[üu]sse\b|(?<!ge)n[üu]ss(?!ig)|erdn[üu]ss|popcorn|cracker|salzst|haribo|goldb[äa]ren|marshmallow|bahlsen|leibniz|milka\b|ritter sport|lindt|ferrero(?! milch)|merci\b"),
    ("fleisch", r"fleisch|chorizo|corned beef|serrano|jam[óo]n|landj[äa]ger|peitsche|pfefferbei[ßs]er|wagyu|patties|\bburger|-burger|griller|r[äa]ucherling|wurst|w[üu]rstchen|schinken|h[äa]hnchen|huhn|gefl[üu]gel|pute\b|puten|\brind(?!e\b|en\b)|rinder|schwein|\bhack|hackfleisch|steak|schnitzel|gulasch|salami|aufschnitt|leberk[äa]se|lachs|fisch(?!er)|forelle|thunfisch|garnele|shrimps|hering|kassler|filet|bacon|speck|saumagen|frikadell|braten\b|tafelspitz|nacken|kotelett|schweinehals|spareribs|ribs\b|\bleber\b|\bwade\b|\bente\b|entenbrust|entenkeule|entenschenkel|entenpfanne|\bgans\b|g[äa]nsebrust|g[äa]nsekeule|cordon bleu|entrec[ôo]te|kaninchen|h[üu]fte\b|roastbeef|pulled (?:beef|pork)|kabanos|\blamm(?!fell)|kalbs|hirsch|wildschwein"),
    ("kuehl", r"ehrmann|protein ?drink|proteindrink|high protein|milch|gr[üu]nl[äa]nder|cheddar|tilsiter|cr[eè]me fra[iî]che|gr[üu]tze|milkana|schmelzk|leerdammer|babybel|burlander|milram|k[äa]se|gouda|emmentaler|camembert|mozzarella|feta|joghurt|jogurt|quark|skyr|sahne|butter|margarine|\beier?\b|pudding|dessert|frischk[äa]se|kefir|molke|ziegen|\brama\b|sanella|l[äa]tta|schmand|buttermilch|appenzeller|grana padano|parmigiano|parmesan|bergader|bonifaz|bavaria blu|fol epi|patros|\bbrie\b|gorgonzola|halloumi|ricotta|mascarpone|actimel|frucht ?zwerge|mousse|\bbuko\b|k[æa]rg[åa]rden|\bfage\b|hummus"),
    ("vorrat", r"backmischung|backzutat|mohnf[üu]llung|tortenguss|pancake|oliven[öo]l(?!-?brot)|sonnenblumen[öo]l|raps[öo]l|speise[öo]l|\bmais\b|pfirsiche|tortelloni|cerealien|haferflocken|chia|noodles|nutella|schwartau|fonds?\b|honig(?!melone)|marmelade|konfit|nudel|pasta\b|teigwaren|spaghetti|lasagne|ravioli|gnocchi|tortiglioni|basmati|\breis\b|mehl\b|type 405|zucker|dressing|senf|mayo|ketchup|gew[üu]rz|gemahlen|chilisalz|\bfix\b|br[üu]he|suppe|heisse tasse|p[üu]ree|fertiggericht|konserve|essig|m[üu]sli|cornflakes|aufstrich|streichcreme|pflanzenfett|cremefine"),
    ("brot", r"brot(?!aufstrich|zeit|dose|kasten|messer|back|box)|kn[äa]cke|comtess|ciabatta|fladen|berliner|amerikaner|kruste|br[öo]tchen|toast|baguette|croissant|brezel|kuchen|backwaren|semmel|laugen|bagel|wrap"),
    ("obst", r"obst|datteln|pastinake|grapefruit|kaki\b|sharon|limette|passionsfrucht|pomelo|pampelmuse|sultanine|zitrus|petersilie|schnittlauch|basilikum|tomate|apfel|[äa]pfel|banane|kartoffel|salat|gurke|paprika|zwiebel|beere|traube|orange|mandarine|clementine|zitrone|k[üu]rbis|pilz|champignon|avocado|m[öo]hre|karotte|birne|kiwi|ananas|mango|melone|kohl|brokkoli|lauch|porree|spinat|zucchini|aubergine|radieschen|ingwer|pflaume|bohnen\b|buschbohnen|rote bete|schalotte|knoblauch|feldsalat|rucola|sellerie|fenchel"),
]
# Alles außer Essen & Drogerie. Reihenfolge = Priorität, gilt nur für Artikel ohne Lebensmittel-Hinweis der Quelle
NF_CATS = [
    # Spielzeug zuerst, sonst landet z. B. ein Kinder-Werkzeugset unter Garten & Heimwerken
    ("freizeit", r"rollenspiel|spielzeug|eisenbahn|kugelbahn|prinzessin|spielb[äa]ckerei|\bzug\b|holzlebensmittel|holz-?k[üu]che|holz k[üu]chen|spielk[üu]che|mini-k[üu]che|kinderk[üu]che|spielset|spieltier|spielk[üu]che|kindersofa|activity|lego|playmobil|puppe|pl[üu]sch|ballzauber"),
    ("tier", r"vitakraft|\bhund|katzenstreu|streu\b|vogel|nager|aquarium|tierbedarf|kratzbaum|halsband|\bleine\b"),
    ("baby", r"baby|windel|kinderwagen|schnuller|feuchtt[üu]cher"),
    ("haushalt", r"somat\b|sp[üu]lmaschinen|geschirrtabs|wasserenth[äa]rter|calgon|reinigungstab|waschmittel|weichsp[üu]l|reiniger|sp[üu]lmittel|geschirrsp[üu]l|putz|m[üu]llbeutel|frischhaltefolie|alufolie|backpapier|schw[äa]mm|wischmop|batterie|gl[üu]hbirne|leuchtmittel|haushalt|denkmit|duftspray|raumspray|raumduft|lufterfrisch|duftstecker|febreze|sodastream|co2-?zylinder|wassersprudler"),
    ("garten", r"garten|zaun|sichtschutz|terrassen|dielen\b|lamellendach|pavillon|carport|gew[äa]chshaus|ger[äa]tehaus|au[ßs]enbau|markise|maler-|(?<!& )orchidee|(?<!led-)weihnachtsstern|poinsettia|rosenstrau|blumenstrau|\bstrau[ßs]\b|amaryllis|ritterstern|calluna|heidekraut|\bheide\b|christrose|nieswurz|kaktus|sukkulente|\brosen?\b|freischneider|laubsauger|holzspalter|schwei[ßs]ger|\baxt\b|schleifer|werkbank|wagenheber|bagger|dumper|sauna|w[äa]rmekabine|streusalz|auftausalz|pflanze(?!nfett)|blume|\berde\b|d[üu]nger|rasen|grillrost|holzkohle|gasgrill|kugelgrill|elektrogrill|grillzange|werkzeug|bohr|schrauber|s[äa]ge\b|schrauben|heimwerk|leiter\b|\bauto\b|kfz|fahrrad|e-bike"),
    ("technik", r"k[üu]hlschrank|heizung|heizl[üu]fter|radiator|kamin\b|ventilator|klimager|mikrowelle|kontaktgrill|kontakt-grill|trockensauger|elektr|\btv\b|fernseher|laptop|notebook|tablet\b|smartphone|handy|kopfh[öo]rer|lautsprecher|kabel|ladeger|\bakku|powerbank|kamera|drucker|monitor|konsole|playstation|gaming|haartrockner|f[öo]hn\b|mixer\b|k[üu]chenmaschine|kaffeemaschine|wasserkocher|toaster|fritteuse|hei[ßs]luft|staubsauger|lampe|leuchte|\bled\b"),
    ("mode", r"\bboots\b|boxer|retroshorts|sohlen\b|kleid|hose\b|f[üu][ßs]ling|hausanzug|overall|jacke|mantel|pullover|pulli|shirt|bluse|socke|strumpf|unterw[äa]sche|\bslip|schuh|stiefel|sneaker|m[üu]tze|\bschal\b|handschuh|pyjama|schlafanzug|bekleidung|jeans|leggings|weste\b"),
    ("wohnen", r"badewanne|whirlpool|sanit[äa]r|waschbecken|duschkabine|\btopf\b|t[öo]pfe|topf-|gusstopf|eisentopf|kochtopf|back-?zubeh[öo]r|tee-set|br[äa]ter|kasserolle|backform|springform|backblech|r[üu]hrsch[üu]ssel|sch[üu]ssel|teller\b|becher\b|\bmug\b|tablett|servier|messerblock|seiher|trinkflasche|eisw[üu]rfel|teelicht|spannbett|bettw[äa]sche|laken\b|grillplatte|backzubeh[öo]r|licht\b|m[öo]bel|k[üu]chenutensil|\bkrug\b|glas\b|regal|tisch\b|stuhl|sofa|\bbett|kissen|decke\b|matratze|teppich|handtuch|gardine|vorhang|deko|weihnachtsbaum|kerze|vase|pfanne|\btopf|geschirr|besteck|gl[äa]ser\b|aufbewahrung|adventskalender"),
    ("freizeit", r"experimentier|bausteine|zaubertafel|modell-|spielzeug|spiel\b|spiele\b|lego|puppe|pl[üu]sch|puzzle|sport|fitness|yoga|camping|zelt|koffer|rucksack|\breisen?\b|rundreise|kreuzfahrt|urlaub|\bhotel|netto-reisen|\bbuch\b|(?:mal|eintrag|tage|notiz|kinder)buch|b[üu]cher|basteln"),
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
    # Audit 06.11.: auch Verbindungsabbrüche beim Lesen (RemoteDisconnected, IncompleteRead, ConnectionReset)
    # dürfen nicht die ganze Quelle beenden -> wie jeder andere Fehlabruf behandeln
    except (OSError, HTTPException, ValueError) as e:
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


# Alkohol eindeutig erkennen (vor allem anderen): Wein-Beschreibungen nennen sonst „passt zu Fisch“, „zu Pizza“ …
ALCOHOL = re.compile(r"\d+(?:[.,]\d+)?\s*%\s*vol|\b(?:aop|aoc|doc|docg|igp|igt|qba|q\.b\.a)\b|qualit[äa]tswein|pr[äa]dikatswein|"
                     r"\b(?:rot|wei[ßs]|ros[ée]|schaum|perl|gl[üu]h|dessert|land)wein\b|\b(?:tempranillo|merlot|cabernet|chardonnay|sauvignon|"
                     r"riesling|grauburgunder|sp[äa]tburgunder|wei[ßs]burgunder|dornfelder|primitivo|rioja|chianti|lambrusco|prosecco|cr[ée]mant|"
                     r"champagner|cava|bordeaux|c[ôo]tes du|pinot|syrah|shiraz|zinfandel|malbec|lugana|chablis)\b", re.I)
# Händler-Kategorien (kaufDA/Lidl, z. B. „Tierfutter / Hundefutter“): zweitbester Hinweis nach dem Artikelnamen
CAT_HINTS = [
    ("katze", r"katzenfutter|katzennahrung|katzensnack"),
    ("tier", r"hundefutter|hunde ?snacks|katzenstreu|vogelfutter"),
    ("getraenke", r"(?:sekt|wein|lik[öo]r|whiske?y|wodka|rum|gin|saft|wasser|bier|softdrink|korn|weinbrand|spirituosen|cola|limo)marken|\bwein\b|alkoholische getr|spirituosen|\bbier\b|wassermarken|mineralwasser|softdrinks|limonade|s[äa]fte\b|fruchtsaft|energy ?drinks?"),
    ("freizeit", r"reiseangebote|\breisen\b|spielzeug|mini-k[üu]che|spielk[üu]che"),
    ("technik", r"k[üu]chenkleinger[äa]te|mikrowelle|elektroger[äa]te|unterhaltungselektronik"),
    ("wohnen", r"t[öo]pfe und pfannen|\btopf\b|m[öo]bel|t[üu]r ?zubeh[öo]r|adventsgesteck|weihnachtsgesteck|dekoleuchten|kerzen|wohnaccessoires"),
    ("garten", r"b[äa]ume|str[äa]ucher|zimmerpflanzen|gartenpflanzen|blumen\b|schnittblumen"),
    ("obst", r"\bkr[äa]uter\b|petersilie|gem[üu]se\b|obst\b"),
    ("tk", r"tiefk[üu]hl|speiseeis|eiscreme"),
    ("kuehl", r"\bk[äa]se\b|milchprodukte|joghurt|\bsahne\b|milchdessert|pudding|milchdrink"),
    ("brot", r"\bbrot\b|geb[äa]ck|kuchengeb[äa]ck|donuts"),
    ("fleisch", r"\bfleisch\b|wurst|gefl[üu]gel|\bfisch\b|fast food|hot dog"),
]


# Geräte sind kein Essen, auch wenn „Kaffee“ oder „Pizza“ im Namen steht (Kaffeevollautomat, Pizzaofen, Wasserkocher).
# Spielzeug-Geräte (Kinder-Pizzaofen, Spiel-Tischgrill) -> Freizeit.
APPLIANCE = re.compile(r"(?:kaffee|espresso|tee|milch|wasser|cappuccino|latte)-?(?:voll)?(?:automat|maschine|kocher|m[üu]hle|aufsch[äa]umer|bereiter)|"
                       r"siebtr[äa]ger|vollautomat|kaffeemaschine|pad-?maschine|kapselmaschine|pizza-?ofen|back-?ofen|mini-?ofen|d[öo]rr-?automat|"
                       r"tischgrill|kontakt-?grill|raclette|fondue-?set|fritteuse|airfryer|toaster|sandwichmaker|waffeleisen|handmixer|standmixer|"
                       r"st[äa]bmixer|zerkleinerer|k[üu]chenmaschine|eierkocher|reiskocher|slow-?cooker|multikocher|thermomix|monsieur cuisine|"
                       r"entsafter|smoothie-?maker|joghurtbereiter|popcorn-?maschine|vakuumierer|elektrogrill|induktionskochplatte|kochplatte")
TOY = re.compile(r"spielzeug|kinder|lupilu|playtive|spiel|zaubertopf")


def appliance(title, cats=None):
    ct = " / ".join(c for c in (cats or []) if isinstance(c, str)).lower()
    t = (title or "").lower()
    if not APPLIANCE.search(t + " / " + " / ".join(c for c in (cats or [])[-2:] if isinstance(c, str)).lower()):
        return None
    if re.search(r"pizza|brot|br[öo]tchen|fisch|lachs|k[äa]se|chips|kartoffel", t) and not APPLIANCE.search(t):
        return None  # Steinofenpizza: Warengruppe nennt evtl. Ofen, der Name ist aber Essen
    return "freizeit" if TOY.search(t + " / " + ct) else "technik"


# Eindeutige Fälle vor allen anderen Regeln, egal ob die Quelle „Lebensmittel“ sagt (01.11. geprüft):
# Mila's-World-Kroketten sind Katzenfutter, Erdtmanns ist Vogelfutter, Lupilu-Bohrhammer ist Spielzeug,
# Zuckerhutfichte ist eine Pflanze (nicht Vorrat wegen „Zucker“), Schneebesen ist Küchenzubehör, Garn ist Basteln.
SPECIAL = [
    ("katze", re.compile(r"^(?!.*streu).*mila'?s world")),
    ("tier", re.compile(r"max'?s world|erdtmann|vogelfutter|streufutter|fettfutter|wildvogel|meisenkn[öo]del|futterstelle|futterhaus")),
    ("freizeit", re.compile(r"hot wheels|mattel|lupiblox|playtive|\blego\b|playmobil|toylino|ravensburger|hasbro|schleich|vtech|fisher-?price|lego duplo|"
                            r"bastel|laubs[äa]ge|gravier|(?<![a-zäöüß])garn\b|-garn\b|strickgarn|strickwolle|wollkn[äa]uel|h[äa]kel|polymer|ton-set|gie[ßs]pulver|crelando|n[äa]hset")),
    ("haushalt", re.compile(r"\btesa(?:film)?\b|klebeband|geschenkband|geschenkpapier|kraftpapier|geschenkt[üu]te|weihnachtst[üu]te|beschriftungsger|etikettierger|schreibwaren")),
    ("garten", re.compile(r"gardenline|(?<!badezusatz )(?:zuckerhut-?)?fichten?\b|zuckerhut-?fichte|chamaecyparis|scheinzypresse|zypresse|konifere|nadelgeh[öo]lz|\bthuja|nordmann|"
                          r"hortensie|alpenveilchen|\bprimel|stiefm[üu]tterchen|blumenzwiebel")),
    ("wohnen", re.compile(r"schneebesen|backhelfer|teigschaber|teigrolle|nudelholz|ausstecher|spritzbeutel|backformen|silikon-?backform|\bcrofton\b|\bernesto\b")),
]
SPECIAL_NOT = re.compile(r"\b(?:bad|badezusatz|duft|kerze|[öo]l|tee|sirup|bonbon)\b|duftkerze|nadel[öo]l")


def special(title, brand="", cats=None):
    name = f"{title or ''} {brand or ''}".lower()
    ct = " / ".join(c for c in (cats or [])[-2:] if isinstance(c, str)).lower()
    for key, rx in SPECIAL:
        if rx.search(name) and not (key == "garten" and SPECIAL_NOT.search(name)):
            if key == "freizeit" and re.search(NF_CATS[6][1], name) and not re.search(r"spiel|puppe", name):
                return "mode"   # Hot-Wheels-Shirt ist Kleidung
            return key
    # Warengruppe „Spielzeug“ (Kinder-Bohrhammer, Spielzeug-Blumenstrauß) – nicht bei Katzen-/Hundespielzeug
    if re.search(r"spielzeug|spielwaren", ct) and not re.search(r"katze|hund|tier", name + ct) and not re.search(NF_CATS[6][1], name):
        return "freizeit"
    return None


def classify(title, brand="", food=True, cats=None):
    """Kevins Vorgabe: Die Beschreibung (Werbetext, „passt zu Fisch“) beeinflusst die Kategorie NICHT.
    Es zählen nur Artikelname, Marke und die zwei genauesten Warengruppen des Händlers (z. B. „Mischbrot“).
    Reihenfolge: Alkohol -> Name + Marke -> Händler-Warengruppe. food=False: Non-Food-Regeln zuerst."""
    name = GENERIC.sub(" ", f"{title or ''} {brand or ''}".lower())
    ct = " / ".join(c for c in (cats or [])[-2:] if isinstance(c, str)).lower()
    ident = name + " / " + ct
    # Katzen-Motiv auf Socken/Shirt ist Kleidung, kein Katzenbedarf (01.11.: dm-Socken landeten bei Katze)
    if re.search(r"katze", ident) and not re.search(r"streu|spielzeug|kratz|toilette|motiv", ident) and not re.search(NF_CATS[6][1], name):
        return "katze"
    # genaueste Warengruppe „Hundefutter“ schlägt den Namen („Rinder-Herzen“ von ZooRoyal ist Hundefutter)
    if re.search(r"hundefutter|hundenahrung|hunde ?snack|katzenfutter|katzennahrung|zooroyal|vitakraft|pedigree|chappi|rinti|frolic|animonda|beneful", ident):
        return "katze" if re.search(r"katze", ident) else "tier"
    sp = special(title, brand, cats)
    if sp:
        return sp
    dev = appliance(title, cats)
    if dev:
        return dev
    if re.search(r"donuts?\b|muffins?\b", name) and not re.search(NF_CATS[6][1] + r"|motiv|kerze|deko|kissen|spiel|form", name):
        return "brot"
    if food:
        # zusammengesetzte Namen: Käse-Aufschnitt ist Käse, Schinken-Croissant ist Backware
        if re.search(r"croissant|br[öo]tchen|baguette|brezel|laugenst|(?<!leb)kuchen\b|\btorte\b", name) and not re.search(r"salami|wurst", name) and not re.search(r"tiefgefr|tk\b|flammkuchen|ristorante|bistro baguette|backmischung", name):
            return "brot"  # 02.11.: Dr. Oetker Bistro Baguette/Ristorante Flammkuchen = Tiefkühl, Backmischung = Vorrat
    # Käse ist Käse, auch wenn die Quelle „kein Lebensmittel“ sagt (Arla Pizzakäse landete unter Tiefkühl)
    if not re.search(r"reibe|glocke|messer|brett|hobel|fondue|dose|laugen|br[öo]tchen|croissant|brezel|stange", name) and re.search(r"k[äa]se", name) and not re.search(r"leberk[äa]se|fleischk[äa]se|wurst|schinken|salami|kuchen|torte|nuggets|chips|cracker|sticks|tiefgefr|\btk\b", name):
        return "kuehl"
    if re.search(r"gutschein|geschenkkarte|guthabenkarte", name):
        return "sonstiges"
    if "langnese" in ident and "honig" in ident:
        return "vorrat"  # Langnese gibt es als Honig und als Eis
    if ALCOHOL.search(ident) and not re.search(r"glas|gl[äa]ser|k[üu]hler|dekanter|essig|sauce|so[ßs]e", name):
        return "getraenke"
    nf = [("drogerie", DROGERIE)] + NF_CATS
    first, second = (CATS, nf) if food else (nf, CATS)
    for rules in (first, second):  # erst die passende Welt (Lebensmittel bzw. Non-Food), dann die andere
        for key, rx in rules:
            if re.search(rx, name):
                return key
        keys = {k for k, _ in rules}
        for key, rx in [h for h in CAT_HINTS if h[0] in keys] + rules:  # nur Hinweise dieser Welt
            if ct and re.search(rx, ct):
                return key
    # letzte Chance vor der Notlösung: alle Warengruppen des Händlers (z. B. „Whiskey“ weiter oben in der Liste)
    ca = " / ".join(c for c in (cats or []) if isinstance(c, str)).lower()
    for rules in (first, second):
        for key, rx in rules:
            if ca and key != "tier" and re.search(rx, ca):
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


def pack_unit_price(price, text):
    """Kein Grundpreis im Prospekt, aber genau eine Packungsgröße („1-l-Pckg.“, „500 g“) -> Preis je kg/l ausrechnen.
    Nie bei Mehrfachpackungen („6 x 1,5 l“), Spannen („87/90/92 g“) oder mehreren Größen (Kevin 01.11.: Milch ohne Grundpreis)."""
    t = (text or "").replace("–", "-")
    if not price or re.search(r"\d\s*[x×]\s*\d", t, re.I):
        return None
    hits = re.findall(r"(?<![\d/,.])(\d+(?:[.,]\d+)?)\s*-?\s*(kg|g|ml|l|liter)\b(?!\s*[/-]\s*\d)", t, re.I)
    sizes = {(float(v.replace(",", ".")), u.lower()) for v, u in hits}
    if len(sizes) != 1 or re.search(r"\d\s*(?:/|-|bis)\s*\d+(?:[.,]\d+)?\s*-?\s*(?:kg|g|ml|l)\b", t, re.I):
        return None
    v, u = sizes.pop()
    amt, unit = (v / 1000, "kg") if u == "g" else (v / 1000, "l") if u == "ml" else (v, "l" if u in ("l", "liter") else "kg")
    if amt <= 0:
        return None
    return round(price / amt, 2), unit


def fake_old(price, old, up, text):
    """kaufDA liefert als „statt“-Preis manchmal den Kilo-/Literpreis oder den Preis der ganzen Packung
    (10 x 0,75 € -> „statt 7,50 €“). Das ist kein Rabatt."""
    if not price or not old:
        return False
    if up and abs(float(up[0]) - float(old)) < 0.006:
        return True
    for n in re.findall(r"(\d+)\s*[x×]\s*\d", text or ""):
        if 1 < int(n) <= 48 and abs(price * int(n) - old) < 0.02:
            return True
    # „250 – 750 ml“ für 1,49 € „statt 4,47 €“: gleicher Grundpreis, „statt“ = Preis der größeren Packung
    if up:
        sz = [float(v.replace(",", ".")) / (1000 if u.lower() in ("g", "ml") else 1)
              for v, u in re.findall(r"(\d+(?:[.,]\d+)?)\s*(?=(?:(?:-|–|/|bis)\s*\d+(?:[.,]\d+)?\s*)*(kg|g|ml|l|liter)\b)", text or "", re.I)]
        g = float(up[0])
        if any(abs(g * v - old) < 0.02 for v in sz) and any(abs(g * v - price) < 0.02 for v in sz):
            return True
    return False


def offer(store, title, price, *, brand=None, desc="", old=None, base=None, img=None, start=None, end=None,
          app=None, extra=None, src="", url=None, food=True, app_only=None, bonus_only=None, img_large=None, info=None, cats=None, page=None, images=None, brochure=None, uvp=None):
    title = re.sub(r"\s+", " ", (title or "").strip())
    if not title or ((not price or price <= 0) and not bonus_only):
        return None
    price = price or 0
    up = unit_price(base) if isinstance(base, str) else base
    if not up:
        up = pack_unit_price(price, f"{title} {desc or ''}")
    if old and fake_old(price, old, up, f"{title} {desc or ''}"):
        old = None
    o = {
        "s": store,
        "n": title,
        "b": (brand or "").strip() or None,
        "d": re.sub(r"\s+", " ", (desc or "").strip())[:300],
        "c": classify(title, brand, food, cats),
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
    if o["o"] and uvp is not None:
        # „statt“-Preis = UVP des Herstellers (1) oder eigener früherer Preis des Markts (0).
        # Eigener Preis: laut Preisangabenverordnung § 11 der niedrigste Preis der letzten 30 Tage.
        o["ou"] = 1 if uvp else 0
    if app_only:
        o["ao"] = app_only        # Preis gilt nur mit dieser App/Karte
    if bonus_only:
        o["bo"] = bonus_only      # Bonus-Aktion: so viel Guthaben gibt es, Preis steht nicht im Prospekt
    o["id"] = f"{store}-{norm(title)[:40]}-{int(o['p'] * 100)}"
    return o


# Alle Artikelnamen, die beim Abruf vorbeikommen (auch ohne Rabatt): für die Vorschläge in Suche und Merkliste
SEEN_NAMES = {}  # Name -> Bild (für die Vorschläge beim Tippen)
SEEN_ST = {}  # Name -> Markt (Vorschläge im Zettel nur aus dem Sortiment des gewählten Markts)


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
            try:
                d = json.loads(raw)
            except ValueError:  # abgeschnittene Antwort/Fehlerseite statt JSON
                log("  ! Lidl: keine gültige Antwort bei offset", offset)
                return
            got = d.get("items") or []
            yield from got
            offset += len(got)
            if not got or offset >= int(d.get("numFound") or 0):
                return

    for q in ("&category.id=10068374", "&q=katzenfutter", "&q=katzennahrung", "&q=duschgel", "&q=deo",
              "&q=shampoo", "&q=zahncreme", "&q=toilettenpapier", "&q=kosmetik"):
        for it in pages(q):
            g = (it.get("gridbox") or {}).get("data") or {}
            if g.get("store") is False:
                continue  # nur online erhältlich (lidl.de: store=false) -> nicht im Markt
            pr = g.get("price") or {}
            dd = pr.get("discount") or {}
            # „statt“-Preis: oldPrice, sonst deletedPrice (z. B. bei UVP-Angeboten fehlt oldPrice)
            p, old = pr.get("price"), pr.get("oldPrice") or dd.get("deletedPrice")
            disc = dd.get("showDiscount")
            # fromRecommendedPrice: True = „statt“ ist die UVP, False = eigener früherer Lidl-Preis
            uvp = dd.get("fromRecommendedPrice") if isinstance(dd.get("fromRecommendedPrice"), bool) else None
            plus = None
            for lp in g.get("lidlPlus") or []:
                v = (lp.get("price") or {}).get("price") if isinstance(lp.get("price"), dict) else lp.get("price")
                if isinstance(v, (int, float)):
                    plus = v
            if g.get("fullTitle") or g.get("title"):
                _t = re.sub(r"\s+", " ", (g.get("fullTitle") or g.get("title")).strip())
                SEEN_NAMES[_t] = g.get("image") or ""
                SEEN_ST[_t] = "lidl"
            if not (disc or (old and p and old > p) or plus):
                continue  # nur Angebote
            kf = g.get("keyfacts") or {}
            bp = pr.get("basePrice") or {}
            o = offer("lidl", g.get("fullTitle") or g.get("title"), p, old=old,
                      base=(bp.get("price"), (bp.get("unit") or "").lower()) if bp.get("price") else None,
                      img=g.get("image"), start=pr.get("startDate"), end=pr.get("endDate"), app=plus,
                      src="lidl.de", url="https://www.lidl.de" + (g.get("canonicalUrl") or ""),
                      info=" ".join(v for v in (kf.values() if isinstance(kf, dict) else []) if isinstance(v, str)),
                      cats=[c for c in (g.get("category"), kf.get("wonCategoryPrimary")) if isinstance(c, str) and c] or None,
                      food=q == "&category.id=10068374", uvp=uvp)
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


ALDI_DAY = re.compile(r'href="(?:https://www\.aldi-sued\.de)?(/(?:de/)?angebote/(20\d\d-\d\d-\d\d))(?:\.html)?"')


def aldi_days(html):
    """Tagesseiten mit Aktionen („/angebote/2026-11-02“) – darüber stehen auch die Angebote der nächsten Woche."""
    return sorted({(m.group(2), m.group(1)) for m in ALDI_DAY.finditer(html or "")})


def aldi_items(html, day=None):
    m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html or "", re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except ValueError:
        return []
    out = []
    for i, v in enumerate(data):
        if not (isinstance(v, dict) and "price" in v and "name" in v and "sku" in v):
            continue
        it = nuxt_resolve(data, i)
        if day and not it.get("onSaleDate"):
            it["onSaleDate"] = day  # Tagesseite: Starttag aus der Adresse
        out.append(it)
    return out


# Rubrik „Wochenangebote“ (Frische-, Marken-, Eigenmarken-Angebote der Woche, ~125 Artikel; die Unterrubriken sind Teilmengen)
ALDI_WEEK = "https://www.aldi-sued.de/produkte/wochenangebote/k/1588161426582123"


def aldi_pages(url, day=None, first=None, limit=15):
    """Aldi-Seite samt allen Folgeseiten (?page=2 …). Tages- und Rubrikseiten zeigen nur 30 Artikel je Seite
    (03.11.: Fr 06.11. = 103 Artikel auf 5 Seiten, bis dahin wurde nur Seite 1 gelesen)."""
    out, skus = [], set()
    for p in range(1, limit + 1):
        if p == 1 and first is not None:
            h = first
        else:
            time.sleep(PAUSE)
            h = http(url + (("&" if "?" in url else "?") + f"page={p}" if p > 1 else ""))
        got = aldi_items(h, day)
        new = [it for it in got if it.get("sku") not in skus]
        if not new:
            break
        skus.update(it.get("sku") for it in new)
        out += new
    return out


def fetch_aldi():
    out, seen = [], set()
    h = http("https://www.aldi-sued.de/de/angebote.html")
    if not h:
        return out
    items = aldi_items(h)
    if not items:
        log("  ! Aldi: keine Daten in der Seite gefunden")
    # zusätzlich jede verlinkte Tagesseite, vor allem die künftigen (nächste Woche), mit allen Folgeseiten
    today = dt.date.today().isoformat()
    for day, path in aldi_days(h):
        if day < today:
            continue
        got = aldi_pages(f"https://www.aldi-sued.de{path}", day)
        if not got:
            got = aldi_pages(f"https://www.aldi-sued.de/de/angebote/{day}.html", day)
        log(f"  Aldi Tagesseite {day}: {len(got)} Artikel")
        items += got
    got = aldi_pages(ALDI_WEEK)
    log(f"  Aldi Wochenangebote: {len(got)} Artikel")
    items += got
    dated = {it.get("sku") for it in items if it.get("onSaleDate")}
    for it in items:
        key = (it.get("sku"), str(it.get("onSaleDate"))[:10])
        if key in seen or (not it.get("onSaleDate") and it.get("sku") in dated):
            continue  # ohne Datum doppelt zu einer Tagesseite -> die mit Datum behalten
        seen.add(key)
        o = aldi_offer(it)
        if o:
            out.append(o)
    log("Aldi Süd:", len(out))
    return out


def aldi_offer(it):
    """Ein Aldi-Artikel aus __NUXT_DATA__ -> Angebot (auch vom Prospekt-Wächter genutzt)."""
    if it.get("isDropship"):
        return None  # Online-Ware (Lieferung direkt vom Hersteller), nicht im Markt
    if any(re.search(r"regional verf|nur online", str(b.get("displayText") or ""), re.I)
           for g in it.get("badges") or [] if isinstance(g, dict) for b in g.get("items") or [] if isinstance(b, dict)):
        return None  # „Regional verfügbar“: nicht sicher, dass es das in Wörth gibt (Kevin 03.11.)
    pr = it.get("price") or {}
    amount = pr.get("amountRelevant") or pr.get("amount")
    if not amount:
        return None
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
              url=f"https://www.aldi-sued.de/de/produkt/{it.get('urlSlugText')}-{it.get('sku')}.html",
              food=food_hint)
    return o


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
    try:
        pi = (((json.loads(m.group(1)).get("props") or {}).get("pageProps") or {}).get("pageInformation") or {})
    except (ValueError, AttributeError):
        return [], 0
    main = (pi.get("offers") or {}).get("main") or {}
    items = main.get("items") or []
    br = pi.get("brochures") or {}
    note_online(br)
    links = ((((pi.get("template") or {}).get("content") or {}).get("OfferLinkbox") or {}).get("PublisherOfferLinkbox") or {}).get("links") or []
    KD_INFO[url] = {
        "brochures": _ids([br.get("viewer"), br.get("publisher")], set()) | {str((it.get("parentContent") or {}).get("id")) for it in items},
        "links": [l.get("link_href") for l in links if isinstance(l, dict) and l.get("link_href")],
        "known": {(str((it.get("parentContent") or {}).get("id")),) + flyer_key(it) + (kd_price(it),) for it in items},
        "pubs": {it.get("publisherId") for it in items if it.get("publisherId")},  # Händler-Kennung, z. B. EDEKA = DE-220164
        "future": any(str((b or {}).get("validFrom") or "")[:10] >= dt.date.today().isoformat()
                      for key in ("viewer", "publisher") for b in (br.get(key) if isinstance(br.get(key), list) else [])),
    }
    return items, int(main.get("totalItems") or 0)


def kd_items(url):
    """Angebote einer kaufDA-Seite. Weiterblättern gibt es nicht (?page= liefert dieselben 16),
    deshalb kommen die übrigen Angebote über die Sortiment-Seiten (fetch_sortiment)."""
    items, total = kd_page(url)
    if total > len(items) and url in KD_STORES.values():
        log(f"  {url.split('/')[-2]}: {len(items)} von {total} Angeboten auf der Händlerseite")
    return items


def scheck_flyers():
    """Prospekt-IDs von Scheck-In Wörth: was die Händlerseite gerade zeigt + Prospekt-Gedächtnis (flyers.json)"""
    return {b for b in KD_INFO.get(KD_STORES["scheck"], {}).get("brochures", set()) if b and b != "None"} | local_flyers("scheck")


def kd_store(it):
    """Markt eines kaufDA-Angebots. Scheck-In läuft bei kaufDA als „EDEKA“ -> über die Prospekt-ID unterscheiden."""
    st = KD_PUBLISHER.get(it.get("publisherName"))
    if st == "edeka" and str((it.get("parentContent") or {}).get("id")) in scheck_flyers():
        return "scheck"
    return st


APP_COND = re.compile(r"lidl\s*plus|app[- ]?preis|mit (der )?app|netto[- ]?app|payback|deutschlandcard|kundenkarte|coupon", re.I)
APP_LABEL = {"lidl": "Lidl Plus", "edeka": "Edeka-App", "netto": "Netto-App", "rewe": "Rewe-App", "dm": "dm-App", "aldi": "Aldi-App", "mueller": "Müller-App", "zookauf": "Zookauf-Karte"}
APP_HINT = re.compile(r"(?:mit\s+(?:der\s+)?app|app[- ]preis|rewe\s+bonus|lidl\s+plus|netto[- ]app)[^0-9]{0,25}(\d+)[,.](\d\d)", re.I)


# Kevin 03.11.: keine Online-Angebote, nur was man direkt im Markt bekommt (gilt für alle Märkte)
ONLINE_ONLY = re.compile(r"nur\s+(?:im\s+)?online(?:[- ]?shop)?\b|online[- ]?exklusiv|exklusiv\s+online|nur\s+im\s+online[- ]?shop"
                         r"|nicht\s+in\s+(?:der|den)\s+filiale|nur\s+auf\s+\w+\.de\b", re.I)


def online_only(txt):
    return bool(ONLINE_ONLY.search(txt or ""))


ONLINE_IDS = set()  # Angebots-IDs, die kaufDA als „Nur online“ führt -> auch gespeicherte Exemplare fliegen raus
ONLINE_BIDS = set()  # Prospekt-IDs reiner Online-Prospekte (03.11.: Netto „netto-online.de - Exklusive Angebote“)


def note_online(br):
    """Online-Prospekte aus den Prospekt-Listen einer kaufDA-Seite merken (Titel mit „online“, z. B. netto-online.de)."""
    for key in ("viewer", "publisher"):
        for b in br.get(key) if isinstance(br.get(key), list) else []:
            if isinstance(b, dict) and re.search(r"online", str(b.get("title") or ""), re.I):
                ONLINE_BIDS.update(str(b[k]) for k in ("id", "contentId", "legacyId") if b.get(k))


def kd_offer(it):
    """kaufDA-Angebot; „Nur online“ (prices.description/conditions) -> None (Kevin 03.11.: nur was man im Markt bekommt,
    „Auch online“ bleibt)."""
    pr = it.get("prices") or {}
    o = _kd_offer(it)
    if o and str((it.get("parentContent") or {}).get("id")) in ONLINE_BIDS:
        ONLINE_IDS.add(o["id"])
        return None
    if o and online_only(" ".join([str(pr.get("description") or ""), it.get("description") or "", it.get("title") or ""]
                                  + [str(c.get("other") or "") for c in pr.get("conditions") or [] if isinstance(c, dict)])):
        ONLINE_IDS.add(o["id"])
        return None
    return o


def _kd_offer(it):
    store = kd_store(it)
    if not store:
        return None
    paths = it.get("categoryPaths") or []
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
                 src="kaufda.de", food=food_hint,
                 app_only=app_only, bonus_only=bonus_only, info=it.get("description"),
                 cats=[n.get("name") for p in paths for n in p if isinstance(n, dict)][-3:] + list(it.get("categories") or []),
                 page=((it.get("parentContent") or {}).get("page") or {}).get("number"),
                 brochure=(it.get("parentContent") or {}).get("id"),
                 uvp=pr.get("secondaryPriceIsUVP") if isinstance(pr.get("secondaryPriceIsUVP"), bool) else None)


# ---------- meinprospekt.de (gleiche Bonial-Daten wie kaufDA, andere Auswahl) ----------
# 03.11. (Kevin: „mehr Edeka und dm, legal“): meinprospekt.de zeigt dieselben Prospekt-Angebote wie kaufDA, aber
# - je Ort eine feste andere Auswahl von 12 (Edeka Jockgrim + Nachbarorte: 71 Jockgrim-Angebote, davon 12 neu) und
# - Stichwortseiten /angebote/<begriff>/dm-de (804 Begriffe laut Sitemap; Vollscan 03.11.: 43 Angebote aus dem
#   dm-Prospekt, davon 24 neu). Edeka-Stichwortseiten zeigen nur Südbayern (München) -> nicht nutzen.
# robots.txt erlaubt /angebote/… und Ortsseiten (verboten: /shelf, /contentViewer, /search, /webapp …).
# Die Angebote laufen durch dieselben Filter wie kaufDA (dm: nur eigene Prospekt-IDs, Edeka: same_flyer).
# Gedächtnis docs/data/mp-terms.json: Begriffe mit Treffer jedes Mal, die übrigen reihum (MP_ROTATE je Lauf).
MP = "https://www.meinprospekt.de"
# Edeka: jeder Ort zeigt 12 Angebote, Orte mit gleichem Prospekt teils andere 12 (Scan 03.11. über 130 Orte)
MP_CITY = {"edeka": ["jockgrim", "kandel", "hagenbach", "bellheim", "ruelzheim", "bad-bergzabern", "karlsruhe",
                     "germersheim", "lingenfeld", "steinweiler", "leimersheim", "scheibenhardt", "hoerdt", "rastatt",
                     "bruchsal", "linkenheim-hochstetten", "eggenstein-leopoldshafen"],
           "dm": ["kandel", "germersheim", "bad-bergzabern", "karlsruhe"]}
MP_TERM_SLUG = {"dm": "dm-de"}
MP_ROTATE = int(os.environ.get("SR_MP_ROTATE", "1000"))  # 03.11.: alle Begriffe je Abruf (läuft parallel zu kaufDA, ~27 min)
MP_PAUSE = 2.0
MP_ITEMS = {}  # Markt -> Bonial-Angebote (füllt der Thread, fetch_kaufda reicht sie an fetch_sortiment weiter)


def mp_items(url):
    h = http(url)
    time.sleep(MP_PAUSE)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h or "", re.S)
    if not m:
        return None
    try:
        pi = json.loads(m.group(1))["props"]["pageProps"]["pageInformation"]
    except Exception:
        return None
    return ((pi.get("offers") or {}).get("main") or {}).get("items") or []


def mp_terms(slug, mem):
    """Stichwortseiten eines Händlers aus der Sitemap (rpp-sitemap-N.xml); fällt sie aus, die gemerkte Liste"""
    terms = []
    for n in range(1, 6):
        x = http(f"{MP}/sitemaps/rpp-sitemap-{n}.xml")
        time.sleep(MP_PAUSE)
        if not x or "<loc>" not in x:
            break
        terms += re.findall(rf"<loc>{re.escape(MP)}/angebote/([^/<]+)/{re.escape(slug)}</loc>", x)
    return list(dict.fromkeys(terms)) or list(mem.get("all", []))


def fetch_meinprospekt():
    mem = load("mp-terms.json", {})
    today = dt.date.today().isoformat()
    for store, cities in MP_CITY.items():
        n = 0
        for c in cities:
            items = mp_items(f"{MP}/{c}/{'edeka' if store == 'edeka' else 'dm-de'}") or []
            MP_ITEMS.setdefault(store, []).extend(items)
            n += len(items)
        log(f"  meinprospekt {store}: {n} Angebote von {len(cities)} Ortsseiten")
    for store, slug in MP_TERM_SLUG.items():
        m = mem.setdefault(store, {})
        terms = mp_terms(slug, m)
        m["all"] = terms
        hit, chk = m.setdefault("hit", {}), m.setdefault("chk", {})
        old = (dt.date.today() - dt.timedelta(days=21)).isoformat()
        hot = [t for t in terms if hit.get(t, "") >= old]
        cold = sorted((t for t in terms if t not in hot), key=lambda t: chk.get(t, ""))[:MP_ROTATE]
        got, t_end = 0, time.time() + 25 * 60  # rechtzeitig vor dem Warten in fetch_kaufda (30 min) fertig werden
        for t in hot + cold:
            if time.time() > t_end:
                log(f"  meinprospekt {store}: Zeit um, Rest beim nächsten Abruf")
                break
            items = mp_items(f"{MP}/angebote/{urllib.parse.quote(t)}/{slug}")
            if items is None:
                continue
            chk[t] = today
            if items:
                hit[t] = today
                got += len(items)
                MP_ITEMS.setdefault(store, []).extend(items)
        for d in (hit, chk):  # Begriffe, die es nicht mehr gibt, vergessen
            for t in [t for t in d if t not in terms]:
                d.pop(t)
        log(f"  meinprospekt {store}: {got} Angebote von {len(hot)} Treffer- + {len(cold)} weiteren Stichwortseiten"
            f" ({len(terms)} Begriffe)")
    save("mp-terms.json", mem)


def fetch_kaufda():
    out = []
    mp = threading.Thread(target=fetch_meinprospekt, daemon=True)
    mp.start()
    pages = list(KD_STORES.values())
    near = {f"https://www.kaufda.de/{city}/{'/'.join(KD_STORES[st].split('/')[4:])}": st for st, cities in KD_NEAR.items() for city in cities}
    pages += list(near)
    near_n = 0
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
        if url in near:
            home = {b for b in KD_INFO.get(KD_STORES[near[url]], {}).get("brochures", set()) if b and b != "None"} | local_flyers(near[url])
            for it in items:
                if str((it.get("parentContent") or {}).get("id")) in home and kd_store(it) == near[url]:
                    o = kd_offer(it)
                    if o:
                        out.append(o)
                        collect([o])
                        near_n += 1
            continue
        for it in items:
            st = kd_store(it)
            if url not in KD_STORES.values() and st in regional:
                regional[st].append(it)
                continue
            o = kd_offer(it)
            if o:
                out.append(o)
                collect([o])
        if n == len(KD_STORES):
            early_save("kaufDA-Händlerseiten")
        if n % 20 == 0:
            log(f"  kaufDA: {n}/{len(pages)} Seiten")
    log(f"  kaufDA Nachbarorte (gleicher Prospekt): {near_n} Angebote")
    mp.join(timeout=1800)
    for st, items in list(MP_ITEMS.items()):  # meinprospekt: dieselben Filter wie die Sortiment-Seiten
        regional.setdefault(st, []).extend(it for it in items if kd_store(it) == st)
    more, accepted = fetch_sortiment(regional)
    out += more
    log("kaufDA:", len(out), "(vor Duplikat-Bereinigung)")
    return out


# kaufDA zeigt auf der Händlerseite nur 16 Angebote. Die öffentlichen Sortiment-Seiten
# (kaufda.de/<Händler>/Sortiment/<Begriff>) zeigen je Begriff alle passenden Angebote des Händlers.
# Sie sind bundesweit -> nur Angebote aus Prospekten behalten, die auch für Wörth/Jockgrim gelten.
KD_PUB_IDS = {"edeka": "DE-220164", "rewe": "DE-1062"}  # kaufDA-Händlerkennung der Region (Edeka Südwest, Rewe)
KD_SLUGS = {"lidl": ["Lidl"], "netto": ["Netto-Marken-Discount"], "rewe": ["REWE"], "edeka": ["Edeka"],
            "dm": ["DM"], "mueller": ["Mueller"]}
# dm heißt bei kaufDA „DM“ (/DM/Sortiment/…); „dm-drogerie-markt“ und „Dm“ = 404 -> bis 03.11. nie Sortiment-Seiten für dm
# zusätzliche Sortiment-Begriffe je Markt (Müller/dm: Drogerie, Parfümerie, Spielwaren, Schreibwaren)
_DROG = """Parfum Duft Make-up Lippenstift Nagellack Mascara Haarfarbe Haarpflege Gesichtspflege Bodylotion Sonnenschutz
Pflaster Vitamine Nahrungsergaenzung Babynahrung Schnuller Adventskalender""".split()
KD_TERMS = {"mueller": _DROG + """Playmobil Schleich Barbie Puzzle Brettspiele Spiele Pluesch Kinderspielzeug
Schreibwaren Basteln Buecher Socken Strumpfhosen Handtaschen Schmuck Uhren Haushaltswaren Deko Weihnachten""".split(),
            "dm": _DROG + """Zahncreme Mundspuelung Rasierklingen Handcreme Gesichtscreme Haarspray Spuelung Deodorant Sonnencreme
Feuchttuecher Wattepads Tampons Binden Kondome Seife Badezusatz Serum Gesichtsmaske Bartpflege Fusscreme Concealer Puder
Lidschatten Pinsel Foehn Glaetteisen Epilierer Magnesium Proteinriegel Duftkerze Geschenkset Allzweckreiniger""".split()}
SORTIMENT = """Butter Milch Kaese Joghurt Quark Sahne Eier Mozzarella Margarine Pudding Skyr Frischkaese Gouda
Hackfleisch Haehnchen Putenbrust Schweinefleisch Rindfleisch Steak Schnitzel Bratwurst Wuerstchen Salami Schinken Wurst Lachs Fisch Garnelen Thunfisch
Obst Gemuese Tomaten Aepfel Bananen Kartoffeln Paprika Zwiebeln Salat Trauben Mandarinen Beeren Pilze
Brot Broetchen Kuchen Toast Croissant Brezel Baguette Berliner Donuts Backwaren Nudeln Reis Mehl Zucker Oel Konserven Suppe Muesli Cornflakes Marmelade Honig Nutella Ketchup Gewuerze
Pizza Eis Pommes Tiefkuehlkost Schokolade Chips Kekse Pralinen Suessigkeiten Gummibaerchen Nuesse
Kaffee Kaffeekapseln Kaffeepads Espresso Tee Kakao Tassimo Senseo Jacobs Tchibo Dallmayr Lavazza
Cola Coca-Cola Pepsi Fanta Limonade Mineralwasser Wasser Saft Bier Wein Sekt Prosecco Spirituosen Whisky Wodka Energy-Drink Red-Bull Monster-Energy
Katzenfutter Hundefutter Katzenstreu Tierfutter
Shampoo Duschgel Deo Zahnpasta Zahnbuerste Rasierer Toilettenpapier Kuechenrolle Taschentuecher Windeln Kosmetik Creme
Waschmittel Persil Ariel Weichspueler Spuelmittel Reiniger Muellbeutel Batterien
Kleidung Schuhe Jacke Socken Unterwaesche Bettwaesche Handtuch Kissen Decke Pfanne Topf Geschirr Lampe Kerzen
Werkzeug Akkuschrauber Garten Pflanzen Blumen Grill Fahrrad Spielzeug Lego Fernseher Kopfhoerer Staubsauger Kaffeemaschine Kuechengeraete""".split()


def kd_price(it):
    return round(float((it.get("prices") or {}).get("mainPrice") or 0), 2)


def flyer_key(it):
    return (norm(it.get("brand") or ""), norm(it.get("title")))


def flyer_ref(items, known, base_ids):
    """Preise des lokalen Prospekts: (Marke, Name) -> Preise. Aus den Händlerseiten (Wörth/Jockgrim + Nachbarorte, nur
    Artikel aus den lokalen Prospekten) und allen gefundenen Artikeln dieser Prospekte."""
    ref = {}
    for b, brand, title, p in known:
        if b in base_ids:
            ref.setdefault((brand, title), set()).add(p)
    for it in items:
        if str((it.get("parentContent") or {}).get("id")) in base_ids:
            ref.setdefault(flyer_key(it), set()).add(kd_price(it))
    return ref


def same_flyer(items, ref, base_ids, store=""):
    """Welche Prospekte entsprechen dem lokalen Prospekt? Manche Märkte haben eine eigene Prospekt-ID mit gleichem
    Inhalt. Ein fremder Prospekt zählt als „unserer“, wenn mindestens 2 Artikel (und mind. 2 % seiner Artikel) mit
    gleicher Marke, gleichem Namen und gleichem Preis wie im lokalen Prospekt vorkommen und höchstens jeder 5.
    gemeinsame Artikel einen anderen Preis hat. Geprüft wird nacheinander, der sicherste Prospekt zuerst; jeder
    übernommene Prospekt erweitert die Vergleichsliste `ref` (nur um Artikel, die dort noch fehlen).
    Anlass 02.11.: ein Edeka-Prospekt einer anderen Gegend hatte 2 gleiche Artikel, aber z. B. Président Meersalzbutter
    2,49 statt 2,79 € und Wagner Pizza 3,99 statt 2,49 € -> über 200 Angebote mit falschen Preisen in der App."""
    groups = {}
    for it in items:
        b = str((it.get("parentContent") or {}).get("id"))
        if b not in base_ids:
            groups.setdefault(b, []).append(it)

    def stat(its):
        same = diff = 0
        for it in its:
            prices = ref.get(flyer_key(it))
            if prices:
                if kd_price(it) in prices:
                    same += 1
                else:
                    diff += 1
        return [len(its), same, diff]

    ok, stats, left = set(), {}, set(groups)
    while left:
        for b in left:
            stats[b] = stat(groups[b])
        good = [b for b in left if stats[b][1] >= max(2, stats[b][0] * 0.02) and stats[b][2] * 4 <= stats[b][1]]
        if not good:
            break
        best = max(good, key=lambda b: (stats[b][1] - 4 * stats[b][2], stats[b][1]))
        ok.add(best)
        left.discard(best)
        for it in groups[best]:
            ref.setdefault(flyer_key(it), {kd_price(it)})
    for b, (n, same, diff) in sorted(stats.items(), key=lambda kv: -kv[1][0]):
        if same or diff:
            log(f"  {store}: Prospekt {b[:8]} ({n} Artikel): {same} gleich, {diff} anderer Preis"
                f" -> {'übernommen' if b in ok else 'abgelehnt'}")
    rest = sum(1 for n, same, diff in stats.values() if not same and not diff)
    if rest:
        log(f"  {store}: {rest} weitere Prospekte ohne gemeinsame Artikel abgelehnt")
    return set(base_ids) | ok


def fetch_sortiment(regional=None):
    regional = regional or {}
    out, accepted = [], {}
    # Märkte mit neuem Prospekt (noch nicht in der App) zuerst, damit sie früh gespeichert werden (early_save)
    have = {o["s"] for o in OLD_OFFERS if (o.get("from") or "") > dt.date.today().isoformat()}
    order = sorted(KD_SLUGS, key=lambda st: not (KD_INFO.get(KD_STORES.get(st), {}).get("future") and st not in have))
    for store in order:
        slugs = KD_SLUGS[store]
        preview = set()
        local = KD_INFO.get(KD_STORES.get(store), {})
        terms = list(dict.fromkeys(SORTIMENT + KD_TERMS.get(store, []) + [l.rstrip("/").split("/")[-1] for l in local.get("links", [])]))
        slug = None
        for sl in slugs:  # gibt es für diesen Händler Sortiment-Seiten?
            items, total = kd_page(f"https://www.kaufda.de/{sl}/Sortiment/Butter" if store not in ("dm", "mueller") else f"https://www.kaufda.de/{sl}/Sortiment/Shampoo")
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
            base = {b for b in local.get("brochures", set()) if b and b != "None"} | local_flyers(store)
            known = set(local.get("known", set()))
            for city in KD_NEAR.get(store, []):  # Händlerseiten der Nachbarorte (gleicher Prospekt) zählen mit
                known |= KD_INFO.get(f"https://www.kaufda.de/{city}/{'/'.join(KD_STORES[store].split('/')[4:])}", {}).get("known", set())
            ref = flyer_ref(found, known, base)
            ok = same_flyer(found, ref, base, store)
            # Vorschau auf die nächste Woche: Solange die lokale Händlerseite noch keinen neuen Prospekt zeigt, die
            # künftigen Prospekte desselben Händlers (gleiche Händler-Kennung) von den Sortiment-Seiten übernehmen.
            # Sobald der lokale Prospekt online ist, greift wieder der Inhaltsabgleich (same_flyer).
            preview = set()
            # Händler-Kennung der Region; ist die lokale Seite leer (z. B. Samstagabend, alter Prospekt weg), die bekannte nehmen
            pubs = local.get("pubs") or {KD_PUB_IDS[store]}
            if not local.get("future"):
                today = dt.date.today().isoformat()
                preview = {str((it.get("parentContent") or {}).get("id")) for it in found
                           if str(it.get("validFrom") or "")[:10] >= today and it.get("publisherId") in pubs}
                # Händler-Kennung gilt bei Edeka bundesweit -> Prospekte mit Eigenmarken anderer Regionen raus
                for fid in sorted(preview):
                    fr = foreign_region(store, [f"{it.get('brand') or ''} {it.get('title') or ''} {it.get('description') or ''}"
                                                for it in found if str((it.get("parentContent") or {}).get("id")) == fid])
                    if fr >= 2:
                        preview.discard(fid)
                        log(f"  {store}: Vorschau-Prospekt {fid} hat {fr} Eigenmarken anderer Regionen -> abgelehnt")
                if preview:
                    log(f"  {store}: Vorschau nächste Woche aus Prospekt(en) {sorted(preview)}")
            ok = ok | preview
            accepted[store] = ok
            # aus übernommenen fremden Prospekten keine Artikel, die im lokalen Prospekt einen anderen Preis haben
            kept_items = [it for it in found if str((it.get("parentContent") or {}).get("id")) in ok
                          and (str((it.get("parentContent") or {}).get("id")) in base | preview
                               or kd_price(it) in ref.get(flyer_key(it), {kd_price(it)}))]
        elif store in ("mueller", "dm"):
            # bundesweite Seite: nur Prospekte, die auch die Wörther Händlerseite zeigt (bzw. flyers.json)
            base = {b for b in local.get("brochures", set()) if b and b != "None"} | local_flyers(store)
            kept_items = [it for it in found if str((it.get("parentContent") or {}).get("id")) in base] if base else found
        else:
            kept_items = found
        n0 = len(out)
        for it in kept_items:
            o = kd_offer(it)
            if o:
                if store in ("rewe", "edeka") and str((it.get("parentContent") or {}).get("id")) in preview:
                    o["pv"] = 1  # Vorschau aus dem Prospekt der Region, noch nicht vom eigenen Markt bestätigt
                out.append(o)
        collect(out[n0:])
        early_save(f"Sortiment {store}")
        log(f"  Sortiment {store}: {len(out) - n0} Angebote übernommen von {len(found)} gefundenen"
            f" ({'keine Sortiment-Seiten, nur Stichwortseiten' if not slug else str(len(terms)) + ' Begriffe'})")
    return out, accepted


# ---------- Zusammenführen und Preisverlauf ----------
# ---------- Vorschau Rewe: prospektewoche.de ----------
# Rewe stellt den Prospekt der nächsten Woche erst spät zu kaufDA. prospektewoche.de zeigt ihn meist schon am
# Wochenende, mit Seitendaten als JSON (/images/prospekte/rewe/weekN/<Seite>.json, robots.txt erlaubt es).
# Achtung: Deren schema.org-Liste trägt das falsche Datum (immer Woche 1) -> nur die Seiten-JSONs nutzen.
# Es ist der allgemeine Rewe-Prospekt, nicht der des Markts in Wörth -> nur als Vorschau (pv), bis kaufDA ihn hat.
PW = "https://prospektewoche.de"


def pw_dates(txt, today):
    m = re.match(r"\s*(\d\d)\.(\d\d)\.?\s*[–-]\s*(\d\d)\.(\d\d)", txt)
    if not m:
        return None
    d1, m1, d2, m2 = map(int, m.groups())
    y = today.year + (1 if m1 < today.month - 6 else 0)
    a = dt.date(y, m1, d1)
    b = dt.date(y + (1 if m2 < m1 else 0), m2, d2)
    return a.isoformat(), b.isoformat()


def pw_week(shop, wk):
    """Alle Artikel einer prospektewoche-Woche: [(Seite, Artikel-JSON)]"""
    hw = http(f"{PW}/{shop}?week={wk}") or ""
    pages = sorted(set(re.findall(rf'data-json-url="(/images/prospekte/{re.escape(shop)}/week{wk}/(\d+)\.json)"', hw)), key=lambda x: int(x[1]))
    out = []
    for path, pg in pages:
        time.sleep(PAUSE)
        raw = http(PW + path)
        if raw is None:  # 429 „zu viele Abrufe“ -> einmal nach einer längeren Pause nochmal
            time.sleep(20)
            raw = http(PW + path)
        try:
            out += [(int(pg), it) for it in json.loads(raw or "{}").get("items") or []]
        except ValueError:
            continue
    return out, len(pages)


def pw_case(t):
    """„CHAMPIGNONS WEIB oder BRAUN“ -> „Champignons Weiß oder Braun“ (frühe Prospekt-Daten in Großbuchstaben)"""
    if sum(c.isupper() for c in t) <= sum(c.islower() for c in t):
        return t
    t = re.sub(r"\bWEIB\b", "WEIß", t)
    return re.sub(r"[A-ZÄÖÜß]{2,}", lambda m: m.group(0) if m.group(0) in PA_KEEP else m.group(0).capitalize(), t)


def pw_words(s):
    return set(re.findall(r"[a-zäöüß]{4,}", (s or "").lower()))


# Regionale Eigenmarken anderer Edeka-Regionen (05.11.: kaufDA-Prospekt 90a11d9f und prospektewoche-Edeka waren
# Edeka Minden-Hannover/Berlin – Bauerngut, Berliner Kindl, Brandenburger Quell –, Jockgrim = Edeka Südwest mit
# „Unsere Heimat“). Bundesweite Markenartikel kosten in allen Regionen oft gleich, der Preisvergleich allein reicht nicht.
REGION_BAD = {"edeka": ("bauerngut", "berliner kindl", "berliner pilsner", "berliner bürgerbräu",
                        "brandenburger quell", "berlimo")}


def foreign_region(store, texts):
    """Wie viele Texte tragen eine Eigenmarke einer anderen Region? Ab 2 = Prospekt einer anderen Gegend."""
    bad = REGION_BAD.get(store, ())
    return sum(1 for t in texts if any(b in (t or "").lower() for b in bad)) if bad else 0


def pw_region_ok(shop, store, items):
    """Passt der prospektewoche-Prospekt zu unserem Markt? (05.11.: Edeka dort = Prospekt der Region Jockgrim,
    früher war es eine andere Gegend.) Vergleich der laufenden Woche mit den echten Angeboten unseres Markts
    (kaufDA, ohne Vorschau). App-Preise (`ao`/`ap`) zählen nicht: kaufDA zeigt dort den App-Preis, prospektewoche
    den Normalpreis. Übernommen wird nur bei mind. 15 gleichen Preisen und höchstens jedem 5. anders."""
    ours = [o for o in OLD_OFFERS if o.get("s") == store and not o.get("pv") and not o.get("ao") and not o.get("ap")
            and o.get("src") == "kaufda.de" and (o.get("from") or "")[:10] <= dt.date.today().isoformat()]
    same = diff = 0
    for _, it in items:
        t = pw_words(it.get("title"))
        try:
            p = float(str(it.get("price") or "0").replace(",", "."))
        except ValueError:
            continue
        if len(t) < 2 or not p:
            continue
        hit = next((o for o in ours if len(t & (pw_words(o.get("n")) | pw_words(o.get("b")))) >= max(2, len(t) * 0.7)), None)
        if hit:
            if abs(hit["p"] - p) < 0.005:
                same += 1
            else:
                diff += 1
    fr = foreign_region(store, [f"{it.get('title')} {it.get('subtitle')}" for _, it in items])
    ok = same >= 15 and diff * 5 <= same and fr < 2
    log(f"  prospektewoche {shop}: laufende Woche {same} gleiche, {diff} andere Preise als unser Markt,"
        f" {fr} Eigenmarken anderer Regionen"
        f" -> {'gleiche Region, Vorschau wird übernommen' if ok else 'andere Region, nicht übernommen'}")
    return ok


def fetch_prospektewoche(shop="rewe", store="rewe", check=False):
    today = dt.date.today()
    h = http(f"{PW}/{shop}") or ""
    tabs = [pw_dates(t, today) for t in re.findall(r'tab-dates">([^<]+)<', h)]
    if check:  # erst die laufende Woche mit unserem Markt vergleichen
        cur = [wk for wk, span in enumerate(tabs, 1) if span and span[0] <= today.isoformat() <= span[1]]
        if not any(span and span[0] >= today.isoformat() for span in tabs):
            log(f"  prospektewoche {shop}: keine neue Woche")
            return []
        if not cur:
            log(f"  prospektewoche {shop}: laufende Woche fehlt -> keine Prüfung möglich, nicht übernommen")
            return []
        time.sleep(PAUSE)
        if not pw_region_ok(shop, store, pw_week(shop, cur[0])[0]):
            return []
    out = []
    for wk, span in enumerate(tabs, 1):
        if not span or span[0] < today.isoformat():  # auch die Woche, die heute beginnt (Montag)
            continue  # nur Wochen, die noch nicht begonnen haben
        time.sleep(PAUSE)
        items, npages = pw_week(shop, wk)
        log(f"  prospektewoche {shop} Woche {wk} ({span[0]} – {span[1]}): {npages} Seiten")
        for pg, it in items:
            title = clean_text((it.get("title") or "").replace("\xad", "")).strip(" ,").lstrip("¹²³⁴⁵*").strip()
            title = pw_case(title)
            desc = clean_text(it.get("subtitle") or "")
            m = re.match(r"([A-ZÄÖÜ][a-zäöüß]+(?:\s[A-ZÄÖÜ][a-zäöüß]+)?):\s+(.+)", title)
            if m and m.group(1) not in ("REWE", "EDEKA"):
                title, desc = m.group(2), f"{m.group(1)}, {desc}".strip(", ")  # „Niederlande: Rispentomaten“
            try:
                price = float(str(it.get("price") or "0").replace(",", "."))
                old = float(str(it.get("old_price") or "0").replace(",", ".")) or None
            except ValueError:
                continue
            up = str(it.get("unit_price") or "")
            base = up if "=" in up else desc
            img = it.get("image")
            o = offer(store, title, price, desc=desc, old=old, base=base,
                      img=f"{PW}/images/prospekte/{shop}/week{wk}/{img}" if img else None,
                      start=span[0], end=span[1], src="prospektewoche.de", page=pg)
            if o:
                o["pv"] = 1
                out.append(o)
                SEEN_NAMES.setdefault(title, o["img"])
                SEEN_ST.setdefault(title, store)
    fr = foreign_region(store, [f"{o.get('b') or ''} {o['n']} {o.get('d') or ''}" for o in out])
    if check and fr >= 2:  # neue Woche selbst prüfen: Eigenmarken einer anderen Region -> verwerfen
        log(f"  prospektewoche {shop}: neue Woche hat {fr} Eigenmarken anderer Regionen -> andere Region, nicht übernommen")
        return []
    log(f"  prospektewoche {shop}: {len(out)} Vorschau-Angebote")
    return out


def fetch_previews():
    """Rewe- und Edeka-Vorschau nacheinander (gleicher Server, prospektewoche antwortet bei zu vielen Abrufen mit 429).
    Edeka nur, wenn die laufende Woche dort zu Jockgrim passt (pw_region_ok)."""
    out = fetch_prospektewoche("rewe", "rewe")
    time.sleep(PAUSE)
    return out + fetch_prospektewoche("edeka", "edeka", check=True)


# ---------- prospektangebote.de (Folderz) ----------
# Öffentliche Angebotslisten je Händler (/geschaefte/<händler>/angebote?page=N, robots.txt erlaubt genau dieses
# Blättern; Suche/Klick-Links sind gesperrt und werden nicht genutzt). Für Müller deutlich mehr als bei kaufDA
# (02.11.: ~860 statt 183). Liste zeigt nur gerade gültige Angebote: Name, Preis, „statt“, Bild, Restlaufzeit
# („5 Tage“ = bis heute + 5). Künftige („Gültig in …“) ohne genaues Startdatum werden übersprungen.
# Eigener Server -> eigene Pause, läuft parallel zu kaufDA. Doppelte zu kaufDA fliegen in pa_dedupe() raus.
PA = "https://www.prospektangebote.de"
PA_STORES = {"mueller": ("mueller", False)}  # Markt -> (Händler-Kürzel bei prospektangebote, Lebensmittel-Markt?)
PA_PAUSE = 2.0
PA_KEEP = {"DIN", "RC", "HO", "H0", "LED", "USB", "TV", "XXL", "XL", "XS", "DM", "PC", "HD", "UV", "SPF", "LSF", "BIO", "3D", "PS5", "PS4", "II", "III"}


def html_unescape(t):
    return _html.unescape(t or "")


def pa_title(t):
    """GROSSBUCHSTABEN-Namen lesbar machen („KUSCHEL-BADEMANTEL“ -> „Kuschel-Bademantel“), Abkürzungen bleiben."""
    def w(m):
        x = m.group(0)
        if x in PA_KEEP or len(x) <= 2 or not re.search(r"[A-ZÄÖÜ]{2}", x):
            return x
        return "-".join(p[:1] + p[1:].lower() for p in x.split("-"))
    return re.sub(r"[A-ZÄÖÜÉÈÔÂÎ0-9][A-ZÄÖÜÉÈÔÂÎ0-9&'!.-]*", w, t)


def pa_money(v):
    m = re.search(r"(\d+(?:\.\d{3})*),(\d\d)", v or "")
    return float(m.group(1).replace(".", "") + "." + m.group(2)) if m else None


def pa_until(txt, today):
    """Restlaufzeit -> letzter Gültigkeitstag (eher zu kurz als zu lang: Monate = 30 Tage, Wochen = 7)."""
    t = (txt or "").strip().lower()
    if not t or t.startswith("gültig in") or "bald" in t:
        return None, True  # beginnt erst später
    m = re.match(r"(\d+)\s*(tag|tage|woche|wochen|monat|monate)\b", t)
    if m:
        n, u = int(m.group(1)), m.group(2)
        return (today + dt.timedelta(days=n * (30 if u.startswith("monat") else 7 if u.startswith("woche") else 1))).isoformat(), False
    if t in ("heute", "letzter tag", "endet heute"):
        return today.isoformat(), False
    return None, False


def fetch_prospektangebote():
    today = dt.date.today()
    out = []
    for store, (slug, food) in PA_STORES.items():
        got, seen, skipped = [], set(), 0
        for page in range(1, 61):
            url = f"{PA}/geschaefte/{slug}/angebote" + (f"?page={page}" if page > 1 else "")
            h = http(url)
            time.sleep(PA_PAUSE)
            blocks = (h or "").split('<a class="js-offer-link-item')[1:]
            if not blocks:
                if page == 1 and not h:  # 03.11.: GitHub-Server bekommen nur „202, leer“ (Bot-Schutz von CloudFront)
                    log(f"  ! prospektangebote {store}: leere Antwort (Bot-Schutz für Rechenzentrums-Server) – nicht umgehen")
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
                price = pa_money((re.search(r'product__price-offer[^>]*>([^<]*)<', b) or [None, ""])[1])
                old = pa_money((re.search(r'product__price-normal[^>]*>([^<]*)<', b) or [None, ""])[1])
                until, future = pa_until((re.search(r'product-date[^>]*>([^<]*)<', b) or [None, ""])[1], today)
                if future:
                    skipped += 1
                    continue
                img = re.search(r'src="(https://img\.offers-cdn\.net/assets/uploads/offers/[^"]+?)-thumb[^"]*"', b)
                title = pa_title(html_unescape(name.group(1)).strip()) if name else ""
                o = offer(store, title, price, old=old, img=(img.group(1) + "-normal.jpeg") if img else None,
                          start=today.isoformat(), end=until, src="prospektangebote.de", url=PA + mid.group(1), food=food)
                if o:
                    o["pa"] = 1  # Quelle prospektangebote (Restlaufzeit gerundet, Start = heute)
                    got.append(o)
            if not new:
                break
        if not got:
            got = pc_rows(store, food, today)
        log(f"  prospektangebote {store}: {len(got)} Angebote ({skipped} künftige ohne Datum übersprungen)")
        out += got
    return out


def pc_data(max_days=4):
    """docs/data/pc-pa.json: prospektangebote.de vom PC zu Hause abgerufen (docs/pc/abruf.py), weil GitHub-Server dort
    nur „202, leer“ bekommen. Nur nehmen, wenn höchstens max_days alt."""
    d = load("pc-pa.json", {})
    try:
        age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(d.get("at"))).total_seconds() / 86400
    except Exception:
        return {}
    if age > max_days:
        log(f"  ! PC-Abruf ist {age:.1f} Tage alt – wird nicht mehr genommen (PC aus? Schlüssel abgelaufen?)")
        return {}
    return d


def pc_rows(store, food, today):
    rows = [r for r in pc_data().get(store) or [] if r.get("p") and (not r.get("t") or r["t"] >= today.isoformat())]
    got = []
    for r in rows:
        o = offer(store, pa_title(html_unescape(r.get("n") or "").strip()), r["p"], old=r.get("o"), img=r.get("img"),
                  start=today.isoformat(), end=r.get("t"), src="prospektangebote.de (vom PC abgerufen)", url=r.get("u"), food=food)
        if o:
            o["pa"] = 1
            got.append(o)
    if got:
        log(f"  prospektangebote {store}: {len(got)} Angebote aus dem PC-Abruf")
    return got


def scheck_pick(rows, kd):
    """Scheck-In druckt mehrere Regional-Ausgaben (02.11.: Pfalz und Baden, ~90 % gleich, andere Weine/Brauereien
    und Preise). Pro Zeitraum gilt nur eine: die mit den meisten Treffern zu den Wörther kaufDA-Angeboten
    (gleicher Preis + gemeinsames Wort), bei Gleichstand die mit mehr „Pfalz“ als „Baden“."""
    W = lambda t: set(re.findall(r"[a-zäöüß]{4,}", (t or "").lower()))
    fl = {}
    for r in rows:
        fl.setdefault(r.get("fid"), []).append(r)
    def score(rs):
        hit = sum(any(abs(r["p"] - o["p"]) < 0.005 and W(o["n"] + " " + (o.get("b") or "")) & W(r["n"]) for r in rs) for o in kd)
        txt = " ".join(f"{r['n']} {r.get('d') or ''}" for r in rs).lower()
        return (hit, txt.count("pfalz") - txt.count("baden"))
    sc = {f: score(rs) for f, rs in fl.items()}
    keep = set()
    for f, rs in sorted(fl.items(), key=lambda x: sc[x[0]], reverse=True):
        a, b = rs[0].get("from") or "", rs[0].get("to") or ""
        if any((fl[k][0].get("from") or "") <= b and a <= (fl[k][0].get("to") or "") for k in keep):
            log(f"  Scheck-In-Prospekt {f}: andere Regional-Ausgabe {sc[f]} – nicht genommen")
            continue
        keep.add(f)
        log(f"  Scheck-In-Prospekt {f}: genommen {sc[f]}")
    return [r for r in rows if r.get("fid") in keep]


def load_scheck(kd=()):
    """Scheck-In-Prospekt, aus den Seitenbildern gelesen (fetch_scheck.py -> docs/data/scheck-ocr.json).
    kaufDA zeigt davon nur 16 Angebote; doppelte zu kaufDA fallen über pa_dedupe raus."""
    today = dt.date.today().isoformat()
    out = []
    rows = [r for r in (load("scheck-ocr.json", {}).get("offers") or []) if r.get("p") and (r.get("to") or "9") >= today]
    for r in scheck_pick(rows, [o for o in kd if o.get("s") == "scheck"]):
        n = re.sub(r"^[^\wÄÖÜäöü]+|\s+[a-z]$", "", (r.get("n") or "").strip())
        n = re.sub(r"(?<=[A-Za-z])&(?=[a-z]|\s|$)", "é", n)  # „Ros&“ -> „Rosé“, „Nescaf&“ -> „Nescafé“
        if not re.search(r"[A-ZÄÖÜ][a-zäöüß]{3,}", n) or re.search(r"APP-PREIS|ERHÄLTLICH|%|[<>]", n, re.I):
            continue  # kein Artikelname erkannt (Störer, Hinweis-Kasten)
        o = offer("scheck", n, r["p"], desc=r.get("d") or "", img=r.get("img"), img_large=r.get("il"),
                  start=r.get("from"), end=r.get("to"), src="prospektangebote.de (Prospekt gelesen)", url=r.get("url"), page=r.get("pg"),
                  old=r.get("o"), uvp=r.get("ou") == 1)
        if o:
            o["pa"], o["ocr"] = 1, 1
            if isinstance(r.get("cr"), list) and len(r["cr"]) == 4:
                o["cr"] = r["cr"]  # Ausschnitt der Prospektseite (oben, rechts, unten, links in %)
            out.append(o)
    log(f"  Scheck-In aus Prospekt gelesen: {len(out)} Angebote")
    return out


def load_zookauf():
    """Zookauf Wörth: Werbeprospekt (Blätterkatalog auf zookauf.de), aus den Seitenbildern gelesen
    (fetch_zookauf.py -> docs/data/zookauf-ocr.json). Keine kaufDA-/meinprospekt-Seite (404, geprüft 04.11.)."""
    today = dt.date.today()
    out = []
    for r in load("zookauf-ocr.json", {}).get("offers") or []:
        if not r.get("p") or (r.get("to") or "9") < today.isoformat():
            continue
        if (r.get("from") or "") > (today + dt.timedelta(days=12)).isoformat():
            continue  # Prospekt für übernächste Woche -> erst später zeigen
        gp = r.get("gp") or {}
        o = offer("zookauf", r.get("n") or "", r["p"], brand=r.get("b"), desc=r.get("d") or "",
                  base=(gp["v"], gp["u"]) if gp.get("v") else None, img=r.get("img"),
                  img_large=r.get("il") or (r.get("img") or "").replace("/large/", "/normal/") or None,  # = ganze Seite
                  start=r.get("from"), end=r.get("to"), src="zookauf.de (Prospekt gelesen)", url=r.get("url"),
                  page=r.get("pg"), cats=[r["cat"]] if r.get("cat") else None)
        if o:
            o["pa"], o["ocr"] = 1, 1
            if isinstance(r.get("cr"), list) and len(r["cr"]) == 4:
                o["cr"] = r["cr"]
            out.append(o)
    log(f"  Zookauf aus Prospekt gelesen: {len(out)} Angebote")
    return out


def pa_dedupe(offers):
    """prospektangebote-Angebote raus, wenn kaufDA denselben Artikel im selben Markt zum selben Preis hat
    (kaufDA hat Marke, Beschreibung, Grundpreis und Prospekt-ID)."""
    def toks(o):
        return {norm(t) for t in re.findall(r"[a-zäöüß0-9]{3,}", f"{o.get('b') or ''} {o.get('n')} {o.get('d') or ''}".lower())} - {""}
    idx = {}
    for o in offers:
        if not o.get("pa"):
            idx.setdefault((o["s"], o["p"]), []).append(toks(o))
    keep, drop = [], 0
    for o in offers:
        if o.get("pa"):
            t = toks(o)
            # aus dem Prospekt gelesene Namen sind oft länger („Familienbraten oder Schweinerücken“) -> reicht, wenn
            # die kaufDA-Wörter weitgehend drinstecken
            if t and any(len(t & k) >= max(1, round(min(len(t), len(k)) * 0.6) if o.get("ocr") else round(len(t) * 0.6))
                         for k in idx.get((o["s"], o["p"]), [])):
                drop += 1
                continue
        keep.append(o)
    if drop:
        log(f"  prospektangebote: {drop} doppelte zu kaufDA entfernt")
    return keep


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


# Gedächtnis der eigenen Prospekte (docs/data/flyers.json = {Markt: {Prospekt-ID: zuletzt gesehen}}): Die Händlerseite
# zeigt je Abruf nur 16 zufällige Angebote, ein echter Jockgrim-Prospekt fehlt dort also manchmal (02.11., 4:47 Uhr:
# fb448281 fehlte -> fremder Prospekt 8c874c03 ohne Gegenbeweis übernommen). Gemerkt wird nur, was die lokale
# Händlerseite selbst gezeigt hat, 21 Tage lang.
FLYERS = None
FLYER_DAYS = 21


def local_flyers(store):
    global FLYERS
    if FLYERS is None:
        FLYERS = load("flyers.json", {})
    return set((FLYERS.get(store) or {}).keys())


def remember_flyers():
    local_flyers("")
    today = dt.date.today()
    cut = (today - dt.timedelta(days=FLYER_DAYS)).isoformat()
    data = {}
    for st, url in KD_STORES.items():
        seen = {b: d for b, d in (FLYERS.get(st) or {}).items() if d >= cut}
        seen.update({b: today.isoformat() for b in KD_INFO.get(url, {}).get("brochures", set()) if b and b != "None"})
        if seen:
            data[st] = dict(sorted(seen.items()))
    FLYERS.clear()
    FLYERS.update(data)
    save("flyers.json", data)


def merge(offers):
    by = {}
    for o in offers:
        k = (o["s"], norm(o["n"])[:30], o["p"])
        cur = by.get(k)
        if not cur:
            by[k] = o
            continue
        # das vollständigere Angebot behalten, fehlende Felder ergänzen
        if cur.get("c") in ("vorrat", "sonstiges") and o.get("c") not in ("vorrat", "sonstiges"):
            cur["c"] = o["c"]  # „Vorrat“/„Sonstiges“ ist nur die Notlösung, wenn nichts passte
        if cur.get("pv") and not o.get("pv"):
            cur.pop("pv", None)  # derselbe Artikel steht auch im bestätigten Prospekt
        if "ou" not in cur and "ou" in o and (not cur.get("o") or cur.get("o") == o.get("o")):
            cur["ou"] = o["ou"]  # 0 = eigener früherer Preis (zählt, obwohl „falsch“ im Sinne von Python)
        for f in ("b", "o", "gp", "img", "il", "ims", "iw", "inf", "cat", "pg", "bid", "from", "to", "ap", "ao", "url", "cr"):
            if not cur.get(f) and o.get(f):
                cur[f] = o[f]
        if o.get("x") and not cur.get("x"):
            cur["x"] = o["x"]
    return app_twins(list(by.values()))


def app_twins(offers):
    """kaufDA liefert manche App-Angebote doppelt: einmal Normalpreis mit App-Preis (ap), einmal der App-Preis
    als normaler Preis (statt = Normalpreis). Die zweite Karte ist falsch (Preis gilt nur mit App) -> raus,
    ihr Bild wandert als weiteres Bild zum echten Angebot (Kevin 01.11.: Skyr doppelt)."""
    by = {}
    for o in offers:
        by.setdefault((o["s"], norm(o["n"])[:30], o.get("b"), o.get("from"), o.get("to")), []).append(o)
    drop = set()
    for grp in by.values():
        for a in grp:
            if not a.get("ap") or id(a) in drop:
                continue
            for t in grp:
                if t is a or t.get("ap") or id(t) in drop or abs(t["p"] - a["ap"]) > 0.005:
                    continue
                if t.get("o") and abs(t["o"] - a["p"]) > 0.005:
                    continue
                drop.add(id(t))
                if t.get("img") and t["img"] != a.get("img"):
                    a["ims"] = list(dict.fromkeys((a.get("ims") or []) + [t["img"]]))
                if a.get("gp") and a["gp"] == t.get("gp") and a["ap"]:
                    a["gp"] = {**a["gp"], "v": round(a["gp"]["v"] * a["p"] / a["ap"], 2)}  # Grundpreis galt dem App-Preis
    # Gleicher Artikel zweimal, nur anders aufgeteilt („Die Frische Milch“ + „1,8% Fett 1-l-Pckg.“ vs.
    # „Die Frische Milch 1,8% Fett“ + „1-l-Pckg.“): gleiche Wörter, Marke, Preis, Zeitraum -> eine Karte (Kevin 01.11.)
    seen = {}
    for o in offers:
        if id(o) in drop:
            continue
        k = (o["s"], o.get("b"), o["p"], o.get("from"), o.get("to"),
             tuple(sorted(re.findall(r"[a-z0-9]+", norm_words(f"{o['n']} {o.get('d') or ''}")))))
        a = seen.get(k)
        if not a:
            seen[k] = o
            continue
        drop.add(id(o))
        if o.get("img") and o["img"] != a.get("img"):
            a["ims"] = list(dict.fromkeys((a.get("ims") or []) + [o["img"]]))
        for f in ("gp", "o", "ou", "ap", "inf"):
            if not a.get(f) and o.get(f):
                a[f] = o[f]
    variant_twins([o for o in offers if id(o) not in drop], drop)
    return [o for o in offers if id(o) not in drop]


VARIANT_UNION = re.compile(r"\s(oder|und|&)\s|/|,", re.I)


def variant_twins(offers, drop):
    """Sorten-Doppel (Kevin 01.11.: Landliebe „Butter“ + „Butter oder Streichzart“, Müller „Joghurt mit der Ecke“ zweimal
    mit vertauschten Sorten-Bildern): gleicher Markt, Marke, Preis, statt-/App-Preis, Zeitraum, gleiche Menge und ein Name
    steckt ganz im anderen -> eine Karte. Ein Name mit „oder/und//“ bleibt (nennt alle Sorten), sonst der allgemeinere
    kürzere. Gleiche Artikel bei verschiedenen Märkten bleiben getrennt (App zeigt dafür den Achtung-Hinweis)."""
    words = lambda o: set(re.findall(r"[a-z0-9]+", norm_words(o["n"])))
    gp_ok = lambda a, b: not a.get("gp") or not b.get("gp") or (
        a["gp"].get("u") == b["gp"].get("u") and abs(a["gp"]["v"] - b["gp"]["v"]) / a["gp"]["v"] < 0.02)
    by = {}
    for o in offers:
        if o.get("b") and o.get("p"):
            by.setdefault((o["s"], norm(o["b"]), o["p"], o.get("o"), o.get("ap"), o.get("from"), o.get("to")), []).append(o)
    for g in by.values():
        if len(g) < 2:
            continue
        ws = [words(o) for o in g]
        par = list(range(len(g)))

        def root(i):
            while par[i] != i:
                par[i] = par[par[i]]
                i = par[i]
            return i
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if ws[i] and ws[j] and (ws[i] <= ws[j] or ws[j] <= ws[i]) and gp_ok(g[i], g[j]):
                    par[root(i)] = root(j)
        cl = {}
        for i in range(len(g)):
            cl.setdefault(root(i), []).append(i)
        for ix in cl.values():
            if len(ix) < 2:
                continue
            un = [i for i in ix if VARIANT_UNION.search(g[i]["n"])]
            keep = max(un, key=lambda i: len(ws[i])) if un else min(ix, key=lambda i: (len(ws[i]), len(g[i]["n"])))
            a = g[keep]
            for i in ix:
                if i == keep:
                    continue
                o = g[i]
                drop.add(id(o))
                im = [x for x in [o.get("img")] + (o.get("ims") or []) if x and x != a.get("img")]
                if im:
                    a["ims"] = list(dict.fromkeys((a.get("ims") or []) + im))
                for f in ("gp", "ou", "inf", "d"):
                    if not a.get(f) and o.get(f):
                        a[f] = o[f]


def norm_words(s):
    s = (s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def drop_previews(offers):
    """Vorschau (pv) eines Markts komplett entfernen, sobald dessen echter Prospekt für dieselbe Woche da ist
    (Kevins Wunsch: echte Daten sofort rein, Vorschau weg). Echt = mind. 10 Angebote ohne pv, die in derselben
    Woche starten wie die Vorschau.
    01.11.: Die kaufDA-Händlerseite liefert nur 16 Angebote – damit flogen 400 Vorschau-Artikel von Rewe/Edeka raus,
    obwohl der Rest erst später über die Sortiment-Seiten kommt. Jetzt: komplett weg erst, wenn die echten Angebote
    mind. halb so viele sind wie die Vorschau. Vorher fliegen nur die Vorschau-Artikel raus, die es schon echt gibt."""
    out = offers
    for s in {o["s"] for o in offers if o.get("pv")}:
        froms = sorted(o["from"][:10] for o in offers if o["s"] == s and o.get("pv") and o.get("from"))
        if not froms:
            continue
        start = dt.date.fromisoformat(froms[0])
        lo, hi = (start - dt.timedelta(days=2)).isoformat(), (start + dt.timedelta(days=6)).isoformat()
        reals = [o for o in offers if o["s"] == s and not o.get("pv") and lo <= (o.get("from") or "")[:10] <= hi]
        n = sum(1 for o in out if o["s"] == s and o.get("pv"))
        if len(reals) >= max(10, n * 0.5):
            out = [o for o in out if not (o["s"] == s and o.get("pv"))]
            log(f"  {s}: echter Prospekt ab {froms[0]} da ({len(reals)} Angebote) -> {n} Vorschau-Angebote entfernt")
        elif reals:
            have = {norm(o["n"]) for o in reals} | {k for k in map(name_key, reals) if k}
            out = [o for o in out if not (o["s"] == s and o.get("pv") and (norm(o["n"]) in have or name_key(o) in have))]
            log(f"  {s}: erst {len(reals)} echte Angebote -> Vorschau bleibt ({n - sum(1 for o in out if o['s'] == s and o.get('pv'))} Doppelte entfernt)")
    return out


def hist_tag(o):
    """Marke + Packungsgröße zum Preis speichern (Kevin 01.11.): „Shampoo“ oder „Lachsfilet“ gibt es in vielen Marken und
    Größen – verglichen wird in der App nur dieselbe Marke und dieselbe Menge."""
    bk = norm(o.get("b") or "")[:20]
    gp = o.get("gp") or {}
    q = round(o["p"] / gp["v"], 3) if gp.get("v") and o.get("p") else None
    return bk, q


def update_history(offers, today):
    hist = load("history.json", {})
    # Alte Zeilen ohne Marke/Menge ([Tag, Preis]) nachträglich zuordnen, wenn genau ein Angebot mit diesem Preis passt
    tags = {}
    for o in offers:
        tags.setdefault((f"{o['s']}|{norm(o['n'])[:40]}", round(o["p"], 2)), set()).add(hist_tag(o))
    for k, rows in hist.items():
        for r in rows:
            if len(r) == 2:
                t = tags.get((k, round(r[1], 2)))
                if t and len(t) == 1:
                    r.extend(next(iter(t)))
    for o in offers:
        k = f"{o['s']}|{norm(o['n'])[:40]}"
        rows = hist.setdefault(k, [])
        bk, q = hist_tag(o)
        same = next((r for r in rows if r[0] == today and len(r) >= 4 and r[2] == bk and r[3] == q), None)
        if same:
            same[1] = min(same[1], o["p"])
        else:
            rows.append([today, o["p"], bk, q])
        rows.sort(key=lambda r: r[0])
        del rows[:-150]
    # Einträge, die seit 120 Tagen nicht mehr auftauchen, löschen
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=120)).isoformat()
    hist = {k: v for k, v in hist.items() if v and v[-1][0] >= cutoff}
    save("history.json", hist)


def update_names(offers, today):
    """Artikelnamen für die Vorschläge beim Tippen sammeln (auch wenn sie später nicht mehr im Angebot sind)."""
    names = load("names.json", {})
    imgs = load("names-img.json", {})  # kleines Produktbild je Name, für die Vorschlagsliste
    for o in offers:
        n, b = o["n"], (o.get("b") or "").strip()
        text = n if not b or norm(b) in norm(n) else f"{b} {n}"
        names[text[:80]] = today
        if o.get("img"):
            imgs[text[:80]] = o["img"]
    for n, img in SEEN_NAMES.items():
        names[n[:80]] = today
        if img:
            imgs[n[:80]] = img
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=400)).isoformat()
    names = {k: v for k, v in names.items() if v >= cutoff}
    names = dict(sorted(names.items(), key=lambda kv: kv[1], reverse=True)[:6000])
    save("names.json", names)
    # Sortiment je Markt (Kevin 04.11.: im Zettel-Reiter eines Markts nur Vorschläge aus dessen Sortiment)
    nst = load("names-store.json", {})
    def put(st, t):
        if st and t:
            nst.setdefault(st, {})[t[:80]] = today
    for o in offers:
        n, b = o["n"], (o.get("b") or "").strip()
        put(o.get("s"), n if not b or norm(b) in norm(n) else f"{b} {n}")
    for n, st in SEEN_ST.items():
        put(st, n)
    for r in (load("dauerpreise.json", {}) or {}).get("items") or []:
        if r and r[0]:
            b = (r[1] or "").strip()
            put("aldi", r[0] if not b or norm(b) in norm(r[0]) else f"{b} {r[0]}")
    for r in (load("zookauf-ocr.json", {}) or {}).get("offers") or []:
        if r.get("n"):
            put("zookauf", f"{r['b']} {r['n']}" if r.get("b") and norm(r["b"]) not in norm(r["n"]) else r["n"])
    for st in list(nst):
        nst[st] = dict(sorted(((k, v) for k, v in nst[st].items() if v >= cutoff), key=lambda kv: kv[1], reverse=True)[:5000])
    save("names-store.json", nst)
    bad = load("img-bad.json", {})
    save("names-img.json", {k: v for k, v in imgs.items() if k in names and isinstance(v, str) and v.startswith("https://") and img_id(v) not in bad})


# ---------- Schnell in die App (Kevins Wunsch: neue Angebote so früh wie möglich, nicht erst nach 40 Minuten) ----------
# Lidl, Aldi und prospektewoche laufen parallel zu kaufDA (andere Server, je Server weiter mit PAUSE).
# Sobald ein Markt mind. 10 neue künftige Angebote hat, die noch nicht in der App sind, wird ein Zwischenstand
# (neue + bisherige Angebote) gespeichert und auf GitHub hochgeladen (nur mit SR_EARLY_PUSH=1, also im Workflow).
OLD_OFFERS = []
COLLECTED = []
LOCK = threading.Lock()
LAST_FUT = {}


def collect(items):
    with LOCK:
        COLLECTED.extend(items)


# ---------- „Kostet eigentlich“: UVP von anderen Märkten übernehmen ----------
# Rewe/Edeka-Prospekte nennen fast nie einen „statt“-Preis. Die UVP (Preisempfehlung des Herstellers) gilt aber
# für denselben Markenartikel überall. Steht derselbe Artikel (gleiche Marke, gleiche Wörter, gleiche Menge ±3 %)
# bei einem anderen Markt mit UVP (Lidl/kaufDA-Angabe „UVP“), übernimmt SparRadar sie – mit Quelle (ous).
# Gemerkt wird sie in uvp.json (180 Tage), damit sie auch gilt, wenn der andere Markt den Artikel nicht mehr anbietet.
def uvp_key(o):
    b = norm(o.get("b") or "")
    if not b or not o.get("gp") or not o.get("p"):
        return None
    toks = sorted({norm(t) for t in re.findall(r"[a-zäöüß0-9]+", f"{o.get('b')} {o.get('n')}".lower())} - {""})
    return b + "|" + " ".join(toks)


def uvp_amount(o):
    gp = o.get("gp") or {}
    try:
        v = float(gp.get("v") or 0)
    except (TypeError, ValueError):
        return None
    return (round(o["p"] / v, 4), gp.get("u")) if v > 0 and gp.get("u") else None


def learn_uvp(offers, mem, today):
    for o in offers:
        if o.get("ou") != 1 or o.get("ous") or not o.get("o") or o["o"] <= o.get("p", 0):
            continue
        k, a = uvp_key(o), uvp_amount(o)
        if not k or not a:
            continue
        lst = [e for e in mem.get(k, []) if not (e["gu"] == a[1] and abs(e["a"] - a[0]) / a[0] < .03)]
        lst.append({"u": o["o"], "gu": a[1], "a": a[0], "s": o["s"], "d": today})
        mem[k] = lst[-6:]
    old = (dt.date.today() - dt.timedelta(days=180)).isoformat()
    for k in list(mem):
        mem[k] = [e for e in mem[k] if e["d"] >= old]
        if not mem[k]:
            del mem[k]
    return mem


def borrow_uvp(offers, mem):
    n = 0
    for o in offers:
        if o.get("ous"):  # alte Übernahme neu berechnen
            for f in ("o", "ou", "ous"):
                o.pop(f, None)
        if o.get("o") or not o.get("p"):
            continue
        k, a = uvp_key(o), uvp_amount(o)
        if not k or not a:
            continue
        hit = [e for e in mem.get(k, []) if e["s"] != o["s"] and e["gu"] == a[1] and abs(e["a"] - a[0]) / a[0] < .03
               and o["p"] * 1.03 < e["u"] <= o["p"] * 3]
        if hit:
            e = max(hit, key=lambda e: e["d"])
            o["o"], o["ou"], o["ous"] = e["u"], 1, e["s"]
            n += 1
    return n


# ---------- Unscharfe Bilder ----------
# kaufDA liefert bei Netto/Rewe/Lidl teils nur winzige Ausschnitte aus dem Prospekt (z. B. 88×325 px, manchmal nur
# ein Flaschendeckel). Größere Versionen gibt es dort nicht (403). Darum: Bildgröße messen (nur die ersten 64 KB,
# Ergebnis wird je Adresse gemerkt) und winzige Bilder durch das scharfe Foto desselben Markenartikels von einem
# anderen Markt ersetzen (gleiche Marke + gleiche Wörter im Namen). Das Original bleibt als weiteres Bild erhalten.
def img_dims(b):
    import struct
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return list(struct.unpack(">II", b[16:24]))
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP" and b[12:16] == b"VP8X":
        return [int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1]
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        if b[i + 1] in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return [w, h]
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def measure_images(offers):
    from concurrent.futures import ThreadPoolExecutor
    known = {o.get("img"): o["iw"] for o in OLD_OFFERS if o.get("img") and o.get("iw")}
    todo = sorted({o["img"] for o in offers if o.get("img") and o["img"] not in known and "bonial" in o["img"]})

    def one(u):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Range": "bytes=0-65535"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return u, img_dims(r.read(65536))
        except Exception:
            return u, None
    with ThreadPoolExecutor(4) as ex:
        for u, d in ex.map(one, todo):
            if d:
                known[u] = d
    for o in offers:
        if o.get("img") in known:
            o["iw"] = known[o["img"]]
    log(f"Bildgrößen: {len(todo)} neu gemessen")


def name_key(o):
    b = norm(o.get("b") or "")
    toks = sorted({norm(t) for t in re.findall(r"[a-zäöüß0-9]+", f"{o.get('b') or ''} {o.get('n')}".lower())} - {""})
    return b + "|" + " ".join(toks) if b and len(toks) >= 2 else None




def img_px(o):
    if o.get("iw"):
        return max(o["iw"])
    u = o.get("img") or ""
    return 1000 if "aldi.cx" in u else 0


def better_images(offers):
    best = {}
    for o in offers:
        k = name_key(o)
        if k and not o.get("cr") and img_px(o) >= 450 and img_px(o) > img_px(best.get(k, {})):  # ganze Prospektseite ist kein Produktfoto
            best[k] = o
    n = 0
    for o in offers:
        px = img_px(o)
        if not o.get("img") or not px or px >= 300 or o.get("cr"):
            continue
        b = best.get(name_key(o) or "")
        if b and b is not o and b.get("img") != o["img"]:
            o["ims"] = [u for u in dict.fromkeys([*(o.get("ims") or []), o["img"]]) if u][:8]
            o["img"], o["io"] = b["img"], b["s"]
            o["iw"] = b.get("iw") or [1000, 1000]
            if b.get("il"):
                o["il"] = b["il"]
            else:
                o.pop("il", None)
            n += 1
    log(f"Unscharfe Bilder ersetzt: {n}")


def img_id(u):
    """Bild-ID = Dateiname ohne Endung (kaufDA nutzt dieselbe Datei in mehreren Ordnern)."""
    return re.sub(r"\.\w+$", "", str(u or "").split("?")[0].rsplit("/", 1)[-1])


def fix_bad_images(offers):
    """Falsche Bilder entfernen (Quelle lieferte das Bild eines anderen Artikels, z. B. Lidl Schoko Drink mit
    H-Milch-Bild). Liste von Hand: docs/data/img-bad.json {Bild-ID: {n: Notiz, r: Ersatzbild (optional)}}."""
    bad = load("img-bad.json", {})
    if not isinstance(bad, dict) or not bad:
        return
    isbad = lambda u: bool(u) and img_id(u) in bad
    n = 0
    for o in offers:
        allu = [o.get("img"), o.get("il"), *(o.get("ims") or [])]
        if not any(isbad(u) for u in allu):
            continue
        rep = next((bad[img_id(u)].get("r") for u in allu if isbad(u) and isinstance(bad[img_id(u)], dict) and bad[img_id(u)].get("r")), None)
        ims = [u for u in (o.get("ims") or []) if u and not isbad(u)]
        if isbad(o.get("img")) or isbad(o.get("il")):
            o.pop("il", None)
        if isbad(o.get("img")):
            o.pop("iw", None)
            o.pop("io", None)
            o["img"] = rep if rep and not isbad(rep) else (ims.pop(0) if ims else None)
            if not o["img"]:
                o.pop("img")
        if ims:
            o["ims"] = ims
        else:
            o.pop("ims", None)
        n += 1
    if n:
        log(f"Falsche Bilder korrigiert: {n}")


def finalize(offers, save_uvp=False):
    today = dt.date.today().isoformat()
    offers = drop_previews(merge(offers))
    n0 = len(offers)
    offers = [o for o in offers if o.get("id") not in ONLINE_IDS and str(o.get("bid")) not in ONLINE_BIDS
              and not online_only(" ".join(str(o.get(k) or "") for k in ("n", "d", "inf")))]
    if len(offers) < n0:
        log(f"  Online-Angebote entfernt: {n0 - len(offers)}")
    fix_bad_images(offers)
    for o in offers:  # auch schon gespeicherte Angebote nach den Geräte-Regeln einordnen
        dev = special(o.get("n"), o.get("b"), o.get("cat")) or appliance(o.get("n"), o.get("cat"))
        if dev and o.get("c") != dev:
            o["c"] = dev
        if not o.get("gp"):
            up = pack_unit_price(o.get("p"), f"{o.get('n')} {o.get('d') or ''}")
            if up:
                o["gp"] = {"v": up[0], "u": up[1]}
    mem = learn_uvp(offers, load("uvp.json", {}), today)
    n = borrow_uvp(offers, mem)
    if save_uvp:
        save("uvp.json", mem)
        log("UVP übernommen:", n, "| UVP-Gedächtnis:", len(mem))
    offers = [o for o in offers if not o.get("to") or o["to"] >= today]  # abgelaufene raus
    offers.sort(key=lambda o: (o["s"], o["c"], o["n"]))
    return offers


def future_counts(offers):
    today = dt.date.today().isoformat()
    c = {}
    for o in offers:
        if (o.get("from") or "") >= today:
            c[o["s"]] = c.get(o["s"], 0) + 1
    return c


def write_offers(offers):
    counts = {}
    for o in offers:
        counts[o["s"]] = counts.get(o["s"], 0) + 1
    gen = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    # „upd“ = letzte Änderung (auch vom Prospekt-Wächter, check_new.add_seen), „generated“ = letzter kompletter Abruf
    save("offers.json", {"generated": gen, "upd": gen, "region": "Wörth am Rhein", "counts": counts, "offers": offers})
    save("stand.json", {"generated": gen, "upd": gen})  # winzige Datei: daran erkennt die App neue Daten, ohne alles zu laden
    return counts


def early_save(why):
    if os.environ.get("SR_EARLY_PUSH") != "1" or not OLD_OFFERS:
        return
    with LOCK:
        offers = finalize(pa_dedupe([dict(o) for o in COLLECTED] + [dict(o) for o in OLD_OFFERS]))
        fut = future_counts(offers)
        gained = {s: n - LAST_FUT.get(s, 0) for s, n in fut.items() if n - LAST_FUT.get(s, 0) >= 10}
        if not gained:
            return
        write_offers(offers)
        LAST_FUT.update(fut)
        log(f"  Zwischenstand nach {why}: neue künftige Angebote {gained} -> sofort in die App")
        try:
            for cmd in (["git", "add", "docs/data/offers.json", "docs/data/stand.json"],
                        ["git", "commit", "-q", "-m", f"Angebote {dt.date.today()} (Zwischenstand: {', '.join(gained)})"],
                        ["git", "pull", "-q", "--rebase", "-X", "theirs", "--autostash"], ["git", "push", "-q"]):
                subprocess.run(cmd, cwd=ROOT, check=True, timeout=120)
        except Exception as e:
            log("  ! Zwischenstand nicht hochgeladen:", e)


def main():
    today = dt.date.today().isoformat()
    OLD_OFFERS.extend(load("offers.json", {}).get("offers") or [])
    LAST_FUT.update(future_counts(OLD_OFFERS))
    results = {}

    def run(name, fn):
        try:
            results[name] = fn()
        except Exception as e:  # eine kaputte Quelle soll die anderen nicht stoppen
            log(f"  ! {name} fehlgeschlagen: {e!r}")
            results[name] = []
            return
        if name != "kaufDA":
            collect(results[name])
            early_save(name)

    threads = [threading.Thread(target=run, args=a) for a in
               (("Lidl", fetch_lidl), ("Aldi", fetch_aldi), ("Vorschau", fetch_previews),
                ("prospektangebote", fetch_prospektangebote))]
    for t in threads:
        t.start()
    run("kaufDA", fetch_kaufda)
    for t in threads:
        t.join()
    # Scheck-In-Prospekt liest fetch_scheck.py parallel (Workflow, ca. 20 min je neuem Prospekt) -> auf das Ende warten
    done = os.environ.get("SR_SCHECK_DONE")
    if done:
        for _ in range(180):
            if os.path.exists(done):
                break
            time.sleep(10)
        else:
            log("  ! Scheck-In-Prospekt noch nicht fertig gelesen – letzter Stand wird genommen")
    run("Scheck-In-Prospekt", lambda: load_scheck(results.get("kaufDA") or []))
    run("Zookauf-Prospekt", load_zookauf)
    new = pa_dedupe([o for name in ("Lidl", "Aldi", "kaufDA", "Vorschau", "prospektangebote", "Scheck-In-Prospekt", "Zookauf-Prospekt") for o in results.get(name, [])])
    # Sortiment-Abgleich: Jeder Abruf baut die Liste neu auf – neue Artikel kommen dazu, verschwundene fliegen raus.
    # Ausnahme: Liefert ein Markt plötzlich fast nichts (Seite kurz down, Sperre, Umbau), bleiben seine noch gültigen
    # alten Angebote stehen, statt dass der ganze Markt bis zum nächsten Abruf leer ist.
    valid = [o for o in OLD_OFFERS if not o.get("to") or o["to"] >= today]
    for st in {o["s"] for o in valid}:
        n_old = sum(o["s"] == st for o in valid)
        n_new = sum(o["s"] == st for o in new)
        if n_old >= 20 and n_new < n_old * 0.3:
            log(f"  ! {st}: nur {n_new} statt bisher {n_old} Angebote – Quelle gestört? Alte gültige Angebote bleiben.")
            new += [dict(o) for o in valid if o["s"] == st]
    # Händlerseiten zeigen je Abruf andere 16 Angebote: Schon gesehene, noch gültige Angebote aus den eigenen Prospekten
    # (alle kaufDA-Märkte, auch was der Prospekt-Wächter tagsüber eingesammelt hat) bleiben stehen, auch wenn sie diesmal
    # nicht dabei waren. Neue Daten zuerst -> merge() bevorzugt sie. Fremde Prospekte sind nie in flyers.json.
    remember_flyers()
    for st in KD_STORES:
        mine = local_flyers(st)
        stick = [dict(o) for o in valid if o["s"] == st and not o.get("pv") and o.get("bid") in mine]
        if stick:
            new += stick
            log(f"  {st}: {len(stick)} bisherige Angebote aus eigenen Prospekten behalten (doppelte fallen in merge raus)")
    offers = finalize(new, save_uvp=True)
    try:
        measure_images(offers)
        better_images(offers)
    except Exception as e:
        log("  ! Bildprüfung fehlgeschlagen:", repr(e))
    if len(offers) < 30:
        log("! Zu wenige Angebote, alte Daten bleiben stehen.")
        sys.exit(1)
    counts = write_offers(offers)
    log("Gesamt:", len(offers), counts)
    update_history(offers, today)
    update_names(offers, today)


if __name__ == "__main__":
    main()
