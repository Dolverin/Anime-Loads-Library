#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anime-Archiver: Durchsucht das Verzeichnis /mnt/mediathek nach Animes, Staffeln und Episoden
und speichert die gefundenen Daten in einer MySQL-Datenbank.
"""

import os
import re
import sys
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
from pymediainfo import MediaInfo

# Laden der Umgebungsvariablen
load_dotenv()

# Konfigurationsvariablen
DB_HOST = os.getenv('DB_HOST', '192.168.178.9')
DB_USER = os.getenv('DB_USER', 'aniworld')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aniworld')
DB_NAME = os.getenv('DB_NAME', 'animeloads')
MEDIA_PATH = os.getenv('MEDIA_PATH', '/mnt/mediathek')
MAX_RECURSION_DEPTH = int(os.getenv('MAX_RECURSION_DEPTH', '5'))

# Logging konfigurieren
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format,
                   handlers=[logging.FileHandler('anime_archiver.log'),
                             logging.StreamHandler()])

# Globale Variablen für Statistik
STATS = {
    'animes': 0,
    'seasons': 0,
    'episodes': 0,
    'skipped_files': 0
}

def setup_database():
    """
    Erstellt die benötigten Tabellen in der Datenbank, falls sie nicht existieren,
    oder aktualisiert bestehende Tabellen um neue Spalten hinzuzufügen.
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = connection.cursor(buffered=True)
        
        # Datenbank erstellen, falls sie nicht existiert
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # Tabellen erstellen oder aktualisieren
        
        # 1. Anime-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS animes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                directory_path VARCHAR(511) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_anime_name (name),
                UNIQUE KEY unique_anime_path (directory_path)
            )
        """)
        
        # 2. Seasons-Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seasons (
                id INT AUTO_INCREMENT PRIMARY KEY,
                anime_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                season_number INT,
                directory_path VARCHAR(511) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (anime_id) REFERENCES animes(id),
                UNIQUE KEY unique_season_path (directory_path)
            )
        """)
        
        # 3. Episodes-Tabelle (hier muss möglicherweise aktualisiert werden)
        # Zuerst prüfen, ob die Tabelle existiert
        cursor.execute("SHOW TABLES LIKE 'episodes'")
        episodes_exists = cursor.fetchone() is not None
        
        if not episodes_exists:
            # Neue Tabelle erstellen mit allen Spalten
            cursor.execute("""
                CREATE TABLE episodes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    season_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    episode_number INT,
                    file_path VARCHAR(511) NOT NULL,
                    file_size BIGINT,
                    file_extension VARCHAR(10),
                    
                    -- Grundlegende Videometadaten
                    duration_ms BIGINT,
                    video_format VARCHAR(50),
                    video_codec VARCHAR(50),
                    video_bitrate BIGINT,
                    resolution_width INT,
                    resolution_height INT,
                    framerate FLOAT,
                    
                    -- Erweiterte Videometadaten
                    aspect_ratio VARCHAR(20),
                    color_depth VARCHAR(10),
                    hdr_format VARCHAR(30),
                    color_space VARCHAR(30),
                    scan_type VARCHAR(20),
                    encoder VARCHAR(100),
                    
                    -- Grundlegende Audiometadaten
                    audio_codec VARCHAR(50),
                    audio_channels INT,
                    audio_bitrate BIGINT,
                    audio_sample_rate INT,
                    
                    -- Erweiterte Audiometadaten
                    audio_language VARCHAR(50),
                    audio_tracks_count INT,
                    audio_languages VARCHAR(255),
                    
                    -- Untertitelmetadaten
                    subtitles_language VARCHAR(255),
                    subtitles_formats VARCHAR(255),
                    subtitles_count INT,
                    forced_subtitles BOOLEAN,
                    
                    -- Dateiinformationen
                    container_format VARCHAR(50),
                    creation_time DATETIME,
                    
                    -- Systemfelder
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (season_id) REFERENCES seasons(id),
                    UNIQUE KEY unique_episode_path (file_path)
                )
            """)
            logging.info("Neue Episodes-Tabelle mit Videometadaten-Spalten erstellt.")
        else:
            # Tabelle existiert, fehlende Spalten hinzufügen
            # Alle neuen Spalten für die Videometadaten prüfen und hinzufügen
            for column_info in [
                # Grundlegende Videometadaten (bereits vorhanden)
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
                
                # Erweiterte Videometadaten (neu)
                ("aspect_ratio", "VARCHAR(20)"),
                ("color_depth", "VARCHAR(10)"),
                ("hdr_format", "VARCHAR(30)"),
                ("color_space", "VARCHAR(30)"),
                ("scan_type", "VARCHAR(20)"),
                ("encoder", "VARCHAR(100)"),
                
                # Erweiterte Audiometadaten (neu)
                ("audio_language", "VARCHAR(50)"),
                ("audio_tracks_count", "INT"),
                ("audio_languages", "VARCHAR(255)"),
                
                # Erweiterte Untertitelmetadaten (neu)
                ("subtitles_formats", "VARCHAR(255)"),
                ("subtitles_count", "INT"),
                ("forced_subtitles", "BOOLEAN"),
                
                # Containerformat (neu)
                ("container_format", "VARCHAR(50)")
            ]:
                column_name, column_type = column_info
                # Prüfen ob die Spalte bereits existiert
                cursor.execute(f"SHOW COLUMNS FROM episodes LIKE '{column_name}'")
                column_exists = cursor.fetchone() is not None
                
                if not column_exists:
                    # Spalte hinzufügen, falls sie nicht existiert
                    try:
                        cursor.execute(f"ALTER TABLE episodes ADD COLUMN {column_name} {column_type}")
                        logging.info(f"Spalte {column_name} ({column_type}) zur Episodes-Tabelle hinzugefügt.")
                    except Error as e:
                        logging.error(f"Fehler beim Hinzufügen der Spalte {column_name}: {e}")
            
            logging.info("Bestehende Episodes-Tabelle wurde mit Videometadaten-Spalten aktualisiert.")
        
        connection.commit()
        logging.info("Datenbankstruktur erfolgreich eingerichtet.")
        
        return connection
    
    except Error as e:
        logging.error(f"Fehler beim Einrichten der Datenbank: {e}")
        sys.exit(1)

