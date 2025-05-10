# API-Tests für Anime-Loads Dashboard

Dieses Verzeichnis enthält Unit-Tests für die API-Endpunkte des Anime-Loads Dashboards. Die Tests überprüfen, ob die API-Antworten die erwartete Struktur haben und alle Daten korrekt serialisiert werden können.

## Testumfang

Die Tests decken folgende API-Endpunkte ab:

### Statistik-Endpunkte
- `/api/stats` - Allgemeine Dashboard-Statistiken
- `/api/stats/resolution` - Auflösungsverteilung
- `/api/stats/hdr` - HDR-Format-Verteilung
- `/api/stats/top_animes` - Top-Animes nach Episodenanzahl

### Such-Endpunkt
- `/api/search` - Suche nach Animes, Staffeln und Episoden

### Filter-Endpunkt
- `/api/filter` - Filterung von Episoden nach verschiedenen Kriterien

## Testfokus

Die Tests konzentrieren sich auf folgende Aspekte:

1. **Strukturvalidierung**: Stellen sicher, dass alle API-Antworten die erwartete JSON-Struktur haben
2. **Typprüfung**: Testen, ob alle Felder den richtigen Datentyp haben
3. **Funktionalität**: Überprüfen, ob die Filter und Suchfunktionen wie erwartet funktionieren
4. **Robustheit**: Testen, wie die API mit Edge Cases umgeht

## Voraussetzungen

Um die Tests auszuführen, benötigst du:

1. Die virtuelle Umgebung mit allen installierten Abhängigkeiten (`venv`)
2. Pytest und pytest-flask (in `requirements.txt` enthalten)

## Ausführung der Tests

Die Tests können mit dem folgenden Befehl ausgeführt werden:

```bash
cd /home/dolverin/CascadeProjects/Anime-Loads-Library
python -m pytest tests/
```

Für detailliertere Ausgabe:

```bash
python -m pytest tests/ -v
```

Um einen bestimmten Test auszuführen:

```bash
python -m pytest tests/test_api_stats.py -v
```

## Fehlerbehebung

Falls die Tests fehlschlagen, können folgende Ursachen vorliegen:

1. **Datenbankverbindung**: Stelle sicher, dass die Verbindung zur Datenbank funktioniert
2. **API-Änderungen**: Wenn die API-Struktur geändert wurde, müssen ggf. die Tests angepasst werden
3. **Abhängigkeiten**: Prüfe, ob alle benötigten Pakete installiert sind

## Erweiterung der Tests

Um neue Tests hinzuzufügen:

1. Erstelle eine neue Testdatei mit dem Präfix `test_`
2. Implementiere Testfunktionen mit dem Präfix `test_`
3. Verwende die vorhandenen Fixtures (`client`, `app`, etc.)
4. Führe alle Tests durch, um sicherzustellen, dass keine Regression auftritt
