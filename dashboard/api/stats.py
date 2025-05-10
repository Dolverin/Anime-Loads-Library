#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistik-API für das Anime-Loads Dashboard.
Bietet Endpunkte für statistische Analysen der Anime-Sammlung.
"""

import logging
import sys
from flask import jsonify, request
from sqlalchemy import func, desc, and_, or_, text
import json

# Füge das übergeordnete Verzeichnis zum Pfad hinzu
sys.path.insert(0, '..')
from models import db, Anime, Season, Episode
from utils.stats import calculate_stats, generate_chart

def get_stats():
    """
    Liefert allgemeine Statistiken über die Anime-Sammlung.
    
    Returns:
        JSON mit verschiedenen Statistiken
    """
    connection = db.engine.connect()
    stats = calculate_stats(connection)
    connection.close()
    
    return jsonify(stats)

def get_resolution_stats():
    """
    Liefert Statistiken zur Verteilung der Auflösungen.
    Optional: Generiert ein Chart, wenn 'chart=true'.
    
    Returns:
        JSON mit Auflösungsverteilung
    """
    # Query für die Auflösungsverteilung
    query = db.session.query(
        db.case([
            (Episode.resolution_width >= 3840, '4K'),
            (Episode.resolution_width >= 1920, 'Full HD'),
            (Episode.resolution_width >= 1280, 'HD'),
            (Episode.resolution_width >= 720, 'HD Ready'),
            (Episode.resolution_width > 0, 'SD')
        ], else_='Unbekannt').label('resolution_category'),
        func.count().label('count')
    ).group_by('resolution_category').order_by(
        db.case({
            '4K': 1,
            'Full HD': 2,
            'HD': 3,
            'HD Ready': 4,
            'SD': 5,
            'Unbekannt': 6
        }, value='resolution_category')
    )
    
    distribution = query.all()
    
    # Ergebnisse formatieren
    results = {}
    for category, count in distribution:
        results[category] = count
    
    # Chart generieren, wenn angefordert
    generate_chart_image = request.args.get('chart', '').lower() in ('true', '1', 'yes')
    if generate_chart_image:
        chart = generate_chart(
            'pie', 
            results,
            title='Auflösungsverteilung',
            width=800, 
            height=500
        )
        return jsonify({
            'distribution': results,
            'chart': chart
        })
    
    return jsonify({
        'distribution': results
    })

def get_codec_stats():
    """
    Liefert Statistiken zur Verteilung der Videocodecs.
    Optional: Generiert ein Chart, wenn 'chart=true'.
    
    Returns:
        JSON mit Codecverteilung
    """
    # Query für die Codecverteilung
    query = db.session.query(
        db.case([(Episode.video_codec != None, Episode.video_codec)], else_='Unbekannt').label('codec'),
        func.count().label('count')
    ).group_by('codec').order_by(desc('count')).limit(10)
    
    distribution = query.all()
    
    # Ergebnisse formatieren
    results = {}
    for codec, count in distribution:
        codec_name = codec if codec else 'Unbekannt'
        results[codec_name] = count
    
    # Chart generieren, wenn angefordert
    generate_chart_image = request.args.get('chart', '').lower() in ('true', '1', 'yes')
    if generate_chart_image:
        chart = generate_chart(
            'bar', 
            results,
            title='Top 10 Videocodecs',
            xlabel='Codec',
            ylabel='Anzahl',
            width=800, 
            height=500
        )
        return jsonify({
            'distribution': results,
            'chart': chart
        })
    
    return jsonify({
        'distribution': results
    })

def get_hdr_stats():
    """
    Liefert Statistiken zur Verteilung der HDR-Formate.
    Optional: Generiert ein Chart, wenn 'chart=true'.
    
    Returns:
        JSON mit HDR-Formatverteilung
    """
    # Query für die HDR-Formatverteilung
    query = db.session.query(
        db.case([
            (and_(Episode.hdr_format != None, Episode.hdr_format != ''), Episode.hdr_format)
        ], else_='Kein HDR').label('hdr_format'),
        func.count().label('count')
    ).group_by('hdr_format').order_by(
        db.case({
            'Kein HDR': 999
        }, value='hdr_format', else_=0),
        desc('count')
    )
    
    distribution = query.all()
    
    # Ergebnisse formatieren
    results = {}
    for hdr_format, count in distribution:
        format_name = hdr_format if hdr_format else 'Kein HDR'
        results[format_name] = count
    
    # Chart generieren, wenn angefordert
    generate_chart_image = request.args.get('chart', '').lower() in ('true', '1', 'yes')
    if generate_chart_image:
        chart = generate_chart(
            'pie', 
            results,
            title='HDR-Formatverteilung',
            width=800, 
            height=500
        )
        return jsonify({
            'distribution': results,
            'chart': chart
        })
    
    return jsonify({
        'distribution': results
    })

def get_top_animes():
    """
    Liefert die Top-Animes nach verschiedenen Kriterien.
    
    Query-Parameter:
        sort_by: Sortierkriterium (episodes, size)
        limit: Maximale Anzahl der Ergebnisse
    
    Returns:
        JSON mit Top-Animes
    """
    sort_by = request.args.get('sort_by', 'episodes').lower()
    limit = int(request.args.get('limit', 10))
    
    if sort_by == 'size':
        # Top-Animes nach Dateigröße
        query = db.session.query(
            Anime.id,
            Anime.name,
            func.sum(Episode.file_size).label('total_size')
        ).join(Season, Season.anime_id == Anime.id
        ).join(Episode, Episode.season_id == Season.id
        ).group_by(Anime.id, Anime.name
        ).order_by(desc('total_size')
        ).limit(limit)
        
        results = []
        for anime_id, name, total_size in query.all():
            # Formatierte Größe
            if total_size < 1024**3:  # Kleiner als 1 GB
                size_formatted = f"{total_size / 1024**2:.2f} MB"
            else:
                size_formatted = f"{total_size / 1024**3:.2f} GB"
            
            results.append({
                'id': anime_id,
                'name': name,
                'total_size': total_size,
                'size_formatted': size_formatted
            })
    else:
        # Top-Animes nach Episodenanzahl (Standard)
        query = db.session.query(
            Anime.id,
            Anime.name,
            func.count(Episode.id).label('episode_count')
        ).join(Season, Season.anime_id == Anime.id
        ).join(Episode, Episode.season_id == Season.id
        ).group_by(Anime.id, Anime.name
        ).order_by(desc('episode_count')
        ).limit(limit)
        
        results = []
        for anime_id, name, episode_count in query.all():
            results.append({
                'id': anime_id,
                'name': name,
                'episode_count': episode_count
            })
    
    return jsonify(results)
