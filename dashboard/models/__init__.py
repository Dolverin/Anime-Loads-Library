#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbankmodelle für das Anime-Loads Dashboard.
Verwendet SQLAlchemy für die ORM-Funktionalität.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .anime import Anime
from .season import Season
from .episode import Episode
