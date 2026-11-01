import re, urllib.request, html, json
UA = "SparRadar/1.0 (+https://tiry38.github.io/sparradar/)"
p = urllib.request.urlopen(urllib.request.Request("https://www.sparwelt.de/gratis/cashback", headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "replace")
print("NEXT_DATA" , "__NEXT_DATA__" in p, "| nuxt", "__NUXT" in p, "| ld+json", p.count("application/ld+json"))
for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', p, re.S):
    print("LD:", m.group(1)[:1500])
cards = p.split('@container/deal w-full relative')
print("Karten", len(cards) - 1)
for c in cards[1:4] + cards[27:30]:
    c = re.sub(r'\sclass="[^"]*"', "", c[:9000])
    c = re.sub(r"<svg.*?</svg>", "<svg/>", c, flags=re.S)
    print("\n=========\n", c[:4500])
