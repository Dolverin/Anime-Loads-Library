"""
Konfigurationsdatei für pytest.
Diese Datei enthält Fixtures und Konfigurationen, die von allen Tests verwendet werden.
"""
import os
import sys
import pytest
from flask import Flask

# Pfad zum Hauptverzeichnis des Projekts hinzufügen, damit wir Module importieren können
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import der Hauptanwendung
from simple_dashboard import app as flask_app

@pytest.fixture
def app():
    """
    Eine Testinstanz der Flask-Anwendung.
    
    Returns:
        Flask: Eine Instanz der Flask-Anwendung im Testmodus.
    """
    flask_app.config.update({
        "TESTING": True,
    })
    
    # Für Tests verwenden wir SQLite im Speicher statt MySQL
    # Damit vermeiden wir, die produktive Datenbank zu verändern
    flask_app.config["DATABASE_URI"] = "sqlite:///:memory:"
    
    yield flask_app

@pytest.fixture
def client(app):
    """
    Ein Test-Client für die Flask-Anwendung.
    
    Args:
        app: Die Flask-Anwendung.
        
    Returns:
        FlaskClient: Ein Test-Client für die Flask-Anwendung.
    """
    return app.test_client()

@pytest.fixture
def runner(app):
    """
    Ein CLI-Test-Runner für die Flask-Anwendung.
    
    Args:
        app: Die Flask-Anwendung.
        
    Returns:
        FlaskCliRunner: Ein CLI-Test-Runner für die Flask-Anwendung.
    """
    return app.test_cli_runner()