def extract_season_number(season_name):
    """
    Extrahiert die Staffelnummer aus dem Staffelnamen.
    """
    match = re.search(r'staffel\s*(\d+)', season_name.lower())
    if match:
        return int(match.group(1))
    
    # Alternativer Versuch über "S01", "S1" Formate
    match = re.search(r's(?:eason)?\s*(\d+)', season_name.lower())
    if match:
        return int(match.group(1))
    
    # Versuchen, einfach nur eine Zahl zu finden
    match = re.search(r'^(\d+)$', season_name.strip())
    if match:
        return int(match.group(1))
    
    return None

def extract_episode_number(episode_name):
    """
    Extrahiert die Episodennummer aus dem Episodennamen.
    """
    # Typische Episodenformate: E01, EP01, Episode 01, 01 - Titel
    match = re.search(r'e(?:p(?:isode)?)?\s*(\d+)', episode_name.lower())
    if match:
        return int(match.group(1))
    
    # Format: 01 - Titel oder 01.Titel oder 01_Titel
    match = re.search(r'^(\d+)(?:\s*[\-_\.]\s*.+)?', os.path.splitext(episode_name)[0])
    if match:
        return int(match.group(1))
    
    return None

def is_video_file(filename):
    """
    Prüft, ob die Datei ein Videoformat hat.
    """
    video_extensions = [
        '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts',
        '.mpg', '.mpeg', '.m2ts', '.3gp', '.vob', '.divx', '.ogm', '.ogg', '.ogv',
        '.asf', '.rm', '.rmvb', '.m2v', '.svi', '.mxf', '.roq', '.nsv', '.f4v',
        '.f4p', '.f4a', '.f4b'
    ]
    _, ext = os.path.splitext(filename)
    return ext.lower() in video_extensions

