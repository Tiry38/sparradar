"""Diagnose (nur von Hand): Open Prices (Open Food Facts) als Quelle für echte Ladenpreise prüfen."""
import json, urllib.request
UA = {"User-Agent": "SparRadar/1.0 (+https://github.com/Tiry38/sparradar) Preisvergleich"}
def get(u, n=3000):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40)
        b = r.read(n); return r.status, b.decode("utf-8", "replace")
    except Exception as e:
        return "ERR", str(e)[:300]
for u in ["https://prices.openfoodfacts.org/robots.txt",
          "https://prices.openfoodfacts.org/api/v1/prices?product_code=4000405004562&size=3",
          "https://prices.openfoodfacts.org/api/v1/prices?location__osm_address_country=Deutschland&size=1",
          "https://huggingface.co/api/datasets/openfoodfacts/open-prices/tree/main",
          "https://huggingface.co/robots.txt"]:
    s, t = get(u)
    print("==", u, s); print(t[:1500])
