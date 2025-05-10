#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbankdienstprogramme für das Anime-Loads Dashboard.
Bietet Funktionen für die Verbindung zur MySQL-Datenbank.
"""

import logging
import mysql.connector
from mysql.connector import Error
import sys
import os

# Füge das übergeordnete Verzeichnis zum Pfad hinzu, um Zugriff auf die Config zu haben
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

def get_db_connection():
    """
    Stellt eine Verbindung zur MySQL-Datenbank her.
    
    Returns:
        connection: MySQLConnection-Objekt oder None im Fehlerfall
    """
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        
        if connection.is_connected():
            logging.debug(f"Verbindung zur Datenbank {DB_NAME} hergestellt")
            return connection
        
    except Error as e:
        logging.error(f"Fehler bei der Verbindung zur MySQL-Datenbank: {e}")
        return None

def close_db_connection(connection):
    """
    Schließt eine aktive Datenbankverbindung.
    
    Args:
        connection: MySQLConnection-Objekt
    """
    if connection and connection.is_connected():
        connection.close()
        logging.debug("Datenbankverbindung geschlossen")

def execute_query(query, params=None, fetch_mode="all", connection=None):
    """
    Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück.
    
    Args:
        query: SQL-Abfrage als String
        params: Parameter für die Abfrage (optional)
        fetch_mode: "all" für fetchall(), "one" für fetchone(), "none" für keine Rückgabe
        connection: MySQLConnection-Objekt (optional - falls nicht vorhanden, wird eine neue erstellt)
    
    Returns:
        Abfrageergebnisse oder None im Fehlerfall
    """
    conn_created = False
    try:
        if not connection:
            connection = get_db_connection()
            conn_created = True
        
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_mode == "all":
            result = cursor.fetchall()
        elif fetch_mode == "one":
            result = cursor.fetchone()
        else:  # fetch_mode == "none"
            connection.commit()
            result = cursor.rowcount
        
        cursor.close()
        return result
        
    except Error as e:
        logging.error(f"Fehler bei der Ausführung der Datenbankabfrage: {e}")
        logging.debug(f"Abfrage: {query}")
        if params:
            logging.debug(f"Parameter: {params}")
        return None
        
    finally:
        if conn_created and connection:
            close_db_connection(connection)
