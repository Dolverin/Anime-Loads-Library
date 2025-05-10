#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suchfunktionen-API für das Anime-Loads Dashboard.
Bietet Endpunkte zum Suchen und Filtern von Animes, Staffeln und Episoden.
"""

import logging
import sys
from flask import jsonify, request
from sqlalchemy import and_, or_, text

# Füge das übergeordnete Verzeichnis zum Pfad hinzu
sys.path.insert(0, '..')
from config import MAX_SEARCH_RESULTS
from models import db, Anime, Season, Episode

def search():
    """
    Generischer Suchendpunkt für Animes, Staffeln und Episoden.
    
    Query-Parameter:
        q: Suchbegriff (in Name, Pfad etc.)
        type: Typ der zu suchenden Elemente (anime, season, episode, all)
        limit: Maximale Anzahl der Ergebnisse (default: MAX_SEARCH_RESULTS)
    
    Returns:
        JSON mit Suchergebnissen
    """
    search_term = request.args.get('q', '')
    search_type = request.args.get('type', 'all').lower()
    limit = int(request.args.get('limit', MAX_SEARCH_RESULTS))
    
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
        animes = Anime.query.filter(
            or_(
                Anime.name.like(search_pattern),
                Anime.directory_path.like(search_pattern)
            )
        ).limit(limit).all()
        
        results['animes'] = [anime.to_dict() for anime in animes]
    
    # Staffeln suchen
    if search_type in ('all', 'season'):
        seasons = Season.query.filter(
            or_(
                Season.name.like(search_pattern),
                Season.directory_path.like(search_pattern)
            )
        ).limit(limit).all()
        
        results['seasons'] = [season.to_dict() for season in seasons]
    
    # Episoden suchen
    if search_type in ('all', 'episode'):
        episodes = Episode.query.filter(
            or_(
                Episode.name.like(search_pattern),
                Episode.file_path.like(search_pattern)
            )
        ).limit(limit).all()
        
        results['episodes'] = [episode.to_dict() for episode in episodes]
    
    return jsonify(results)

def get_anime(anime_id):
    """
    Liefert detaillierte Informationen zu einem bestimmten Anime.
    
    Args:
        anime_id: ID des Animes
    
    Returns:
        JSON mit Anime-Details und zugehörigen Staffeln
    """
    anime = Anime.query.get(anime_id)
    
    if not anime:
        return jsonify({
            'error': f'Anime mit ID {anime_id} nicht gefunden.'
        }), 404
    
    # Anime-Basisdaten
    result = anime.to_dict()
    
    # Staffeln hinzufügen
    seasons = Season.query.filter_by(anime_id=anime_id).all()
    result['seasons'] = [season.to_dict() for season in seasons]
    
    return jsonify(result)

def get_season(season_id):
    """
    Liefert detaillierte Informationen zu einer bestimmten Staffel.
    
    Args:
        season_id: ID der Staffel
    
    Returns:
        JSON mit Staffel-Details und zugehörigen Episoden
    """
    season = Season.query.get(season_id)
    
    if not season:
        return jsonify({
            'error': f'Staffel mit ID {season_id} nicht gefunden.'
        }), 404
    
    # Staffel-Basisdaten
    result = season.to_dict()
    
    # Anime-Informationen hinzufügen
    anime = Anime.query.get(season.anime_id)
    if anime:
        result['anime'] = {
            'id': anime.id,
            'name': anime.name
        }
    
    # Episoden hinzufügen
    episodes = Episode.query.filter_by(season_id=season_id).all()
    result['episodes'] = [episode.to_dict() for episode in episodes]
    
    return jsonify(result)

def get_episode(episode_id):
    """
    Liefert detaillierte Informationen zu einer bestimmten Episode.
    
    Args:
        episode_id: ID der Episode
    
    Returns:
        JSON mit vollständigen Episode-Details
    """
    episode = Episode.query.get(episode_id)
    
    if not episode:
        return jsonify({
            'error': f'Episode mit ID {episode_id} nicht gefunden.'
        }), 404
    
    # Episode-Basisdaten
    result = episode.to_dict()
    
    # Staffel- und Anime-Informationen hinzufügen
    season = Season.query.get(episode.season_id)
    if season:
        result['season'] = {
            'id': season.id,
            'name': season.name,
            'season_number': season.season_number
        }
        
        anime = Anime.query.get(season.anime_id)
        if anime:
            result['anime'] = {
                'id': anime.id,
                'name': anime.name
            }
    
    return jsonify(result)

def filter_episodes():
    """
    Filtert Episoden nach verschiedenen Kriterien.
    
    Query-Parameter:
        anime_id: ID des Animes
        season_id: ID der Staffel
        resolution_min: Minimale Auflösung (z.B. 1080, 2160)
        codec: Videocodec (z.B. HEVC, AVC)
        hdr: Ob HDR vorhanden sein soll (true/false)
        audio_language: Audiosprache (z.B. jpn, ger)
        subtitles: Ob Untertitel vorhanden sein sollen (true/false)
        subtitles_language: Untertitelsprache
        limit: Maximale Anzahl der Ergebnisse
    
    Returns:
        JSON mit gefilterten Episoden
    """
    # Parameter auslesen
    anime_id = request.args.get('anime_id')
    season_id = request.args.get('season_id')
    resolution_min = request.args.get('resolution_min')
    codec = request.args.get('codec')
    hdr = request.args.get('hdr')
    audio_language = request.args.get('audio_language')
    subtitles = request.args.get('subtitles')
    subtitles_language = request.args.get('subtitles_language')
    limit = int(request.args.get('limit', MAX_SEARCH_RESULTS))
    
    # Basis-Query aufbauen
    query = Episode.query
    
    # Filter hinzufügen
    filters = []
    
    if season_id:
        filters.append(Episode.season_id == season_id)
    elif anime_id:
        # Alle Staffeln des Animes finden
        season_ids = [s.id for s in Season.query.filter_by(anime_id=anime_id).all()]
        if season_ids:
            filters.append(Episode.season_id.in_(season_ids))
    
    if resolution_min:
        res_min = int(resolution_min)
        filters.append(Episode.resolution_height >= res_min)
    
    if codec:
        filters.append(Episode.video_codec.like(f"%{codec}%"))
    
    if hdr and hdr.lower() in ('true', '1', 'yes'):
        filters.append(Episode.hdr_format.isnot(None))
        filters.append(Episode.hdr_format != '')
    
    if audio_language:
        filters.append(
            or_(
                Episode.audio_language.like(f"%{audio_language}%"),
                Episode.audio_languages.like(f"%{audio_language}%")
            )
        )
    
    if subtitles and subtitles.lower() in ('true', '1', 'yes'):
        filters.append(Episode.subtitles_language.isnot(None))
        filters.append(Episode.subtitles_language != '')
    
    if subtitles_language:
        filters.append(Episode.subtitles_language.like(f"%{subtitles_language}%"))
    
    # Filter anwenden und Abfrage ausführen
    if filters:
        query = query.filter(and_(*filters))
    
    episodes = query.limit(limit).all()
    
    # Ergebnisse formatieren
    results = [episode.to_dict() for episode in episodes]
    
    return jsonify({
        'count': len(results),
        'episodes': results
    })
