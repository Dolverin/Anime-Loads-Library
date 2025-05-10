#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbankmodell für Animes.
"""

from datetime import datetime
from . import db

class Anime(db.Model):
    __tablename__ = 'animes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    directory_path = db.Column(db.String(511), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Beziehungen
    seasons = db.relationship('Season', backref='anime', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Anime {self.name}>"
    
    def to_dict(self):
        """Konvertiert das Modell in ein Dictionary für die API."""
        return {
            'id': self.id,
            'name': self.name,
            'directory_path': self.directory_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'seasons_count': self.seasons.count(),
            'episodes_count': sum(season.episodes.count() for season in self.seasons)
        }
    
    @property
    def file_size_total(self):
        """Berechnet die Gesamtgröße aller Episoden in Bytes."""
        total_size = 0
        for season in self.seasons:
            for episode in season.episodes:
                if episode.file_size:
                    total_size += episode.file_size
        return total_size
    
    @property
    def file_size_formatted(self):
        """Gibt die formatierte Gesamtgröße zurück (GB oder TB)."""
        size_bytes = self.file_size_total
        if size_bytes < 1024**3: # Weniger als 1 GB
            return f"{size_bytes / 1024**2:.2f} MB"
        elif size_bytes < 1024**4: # Weniger als 1 TB
            return f"{size_bytes / 1024**3:.2f} GB"
        else:
            return f"{size_bytes / 1024**4:.2f} TB"
