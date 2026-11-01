"""Diagnose (nur von Hand): Open-Prices-Datenexport (Hugging Face, ODbL) – wie viele echte Ladenpreise gibt es für unsere Märkte?"""
import subprocess, sys, collections, urllib.request
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyarrow"], check=True)
import pyarrow.parquet as pq
URL = "https://huggingface.co/datasets/openfoodfacts/open-prices/resolve/main/prices.parquet"
req = urllib.request.Request(URL, headers={"User-Agent": "SparRadar/1.0 (+https://github.com/Tiry38/sparradar)"})
open("/tmp/p.parquet", "wb").write(urllib.request.urlopen(req, timeout=120).read())
t = pq.read_table("/tmp/p.parquet")
print("Zeilen", t.num_rows); print(t.schema)
rows = t.to_pylist()
print(rows[0])
cc = collections.Counter(r.get("location_osm_address_country_code") or r.get("location_osm_address_country") for r in rows)
print(cc.most_common(10))
de = [r for r in rows if (r.get("location_osm_address_country_code") or "") == "DE" or (r.get("location_osm_address_country") or "") in ("Deutschland", "Germany")]
print("DE", len(de))
br = collections.Counter((r.get("location_osm_brand") or r.get("location_osm_name") or "?") for r in de)
print(br.most_common(30))
print("Datum", min(str(r.get("date")) for r in de), max(str(r.get("date")) for r in de))
print("Produkte DE", len({r.get("product_code") for r in de}))
