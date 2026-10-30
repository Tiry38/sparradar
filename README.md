# SparRadar

Private Angebots-App für Lebensmittel, Getränke, Katzenfutter und Drogerie & Pflege rund um Wörth am Rhein.

- **App:** `docs/` (läuft auf GitHub Pages, auf dem Handy über „Zum Startbildschirm hinzufügen“ installierbar)
- **Abruf:** `fetcher/fetch_offers.py` läuft jeden Morgen über GitHub Actions (`.github/workflows/angebote.yml`) und schreibt `docs/data/offers.json` und `docs/data/history.json`
- **Quellen:** Lidl und Aldi Süd direkt von deren Websites, Rewe, Netto, Edeka Jockgrim und dm über die öffentlichen Prospekt-Seiten von kaufDA. Scheck-In und Serpa werden in der App selbst eingetragen.
- **Merkliste:** liegt nur im Browser des jeweiligen Geräts. Treffer zeigt die App beim Öffnen an.

Der Abruf ruft jede Seite höchstens einmal am Tag auf und nutzt nur öffentlich zugängliche Seiten ohne Login.

Von Hand starten: Tab „Actions“ → „Angebote abrufen“ → „Run workflow“.
