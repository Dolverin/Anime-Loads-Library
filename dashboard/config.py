#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfigurationsdatei für das Anime-Loads Dashboard.
Enthält gemeinsame Einstellungen für alle Komponenten.
"""

import os
import logging
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# Basisverzeichnis
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

# Logging-Konfiguration
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "anime_dashboard.log")
LOG_LEVEL = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'

# Datenbank-Konfiguration
DB_HOST = os.getenv('DB_HOST', '192.168.178.9')
DB_USER = os.getenv('DB_USER', 'aniworld')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'aniworld')
DB_NAME = os.getenv('DB_NAME', 'animeloads')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

# Medienpfad-Konfiguration
MEDIA_PATH = os.getenv('MEDIA_PATH', '/mnt/mediathek')

# Flask-Konfiguration
SECRET_KEY = os.getenv('SECRET_KEY', 'anime_loads_secret_key_change_in_production')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', 'yes', '1')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# Update-Job-Konfiguration
UPDATE_INTERVAL_HOURS = int(os.getenv('UPDATE_INTERVAL_HOURS', '24'))
UPDATE_TIME = os.getenv('UPDATE_TIME', '03:00')  # Format: HH:MM
LOCK_FILE = os.path.join(PARENT_DIR, ".update.lock")

# Statistik-Konfiguration
CACHE_DIR = os.path.join(BASE_DIR, "static/cache")
STATS_CACHE_TIMEOUT = int(os.getenv('STATS_CACHE_TIMEOUT', '3600'))  # 1 Stunde

# Suche-Konfiguration
MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', '100'))

# E-Mail-Benachrichtigung (optional)
ENABLE_EMAIL = os.getenv('ENABLE_EMAIL', 'False').lower() in ('true', 'yes', '1')
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')
EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT', 'Anime-Loads Update Report')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', '25'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

# Logging einrichten
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# SQLAlchemy-Konfiguration
SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