def extract_media_info(file_path):
    """
    Extrahiert erweiterte Metadaten aus einer Videodatei mit MediaInfo.
    Angepasst für verschiedene pymediainfo-Versionen mit verbesserten Attributen.
    """
    try:
        logging.debug(f"Extrahiere Metadaten aus: {file_path}")
        media_info = MediaInfo.parse(file_path)
        result = {
            # Allgemeine Metadaten
            'duration_ms': None,
            'video_format': None,
            'video_codec': None,
            'video_bitrate': None,
            'resolution_width': None,
            'resolution_height': None,
            'framerate': None,
            'aspect_ratio': None,
            # Erweiterte Videometadaten
            'color_depth': None,       # z.B. 8bit, 10bit
            'hdr_format': None,        # z.B. HDR10, Dolby Vision, HLG
            'color_space': None,       # z.B. BT.2020, BT.709
            'scan_type': None,         # z.B. Progressive, Interlaced
            'encoder': None,           # Verwendeter Encoder
            # Audio-Metadaten (primärer Track)
            'audio_codec': None,
            'audio_channels': None,
            'audio_bitrate': None,
            'audio_sample_rate': None,
            'audio_language': None,
            # Multi-Audiospur-Informationen
            'audio_tracks_count': 0,
            'audio_languages': None,    # Alle verfügbaren Sprachen
            # Untertitel-Informationen
            'subtitles_language': None,
            'subtitles_formats': None,  # Formate der Untertitel
            'subtitles_count': 0,       # Anzahl der Untertitelspuren
            'forced_subtitles': False,  # Gibt es erzwungene Untertitel?
            # Dateiinformationen
            'creation_time': None,
            'container_format': None    # z.B. Matroska, MP4
        }
        
        # Allgemeine Informationen
        general_tracks = [t for t in media_info.tracks if t.track_type == 'General']
        if general_tracks:
            general_track = general_tracks[0]
            # Container-Format
            result['container_format'] = safe_get_attr(general_track, 'format')
            result['video_format'] = result['container_format']  # Für Abwärtskompatibilität
            
            # Dauer extrahieren - verschiedene Möglichkeiten prüfen
            duration = None
            for attr_name in ['duration', 'duration_ms', 'other_duration']:
                duration = safe_get_duration(general_track, attr_name)
                if duration is not None:
                    break
            
            result['duration_ms'] = duration
            
            # Erstellungsdatum mit erweiterter Unterstützung für verschiedene Formate
            result['creation_time'] = get_creation_time(general_track)
        
        # Video-Track-Informationen (erweitert)
        video_tracks = [track for track in media_info.tracks if track.track_type == 'Video']
        if video_tracks:
            video_track = video_tracks[0]  # Wir nehmen den ersten Video-Track
            
            # Grundlegende Videoattribute
            codec_mapping = {
                'codec_id': 'video_codec',
                'format': 'video_codec',
                'bit_rate': 'video_bitrate',
                'width': 'resolution_width',
                'height': 'resolution_height'
            }
            
            for attr_name, target_key in codec_mapping.items():
                value = safe_get_attr(video_track, attr_name)
                if value and target_key in ['resolution_width', 'resolution_height', 'video_bitrate']:
                    try:
                        if isinstance(value, str):
                            # Extrahiere nur Zahlen und Dezimalpunkte
                            value = ''.join(c for c in value if c.isdigit() or c == '.')
                        result[target_key] = int(float(value)) if value else None
                    except (ValueError, TypeError):
                        logging.debug(f"Konnte {attr_name} nicht in Zahl konvertieren: {value}")
                elif value:
                    result[target_key] = value
            
            # Framerate mit verbessertem Parsing
            result['framerate'] = get_framerate(video_track)
            
            # Seitenverhältnis berechnen
            if result['resolution_width'] and result['resolution_height'] and result['resolution_height'] > 0:
                ratio = result['resolution_width'] / result['resolution_height']
                # Runde auf gängige Aspektverhältnisse
                if 1.3 <= ratio <= 1.4:
                    result['aspect_ratio'] = "4:3"
                elif 1.75 <= ratio <= 1.85:
                    result['aspect_ratio'] = "16:9"
                elif 2.2 <= ratio <= 2.4:
                    result['aspect_ratio'] = "21:9"
                else:
                    result['aspect_ratio'] = f"{result['resolution_width']}:{result['resolution_height']}"
            
            # Erweiterte Videometadaten - HDR, Farbtiefe, etc.
            # HDR-Format erkennen
            hdr_format = None
            # Prüfe auf HDR10, HDR10+, Dolby Vision, HLG
            for attr_name in ['hdr_format', 'hdr_format_profile', 'hdr_format_compatibility', 'transfer_characteristics']:
                value = safe_get_attr(video_track, attr_name)
                if value:
                    value_lower = value.lower() if isinstance(value, str) else str(value).lower()
                    if any(hdr_type in value_lower for hdr_type in ['hdr10', 'hdr 10', 'dolby vision', 'dolbyvision', 'hlg']):
                        if 'dolby' in value_lower or 'dovi' in value_lower:
                            hdr_format = "Dolby Vision"
                        elif 'hlg' in value_lower:
                            hdr_format = "HLG"
                        elif 'hdr10+' in value_lower:
                            hdr_format = "HDR10+"
                        elif any(hdr in value_lower for hdr in ['hdr10', 'hdr 10']):
                            hdr_format = "HDR10"
                        break
            
            # Alternativ nach bestimmten Eigenschaften suchen
            if not hdr_format:
                bit_depth = safe_get_attr(video_track, 'bit_depth')
                color_primaries = safe_get_attr(video_track, 'color_primaries')
                if bit_depth and int(bit_depth) > 8 and color_primaries and 'bt.2020' in str(color_primaries).lower():
                    hdr_format = "HDR (unspezifiziert)"
            
            result['hdr_format'] = hdr_format
            
            # Farbtiefe
            color_depth = safe_get_attr(video_track, 'bit_depth')
            if color_depth:
                try:
                    result['color_depth'] = f"{int(color_depth)}bit"
                except (ValueError, TypeError):
                    result['color_depth'] = str(color_depth)
            
            # Farbraum
            for attr_name in ['color_space', 'color_primaries', 'color_range']:
                value = safe_get_attr(video_track, attr_name)
                if value and not result['color_space']:
                    result['color_space'] = value
            
            # Scan-Typ (Progressive/Interlaced)
            scan_type = safe_get_attr(video_track, 'scan_type')
            if scan_type:
                result['scan_type'] = "Progressive" if 'progressive' in str(scan_type).lower() else "Interlaced"
            
            # Encoder-Informationen
            for attr_name in ['encoded_library_name', 'writing_library', 'encoder']:
                value = safe_get_attr(video_track, attr_name)
                if value and not result['encoder']:
                    result['encoder'] = value
        
        # Audio-Track-Informationen (erweitert mit Multi-Track-Support)
        audio_tracks = [track for track in media_info.tracks if track.track_type == 'Audio']
        result['audio_tracks_count'] = len(audio_tracks)
        
        # Sammle alle Audiosprachen
        audio_languages = []
        
        if audio_tracks:
            # Primärer Audio-Track (erster)
            audio_track = audio_tracks[0]
            
            # Grundlegende Audio-Attribute
            audio_mapping = {
                'codec_id': 'audio_codec',
                'format': 'audio_codec',
                'bit_rate': 'audio_bitrate',
                'channel_s': 'audio_channels',
                'channels': 'audio_channels',
                'sampling_rate': 'audio_sample_rate'
            }
            
            for attr_name, target_key in audio_mapping.items():
                value = safe_get_attr(audio_track, attr_name)
                if value and target_key in ['audio_bitrate', 'audio_channels', 'audio_sample_rate']:
                    try:
                        if isinstance(value, str):
                            value = ''.join(c for c in value if c.isdigit() or c == '.')
                        result[target_key] = int(float(value)) if value else None
                    except (ValueError, TypeError):
                        logging.debug(f"Konnte Audio-Attribut {attr_name} nicht konvertieren: {value}")
                elif value:
                    result[target_key] = value
            
            # Audiosprachenerkennung für primären Track
            primary_audio_lang = safe_get_attr(audio_track, 'language')
            if primary_audio_lang:
                result['audio_language'] = primary_audio_lang
                audio_languages.append(primary_audio_lang)
            
            # Erweiterte Audioinformationen für alle Tracks
            for track in audio_tracks:
                lang = safe_get_attr(track, 'language')
                if lang and lang not in audio_languages:
                    audio_languages.append(lang)
            
            if audio_languages:
                result['audio_languages'] = ','.join(set(audio_languages))
        
        # Untertitel-Informationen (erweitert)
        subtitle_tracks = [track for track in media_info.tracks if track.track_type in ['Text', 'Subtitle']]
        result['subtitles_count'] = len(subtitle_tracks)
        
        if subtitle_tracks:
            languages = []
            formats = []
            has_forced = False
            
            for track in subtitle_tracks:
                # Sprache
                lang = safe_get_attr(track, 'language')
                if lang and lang not in languages:
                    languages.append(lang)
                
                # Format
                fmt = safe_get_attr(track, 'format') or safe_get_attr(track, 'codec_id')
                if fmt and fmt not in formats:
                    formats.append(fmt)
                
                # Forced-Untertitel prüfen
                forced = safe_get_attr(track, 'forced')
                if forced and str(forced).lower() in ['yes', 'true', '1']:
                    has_forced = True
            
            if languages:
                result['subtitles_language'] = ','.join(set(languages))
            
            if formats:
                result['subtitles_formats'] = ','.join(set(formats))
            
            result['forced_subtitles'] = has_forced
        
        logging.debug(f"Metadaten erfolgreich extrahiert aus: {file_path}")
        return result
    
    except Exception as e:
        logging.error(f"Fehler beim Extrahieren der Mediendaten aus {file_path}: {e}")
        return None


