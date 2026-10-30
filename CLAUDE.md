# SparRadar – Projektwissen für Claude

Private Angebots-App von Kevin (GitHub: Tiry38). Antworte auf **Deutsch**, einfach und Schritt für Schritt erklärt.
App: https://tiry38.github.io/sparradar/ · Repo: https://github.com/Tiry38/sparradar

## Arbeitsweise
- **Änderungen direkt auf `main` committen und pushen** (kein Pull Request), außer der Nutzer sagt etwas anderes. Nur `main` wird veröffentlicht.
- Vor dem Push `git pull --rebase`: Der Bot committet jeden Morgen neue Daten nach `docs/data/`.
- Nach Änderungen an `docs/app.js` oder `docs/app.css`/`style.css` die Versionsnummer in `docs/index.html` hochzählen (`app.js?v=…`), sonst hält der Browser-Cache die alte Version. Bei größeren Änderungen am Service Worker `CACHE` in `docs/sw.js` hochzählen.
- Commit-Nachrichten auf Deutsch.
- Fehler rückgängig machen: `git revert` des letzten Commits und auf `main` pushen.

## Aufbau
- `docs/` – die App (statisches HTML/CSS/JS, kein Build-Schritt), läuft auf GitHub Pages. PWA mit `manifest.webmanifest` und `sw.js`.
  - `app.js` – gesamte Logik; Daten liegen pro Gerät in `localStorage` (Merkliste, Einkaufszettel, eigene Angebote, Coupons).
  - `data/offers.json` und `data/history.json` – werden vom Abruf geschrieben, nicht von Hand ändern.
- `fetcher/fetch_offers.py` – täglicher Angebots-Abruf, nur Python-Standardbibliothek.
- `.github/workflows/angebote.yml` – Abruf jeden Morgen ca. 5:15/6:15 Uhr, committet nach `docs/data/`.
- `android/` – Android-App (WebView auf die Pages-URL), `desktop/src-tauri/` – Windows-App (Tauri 2, WebView2).
- `.github/workflows/apps.yml` – baut `SparRadar.apk` und `SparRadar-Setup.exe` und lädt sie in den Release `apps` hoch. Beide Apps zeigen immer die Online-Version, müssen also nur bei Änderungen in `android/` oder `desktop/` neu gebaut werden.

## Märkte (Region Wörth am Rhein, ca. 20 km)
| Markt | Quelle |
|---|---|
| Lidl | lidl.de Such-API, Kategorie „Essen & Trinken“ (`category.id=10068374`), nur `store=1` (Filiale) mit Rabatt; plus kaufDA |
| Aldi Süd | aldi-sued.de/de/angebote.html, Daten aus `__NUXT_DATA__` |
| Rewe | kaufDA `Woerth-am-Rhein/REWE/p-r101` |
| Netto Marken-Discount | kaufDA `Woerth-am-Rhein/Netto-Marken-Discount/p-r9` |
| Edeka **Jockgrim** | kaufDA `Jockgrim/EDEKA/p-r107` (ausdrücklich der Markt in Jockgrim) |
| dm | kaufDA `Woerth-am-Rhein/dm-drogerie-markt/p-r104` |
| Scheck-In (Wörth, Maximiliancenter) | nicht automatisch – Nutzer trägt Angebote in der App selbst ein |
| Serpa Markt (Wörth) | nicht automatisch – Nutzer trägt Angebote in der App selbst ein |

Zusätzlich fragt der Abruf kaufDA-Stichwortseiten für Karlsruhe ab (`/Karlsruhe/Angebote/<Begriff>`, Umlaute ausgeschrieben: Käse → Kaese). Für Wörth gibt es keine Stichwortseiten.

## Was in die App gehört
- **Ja:** Lebensmittel, Getränke, **Katzenfutter**, **Drogerie & Pflege** (Duschgel, Deo, Kosmetik, Zahnpflege, Rasierer, Klopapier, Taschentücher, Küchenrolle).
- **Nein:** Non-Food (Kleidung, Werkzeug, Elektro, Deko usw.), Katzenstreu, Hundefutter, Waschmittel, Putz- und Spülmittel, Windeln.
- Filter und Kategorien: `NONFOOD`, `DROGERIE`, `CATS`, `is_food()`, `classify()` in `fetcher/fetch_offers.py`. Kategorien müssen mit `CATS` in `docs/app.js` übereinstimmen.

## Bewusste Entscheidungen – nicht ändern ohne ausdrücklichen Wunsch
- **Keine Push-Benachrichtigungen.** Wurden gebaut und auf Wunsch wieder komplett entfernt. Der Nutzer schaut selbst in die App.
- **Keine Logins** für Lidl Plus, Rewe Bonus, Payback o. Ä. Es gibt keine offiziellen Schnittstellen. Die Passwörter lägen im öffentlichen Repo, und es drohen Kontosperren. Stattdessen gibt es **„Meine Coupons“** zum Selbst-Eintragen (Tab „Coupons“).
- **Sperren nicht umgehen:** rewe.de und netto-online.de blocken automatische Abrufe (403). Diese Sperren nicht umgehen, keine API-Schlüssel aus Websites auslesen (z. B. bei Marktguru). Nur öffentliche Seiten, die robots.txt erlaubt, mit ehrlichem User-Agent, höchstens einmal pro Tag und mit Pausen (`PAUSE`).
- Das Repository ist öffentlich (nötig für kostenloses GitHub Pages). Keine Passwörter, Tokens oder persönlichen Daten hineinschreiben.

## App-Funktionen (Überblick)
Suche nur in Angeboten · Filter nach Markt und Kategorie · Sortierung nach Ersparnis/Grundpreis/Preis · „Jetzt gültig“/„Demnächst“ · **Kracher**-Button (bestes Angebot inkl. Kombi aus App-Preis, Rewe-Bonus, eigenen Coupons) · Preisverlauf mit Tiefstpreis- und Fake-Rabatt-Erkennung · Merkliste mit Wunsch-Grundpreis (Vorrats-Alarm) · Wochenplan · Einkaufszettel im Kassenbon-Stil · eigene Angebote eintragen · Meine Coupons · Spartipps · echte Produktfotos (Fallback: gezeichnete Illustrationen).

## Testen
- Abruf lokal: `python fetcher/fetch_offers.py` (dauert ca. 3–5 Minuten). Auf Kevins Windows-PC scheitert Aldi lokal an einem Zertifikatsfehler, auf GitHub funktioniert es.
- App lokal: `python -m http.server 8765 --directory docs`, dann http://localhost:8765 öffnen.
- Abruf auf GitHub von Hand starten: Actions → „Angebote abrufen“ → „Run workflow“ (oder `gh workflow run angebote.yml`).
