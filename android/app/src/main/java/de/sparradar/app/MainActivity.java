package de.sparradar.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Zeigt die SparRadar-Web-App im Vollbild. Links zu anderen Seiten öffnen im Browser. */
public class MainActivity extends Activity {

    private static final String APP_URL = "https://tiry38.github.io/sparradar/";
    private static final String APP_HOST = "tiry38.github.io";
    private static final long RELOAD_AFTER_MS = 30 * 60 * 1000; // nach 30 Minuten im Hintergrund neu laden

    // Updates der App selbst: der Build legt version.json und die APK in den Release "apps"
    private static final String REL = "https://github.com/Tiry38/sparradar/releases/download/apps/";
    private static final String ACTION_INSTALL_STATUS = "de.sparradar.app.INSTALL_STATUS";
    private static final long CHECK_EVERY_MS = 10 * 60 * 1000; // beim Öffnen prüfen, höchstens alle 10 Minuten

    private WebView web;
    private long pausedAt = 0;
    private long lastCheck = 0;
    private boolean updateRunning = false;
    private boolean waitForPermission = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.parseColor("#16191C"));

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#16191C"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true); // Merkliste, Einkaufszettel und Coupons bleiben gespeichert
        s.setDatabaseEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setSupportMultipleWindows(false);
        // Knopf „Nach App-Update suchen“ in der Web-App ruft SparRadarApp.checkUpdate() auf
        web.addJavascriptInterface(new Object() {
            @JavascriptInterface
            public void checkUpdate() {
                runOnUiThread(() -> {
                    lastCheck = SystemClock.elapsedRealtime();
                    checkForUpdate(true);
                });
            }
        }, "SparRadarApp");
        // Versionsnummer für die Anzeige in den Einstellungen der Web-App
        s.setUserAgentString(s.getUserAgentString() + " SparRadarAndroid/" + installedVersion());

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (APP_HOST.equals(uri.getHost()) && uri.getPath() != null && uri.getPath().startsWith("/sparradar")) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                    // kein Programm für diesen Link vorhanden
                }
                return true;
            }
        });

        setContentView(web);
        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState);
        } else {
            web.loadUrl(APP_URL);
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }

    @Override
    protected void onPause() {
        super.onPause();
        pausedAt = SystemClock.elapsedRealtime();
        web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
        if (pausedAt > 0 && SystemClock.elapsedRealtime() - pausedAt > RELOAD_AFTER_MS) {
            web.reload(); // frische Angebote nach längerer Pause
        }
        if (waitForPermission) {
            // zurück aus den Einstellungen "Unbekannte Apps installieren"
            waitForPermission = false;
            if (getPackageManager().canRequestPackageInstalls()) downloadAndInstall();
            else toast("Update abgebrochen: Installation wurde nicht erlaubt.");
        } else if (!updateRunning && (lastCheck == 0 || SystemClock.elapsedRealtime() - lastCheck > CHECK_EVERY_MS)) {
            lastCheck = SystemClock.elapsedRealtime();
            checkForUpdate(false);
        }
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    // ---------- Update der App ----------

    @SuppressWarnings("deprecation")
    private int installedVersion() {
        try {
            return getPackageManager().getPackageInfo(getPackageName(), 0).versionCode;
        } catch (Exception e) {
            return Integer.MAX_VALUE; // im Zweifel nicht nerven
        }
    }

    /** Fragt im Hintergrund version.json ab, z. B. {"code":12}. Kein Netz = kein Hinweis. */
    private void checkForUpdate(boolean manual) {
        if (manual) toast("Suche nach Updates …");
        new Thread(() -> {
            try {
                String json = new String(get(REL + "version.json"), "UTF-8");
                java.util.regex.Matcher m = java.util.regex.Pattern.compile("\"code\"\\s*:\\s*(\\d+)").matcher(json);
                if (m.find() && Integer.parseInt(m.group(1)) > installedVersion()) {
                    runOnUiThread(this::askForUpdate);
                } else if (manual) {
                    runOnUiThread(() -> toast("Du hast schon die neueste App-Version."));
                }
            } catch (Exception e) {
                // offline oder Release noch ohne version.json
                if (manual) runOnUiThread(() -> toast("Keine Verbindung. Bitte später noch einmal versuchen."));
            }
        }).start();
    }

    private void askForUpdate() {
        if (isFinishing() || updateRunning) return;
        new AlertDialog.Builder(this)
                .setTitle("Neue SparRadar-Version")
                .setMessage("Ein Update für die App ist da. Jetzt aktualisieren?\n\nAndroid fragt danach noch einmal zur Sicherheit nach. Einfach bestätigen.")
                .setPositiveButton("Aktualisieren", (d, w) -> startUpdate())
                .setNegativeButton("Später", null)
                .show();
    }

    private void startUpdate() {
        if (!getPackageManager().canRequestPackageInstalls()) {
            // nur beim allerersten Update: Android muss SparRadar einmal das Installieren erlauben
            new AlertDialog.Builder(this)
                    .setTitle("Einmal erlauben")
                    .setMessage("Damit sich SparRadar selbst aktualisieren darf, gleich bei „Aus dieser Quelle zulassen“ den Schalter einschalten und dann zurück tippen. Das ist nur einmal nötig.")
                    .setPositiveButton("Weiter", (d, w) -> {
                        waitForPermission = true;
                        startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                                Uri.parse("package:" + getPackageName())));
                    })
                    .setNegativeButton("Später", null)
                    .show();
            return;
        }
        downloadAndInstall();
    }

    private void downloadAndInstall() {
        updateRunning = true;
        toast("Update wird geladen …");
        new Thread(() -> {
            try {
                byte[] apk = get(REL + "SparRadar.apk");
                PackageInstaller pi = getPackageManager().getPackageInstaller();
                PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
                params.setAppPackageName(getPackageName());
                int id = pi.createSession(params);
                try (PackageInstaller.Session session = pi.openSession(id)) {
                    try (OutputStream out = session.openWrite("sparradar.apk", 0, apk.length)) {
                        out.write(apk);
                        session.fsync(out);
                    }
                    Intent status = new Intent(this, MainActivity.class).setAction(ACTION_INSTALL_STATUS);
                    PendingIntent p = PendingIntent.getActivity(this, 0, status,
                            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE);
                    session.commit(p.getIntentSender());
                }
            } catch (Exception e) {
                updateRunning = false;
                runOnUiThread(() -> toast("Update hat nicht geklappt. Bitte später noch einmal versuchen."));
            }
        }).start();
    }

    /** Rückmeldung von Android zur Installation (Activity läuft als singleTask). */
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (!ACTION_INSTALL_STATUS.equals(intent.getAction())) return;
        int st = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (st == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            @SuppressWarnings("deprecation")
            Intent confirm = intent.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirm != null) startActivity(confirm); // Androids eigene Sicherheitsabfrage
            return;
        }
        updateRunning = false;
        if (st != PackageInstaller.STATUS_SUCCESS && st != PackageInstaller.STATUS_FAILURE_ABORTED) {
            toast("Update hat nicht geklappt. Bitte später noch einmal versuchen.");
        }
    }

    private static byte[] get(String url) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setConnectTimeout(15000);
        c.setReadTimeout(60000);
        c.setInstanceFollowRedirects(true); // GitHub leitet Release-Dateien weiter
        c.setRequestProperty("Cache-Control", "no-cache");
        try (InputStream in = c.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            if (c.getResponseCode() != 200) throw new Exception("HTTP " + c.getResponseCode());
            byte[] buf = new byte[16384];
            int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            return out.toByteArray();
        } finally {
            c.disconnect();
        }
    }

    private void toast(String m) {
        Toast.makeText(this, m, Toast.LENGTH_LONG).show();
    }
}