def safe_get_attr(obj, attr_name):
    """
    Sichere Methode, um ein Attribut aus einem Objekt zu extrahieren.
    Behandelt verschiedene pymediainfo-Versionen und Datentypen.
    """
    if not hasattr(obj, attr_name):
        return None
    
    try:
        value = getattr(obj, attr_name)
        # Behandeln von Listen (neuere pymediainfo-Versionen)
        if isinstance(value, list) and value:
            return value[0]
        return value
    except (AttributeError, IndexError):
        return None


def safe_get_duration(track, attr_name):
    """
    Extrahiert die Dauer aus einem MediaInfo-Track auf sichere Weise.
    Unterstützt verschiedene Formate und Einheiten.
    """
    if not hasattr(track, attr_name):
        return None
    
    try:
        duration_value = getattr(track, attr_name)
        if isinstance(duration_value, list) and duration_value:
            duration_value = duration_value[0]
        
        # Wenn es ein String ist mit 'ms' oder anderen Einheiten
        if isinstance(duration_value, str):
            if 'ms' in duration_value:
                return int(duration_value.replace('ms', '').strip())
            elif 's' in duration_value and not any(unit in duration_value for unit in ['ms', 'minute', 'hour']):
                # Sekunden, aber nicht Millisekunden oder längere Einheiten
                return int(float(duration_value.replace('s', '').strip()) * 1000)
            else:
                # Versuche zu parsen, falls es nur eine Zahl ist
                return int(float(''.join(c for c in duration_value if c.isdigit() or c == '.')) * 1000)
        
        # Wenn es eine Zahl ist
        elif isinstance(duration_value, (int, float)):
            # Wenn die Dauer in Sekunden vorliegt, in ms umrechnen
            if duration_value < 10000:  # Wahrscheinlich Sekunden
                return int(duration_value * 1000)
            else:  # Wahrscheinlich schon Millisekunden
                return int(duration_value)
    except (ValueError, TypeError, AttributeError) as e:
        logging.debug(f"Fehler beim Extrahieren der Dauer aus {attr_name}: {e}")
    
    return None


def get_framerate(video_track):
    """
    Extrahiert die Framerate aus einem Video-Track mit verbesserter Fehlerbehandlung.
    """
    for attr_name in ['frame_rate', 'framerate', 'original_frame_rate']:
        try:
            framerate_value = safe_get_attr(video_track, attr_name)
            if framerate_value:
                if isinstance(framerate_value, str):
                    # Extrahiere nur Zahlen und Dezimalpunkte (z.B. aus "24.000 FPS")
                    framerate_value = ''.join(c for c in framerate_value if c.isdigit() or c == '.')
                return float(framerate_value)
        except (ValueError, TypeError) as e:
            logging.debug(f"Fehler beim Parsen der Framerate: {e}")
    
    return None


def get_creation_time(general_track):
    """
    Extrahiert das Erstellungsdatum mit Unterstützung für verschiedene Formate.
    """
    date_attrs = ['encoded_date', 'recorded_date', 'file_creation_date', 'mastered_date', 'tagged_date']
    
    for attr_name in date_attrs:
        date_str = safe_get_attr(general_track, attr_name)
        if not date_str:
            continue
            
        # Liste bekannter Datumsformate
        date_formats = [
            # Standard ISO und UTC
            '%Y-%m-%d %H:%M:%S',   # 2021-01-30 15:30:45
            '%Y-%m-%dT%H:%M:%S',   # 2021-01-30T15:30:45
            '%Y-%m-%d',            # 2021-01-30
            '%Y%m%d_%H%M%S',       # 20210130_153045
            '%d.%m.%Y %H:%M:%S',   # 30.01.2021 15:30:45 (de_DE)
            '%d/%m/%Y %H:%M:%S',   # 30/01/2021 15:30:45 (fr_FR)
            '%m/%d/%Y %H:%M:%S'    # 01/30/2021 15:30:45 (en_US)
        ]
            
        # Bereinige das Datum, wenn es UTC oder Z enthält
        if isinstance(date_str, str):
            date_str = date_str.replace('UTC ', '').replace('Z', '')
            
        # Versuche alle Formate
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except (ValueError, TypeError):
                continue
                
        # Fallback auf ISO-Format
        try:
            if hasattr(datetime, 'fromisoformat'):  # Python 3.7+
                return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            pass
    
    return None

