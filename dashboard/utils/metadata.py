#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metadaten-Extraktionsfunktionen für das Anime-Loads Dashboard.
Basiert auf dem Code aus anime_archiver.py, jedoch mit Fokus auf
Wiederverwendbarkeit und Integration ins Dashboard.
"""

import os
import logging
import sys
from datetime import datetime
from pymediainfo import MediaInfo

# Füge das übergeordnete Verzeichnis zum Pfad hinzu, um Zugriff auf die Config zu haben
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
