#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistikfunktionen für das Anime-Loads Dashboard.
Bietet Funktionen zur Berechnung und Visualisierung von Statistiken
über die Anime-Sammlung.
"""

import os
import logging
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from io import BytesIO
import base64
from datetime import datetime, timedelta
import sys

# Füge das übergeordnete Verzeichnis zum Pfad hinzu, um Zugriff auf die Config zu haben
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import CACHE_DIR, STATS_CACHE_TIMEOUT

# Stelle sicher, dass das Cache-Verzeichnis existiert
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def calculate_stats(connection):
    """
    Berechnet allgemeine Statistiken über die Anime-Sammlung.
    
    Args:
        connection: Datenbankverbindung oder SQLAlchemy-Session
    
    Returns:
        dictionary mit verschiedenen Statistiken
    """
    from .db import execute_query
    
    # Cache-Datei prüfen
    cache_file = os.path.join(CACHE_DIR, "general_stats.json")
    if os.path.exists(cache_file):
        try:
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mod_time < timedelta(seconds=STATS_CACHE_TIMEOUT):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    logging.debug(f"Lade Statistiken aus Cache: {cache_file}")
                    return json.load(f)
        except Exception as e:
            logging.warning(f"Fehler beim Laden des Statistik-Cache: {e}")
    
    # Statistiken berechnen, wenn kein gültiger Cache vorhanden ist
    stats = {}
    
    # Basisstatistiken (Anzahl Animes, Staffeln, Episoden)
    stats['animes_count'] = execute_query("SELECT COUNT(*) as count FROM animes", fetch_mode="one", connection=connection)['count']
    stats['seasons_count'] = execute_query("SELECT COUNT(*) as count FROM seasons", fetch_mode="one", connection=connection)['count']
    stats['episodes_count'] = execute_query("SELECT COUNT(*) as count FROM episodes", fetch_mode="one", connection=connection)['count']
    
    # Dateigröße und Dauer
    total_size_query = "SELECT SUM(file_size) as total_size FROM episodes"
    total_size_result = execute_query(total_size_query, fetch_mode="one", connection=connection)
    stats['total_size_bytes'] = total_size_result['total_size'] if total_size_result and total_size_result['total_size'] else 0
    
    # Formatierte Größe
    if stats['total_size_bytes'] < 1024**3:  # Kleiner als 1 GB
        stats['total_size_formatted'] = f"{stats['total_size_bytes'] / 1024**2:.2f} MB"
    elif stats['total_size_bytes'] < 1024**4:  # Kleiner als 1 TB
        stats['total_size_formatted'] = f"{stats['total_size_bytes'] / 1024**3:.2f} GB"
    else:
        stats['total_size_formatted'] = f"{stats['total_size_bytes'] / 1024**4:.2f} TB"
    
    # Gesamtdauer
    total_duration_query = "SELECT SUM(duration_ms) as total_duration FROM episodes"
    total_duration_result = execute_query(total_duration_query, fetch_mode="one", connection=connection)
    total_duration_ms = total_duration_result['total_duration'] if total_duration_result and total_duration_result['total_duration'] else 0
    
    # Formatierte Dauer
    total_seconds = total_duration_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    stats['total_duration_formatted'] = f"{hours} Stunden, {minutes} Minuten"
    
    # HDR-Inhalte
    hdr_query = "SELECT COUNT(*) as count FROM episodes WHERE hdr_format IS NOT NULL AND hdr_format != ''"
    stats['hdr_count'] = execute_query(hdr_query, fetch_mode="one", connection=connection)['count']
    stats['hdr_percentage'] = (stats['hdr_count'] / stats['episodes_count'] * 100) if stats['episodes_count'] > 0 else 0
    
    # 4K-Inhalte
    uhd_query = "SELECT COUNT(*) as count FROM episodes WHERE resolution_width >= 3840"
    stats['uhd_count'] = execute_query(uhd_query, fetch_mode="one", connection=connection)['count']
    stats['uhd_percentage'] = (stats['uhd_count'] / stats['episodes_count'] * 100) if stats['episodes_count'] > 0 else 0
    
    # Verteilung nach Auflösung
    resolution_query = """
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
        GROUP BY resolution_category
        ORDER BY 
            CASE resolution_category
                WHEN '4K' THEN 1
                WHEN 'Full HD' THEN 2
                WHEN 'HD' THEN 3
                WHEN 'HD Ready' THEN 4
                WHEN 'SD' THEN 5
                ELSE 6
            END
    """
    stats['resolution_distribution'] = execute_query(resolution_query, connection=connection)
    
    # Verteilung nach Videocodec
    codec_query = """
        SELECT 
            IFNULL(video_codec, 'Unbekannt') as codec,
            COUNT(*) as count
        FROM episodes
        GROUP BY codec
        ORDER BY count DESC
        LIMIT 10
    """
    stats['codec_distribution'] = execute_query(codec_query, connection=connection)
    
    # Verteilung nach Containerformat
    container_query = """
        SELECT 
            IFNULL(container_format, 'Unbekannt') as container,
            COUNT(*) as count
        FROM episodes
        GROUP BY container
        ORDER BY count DESC
    """
    stats['container_distribution'] = execute_query(container_query, connection=connection)
    
    # Top 10 Animes nach Anzahl Episoden
    top_animes_query = """
        SELECT 
            a.id, a.name, 
            COUNT(e.id) as episode_count
        FROM animes a
        JOIN seasons s ON a.id = s.anime_id
        JOIN episodes e ON s.id = e.season_id
        GROUP BY a.id, a.name
        ORDER BY episode_count DESC
        LIMIT 10
    """
    stats['top_animes'] = execute_query(top_animes_query, connection=connection)
    
    # Top 10 größte Animes nach Dateigröße
    size_animes_query = """
        SELECT 
            a.id, a.name, 
            SUM(e.file_size) as total_size
        FROM animes a
        JOIN seasons s ON a.id = s.anime_id
        JOIN episodes e ON s.id = e.season_id
        GROUP BY a.id, a.name
        ORDER BY total_size DESC
        LIMIT 10
    """
    size_animes = execute_query(size_animes_query, connection=connection)
    
    # Formatierte Größen hinzufügen
    for anime in size_animes:
        size_bytes = anime['total_size']
        if size_bytes < 1024**3:  # Kleiner als 1 GB
            anime['size_formatted'] = f"{size_bytes / 1024**2:.2f} MB"
        else:
            anime['size_formatted'] = f"{size_bytes / 1024**3:.2f} GB"
    
    stats['largest_animes'] = size_animes
    
    # Häufigste Audiospuren
    audio_query = """
        SELECT 
            IFNULL(audio_language, 'Unbekannt') as language,
            COUNT(*) as count
        FROM episodes
        GROUP BY language
        ORDER BY count DESC
        LIMIT 5
    """
    stats['audio_languages'] = execute_query(audio_query, connection=connection)
    
    # Häufigste Untertitelsprachen
    subtitle_query = """
        SELECT 
            SUBSTRING_INDEX(IFNULL(subtitles_language, 'Keine'), ',', 1) as language,
            COUNT(*) as count
        FROM episodes
        GROUP BY language
        ORDER BY count DESC
        LIMIT 5
    """
    stats['subtitle_languages'] = execute_query(subtitle_query, connection=connection)
    
    # Verteilung nach HDR-Format
    hdr_format_query = """
        SELECT 
            IFNULL(hdr_format, 'Kein HDR') as format,
            COUNT(*) as count
        FROM episodes
        GROUP BY format
        ORDER BY 
            CASE 
                WHEN format = 'Kein HDR' THEN 999
                ELSE count
            END DESC
    """
    stats['hdr_format_distribution'] = execute_query(hdr_format_query, connection=connection)
    
    # Cache aktualisieren
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logging.debug(f"Statistiken im Cache gespeichert: {cache_file}")
    except Exception as e:
        logging.warning(f"Fehler beim Speichern des Statistik-Cache: {e}")
    
    return stats


def generate_chart(chart_type, data, title=None, xlabel=None, ylabel=None, width=800, height=500, labels=None):
    """
    Generiert ein Chart-Bild basierend auf den bereitgestellten Daten.
    
    Args:
        chart_type: Art des Charts ("bar", "pie", "line", etc.)
        data: Daten für das Chart
        title: Titel des Charts (optional)
        xlabel: Beschriftung der X-Achse (optional)
        ylabel: Beschriftung der Y-Achse (optional)
        width: Breite des Charts in Pixeln (optional)
        height: Höhe des Charts in Pixeln (optional)
        labels: Beschriftungen für die Datenpunkte (optional)
    
    Returns:
        Base64-kodiertes PNG-Bild
    """
    # Cache-Datei prüfen
    cache_key = f"{chart_type}_{title}_{width}_{height}"
    # Einfacher Hash für den Cache-Schlüssel
    import hashlib
    cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + ".png"
    cache_file = os.path.join(CACHE_DIR, cache_filename)
    
    if os.path.exists(cache_file):
        try:
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_mod_time < timedelta(seconds=STATS_CACHE_TIMEOUT):
                with open(cache_file, 'rb') as f:
                    logging.debug(f"Lade Chart aus Cache: {cache_file}")
                    return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logging.warning(f"Fehler beim Laden des Chart-Cache: {e}")
    
    # Figure mit der angegebenen Größe erstellen
    dpi = 100
    fig = Figure(figsize=(width/dpi, height/dpi), dpi=dpi)
    ax = fig.add_subplot(111)
    
    # Chart basierend auf dem Typ erstellen
    if chart_type == 'bar':
        ax.bar(data.keys(), data.values(), color='skyblue')
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.tick_params(axis='x', rotation=45)
    
    elif chart_type == 'pie':
        wedges, texts, autotexts = ax.pie(
            data.values(), 
            labels=data.keys() if not labels else labels,
            autopct='%1.1f%%',
            startangle=90,
            shadow=False
        )
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Legende für bessere Lesbarkeit
        if len(data) > 5:
            ax.legend(
                wedges, data.keys(),
                title=title,
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1)
            )
    
    elif chart_type == 'line':
        ax.plot(list(data.keys()), list(data.values()), marker='o', linestyle='-', color='royalblue')
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        ax.grid(True, linestyle='--', alpha=0.7)
    
    # Chart-Titel setzen, wenn angegeben
    if title:
        ax.set_title(title)
    
    # Layout optimieren
    fig.tight_layout()
    
    # Chart in einen BytesIO-Puffer rendern
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi)
    buf.seek(0)
    
    # Als Base64 kodieren
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    # Im Cache speichern
    try:
        with open(cache_file, 'wb') as f:
            buf.seek(0)
            f.write(buf.read())
        logging.debug(f"Chart im Cache gespeichert: {cache_file}")
    except Exception as e:
        logging.warning(f"Fehler beim Speichern des Chart-Cache: {e}")
    
    return img_base64