def update_episodes_metadata(connection, filter_path=None, reprocess_all=False):
    """
    Aktualisiert die Metadaten aller vorhandener Episoden mit den erweiterten Metadatenfeldern.
    
    Args:
        connection: Datenbankverbindung
        filter_path: Optional. Wenn angegeben, werden nur Episoden in diesem Pfad aktualisiert
        reprocess_all: Wenn True, werden auch bereits aktualisierte Episoden erneut verarbeitet
    """
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Abfrage zum Abrufen von Episoden, die aktualisiert werden müssen
        query = "SELECT id, file_path FROM episodes"
        params = []
        
        # Optional nur nicht aktualisierte Episoden abfragen
        if not reprocess_all:
            query += " WHERE container_format IS NULL OR aspect_ratio IS NULL"
        
        # Optional nur Episoden in einem bestimmten Pfad abfragen
        if filter_path:
            if "WHERE" in query:
                query += " AND file_path LIKE %s"
            else:
                query += " WHERE file_path LIKE %s"
            params.append(f"{filter_path}%")
        
        cursor.execute(query, params)
        episodes = cursor.fetchall()
        
        if not episodes:
            logging.info("Keine Episoden gefunden, die aktualisiert werden müssen.")
            return 0
        
        logging.info(f"Aktualisiere Metadaten für {len(episodes)} Episoden...")
        
        # Zähler für erfolgreiche Aktualisierungen
        successful_updates = 0
        
        # Episoden mit Fortschrittsbalken verarbeiten
        for episode in tqdm(episodes, desc="Aktualisiere Metadaten"):
            episode_id = episode['id']
            file_path = episode['file_path']
            
            # Prüfen, ob die Datei existiert
            if not os.path.exists(file_path):
                logging.warning(f"Datei nicht gefunden: {file_path}")
                continue
            
            # Metadaten erneut extrahieren
            media_info = extract_media_info(file_path)
            if not media_info:
                logging.error(f"Konnte keine Metadaten extrahieren aus: {file_path}")
                continue
            
            # SQL für das Update aller Metadatenfelder generieren
            update_query = """
                UPDATE episodes SET
                    duration_ms = %s,
                    video_format = %s,
                    video_codec = %s,
                    video_bitrate = %s,
                    resolution_width = %s,
                    resolution_height = %s,
                    framerate = %s,
                    audio_codec = %s,
                    audio_channels = %s,
                    audio_bitrate = %s,
                    audio_sample_rate = %s,
                    subtitles_language = %s,
                    creation_time = %s,
                    
                    -- Erweiterte Metadaten
                    aspect_ratio = %s,
                    color_depth = %s,
                    hdr_format = %s,
                    color_space = %s,
                    scan_type = %s,
                    encoder = %s,
                    audio_language = %s,
                    audio_tracks_count = %s,
                    audio_languages = %s,
                    subtitles_formats = %s,
                    subtitles_count = %s,
                    forced_subtitles = %s,
                    container_format = %s
                WHERE id = %s
            """
            
            try:
                cursor.execute(update_query, (
                    media_info['duration_ms'],
                    media_info['video_format'],
                    media_info['video_codec'],
                    media_info['video_bitrate'],
                    media_info['resolution_width'],
                    media_info['resolution_height'],
                    media_info['framerate'],
                    media_info['audio_codec'],
                    media_info['audio_channels'],
                    media_info['audio_bitrate'],
                    media_info['audio_sample_rate'],
                    media_info['subtitles_language'],
                    media_info['creation_time'],
                    
                    # Erweiterte Metadaten
                    media_info['aspect_ratio'],
                    media_info['color_depth'],
                    media_info['hdr_format'],
                    media_info['color_space'],
                    media_info['scan_type'],
                    media_info['encoder'],
                    media_info['audio_language'],
                    media_info['audio_tracks_count'],
                    media_info['audio_languages'],
                    media_info['subtitles_formats'],
                    media_info['subtitles_count'],
                    1 if media_info['forced_subtitles'] else 0,  # BOOLEAN für MySQL
                    media_info['container_format'],
                    
                    # WHERE-Klausel
                    episode_id
                ))
                connection.commit()
                
                # Episode wurde aktualisiert
                if cursor.rowcount > 0:
                    successful_updates += 1
                    resolution = f"{media_info['resolution_width']}x{media_info['resolution_height']}" if media_info['resolution_width'] and media_info['resolution_height'] else "unbekannt"
                    if successful_updates % 10 == 0 or successful_updates <= 5:  # Log nur jede 10. Aktualisierung oder die ersten 5
                        logging.info(f"Metadaten aktualisiert für: {os.path.basename(file_path)} | Auflösung: {resolution} | Codec: {media_info['video_codec'] or 'unbekannt'}")
            
            except Error as e:
                logging.error(f"Fehler beim Aktualisieren der Metadaten für {file_path}: {e}")
        
        logging.info(f"Metadatenaktualisierung abgeschlossen. {successful_updates} von {len(episodes)} Episoden erfolgreich aktualisiert.")
        return successful_updates
    
    except Error as e:
        logging.error(f"Datenbankfehler bei der Aktualisierung von Metadaten: {e}")
        return 0


