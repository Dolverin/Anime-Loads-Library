#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API-Endpunkte für das Anime-Loads Dashboard.
Bietet Zugriff auf die Daten der Anime-Sammlung über REST-API.
"""

from flask import Blueprint, jsonify, request
from . import search, stats

api = Blueprint('api', __name__, url_prefix='/api')

# Suchendpunkte einbinden
api.add_url_rule('/search', view_func=search.search, methods=['GET'])
api.add_url_rule('/anime/<int:anime_id>', view_func=search.get_anime, methods=['GET'])
api.add_url_rule('/season/<int:season_id>', view_func=search.get_season, methods=['GET'])
api.add_url_rule('/episode/<int:episode_id>', view_func=search.get_episode, methods=['GET'])
api.add_url_rule('/filter', view_func=search.filter_episodes, methods=['GET'])

# Statistikendpunkte einbinden
api.add_url_rule('/stats', view_func=stats.get_stats, methods=['GET'])
api.add_url_rule('/stats/resolution', view_func=stats.get_resolution_stats, methods=['GET'])
api.add_url_rule('/stats/codec', view_func=stats.get_codec_stats, methods=['GET'])
api.add_url_rule('/stats/hdr', view_func=stats.get_hdr_stats, methods=['GET'])
api.add_url_rule('/stats/top_animes', view_func=stats.get_top_animes, methods=['GET'])

# API-Basisendpunkt für Statusprüfung
@api.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Anime-Loads API ist aktiv',
        'version': '1.0.0'
    })
