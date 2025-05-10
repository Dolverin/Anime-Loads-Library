# UI-Tests für Anime-Loads Dashboard

Dieses Verzeichnis enthält UI-Tests mit Playwright für das Anime-Loads Dashboard. Die Tests überprüfen die Benutzeroberfläche und die Interaktion mit dem Dashboard.

## Testumfang

Die UI-Tests decken folgende Bereiche des Dashboards ab:

### Startseite (Homepage)
- Seitentitel und Hauptüberschrift
- Dashboard-Karten
- Navigationslinks
- Charts (Auflösung und HDR)
- Top-Animes-Liste

### Anime-Liste
- Seitentitel und Hauptüberschrift
- Suchfunktion
- Anime-Karten
- Navigation zu Detailseiten
- Breadcrumb-Navigation

### Statistikseite
- Seitentitel und Hauptüberschrift
- Charts (Auflösung, Codec, etc.)
- Tab-Navigation
- Responsives Layout

## Voraussetzungen

Für die Ausführung der UI-Tests benötigst du:

1. Die virtuelle Umgebung mit allen installierten Abhängigkeiten (`venv`)
2. Playwright und pytest-playwright (in `requirements.txt` enthalten)
3. Playwright-Browser (werden automatisch bei der ersten Ausführung installiert)

## Testkonzept

Die Tests verwenden folgende Konzepte:

1. **Page Object Model**: Tests nutzen Fixtures für verschiedene Seiten
2. **Automatischer Testserver**: Ein Flask-Server wird für die Tests automatisch gestartet
3. **Browserkontext**: Jeder Test erhält einen eigenen Browser-Kontext für Isolation
4. **Viewport-Tests**: Prüfung des responsiven Designs durch Viewport-Änderungen

## Ausführung der Tests

Die UI-Tests können mit dem speziellen Skript `run_ui_tests.py` ausgeführt werden:

```bash
# Alle UI-Tests ausführen
./run_ui_tests.py

# Tests mit sichtbarem Browser ausführen
./run_ui_tests.py --headed

# Tests langsamer ausführen (für Debugging)
./run_ui_tests.py --slow

# Einen bestimmten Test ausführen
./run_ui_tests.py --test homepage
```

Alternativ kannst du die Tests auch direkt mit pytest ausführen:

```bash
# Alle UI-Tests ausführen
python -m pytest tests/ui/

# Einen spezifischen Test ausführen
python -m pytest tests/ui/test_homepage.py
```

## Fehlerbehebung

Bei Problemen mit den UI-Tests:

1. **Browser-Installation**: Stelle sicher, dass die Playwright-Browser installiert sind: `playwright install`
2. **Portkonflikte**: Prüfe, ob der Port für den Testserver (5050) frei ist
3. **Timeout-Fehler**: Bei langsamer Verbindung die Timeouts erhöhen (`--slow` Option verwenden)
4. **DOM-Änderungen**: Bei Änderungen am Frontend müssen ggf. die Selektoren in den Tests angepasst werden

## Erweiterung der Tests

Um neue UI-Tests hinzuzufügen:

1. Erstelle eine neue Testdatei mit dem Präfix `test_`
2. Importiere die benötigten Playwright-Komponenten und Fixtures
3. Implementiere Testfunktionen, die die UI-Funktionalität überprüfen
4. Verwende die vorhandenen Fixtures (`navigate_to_*`, etc.) oder erstelle neue bei Bedarf
