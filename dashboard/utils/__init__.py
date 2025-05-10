#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dienstprogramme für das Anime-Loads Dashboard.
"""

from .db import get_db_connection, close_db_connection, execute_query
from .metadata import extract_media_info
from .stats import calculate_stats, generate_chart
