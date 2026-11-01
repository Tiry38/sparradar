import re, sys
sys.path.insert(0, ".")
from fetch_cashback import get, txt, URL
p = get(URL)
secs = re.split(r'<section', p)
for s in secs[1:]:
    sid = re.search(r'id="([^"]+)"', s[:300]); h = re.search(r'<h2[^>]*>(.*?)</h2>', s, re.S)
    blks = re.split(r'<div class="tbl tbl-competition', s)[1:]
    print("== SECTION", sid.group(1) if sid else "-", "|", txt(h.group(1)) if h else "-", "| Blöcke", len(blks))
    for b in blks[:60]:
        t = re.search(r'<div class="tbl-title">(.*?)</div>', b, re.S)
        f = {txt(k): txt(v)[:90] for k, v in re.findall(r"<strong>(.*?)</strong>\s*:(.*?)</li>", b, re.S)}
        l = re.search(r'href="([^"]+)"[^>]*class="tbl-button"', b) or re.search(r'class="tbl-button"[^>]*href="([^"]+)"', b)
        print("  -", txt(t.group(1))[:60] if t else "?", "|", f.get("Cashback") or f.get("Rabatt") or list(f.items())[:2], "|", f.get("Aktionszeitraum", ""), "|", (l.group(1)[:50] if l else ""))
print("== LINKS")
for u in sorted(set(re.findall(r'href="(https://www\.mystipendium\.de/[^"#]*(?:cashback|geld-zurueck|gratis|coupon|gutschein|rabatt)[^"#]*)"', p))): print(u)