def process_episode(cursor, connection, season_id, episode_path):
    """
    Verarbeitet eine einzelne Episodendatei und fügt sie zur Datenbank hinzu.
    Extrahiert und speichert zusätzlich Videometadaten.
    """
    episode_name = os.path.basename(episode_path)
    episode_number = extract_episode_number(episode_name)
    file_size = os.path.getsize(episode_path)
    _, file_extension = os.path.splitext(episode_path)
    
    # Videometadaten extrahieren
    media_info = extract_media_info(episode_path)
    if not media_info:
        media_info = {'duration_ms': None, 'video_format': None, 'video_codec': None, 'video_bitrate': None,
                      'resolution_width': None, 'resolution_height': None, 'framerate': None,
                      'audio_codec': None, 'audio_channels': None, 'audio_bitrate': None,
                      'audio_sample_rate': None, 'subtitles_language': None, 'creation_time': None,
                      'aspect_ratio': None, 'color_depth': None, 'hdr_format': None, 'color_space': None,
                      'scan_type': None, 'encoder': None, 'audio_language': None, 'audio_tracks_count': 0,
                      'audio_languages': None, 'subtitles_formats': None, 'subtitles_count': 0,
                      'forced_subtitles': False, 'container_format': None}
    
    # Episode zur Datenbank hinzufügen
    try:
        cursor.execute("""
            INSERT IGNORE INTO episodes 
            (season_id, name, episode_number, file_path, file_size, file_extension,
             duration_ms, video_format, video_codec, video_bitrate, resolution_width, resolution_height,
             framerate, audio_codec, audio_channels, audio_bitrate, audio_sample_rate,
             subtitles_language, creation_time, aspect_ratio, color_depth, hdr_format, 
             color_space, scan_type, encoder, audio_language, audio_tracks_count, audio_languages,
             subtitles_formats, subtitles_count, forced_subtitles, container_format) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            season_id, episode_name, episode_number, episode_path, file_size, file_extension,
            media_info['duration_ms'], media_info['video_format'], media_info['video_codec'], 
            media_info['video_bitrate'], media_info['resolution_width'], media_info['resolution_height'],
            media_info['framerate'], media_info['audio_codec'], media_info['audio_channels'], 
            media_info['audio_bitrate'], media_info['audio_sample_rate'], media_info['subtitles_language'],
            media_info['creation_time'], media_info['aspect_ratio'], media_info['color_depth'], 
            media_info['hdr_format'], media_info['color_space'], media_info['scan_type'], 
            media_info['encoder'], media_info['audio_language'], media_info['audio_tracks_count'], 
            media_info['audio_languages'], media_info['subtitles_formats'], media_info['subtitles_count'], 
            1 if media_info['forced_subtitles'] else 0, media_info['container_format']
        ))
        connection.commit()
        
        # Episode wurde hinzugefügt oder existiert bereits
        if cursor.rowcount > 0:
            STATS['episodes'] += 1
            resolution = f"{media_info['resolution_width']}x{media_info['resolution_height']}" if media_info['resolution_width'] and media_info['resolution_height'] else "unbekannt"
            logging.info(f"Episode hinzugefügt: {episode_name} | Auflösung: {resolution} | Codec: {media_info['video_codec'] or 'unbekannt'}")
            return True
    except Error as e:
        logging.error(f"Fehler beim Hinzufügen der Episode {episode_name}: {e}")
    
    return False

def scan_directory_recursive(connection, path, anime_id=None, season_id=None, depth=0):
    """
    Durchsucht das Verzeichnis rekursiv nach Animes, Staffeln und Episoden.
    """
    if depth > MAX_RECURSION_DEPTH:
        logging.warning(f"Maximale Rekursionstiefe ({MAX_RECURSION_DEPTH}) erreicht bei: {path}")
        return
    
    cursor = connection.cursor(dictionary=True)
    path_obj = Path(path)
    
    # Alle Dateien im aktuellen Verzeichnis überprüfen
    for item in path_obj.iterdir():
        if item.is_file() and is_video_file(item.name):
            # Wenn wir uns in einem Staffelverzeichnis befinden
            if season_id:
                process_episode(cursor, connection, season_id, str(item))
            # Wenn wir uns in einem Anime-Verzeichnis befinden, erstelle eine Standard-Staffel
            elif anime_id:
                cursor.execute("""
                    INSERT IGNORE INTO seasons (anime_id, name, season_number, directory_path) 
                    VALUES (%s, %s, %s, %s)
                """, (anime_id, "Staffel 1", 1, str(path_obj)))
                connection.commit()
                
                cursor.execute("SELECT id FROM seasons WHERE anime_id = %s AND name = 'Staffel 1'", (anime_id,))
                season_result = cursor.fetchone()
                
                if season_result:
                    if cursor.rowcount > 0:
                        STATS['seasons'] += 1
                    process_episode(cursor, connection, season_result['id'], str(item))
            continue
        
        # Wenn es sich um ein Verzeichnis handelt
        if item.is_dir():
            dir_name = item.name
            
            # Falls kein Anime erkannt wurde, ist dies möglicherweise ein Anime
            if not anime_id:
                try:
                    cursor.execute("INSERT IGNORE INTO animes (name, directory_path) VALUES (%s, %s)",
                                  (dir_name, str(item)))
                    connection.commit()
                    
                    cursor.execute("SELECT id FROM animes WHERE directory_path = %s", (str(item),))
                    anime_result = cursor.fetchone()
                    
                    if anime_result:
                        if cursor.rowcount > 0:
                            STATS['animes'] += 1
                            logging.info(f"Anime hinzugefügt: {dir_name}")
                        
                        # Rekursiver Aufruf mit dem neuen Anime
                        scan_directory_recursive(connection, str(item), anime_id=anime_result['id'], depth=depth+1)
                except Error as e:
                    logging.error(f"Fehler beim Hinzufügen des Animes {dir_name}: {e}")
            
            # Falls ein Anime erkannt wurde, ist dies möglicherweise eine Staffel
            elif anime_id and not season_id:
                season_number = extract_season_number(dir_name)
                
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO seasons (anime_id, name, season_number, directory_path) 
                        VALUES (%s, %s, %s, %s)
                    """, (anime_id, dir_name, season_number, str(item)))
                    connection.commit()
                    
                    cursor.execute("SELECT id FROM seasons WHERE directory_path = %s", (str(item),))
                    season_result = cursor.fetchone()
                    
                    if season_result:
                        if cursor.rowcount > 0:
                            STATS['seasons'] += 1
                            logging.info(f"Staffel hinzugefügt: {dir_name} (Staffel {season_number if season_number else 'unbekannt'})")
                        
                        # Rekursiver Aufruf mit der neuen Staffel
                        scan_directory_recursive(connection, str(item), anime_id=anime_id, season_id=season_result['id'], depth=depth+1)
                except Error as e:
                    logging.error(f"Fehler beim Hinzufügen der Staffel {dir_name}: {e}")
            
            # Wenn sowohl Anime als auch Staffel erkannt wurden, könnte es eine Unterordnerstruktur sein
            # (z.B. für Extramaterial) - wir durchsuchen es trotzdem
            elif anime_id and season_id:
                scan_directory_recursive(connection, str(item), anime_id=anime_id, season_id=season_id, depth=depth+1)
    
    cursor.close()

