# Anime-Loads-Library

Dieses Projekt archiviert Anime, Staffeln und Episoden aus dem Dateisystem in eine MySQL-Datenbank.

## Voraussetzungen

- Python 3.8+
- MySQL-Datenbankserver
- Zugriff auf das Verzeichnis `/mnt/mediathek`

## Installation

```bash
pip install -r requirements.txt
```

## Konfiguration

Die Datenbankkonfiguration kann über die `.env`-Datei oder direkt im Skript angepasst werden.

## Verwendung

```bash
python anime_archiver.py
```

Das Skript durchsucht den Ordner `/mnt/mediathek` und speichert alle gefundenen Anime, Staffeln und Episoden in der MySQL-Datenbank.
