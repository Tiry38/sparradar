"""Diagnose (nur von Hand): Open-Prices-Export – wie viele aktuelle Angebote bekommen einen echten Ladenpreis?"""
import subprocess, sys, collections, urllib.request, json, re, datetime as dt
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyarrow"], check=True)
import pyarrow.parquet as pq
URL = "https://huggingface.co/datasets/openfoodfacts/open-prices/resolve/main/prices.parquet"
req = urllib.request.Request(URL, headers={"User-Agent": "SparRadar/1.0 (+https://github.com/Tiry38/sparradar)"})
open("/tmp/p.parquet", "wb").write(urllib.request.urlopen(req, timeout=120).read())
cols = ["product_code", "price", "price_is_discounted", "date", "location_osm_display_name", "location_osm_address_country_code", "location_osm_address_postcode"]
rows = [r for r in pq.read_table("/tmp/p.parquet", columns=cols).to_pylist() if r["location_osm_address_country_code"] == "DE" and r["product_code"]]
chain = lambda r: (r["location_osm_display_name"] or "").split(",")[0].strip()
print("DE", len(rows))
print("Ketten", collections.Counter(chain(r) for r in rows).most_common(25))
yr = dt.date.today() - dt.timedelta(days=365)
recent = [r for r in rows if r["date"] and r["date"] >= yr]
print("letzte 12 Monate", len(recent), "Produkte", len({r["product_code"] for r in recent}))
print("PLZ-Bereich 76/67", sum(1 for r in recent if (r["location_osm_address_postcode"] or "")[:2] in ("76", "67")))
codes = {r["product_code"] for r in recent}
# Angebote -> EAN über den Artikelstamm (catalog.json + Bildpfad = EAN)
cat = json.load(open("../docs/data/catalog.json")); img = json.load(open("../docs/data/catalog-img.json"))
def ean(p):
    m = re.match(r"[fb]:([\d/]+)/front", p or "");
    return m.group(1).replace("/", "") if m else None
def toks(s):
    s = (s or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return set(re.findall(r"[a-z0-9]{3,}", s))
idx = collections.defaultdict(list)
for n, p in zip(cat, img):
    e = ean(p)
    if e:
        t = toks(n)
        for w in t:
            idx[w].append((t, e))
offers = json.load(open("../docs/data/offers.json"))["offers"]
hit = collections.Counter(); tot = collections.Counter(); ex = []
for o in offers:
    if o.get("o") or not o.get("b"):
        continue
    tot[o["s"]] += 1
    want = toks(o["b"]) | toks(o["n"])
    b = toks(o["b"])
    cand = {e for w in b for t, e in idx.get(w, []) if want <= t}
    if cand & codes:
        hit[o["s"]] += 1
        if len(ex) < 15: ex.append((o["s"], o["b"], o["n"], sorted(cand & codes)[:2]))
print("ohne statt, mit Marke:", dict(tot)); print("mit Open-Prices-Preis:", dict(hit)); print(ex)
