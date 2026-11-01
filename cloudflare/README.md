# Sync-Speicher (Familien-Codes)

Damit jeder in SparRadar per Knopfdruck einen **eigenen Familien-Code** erstellen kann – ohne GitHub-Konto.
Läuft kostenlos auf Cloudflare (Workers + D1-Datenbank). Gespeichert wird nur, was die Geräte teilen
(Einkaufszettel, ggf. Merkliste/Coupons, Gerätenamen). Der Code ist eine zufällige, nicht erratbare ID.

## Einmalig einrichten (ca. 10 Minuten)
1. Auf https://dash.cloudflare.com/sign-up kostenlos registrieren und die E-Mail bestätigen.
2. **Schlüssel erstellen:** https://dash.cloudflare.com/profile/api-tokens → „Create Token“ →
   Vorlage **„Edit Cloudflare Workers“** → „Use template“ → bei *Permissions* mit „+ Add more“ zusätzlich
   **Account · D1 · Edit** hinzufügen → ganz unten „Continue to summary“ → „Create Token“ → Schlüssel kopieren.
3. **In GitHub eintragen:** https://github.com/Tiry38/sparradar/settings/secrets/actions/new
   - Name `CLOUDFLARE_API_TOKEN`, Wert = Schlüssel aus Schritt 2 → „Add secret“
   - (Die Account-ID sucht die Einrichtung selbst. Optional als Secret `CLOUDFLARE_ACCOUNT_ID`.)
4. https://github.com/Tiry38/sparradar/actions/workflows/sync-server.yml → „Run workflow“.
   Nach ca. 1 Minute steht die Adresse in `docs/sync.json` – ab dann zeigt die App „Familien-Code erstellen“.

Den Schlüssel nie ins Repo schreiben. Kostenloser Rahmen: 100.000 Schreibvorgänge und 5 Mio. Lesevorgänge pro Tag.