def scan_directory(connection):
    """
    Durchsucht das Medienverzeichnis nach Animes, Staffeln und Episoden.
    Verwendet die rekursive Suchfunktion.
    """
    if not os.path.exists(MEDIA_PATH):
        logging.error(f"Fehler: Der Pfad {MEDIA_PATH} existiert nicht.")
        return
    
    logging.info(f"Starte die Archivierung von Anime-Daten aus: {MEDIA_PATH}")
    logging.info(f"Maximale Rekursionstiefe: {MAX_RECURSION_DEPTH}")
    
    # Starte den rekursiven Scan vom Hauptverzeichnis aus
    scan_directory_recursive(connection, MEDIA_PATH)
    
    # Alte Methode als Backup, falls die rekursive Methode Probleme hat
    cursor = connection.cursor(dictionary=True)
    anime_dirs = [d for d in os.listdir(MEDIA_PATH) if os.path.isdir(os.path.join(MEDIA_PATH, d))]
    logging.info(f"Verarbeite {len(anime_dirs)} mögliche Anime-Verzeichnisse auf oberster Ebene...")
    
    for anime_name in tqdm(anime_dirs, desc="Verarbeite Top-Level Animes"):
        anime_path = os.path.join(MEDIA_PATH, anime_name)
        
        # Anime zur Datenbank hinzufügen
        try:
            cursor.execute("INSERT IGNORE INTO animes (name, directory_path) VALUES (%s, %s)",
                          (anime_name, anime_path))
            connection.commit()
            
            cursor.execute("SELECT id FROM animes WHERE directory_path = %s", (anime_path,))
            anime_result = cursor.fetchone()
            
            if anime_result is None:
                logging.warning(f"Konnte Anime {anime_name} nicht in der Datenbank finden nach dem Hinzufügen.")
                continue
            
            anime_id = anime_result['id']
            
            # Anime wurde hinzugefügt oder existiert bereits
            if cursor.rowcount > 0:
                STATS['animes'] += 1
            
            # Suche nach Staffeln
            for item in os.listdir(anime_path):
                season_path = os.path.join(anime_path, item)
                if os.path.isdir(season_path):
                    season_name = item
                    season_number = extract_season_number(season_name)
                    
                    # Staffel zur Datenbank hinzufügen
                    cursor.execute("""
                        INSERT IGNORE INTO seasons (anime_id, name, season_number, directory_path) 
                        VALUES (%s, %s, %s, %s)
                    """, (anime_id, season_name, season_number, season_path))
                    connection.commit()
                    
                    cursor.execute("SELECT id FROM seasons WHERE directory_path = %s", (season_path,))
                    season_result = cursor.fetchone()
                    
                    # Staffel wurde hinzugefügt oder existiert bereits
                    if cursor.rowcount > 0 and season_result:
                        STATS['seasons'] += 1
                        season_id = season_result['id']
                        
                        # Suche nach Episoden
                        for episode_file in os.listdir(season_path):
                            episode_path = os.path.join(season_path, episode_file)
                            if os.path.isfile(episode_path) and is_video_file(episode_file):
                                episode_name = episode_file
                                episode_number = extract_episode_number(episode_file)
                                file_size = os.path.getsize(episode_path)
                                _, file_extension = os.path.splitext(episode_path)
                                
                                # Episode zur Datenbank hinzufügen
                                cursor.execute("""
                                    INSERT IGNORE INTO episodes 
                                    (season_id, name, episode_number, file_path, file_size, file_extension) 
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (season_id, episode_name, episode_number, episode_path, file_size, file_extension))
                                connection.commit()
                                
                                # Episode wurde hinzugefügt oder existiert bereits
                                if cursor.rowcount > 0:
                                    STATS['episodes'] += 1
                            else:
                                STATS['skipped_files'] += 1
                    
                    # Suchen nach Episoden in Anime-Verzeichnis (für Animes mit nur einer Staffel)
                    elif os.path.isfile(season_path) and is_video_file(item):
                        # Erstelle eine Standard-Staffel für Animes ohne Staffelverzeichnis
                        cursor.execute("""
                            INSERT IGNORE INTO seasons (anime_id, name, season_number, directory_path) 
                            VALUES (%s, %s, %s, %s)
                        """, (anime_id, "Staffel 1", 1, anime_path))
                        connection.commit()
                        
                        cursor.execute("SELECT id FROM seasons WHERE anime_id = %s AND name = 'Staffel 1'", (anime_id,))
                        season_id = cursor.fetchone()['id']
                        
                        # Episode zur Datenbank hinzufügen
                        episode_name = item
                        episode_number = extract_episode_number(episode_name)
                        file_size = os.path.getsize(season_path)
                        _, file_extension = os.path.splitext(season_path)
                        
                        cursor.execute("""
                            INSERT IGNORE INTO episodes 
                            (season_id, name, episode_number, file_path, file_size, file_extension) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (season_id, episode_name, episode_number, season_path, file_size, file_extension))
                        connection.commit()
                        
                        if cursor.rowcount > 0:
                            STATS['episodes'] += 1
                            logging.info(f"Episode hinzugefügt: {episode_name}")
                        else:
                            STATS['skipped_files'] += 1
                            logging.info(f"Episode übersprungen: {episode_name}")
                    else:
                        STATS['skipped_files'] += 1
                        logging.info(f"Episode übersprungen: {episode_name}")
                else:
                    STATS['skipped_files'] += 1
                    logging.info(f"Episode übersprungen: {episode_name}")
            else:
                STATS['skipped_files'] += 1
                logging.info(f"Episode übersprungen: {episode_name}")
        except Error as e:
            logging.error(f"Fehler bei der Verarbeitung von '{anime_name}': {e}")
            continue
    
    cursor.close()

