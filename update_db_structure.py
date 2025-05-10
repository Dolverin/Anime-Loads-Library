#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimiertes Skript zur Aktualisierung der Datenbankstruktur und Episoden-Metadaten
mit verbesserter Fortschrittsanzeige und flexiblen Update-Optionen
"""

import os
import sys
import logging
import argparse
import mysql.connector
from mysql.connector import Error
from anime_archiver import setup_database, update_episodes_metadata
from tqdm import tqdm
from datetime import datetime

# Logging konfigurieren
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format,
                   handlers=[logging.FileHandler('db_update.log'),
                             logging.StreamHandler()])

def update_db_structure(connection):
    """
    Aktualisiert nur die Datenbankstruktur ohne Metadaten-Updates
    """
    cursor = connection.cursor(buffered=True)
    tables_updated = False
    
    # Prüfen, ob die Episodes-Tabelle existiert
    cursor.execute("SHOW TABLES LIKE 'episodes'")
    episodes_exists = cursor.fetchone() is not None
    
    if not episodes_exists:
        logging.error("Episodes-Tabelle existiert nicht! Führe zuerst anime_archiver.py aus.")
        return False
    
    # Prüfen, welche Spalten schon existieren
    cursor.execute("DESCRIBE episodes")
    existing_columns = [row[0].lower() for row in cursor.fetchall()]
    
    # Liste der erwarteten Spalten und ihre Datentypen
    # Basierend auf setup_database()-Funktion aus anime_archiver.py
    expected_columns = [
        # Grundlegende Videometadaten
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
        
        # Erweiterte Videometadaten
        ("aspect_ratio", "VARCHAR(20)"),
        ("color_depth", "VARCHAR(10)"),
        ("hdr_format", "VARCHAR(30)"),
        ("color_space", "VARCHAR(30)"),
        ("scan_type", "VARCHAR(20)"),
        ("encoder", "VARCHAR(100)"),
        
        # Erweiterte Audiometadaten
        ("audio_language", "VARCHAR(50)"),
        ("audio_tracks_count", "INT"),
        ("audio_languages", "VARCHAR(255)"),
        
        # Erweiterte Untertitelmetadaten
        ("subtitles_formats", "VARCHAR(255)"),
        ("subtitles_count", "INT"),
        ("forced_subtitles", "BOOLEAN"),
        
        # Containerformat
        ("container_format", "VARCHAR(50)")
    ]
    
    # Hinzufügen fehlender Spalten
    added_columns = 0
    for column_name, column_type in expected_columns:
        if column_name.lower() not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE episodes ADD COLUMN {column_name} {column_type}")
                added_columns += 1
                logging.info(f"Spalte {column_name} ({column_type}) zur Episodes-Tabelle hinzugefügt.")
                tables_updated = True
            except Error as e:
                logging.error(f"Fehler beim Hinzufügen der Spalte {column_name}: {e}")
    
    if added_columns > 0:
        connection.commit()
        logging.info(f"{added_columns} neue Spalten zur Episodes-Tabelle hinzugefügt.")
    else:
        logging.info("Alle erwarteten Spalten sind bereits vorhanden.")
    
    return tables_updated

def get_episode_count(connection):
    """
    Ermittelt die Anzahl der Episoden in der Datenbank
    """
    try:
        cursor = connection.cursor(buffered=True)
        cursor.execute("SELECT COUNT(*) FROM episodes")
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    except Error as e:
        logging.error(f"Fehler beim Zählen der Episoden: {e}")
        return 0

def get_anime_list(connection):
    """
    Gibt eine Liste aller Animes mit ihren IDs zurück
    """
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM animes ORDER BY name")
        animes = cursor.fetchall()
        cursor.close()
        return animes
    except Error as e:
        logging.error(f"Fehler beim Abrufen der Anime-Liste: {e}")
        return []

def update_metadata_for_anime(connection, anime_id):
    """
    Aktualisiert nur die Metadaten für einen bestimmten Anime
    """
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Anime-Name zur Bestätigung abrufen
        cursor.execute("SELECT name FROM animes WHERE id = %s", (anime_id,))
        anime = cursor.fetchone()
        if not anime:
            logging.error(f"Anime mit ID {anime_id} nicht gefunden.")
            return 0
        
        # Anime-Verzeichnispfad abrufen
        cursor.execute("SELECT directory_path FROM animes WHERE id = %s", (anime_id,))
        path_data = cursor.fetchone()
        if not path_data:
            logging.error(f"Pfad für Anime mit ID {anime_id} nicht gefunden.")
            return 0
        
        anime_path = path_data['directory_path']
        logging.info(f"Aktualisiere Metadaten für Anime: {anime['name']} (Pfad: {anime_path})")
        
        # Metadaten für diesen Anime aktualisieren
        count = update_episodes_metadata(connection, filter_path=anime_path, reprocess_all=True)
        
        cursor.close()
        return count
    except Error as e:
        logging.error(f"Fehler beim Aktualisieren der Metadaten für Anime {anime_id}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Datenbankstruktur und Episoden-Metadaten aktualisieren')
    parser.add_argument('--structure-only', action='store_true', 
                      help='Nur die Datenbankstruktur aktualisieren, keine Metadaten')
    parser.add_argument('--metadata-only', action='store_true', 
                      help='Nur die Metadaten aktualisieren, keine Strukturänderungen')
    parser.add_argument('--anime', type=int, 
                      help='Nur für einen bestimmten Anime aktualisieren (ID angeben)')
    parser.add_argument('--list-animes', action='store_true', 
                      help='Liste aller verfügbaren Animes anzeigen')
    parser.add_argument('--incomplete-only', action='store_true', 
                      help='Nur Episoden mit fehlenden Metadaten aktualisieren')
    
    args = parser.parse_args()
    
    logging.info("=== Optimierte Datenbank-Struktur und Metadaten-Aktualisierung ===")
    logging.info(f"Gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Verbindung herstellen
        connection = setup_database()
        
        # Anzeigen der Anime-Liste, falls angefordert
        if args.list_animes:
            animes = get_anime_list(connection)
            print("\nVerfügbare Animes:")
            for anime in animes:
                print(f"ID: {anime['id']} - {anime['name']}")
            connection.close()
            return
        
        # Nur Datenbankstruktur aktualisieren
        if not args.metadata_only:
            logging.info("Aktualisiere Datenbankstruktur...")
            update_db_structure(connection)
        
        # Metadaten aktualisieren, falls gewünscht
        if not args.structure_only:
            if args.anime:
                # Nur einen bestimmten Anime aktualisieren
                count = update_metadata_for_anime(connection, args.anime)
                logging.info(f"Metadaten-Aktualisierung abgeschlossen. {count} Episoden wurden verarbeitet.")
            else:
                # Alle Metadaten aktualisieren
                total_episodes = get_episode_count(connection)
                reprocess = not args.incomplete_only
                logging.info(f"Aktualisiere Metadaten für {total_episodes} Episoden")
                logging.info(f"Modus: {'Alle neu verarbeiten' if reprocess else 'Nur fehlende Metadaten'}")
                
                # Metadatenaktualisierung ausführen
                count = update_episodes_metadata(
                    connection, 
                    reprocess_all=reprocess
                )
                
                logging.info(f"Metadaten-Aktualisierung abgeschlossen. {count if count is not None else 'Unbekannte Anzahl'} Episoden verarbeitet.")
        
        connection.close()
        logging.info(f"Abgeschlossen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logging.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
