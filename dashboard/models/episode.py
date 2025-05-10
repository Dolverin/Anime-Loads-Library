#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbankmodell für Episoden mit erweiterten Metadatenfeldern.
"""

from datetime import datetime
from . import db

class Episode(db.Model):
    __tablename__ = 'episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    episode_number = db.Column(db.Integer)
    file_path = db.Column(db.String(511), nullable=False, unique=True)
    file_size = db.Column(db.BigInteger)
    file_extension = db.Column(db.String(10))
    
    # Grundlegende Videometadaten
    duration_ms = db.Column(db.BigInteger)
    video_format = db.Column(db.String(50))
    video_codec = db.Column(db.String(50))
    video_bitrate = db.Column(db.BigInteger)
    resolution_width = db.Column(db.Integer)
    resolution_height = db.Column(db.Integer)
    framerate = db.Column(db.Float)
    
    # Erweiterte Videometadaten
    aspect_ratio = db.Column(db.String(20))
    color_depth = db.Column(db.String(10))
    hdr_format = db.Column(db.String(30))
    color_space = db.Column(db.String(30))
    scan_type = db.Column(db.String(20))
    encoder = db.Column(db.String(100))
    
    # Audio-Metadaten
    audio_codec = db.Column(db.String(50))
    audio_channels = db.Column(db.Integer)
    audio_bitrate = db.Column(db.BigInteger)
    audio_sample_rate = db.Column(db.Integer)
    audio_language = db.Column(db.String(50))
    audio_tracks_count = db.Column(db.Integer)
    audio_languages = db.Column(db.String(255))
    
    # Untertitel-Metadaten
    subtitles_language = db.Column(db.String(255))
    subtitles_formats = db.Column(db.String(255))
    subtitles_count = db.Column(db.Integer)
    forced_subtitles = db.Column(db.Boolean)
    
    # Dateiinformationen
    container_format = db.Column(db.String(50))
    creation_time = db.Column(db.DateTime)
    
    # Systemfelder
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Episode {self.name} (Season ID: {self.season_id})>"
    
    def to_dict(self):
        """Konvertiert das Modell in ein Dictionary für die API."""
        return {
            'id': self.id,
            'season_id': self.season_id,
            'name': self.name,
            'episode_number': self.episode_number,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_formatted': self.file_size_formatted,
            'file_extension': self.file_extension,
            
            # Videometadaten
            'duration_ms': self.duration_ms,
            'duration_formatted': self.duration_formatted,
            'video_format': self.video_format,
            'video_codec': self.video_codec,
            'video_bitrate': self.video_bitrate,
            'resolution': self.resolution,
            'framerate': self.framerate,
            'aspect_ratio': self.aspect_ratio,
            'color_depth': self.color_depth,
            'hdr_format': self.hdr_format,
            'color_space': self.color_space,
            'scan_type': self.scan_type,
            'encoder': self.encoder,
            
            # Audiometadaten
            'audio_codec': self.audio_codec,
            'audio_channels': self.audio_channels,
            'audio_bitrate': self.audio_bitrate,
            'audio_sample_rate': self.audio_sample_rate,
            'audio_language': self.audio_language,
            'audio_tracks_count': self.audio_tracks_count,
            'audio_languages': self.audio_languages,
            
            # Untertitelmetadaten
            'subtitles_language': self.subtitles_language,
            'subtitles_formats': self.subtitles_formats,
            'subtitles_count': self.subtitles_count,
            'forced_subtitles': self.forced_subtitles,
            
            # Dateiinformationen
            'container_format': self.container_format,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            
            # Systemfelder
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def duration_formatted(self):
        """Formatiert die Dauer in Minuten und Sekunden."""
        if not self.duration_ms:
            return "Unbekannt"
        
        seconds = self.duration_ms / 1000
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds % 60)
        
        return f"{minutes}:{remaining_seconds:02d} Min."
    
    @property
    def file_size_formatted(self):
        """Formatiert die Dateigröße in KB, MB oder GB."""
        if not self.file_size:
            return "Unbekannt"
        
        if self.file_size < 1024**2: # Kleiner als 1 MB
            return f"{self.file_size / 1024:.2f} KB"
        elif self.file_size < 1024**3: # Kleiner als 1 GB
            return f"{self.file_size / 1024**2:.2f} MB"
        else:
            return f"{self.file_size / 1024**3:.2f} GB"
    
    @property
    def resolution(self):
        """Gibt die Auflösung als formatierte Zeichenkette zurück."""
        if not self.resolution_width or not self.resolution_height:
            return "Unbekannt"
        
        return f"{self.resolution_width}x{self.resolution_height}"
    
    @property
    def is_hdr(self):
        """Überprüft, ob die Episode in HDR vorliegt."""
        return bool(self.hdr_format)
    
    @property
    def is_4k(self):
        """Überprüft, ob die Episode in 4K-Auflösung vorliegt."""
        return self.resolution_width and self.resolution_width >= 3840
    
    @property
    def display_name(self):
        """Gibt einen anzeigbaren Namen mit Episodennummer zurück, wenn verfügbar."""
        if self.episode_number:
            return f"Episode {self.episode_number}: {self.name}"
        return self.name