def print_statistics(connection):
    """
    Druckt Statistiken zur Datenbank und zum Scan-Vorgang.
    """
    cursor = connection.cursor(dictionary=True)
    
    separator = "="*50
    logging.info(f"\n{separator}\nSTATISTIK\n{separator}")
    
    # Datenbankstatistiken
    cursor.execute("SELECT COUNT(*) as count FROM animes")
    db_animes = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM seasons")
    db_seasons = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM episodes")
    db_episodes = cursor.fetchone()['count']
    
    # Top 10 Animes mit den meisten Episoden
    cursor.execute("""
        SELECT a.name, COUNT(e.id) as episode_count 
        FROM animes a 
        JOIN seasons s ON a.id = s.anime_id 
        JOIN episodes e ON s.id = e.season_id 
        GROUP BY a.id 
        ORDER BY episode_count DESC 
        LIMIT 10
    """)
    top_animes = cursor.fetchall()
    
    # Auflösungsstatistiken
    cursor.execute("""
        SELECT 
            CONCAT(resolution_width, 'x', resolution_height) as resolution,
            COUNT(*) as count 
        FROM episodes 
        WHERE resolution_width IS NOT NULL AND resolution_height IS NOT NULL 
        GROUP BY resolution 
        ORDER BY count DESC
        LIMIT 5
    """)
    resolutions = cursor.fetchall()
    
    # Codec-Statistiken
    cursor.execute("""
        SELECT video_codec, COUNT(*) as count 
        FROM episodes 
        WHERE video_codec IS NOT NULL 
        GROUP BY video_codec 
        ORDER BY count DESC
        LIMIT 5
    """)
    codecs = cursor.fetchall()
    
    logging.info(f"\nIn der Datenbank gespeichert:")
    logging.info(f"- Animes: {db_animes}")
    logging.info(f"- Staffeln: {db_seasons}")
    logging.info(f"- Episoden: {db_episodes}")
    
    # Scan-Statistiken
    logging.info(f"\nBei diesem Scan verarbeitet:")
    logging.info(f"- Animes: {STATS['animes']} {'(neu)' if STATS['animes'] > 0 else '(keine neuen)'}")
    logging.info(f"- Staffeln: {STATS['seasons']} {'(neu)' if STATS['seasons'] > 0 else '(keine neuen)'}")
    logging.info(f"- Episoden: {STATS['episodes']} {'(neu)' if STATS['episodes'] > 0 else '(keine neuen)'}")
    logging.info(f"- Übersprungene Dateien: {STATS['skipped_files']}")
    
    if top_animes:
        logging.info(f"\nTop 10 Animes mit den meisten Episoden:")
        for i, anime in enumerate(top_animes, 1):
            logging.info(f"{i}. {anime['name']} - {anime['episode_count']} Episoden")
    
    if resolutions:
        logging.info(f"\nHäufigste Videoauflösungen:")
        for i, res in enumerate(resolutions, 1):
            logging.info(f"{i}. {res['resolution']} - {res['count']} Episoden")
    
    if codecs:
        logging.info(f"\nHäufigste Videocodecs:")
        for i, codec in enumerate(codecs, 1):
            logging.info(f"{i}. {codec['video_codec']} - {codec['count']} Episoden")
    
    cursor.close()

def main():
    """
    Hauptfunktion zum Ausführen des Programms.
    """
    start_time = datetime.now()
    
    logging.info("=== Anime-Archiver mit Videometadaten-Extraktion ===")
    logging.info(f"Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Medienpfad: {MEDIA_PATH}")
    logging.info(f"Datenbankserver: {DB_HOST}")
    
    try:
        # MediaInfo-Bibliothek prüfen
        try:
            # Neuere Versionen haben keine version() Methode mehr
            # Einfach ein leeres Video parsen, um zu sehen, ob es funktioniert
            test_info = MediaInfo.parse(os.path.join(os.path.dirname(__file__), __file__))
            logging.info(f"MediaInfo erfolgreich initialisiert. Extrahiere Videometadaten...")
        except Exception as e:
            logging.warning(f"MediaInfo nicht korrekt installiert oder kann nicht initialisiert werden: {e}")
            logging.warning("Videometadaten können nicht vollständig extrahiert werden.")
        
        connection = setup_database()
        scan_directory(connection)
        logging.info("Aktualisiere Videometadaten für vorhandene Episoden...")
        update_episodes_metadata(connection)
        print_statistics(connection)
        connection.close()
        
        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"\nArchivierung abgeschlossen. Dauer: {duration}")
        
    except Error as e:
        logging.error(f"Fehler bei der Datenbankverbindung: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.warning("Prozess durch Benutzer abgebrochen")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unerwarteter Fehler: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
