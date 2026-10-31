package de.sparradar.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Zeigt die SparRadar-Web-App im Vollbild. Links zu anderen Seiten öffnen im Browser. */
public class MainActivity extends Activity {

    private static final String APP_URL = "https://tiry38.github.io/sparradar/";
    private static final String APP_HOST = "tiry38.github.io";
    private static final long RELOAD_AFTER_MS = 30 * 60 * 1000; // nach 30 Minuten im Hintergrund neu laden

    // Updates der App selbst: der Build legt version.json und die APK in den Release "apps"
    private static final String REL = "https://github.com/Tiry38/sparradar/releases/download/apps/";
    private static final long CHECK_EVERY_MS = 10 * 60 * 1000; // beim Öffnen prüfen, höchstens alle 10 Minuten

    private WebView web;
    private long pausedAt = 0;
    private long lastCheck = 0;
    private boolean updateRunning = false;
    private boolean waitForPermission = false;
    private long downloadId = -1;

    /** Download fertig -> Androids eigene Installation öffnen („Aktualisieren?“) */
    private final BroadcastReceiver downloadDone = new BroadcastReceiver() {
        @Override
        public void onReceive(Context c, Intent i) {
            if (i.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -2) != downloadId) return;
            updateRunning = false;
            Uri apk = ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).getUriForDownloadedFile(downloadId);
            if (apk == null) {
                toast("Download hat nicht geklappt. Bitte später noch einmal versuchen.");
                return;
            }
            Intent install = new Intent(Intent.ACTION_VIEW)
                    .setDataAndType(apk, "application/vnd.android.package-archive")
                    .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
            try {
                startActivity(install);
            } catch (Exception e) {
                toast("Installation konnte nicht geöffnet werden. Bitte die Datei unter Downloads antippen.");
            }
        }
    };

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

            /** „Ja, schließen“ in der Web-App: App wirklich beenden */
            @JavascriptInterface
            public void exitApp() {
                runOnUiThread(() -> finish());
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

        IntentFilter done = new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(downloadDone, done, Context.RECEIVER_EXPORTED);
        else registerReceiver(downloadDone, done);

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
                int latest = m.find() ? Integer.parseInt(m.group(1)) : 0;
                SharedPreferences prefs = getSharedPreferences("sparradar", MODE_PRIVATE);
                // automatisch nur einmal pro neuer Version fragen, über den Knopf in den Einstellungen immer
                if (latest > installedVersion() && (manual || prefs.getInt("askedVersion", 0) < latest)) {
                    prefs.edit().putInt("askedVersion", latest).apply();
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

    /** Update über den Android-Download-Manager laden (Fortschritt in der Benachrichtigungsleiste). */
    private void downloadAndInstall() {
        try {
            File dir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
            File old = new File(dir, "SparRadar-Update.apk");
            if (old.exists()) old.delete();
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(REL + "SparRadar.apk"))
                    .setTitle("SparRadar-Update")
                    .setDescription("Neue Version wird geladen")
                    .setMimeType("application/vnd.android.package-archive")
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationInExternalFilesDir(this, Environment.DIRECTORY_DOWNLOADS, "SparRadar-Update.apk");
            downloadId = ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(r);
            updateRunning = true;
            toast("Update wird geladen … gleich fragt Android „Aktualisieren?“ – einfach bestätigen.");
        } catch (Exception e) {
            updateRunning = false;
            toast("Update hat nicht geklappt. Bitte später noch einmal versuchen.");
        }
    }

    @Override
    protected void onDestroy() {
        try {
            unregisterReceiver(downloadDone);
        } catch (Exception ignored) {
            // war nicht registriert
        }
        super.onDestroy();
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
