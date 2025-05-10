#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hauptanwendung für das Anime-Loads Dashboard.
Stellt eine Weboberfläche zur Verfügung, um die Anime-Sammlung zu durchsuchen,
zu analysieren und zu verwalten.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash
from flask_apscheduler import APScheduler
import sys

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Projekt-Verzeichnis
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(PROJECT_DIR)

# Füge das übergeordnete Verzeichnis zum Pfad hinzu, um auf anime_archiver.py zuzugreifen
sys.path.insert(0, PARENT_DIR)

# Konfiguration importieren
from config import (
    SECRET_KEY, DEBUG, LOG_DIR, LOG_LEVEL, 
    UPDATE_INTERVAL_HOURS, UPDATE_TIME, CACHE_DIR,
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
)

# Initialisiere die Flask-App
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.debug = DEBUG

# Datenbankeinstellungen
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# Stelle sicher, dass die Verzeichnisse existieren
for directory in [LOG_DIR, CACHE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Logging konfigurieren
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, 'dashboard.log')
handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(LOG_LEVEL)
app.logger.addHandler(handler)
app.logger.setLevel(LOG_LEVEL)
app.logger.info('Anime-Loads Dashboard startet...')

# Datenbankmodelle importieren und initialisieren
from models import db
db.init_app(app)

# Zeitplaner für regelmäßige Aufgaben initialisieren
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Anime-Archiver importieren
from anime_archiver import setup_database, update_episodes_metadata

# API Blueprint einbinden
from api import api
app.register_blueprint(api)

# Scheduler-Jobs konfigurieren
@scheduler.task('cron', id='update_metadata', hour=UPDATE_TIME.split(':')[0], minute=UPDATE_TIME.split(':')[1])
def scheduled_metadata_update():
    """Task, der regelmäßig die Metadaten aktualisiert."""
    app.logger.info('Starte geplante Metadatenaktualisierung...')
    
    try:
        connection = db.engine.raw_connection()
        update_episodes_metadata(connection)
        connection.close()
        app.logger.info('Metadatenaktualisierung abgeschlossen.')
    except Exception as e:
        app.logger.error(f'Fehler bei der Metadatenaktualisierung: {e}')

