"""Diagnose (nur von Hand): Bilder-Wächter für einen einzelnen Artikel testen (Archiv + Sitemap-Größe)."""
import fill_images as fi

name = "IronMaxx SqueeBarista Caramel"
ts, orig = fi.wayback_aldi(name)
print("Archiv:", ts, orig)
if ts:
    html = fi.http(f"https://web.archive.org/web/{ts}id_/{orig}")
    im = fi.page_img(html)
    print("Bild:", im, "->", f"https://web.archive.org/web/{ts}im_/{im}" if im else "-")
for shop, sm in fi.SITEMAPS.items():
    urls = fi.sitemap_urls(sm, r"/produkt/|/p/[^/]+/p\d+")
    print(shop, len(urls), urls[:3])
    if urls:
        h = fi.http(urls[0]); print("   og:image", fi.page_img(h))
