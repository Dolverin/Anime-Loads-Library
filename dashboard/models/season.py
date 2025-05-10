#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbankmodell für Staffeln.
"""

from datetime import datetime
from . import db

class Season(db.Model):
    __tablename__ = 'seasons'
    
    id = db.Column(db.Integer, primary_key=True)
    anime_id = db.Column(db.Integer, db.ForeignKey('animes.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    season_number = db.Column(db.Integer)
    directory_path = db.Column(db.String(511), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Beziehungen
    episodes = db.relationship('Episode', backref='season', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Season {self.name} (Anime ID: {self.anime_id})>"
    
    def to_dict(self):
        """Konvertiert das Modell in ein Dictionary für die API."""
        return {
            'id': self.id,
            'anime_id': self.anime_id,
            'name': self.name,
            'season_number': self.season_number,
            'directory_path': self.directory_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'episodes_count': self.episodes.count()
        }
    
    @property
    def file_size_total(self):
        """Berechnet die Gesamtgröße aller Episoden in Bytes."""
        total_size = 0
        for episode in self.episodes:
            if episode.file_size:
                total_size += episode.file_size
        return total_size
    
    @property
    def file_size_formatted(self):
        """Gibt die formatierte Gesamtgröße zurück (MB oder GB)."""
        size_bytes = self.file_size_total
        if size_bytes < 1024**3: # Weniger als 1 GB
            return f"{size_bytes / 1024**2:.2f} MB"
        else:
            return f"{size_bytes / 1024**3:.2f} GB"
    
    @property
    def display_name(self):
        """Gibt einen anzeigbaren Namen mit Staffelnummer zurück, wenn verfügbar."""
        if self.season_number:
            return f"{self.name} (Staffel {self.season_number})"
        return self.name