# Eigene HTML-Export-Funktion, da die original-Funktion nicht verfügbar ist
def export_metadata_to_html(connection, output_file):
    """Exportiert die Metadaten aus der Datenbank als HTML-Datei."""
    cursor = connection.cursor(dictionary=True)
    
    # Animes abrufen
    cursor.execute("SELECT * FROM animes ORDER BY name")
    animes = cursor.fetchall()
    
    # HTML-Kopf erstellen
    html_content = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Anime-Metadaten</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .anime {{ margin-bottom: 30px; border-bottom: 1px solid #ccc; padding-bottom: 20px; }}
            .season {{ margin-left: 20px; margin-bottom: 20px; }}
            .episode {{ margin-left: 40px; margin-bottom: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
            .metadata {{ font-size: 0.9em; color: #666; }}
            .resolution {{ font-weight: bold; color: #3498db; }}
            .codec {{ font-weight: bold; color: #2ecc71; }}
        </style>
    </head>
    <body>
        <h1>Anime-Metadaten Export</h1>
        <p>Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    """
    
    # Anime-Daten hinzufügen
    for anime in animes:
        html_content += f"""<div class='anime'>
            <h2>{anime['name']}</h2>
            <p class='metadata'>Pfad: {anime['directory_path']}</p>
        """
        
        # Staffeln abrufen
        cursor.execute("SELECT * FROM seasons WHERE anime_id = %s ORDER BY season_number", (anime['id'],))
        seasons = cursor.fetchall()
        
        for season in seasons:
            html_content += f"""<div class='season'>
                <h3>{season['name']}</h3>
                <p class='metadata'>Pfad: {season['directory_path']}</p>
            """
            
            # Episoden abrufen
            cursor.execute("SELECT * FROM episodes WHERE season_id = %s ORDER BY episode_number", (season['id'],))
            episodes = cursor.fetchall()
            
            for episode in episodes:
                resolution = f"{episode['resolution_width']}x{episode['resolution_height']}" if episode['resolution_width'] and episode['resolution_height'] else "Unbekannt"
                duration = f"{int((episode['duration_ms'] or 0) / 1000 / 60)} Min" if episode['duration_ms'] else "Unbekannt"
                
                html_content += f"""<div class='episode'>
                    <h4>{episode['name']}</h4>
                    <p class='metadata'>
                        <span class='resolution'>{resolution}</span> | 
                        <span class='codec'>{episode['video_codec'] or 'Unbekannt'}</span> | 
                        Dauer: {duration} | 
                        Größe: {(episode['file_size'] or 0) / (1024*1024):.2f} MB
                    </p>
                    <p class='metadata'>Datei: {episode['file_path']}</p>
                </div>
                """
            
            html_content += "</div>\n"
        
        html_content += "</div>\n"
    
    # HTML abschließen
    html_content += """    
    </body>
    </html>
    """
    
    # In Datei schreiben
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    cursor.close()
    return output_file

@scheduler.task('interval', id='export_html', hours=12)
def scheduled_html_export():
    """Task, der regelmäßig eine HTML-Exportdatei erstellt."""
    app.logger.info('Exportiere Metadaten als HTML...')
    
    try:
        connection = db.engine.raw_connection()
        export_file = os.path.join(app.static_folder, 'exports', 'anime_metadaten.html')
        
        # Stelle sicher, dass das Export-Verzeichnis existiert
        export_dir = os.path.dirname(export_file)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            
        export_metadata_to_html(connection, export_file)
        connection.close()
        app.logger.info(f'HTML-Export abgeschlossen: {export_file}')
    except Exception as e:
        app.logger.error(f'Fehler beim HTML-Export: {e}')

# Routen definieren
@app.route('/')
def index():
    """Zeigt die Startseite des Dashboards an."""
    return render_template('index.html')

@app.route('/anime')
def anime_list():
    """Zeigt eine Liste aller Animes an."""
    from models import Anime
    animes = Anime.query.order_by(Anime.name).all()
    return render_template('anime_list.html', animes=animes)

@app.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    """Zeigt detaillierte Informationen zu einem Anime an."""
    from models import Anime, Season
    anime = Anime.query.get_or_404(anime_id)
    seasons = Season.query.filter_by(anime_id=anime_id).order_by(Season.season_number).all()
    return render_template('anime_detail.html', anime=anime, seasons=seasons)

@app.route('/season/<int:season_id>')
def season_detail(season_id):
    """Zeigt detaillierte Informationen zu einer Staffel an."""
    from models import Season, Episode, Anime
    season = Season.query.get_or_404(season_id)
    anime = Anime.query.get(season.anime_id)
    episodes = Episode.query.filter_by(season_id=season_id).order_by(Episode.episode_number).all()
    return render_template('season_detail.html', season=season, anime=anime, episodes=episodes)

@app.route('/episode/<int:episode_id>')
def episode_detail(episode_id):
    """Zeigt detaillierte Informationen zu einer Episode an."""
    from models import Episode, Season, Anime
    episode = Episode.query.get_or_404(episode_id)
    season = Season.query.get(episode.season_id)
    anime = Anime.query.get(season.anime_id) if season else None
    return render_template('episode_detail.html', episode=episode, season=season, anime=anime)

@app.route('/search')
def search():
    """Zeigt die Suchseite mit Ergebnissen an."""
    query = request.args.get('q', '')
    return render_template('search.html', query=query)

@app.route('/filter')
def filter_page():
    """Zeigt die Filterseite an."""
    from models import Anime
    animes = Anime.query.order_by(Anime.name).all()
    return render_template('filter.html', animes=animes)

@app.route('/stats')
def stats():
    """Zeigt die Statistikseite an."""
    return render_template('stats.html')

@app.route('/export')
def export():
    """Zeigt die Exportseite an."""
    return render_template('export.html')

@app.route('/perform_export', methods=['POST'])
def perform_export():
    """Führt einen Export der Datenbank aus."""
    export_type = request.form.get('export_type', 'html')
    try:
        connection = db.engine.raw_connection()
        
        if export_type == 'html':
            export_file = os.path.join(app.static_folder, 'exports', f'anime_metadaten_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
            export_dir = os.path.dirname(export_file)
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            export_metadata_to_html(connection, export_file)
            flash(f'HTML-Export erfolgreich erstellt: {os.path.basename(export_file)}', 'success')
            return redirect(url_for('download_export', filename=os.path.basename(export_file)))
        
    except Exception as e:
        app.logger.error(f'Fehler beim Export: {e}')
        flash(f'Fehler beim Export: {e}', 'error')
    finally:
        connection.close()
    
    return redirect(url_for('export'))

@app.route('/downloads/<path:filename>')
def download_export(filename):
    """Ermöglicht das Herunterladen von exportierten Dateien."""
    return send_from_directory(os.path.join(app.static_folder, 'exports'), filename, as_attachment=True)

@app.route('/update', methods=['GET', 'POST'])
def update_metadata():
    """Manuelle Aktualisierung der Metadaten."""
    if request.method == 'POST':
        try:
            connection = db.engine.raw_connection()
            update_episodes_metadata(connection, reprocess_all=True)
            connection.close()
            flash('Metadatenaktualisierung erfolgreich abgeschlossen.', 'success')
        except Exception as e:
            app.logger.error(f'Fehler bei der manuellen Metadatenaktualisierung: {e}')
            flash(f'Fehler bei der Metadatenaktualisierung: {e}', 'error')
        return redirect(url_for('index'))
    
    return render_template('update.html')

@app.errorhandler(404)
def not_found_error(error):
    """Behandelt 404-Fehler."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Behandelt 500-Fehler."""
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
