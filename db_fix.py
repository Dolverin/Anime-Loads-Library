#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfaches Skript zur direkten Fehlerbehebung der Datenbankstruktur
"""

import os
import mysql.connector
from mysql.connector import Error
import sys
import logging

# Konfigurationsvariablen aus .env Datei oder Standard-Werte
DB_HOST = "192.168.178.9"
DB_USER = "aniworld"
DB_PASSWORD = "aniworld"
DB_NAME = "animeloads"

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_database_structure():
    """Fügt fehlende Spalten zur Episodes-Tabelle hinzu."""
    try:
        print("Verbinde mit Datenbank...")
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        if not connection.is_connected():
            print("Datenbankverbindung fehlgeschlagen!")
            return False
            
        cursor = connection.cursor(buffered=True)
        print(f"Verbindung zur Datenbank {DB_NAME} hergestellt.")
        
        # Prüfen, ob die Tabelle existiert
        cursor.execute("SHOW TABLES LIKE 'episodes'")
        if not cursor.fetchone():
            print("Die Episodes-Tabelle existiert nicht! Führe zuerst anime_archiver.py aus.")
            return False
            
        # Vorhandene Spalten abrufen
        print("Prüfe vorhandene Tabellenspalten...")
        cursor.execute("DESCRIBE episodes")
        existing_columns = [row[0].lower() for row in cursor.fetchall()]
        print(f"Gefundene Spalten: {len(existing_columns)}")
        
        # Liste der Spalten, die hinzugefügt werden sollen
        columns_to_add = [
            ("duration_ms", "BIGINT"),
            ("video_format", "VARCHAR(50)"),
            ("video_codec", "VARCHAR(50)"),
            ("video_bitrate", "BIGINT"),
            ("resolution_width", "INT"),
            ("resolution_height", "INT"),
            ("framerate", "FLOAT"),
            ("audio_codec", "VARCHAR(50)"),
            ("audio_channels", "INT"),
            ("audio_bitrate", "BIGINT"),
            ("audio_sample_rate", "INT"),
            ("subtitles_language", "VARCHAR(255)"),
            ("creation_time", "DATETIME"),
            ("aspect_ratio", "VARCHAR(20)"),
            ("color_depth", "VARCHAR(10)"),
            ("hdr_format", "VARCHAR(30)"),
            ("color_space", "VARCHAR(30)"),
            ("scan_type", "VARCHAR(20)"),
            ("encoder", "VARCHAR(100)"),
            ("audio_language", "VARCHAR(50)"),
            ("audio_tracks_count", "INT"),
            ("audio_languages", "VARCHAR(255)"),
            ("subtitles_formats", "VARCHAR(255)"),
            ("subtitles_count", "INT"),
            ("forced_subtitles", "BOOLEAN"),
            ("container_format", "VARCHAR(50)")
        ]
        
        # Spalten hinzufügen
        added_columns = 0
        for column_name, column_type in columns_to_add:
            if column_name.lower() not in existing_columns:
                try:
                    print(f"Füge Spalte {column_name} ({column_type}) hinzu...")
                    cursor.execute(f"ALTER TABLE episodes ADD COLUMN {column_name} {column_type}")
                    added_columns += 1
                except Error as e:
                    print(f"Fehler beim Hinzufügen der Spalte {column_name}: {e}")
        
        if added_columns > 0:
            connection.commit()
            print(f"Erfolgreich {added_columns} neue Spalte(n) zur Episodes-Tabelle hinzugefügt.")
        else:
            print("Keine neuen Spalten hinzugefügt. Die Tabelle hat bereits alle benötigten Spalten.")
            
        # Fertig
        cursor.close()
        connection.close()
        print("Datenbankverbindung geschlossen.")
        return True
        
    except Error as e:
        print(f"Datenbankfehler: {e}")
        return False
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        return False

if __name__ == "__main__":
    print("=== Datenbank-Strukturanpassung ===")
    success = fix_database_structure()
    if success:
        print("Datenbank-Strukturanpassung abgeschlossen.")
    else:
        print("Datenbank-Strukturanpassung fehlgeschlagen!")
        sys.exit(1)
