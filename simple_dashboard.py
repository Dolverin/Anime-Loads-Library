#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfaches Dashboard für die Anime-Loads Library ohne komplexe Abhängigkeiten.
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from dotenv import load_dotenv
import mysql.connector

# Umgebungsvariablen laden
load_dotenv()

# Konfigurationsvariablen
DB_HOST = os.getenv('DB_HOST', '192.168.178.9')
DB_USER = os.getenv('DB_USER', 'aniworld')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aniworld')
DB_NAME = os.getenv('DB_NAME', 'animeloads')
MEDIA_PATH = os.getenv('MEDIA_PATH', '/mnt/mediathek')

# Flask-App initialisieren
app = Flask(__name__, 
            template_folder='dashboard/templates',
            static_folder='dashboard/static')
app.secret_key = 'ein_sicherer_geheimer_schluessel'
app.debug = True

# Logging konfigurieren
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format,
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Datenbank-Verbindung herstellen
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

# Hilfsfunktionen
def execute_query(query, params=None, fetch_mode="all"):
    """Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_mode == "one":
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        
        return result
    finally:
        cursor.close()
        connection.close()

# Statistik-Funktionen
def calculate_stats():
    """Berechnet erweiterte Statistiken für das Dashboard mit detaillierten Metadaten."""
    stats = {}
    
    # Basis-Statistiken
    stats['animes_count'] = execute_query("SELECT COUNT(*) as count FROM animes", fetch_mode="one")['count']
    stats['seasons_count'] = execute_query("SELECT COUNT(*) as count FROM seasons", fetch_mode="one")['count']
    stats['episodes_count'] = execute_query("SELECT COUNT(*) as count FROM episodes", fetch_mode="one")['count']
    
    # Speichernutzung
    total_size_result = execute_query("SELECT SUM(file_size) as total_size FROM episodes", fetch_mode="one")
    stats['total_size_bytes'] = total_size_result['total_size'] if total_size_result and total_size_result['total_size'] else 0
    
    # Formatierte Größe
    if stats['total_size_bytes'] < 1024**3:  # Kleiner als 1 GB
        stats['total_size_formatted'] = f"{stats['total_size_bytes'] / 1024**2:.2f} MB"
    elif stats['total_size_bytes'] < 1024**4:  # Kleiner als 1 TB
        stats['total_size_formatted'] = f"{stats['total_size_bytes'] / 1024**3:.2f} GB"
    else:
        stats['total_size_formatted'] = f"{stats['total_size_bytes'] / 1024**4:.2f} TB"
    
    # Gesamtdauer
    total_duration_result = execute_query("SELECT SUM(duration_ms) as total_duration FROM episodes", fetch_mode="one")
    total_duration_ms = total_duration_result['total_duration'] if total_duration_result and total_duration_result['total_duration'] else 0
    
    # Formatierte Dauer
    total_seconds = total_duration_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    stats['total_duration_formatted'] = f"{hours} Stunden, {minutes} Minuten"
    
    # Auflösungsverteilung für Pie-Chart und Bar-Chart
    resolution_data = execute_query("""
        SELECT 
            CASE 
                WHEN resolution_width >= 3840 THEN '4K' 
                WHEN resolution_width >= 1920 THEN 'Full HD' 
                WHEN resolution_width >= 1280 THEN 'HD'
                WHEN resolution_width >= 720 THEN 'HD Ready'
                WHEN resolution_width > 0 THEN 'SD'
                ELSE 'Unbekannt'
            END as resolution_category,
            COUNT(*) as count
        FROM episodes
        WHERE resolution_width IS NOT NULL
        GROUP BY resolution_category
        ORDER BY 
            CASE 
                WHEN resolution_category = '4K' THEN 1
                WHEN resolution_category = 'Full HD' THEN 2
                WHEN resolution_category = 'HD' THEN 3
                WHEN resolution_category = 'HD Ready' THEN 4
                WHEN resolution_category = 'SD' THEN 5
                ELSE 6
            END
    """)
    
    # Formatieren als Dictionary für den Chart
    stats['resolution_distribution'] = {}
    for row in resolution_data:
        stats['resolution_distribution'][row['resolution_category']] = row['count']
    
    # Speicherverbrauch nach Auflösung
    storage_by_resolution = execute_query("""
        SELECT 
            CASE 
                WHEN resolution_width >= 3840 THEN '4K' 
                WHEN resolution_width >= 1920 THEN 'Full HD' 
                WHEN resolution_width >= 1280 THEN 'HD'
                WHEN resolution_width >= 720 THEN 'HD Ready'
                WHEN resolution_width > 0 THEN 'SD'
                ELSE 'Unbekannt'
            END as resolution_category,
            SUM(file_size) as total_size
        FROM episodes
        WHERE resolution_width IS NOT NULL AND file_size IS NOT NULL
        GROUP BY resolution_category
        ORDER BY 
            CASE 
                WHEN resolution_category = '4K' THEN 1
                WHEN resolution_category = 'Full HD' THEN 2
                WHEN resolution_category = 'HD' THEN 3
                WHEN resolution_category = 'HD Ready' THEN 4
                WHEN resolution_category = 'SD' THEN 5
                ELSE 6
            END
    """)
    
    # Formatieren als Dictionary für den Chart
    stats['storage_by_resolution'] = {}
    for row in storage_by_resolution:
        stats['storage_by_resolution'][row['resolution_category']] = row['total_size']
    
    # Codec-Verteilung - normalisiert für bessere Lesbarkeit
    codec_data = execute_query("""
        SELECT 
            CASE
                WHEN video_codec LIKE '%HEVC%' OR video_codec LIKE '%x265%' THEN 'HEVC'
                WHEN video_codec LIKE '%AVC%' OR video_codec LIKE '%x264%' THEN 'AVC'
                WHEN video_codec LIKE '%AV1%' THEN 'AV1'
                WHEN video_codec LIKE '%VP9%' THEN 'VP9'
                WHEN video_codec LIKE '%MPEG%' THEN 'MPEG'
                ELSE IFNULL(video_codec, 'Unbekannt')
            END as codec_category,
            COUNT(*) as count
        FROM episodes
        WHERE video_codec IS NOT NULL
        GROUP BY codec_category
        ORDER BY count DESC
        LIMIT 10
    """)
    
    # Formatieren als Dictionary für den Chart
    stats['codec_distribution'] = {}
    for row in codec_data:
        stats['codec_distribution'][row['codec_category']] = row['count']
    
    # HDR-Verteilung
    hdr_data = execute_query("""
        SELECT 
            SUM(CASE WHEN hdr_format IS NOT NULL AND hdr_format != '' THEN 1 ELSE 0 END) as hdr,
            SUM(CASE WHEN hdr_format IS NULL OR hdr_format = '' THEN 1 ELSE 0 END) as non_hdr
        FROM episodes
    """, fetch_mode="one")
    
    stats['hdr_distribution'] = {
        'hdr': hdr_data['hdr'] if hdr_data and 'hdr' in hdr_data else 0,
        'non_hdr': hdr_data['non_hdr'] if hdr_data and 'non_hdr' in hdr_data else 0
    }
    
    # HDR-Typen-Verteilung
    hdr_types = execute_query("""
        SELECT 
            IFNULL(hdr_format, 'Kein HDR') as hdr_type,
            COUNT(*) as count
        FROM episodes
        WHERE hdr_format IS NOT NULL AND hdr_format != ''
        GROUP BY hdr_type
        ORDER BY count DESC
    """)
    
    stats['hdr_types'] = {}
    for row in hdr_types:
        stats['hdr_types'][row['hdr_type']] = row['count']
    
    # Top Animes nach Episodenzahl
    stats['top_animes'] = execute_query("""
        SELECT 
            a.id, a.name, 
            COUNT(e.id) as episode_count
        FROM animes a
        JOIN seasons s ON a.id = s.anime_id
        JOIN episodes e ON s.id = e.season_id
        GROUP BY a.id, a.name
        ORDER BY episode_count DESC
        LIMIT 10
    """)
    
    # Episoden nach Audio-Sprachen
    audio_languages = execute_query("""
        SELECT 
            IFNULL(audio_language, 'Unbekannt') as language,
            COUNT(*) as count
        FROM episodes
        WHERE audio_language IS NOT NULL AND audio_language != ''
        GROUP BY language
        ORDER BY count DESC
        LIMIT 5
    """)
    
    stats['audio_languages'] = {}
    for row in audio_languages:
        stats['audio_languages'][row['language']] = row['count']
    
    return stats

# API-Endpunkte
@app.route('/api/stats')
def api_stats():
    """API-Endpunkt für Dashboard-Statistiken."""
    return jsonify(calculate_stats())

@app.route('/api/search')
def api_search():
    """API-Endpunkt für die Suche."""
    search_term = request.args.get('q', '')
    search_type = request.args.get('type', 'all').lower()
    limit = int(request.args.get('limit', 100))
    
    # Leere Suche verhindern
    if not search_term or len(search_term) < 2:
        return jsonify({
            'error': 'Suchbegriff muss mindestens 2 Zeichen enthalten.'
        }), 400
    
    results = {
        'animes': [],
        'seasons': [],
        'episodes': []
    }
    
    # Prozentzeichen hinzufügen für LIKE-Operator
    search_pattern = f"%{search_term}%"
    
    # Animes suchen
    if search_type in ('all', 'anime'):
        animes = execute_query("""
            SELECT id, name, directory_path 
            FROM animes 
            WHERE name LIKE %s OR directory_path LIKE %s
            LIMIT %s
        """, (search_pattern, search_pattern, limit))
        
        results['animes'] = animes
    
    # Staffeln suchen
    if search_type in ('all', 'season'):
        seasons = execute_query("""
            SELECT id, anime_id, name, directory_path, season_number
            FROM seasons 
            WHERE name LIKE %s OR directory_path LIKE %s
            LIMIT %s
        """, (search_pattern, search_pattern, limit))
        
        results['seasons'] = seasons
    
    # Episoden suchen
    if search_type in ('all', 'episode'):
        episodes = execute_query("""
            SELECT id, season_id, name, file_path, file_size, 
                   resolution_width, resolution_height, video_codec
            FROM episodes 
            WHERE name LIKE %s OR file_path LIKE %s
            LIMIT %s
        """, (search_pattern, search_pattern, limit))
        
        results['episodes'] = episodes
    
    return jsonify(results)

@app.route('/api/filter')
def api_filter():
    """API-Endpunkt zum Filtern von Episoden."""
    # Parameter auslesen
    anime_id = request.args.get('anime_id')
    season_id = request.args.get('season_id')
    resolution_min = request.args.get('resolution_min')
    codec = request.args.get('codec')
    hdr = request.args.get('hdr')
    limit = int(request.args.get('limit', 100))
    
    # Query und Parameter vorbereiten
    query = """
        SELECT e.*, s.name as season_name, a.name as anime_name
        FROM episodes e
        JOIN seasons s ON e.season_id = s.id
        JOIN animes a ON s.anime_id = a.id
        WHERE 1=1
    """
    params = []
    
    # Filter hinzufügen
    if season_id:
        query += " AND e.season_id = %s"
        params.append(int(season_id))
    elif anime_id:
        query += " AND s.anime_id = %s"
        params.append(int(anime_id))
    
    if resolution_min:
        query += " AND e.resolution_height >= %s"
        params.append(int(resolution_min))
    
    if codec:
        query += " AND e.video_codec LIKE %s"
        params.append(f"%{codec}%")
    
    if hdr and hdr.lower() in ('true', '1', 'yes'):
        query += " AND e.hdr_format IS NOT NULL AND e.hdr_format != ''"
    
    # Limit hinzufügen
    query += " LIMIT %s"
    params.append(limit)
    
    # Abfrage ausführen
    episodes = execute_query(query, tuple(params))
    
    return jsonify({
        'count': len(episodes),
        'episodes': episodes
    })

# Routen für die Weboberfläche
# Jinja-Environment anpassen, um simple_base.html zu verwenden
@app.context_processor
def inject_simple_base():
    return {'simple_base': True}

# Benutzerdefinierter Template-Loader
class PrefixedLoader:
    def __init__(self, app):
        self.app = app
        self.original_loader = app.jinja_loader
    
    def get_source(self, environment, template):
        if template == 'base.html' and request.endpoint in ['index', 'anime_list', 'search', 'filter_page', 'stats', 'anime_detail', 'season_detail', 'episode_detail']:
            try:
                return self.original_loader.get_source(environment, 'simple_base.html')
            except Exception:
                pass
        return self.original_loader.get_source(environment, template)

app.jinja_loader = PrefixedLoader(app)

@app.route('/')
def index():
    """Zeigt die Startseite des Dashboards an."""
    return render_template('simple_index.html')

@app.route('/anime')
def anime_list():
    """Zeigt eine Liste aller Animes an."""
    animes = execute_query("SELECT * FROM animes ORDER BY name")
    
    # Für jedes Anime die Anzahl der Staffeln und Episoden berechnen
    for anime in animes:
        # Anzahl der Staffeln
        season_count = execute_query(
            "SELECT COUNT(*) as count FROM seasons WHERE anime_id = %s",
            (anime['id'],),
            "one"
        )['count']
        anime['season_count'] = season_count
        
        # Anzahl der Episoden (über alle Staffeln)
        episode_count = execute_query(
            """SELECT COUNT(*) as count FROM episodes e 
               JOIN seasons s ON e.season_id = s.id 
               WHERE s.anime_id = %s""",
            (anime['id'],),
            "one"
        )['count']
        anime['episode_count'] = episode_count
    
    return render_template('anime_list.html', animes=animes)

@app.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    """Zeigt detaillierte Informationen zu einem Anime an."""
    anime = execute_query("SELECT * FROM animes WHERE id = %s", (anime_id,), "one")
    if not anime:
        return render_template('errors/404.html'), 404
    
    # Staffeln abrufen
    seasons = execute_query(
        "SELECT * FROM seasons WHERE anime_id = %s ORDER BY season_number", 
        (anime_id,)
    )
    
    # Episodenzahlen für jede Staffel hinzufügen
    total_episodes = 0
    for season in seasons:
        episode_count = execute_query(
            "SELECT COUNT(*) as count FROM episodes WHERE season_id = %s",
            (season['id'],),
            "one"
        )['count']
        season['episode_count'] = episode_count
        total_episodes += episode_count
        
    return render_template('anime_detail.html', anime=anime, seasons=seasons, total_episodes=total_episodes)

@app.route('/season/<int:season_id>')
def season_detail(season_id):
    """Zeigt detaillierte Informationen zu einer Staffel an."""
    season = execute_query("SELECT * FROM seasons WHERE id = %s", (season_id,), "one")
    if not season:
        return render_template('errors/404.html'), 404
    
    anime = execute_query("SELECT * FROM animes WHERE id = %s", (season['anime_id'],), "one")
    episodes = execute_query(
        "SELECT * FROM episodes WHERE season_id = %s ORDER BY episode_number", 
        (season_id,)
    )
    return render_template('season_detail.html', season=season, anime=anime, episodes=episodes)

@app.route('/episode/<int:episode_id>')
def episode_detail(episode_id):
    """Zeigt detaillierte Informationen zu einer Episode an."""
    episode = execute_query("SELECT * FROM episodes WHERE id = %s", (episode_id,), "one")
    if not episode:
        return render_template('errors/404.html'), 404
    
    season = execute_query("SELECT * FROM seasons WHERE id = %s", (episode['season_id'],), "one")
    anime = None
    if season:
        anime = execute_query("SELECT * FROM animes WHERE id = %s", (season['anime_id'],), "one")
    
    return render_template('episode_detail.html', episode=episode, season=season, anime=anime)

@app.route('/search')
def search():
    """Zeigt die Suchseite mit Ergebnissen an."""
    query = request.args.get('q', '')
    return render_template('simple_search.html', query=query)

@app.route('/filter')
def filter_page():
    """Zeigt die Filterseite an."""
    animes = execute_query("SELECT * FROM animes ORDER BY name")
    return render_template('filter.html', animes=animes)

@app.route('/stats')
def stats():
    """Zeigt die Statistikseite an."""
    return render_template('stats.html')

@app.errorhandler(404)
def not_found_error(error):
    """Behandelt 404-Fehler."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Behandelt 500-Fehler."""
    return render_template('errors/500.html'), 500

# Kontext-Prozessor für Template-Variablen
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

if __name__ == '__main__':
    import argparse
    
    # Befehlszeilenargumente parsen
    parser = argparse.ArgumentParser(description='Anime-Loads Dashboard starten')
    parser.add_argument('--port', type=int, default=5002, help='Port, auf dem das Dashboard laufen soll (Standard: 5002)')
    args = parser.parse_args()
    
    try:
        # Test-Verbindung zur Datenbank
        connection = get_db_connection()
        connection.close()
        logger.info("Datenbank-Verbindung erfolgreich")
        
        # Server starten
        port = args.port
        logger.info(f"Starte Anime-Loads Dashboard auf Port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Fehler beim Starten des Dashboards: {e}")
        sys.exit(1)
