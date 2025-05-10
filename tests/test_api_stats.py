"""
Test-Modul für die API-Statistik-Endpunkte.
"""
import json
import pytest
from flask import url_for

def test_api_stats_response_structure(client):
    """
    Testet, ob der API-Stats-Endpunkt die erwartete Struktur zurückgibt.
    
    Args:
        client: Flask-Testclient.
    """
    response = client.get('/api/stats')
    
    # Prüfen, ob die Anfrage erfolgreich war
    assert response.status_code == 200
    
    # Prüfen, ob der Content-Type korrekt ist
    assert response.content_type == 'application/json'
    
    # Versuchen, die JSON-Antwort zu parsen
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen, ob alle erforderlichen Felder vorhanden sind
    required_fields = [
        'animes_count', 'seasons_count', 'episodes_count', 
        'total_size_bytes', 'total_size_formatted', 'total_duration_formatted'
    ]
    
    for field in required_fields:
        assert field in data, f"Feld '{field}' fehlt in der API-Antwort"
    
    # Prüfen, ob die Typen der Felder korrekt sind
    assert isinstance(data['animes_count'], int), "animes_count sollte ein Integer sein"
    assert isinstance(data['seasons_count'], int), "seasons_count sollte ein Integer sein"
    assert isinstance(data['episodes_count'], int), "episodes_count sollte ein Integer sein"
    assert isinstance(data['total_size_bytes'], (int, float)), "total_size_bytes sollte numerisch sein"
    assert isinstance(data['total_size_formatted'], str), "total_size_formatted sollte ein String sein"
    assert isinstance(data['total_duration_formatted'], str), "total_duration_formatted sollte ein String sein"

def test_api_stats_resolution_chart(client):
    """
    Testet, ob der API-Endpunkt für Auflösungsstatistiken die erwartete Struktur zurückgibt.
    
    Args:
        client: Flask-Testclient.
    """
    response = client.get('/api/stats/resolution?chart=true')
    
    # Prüfen, ob die Anfrage erfolgreich war
    assert response.status_code == 200
    
    # Prüfen, ob der Content-Type korrekt ist
    assert response.content_type == 'application/json'
    
    # Versuchen, die JSON-Antwort zu parsen
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen, ob das Feld 'distribution' vorhanden ist
    assert 'distribution' in data, "Feld 'distribution' fehlt in der API-Antwort"
    
    # Prüfen, ob 'distribution' ein Dictionary ist
    assert isinstance(data['distribution'], dict), "distribution sollte ein Dictionary sein"

def test_api_stats_hdr_chart(client):
    """
    Testet, ob der API-Endpunkt für HDR-Statistiken die erwartete Struktur zurückgibt.
    
    Args:
        client: Flask-Testclient.
    """
    response = client.get('/api/stats/hdr?chart=true')
    
    # Prüfen, ob die Anfrage erfolgreich war
    assert response.status_code == 200
    
    # Prüfen, ob der Content-Type korrekt ist
    assert response.content_type == 'application/json'
    
    # Versuchen, die JSON-Antwort zu parsen
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen, ob das Feld 'distribution' vorhanden ist
    assert 'distribution' in data, "Feld 'distribution' fehlt in der API-Antwort"
    
    # Prüfen, ob 'distribution' ein Dictionary ist
    assert isinstance(data['distribution'], dict), "distribution sollte ein Dictionary sein"

def test_api_stats_top_animes(client):
    """
    Testet, ob der API-Endpunkt für Top-Animes die erwartete Struktur zurückgibt.
    
    Args:
        client: Flask-Testclient.
    """
    response = client.get('/api/stats/top_animes')
    
    # Prüfen, ob die Anfrage erfolgreich war
    assert response.status_code == 200
    
    # Prüfen, ob der Content-Type korrekt ist
    assert response.content_type == 'application/json'
    
    # Versuchen, die JSON-Antwort zu parsen
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen, ob das Feld 'top_animes' vorhanden ist
    assert 'top_animes' in data, "Feld 'top_animes' fehlt in der API-Antwort"
    
    # Prüfen, ob 'top_animes' eine Liste ist
    assert isinstance(data['top_animes'], list), "top_animes sollte eine Liste sein"
    
    # Wenn die Liste nicht leer ist, prüfen wir die Struktur der Elemente
    if data['top_animes']:
        anime = data['top_animes'][0]
        assert 'id' in anime, "Feld 'id' fehlt in einem Anime-Objekt"
        assert 'name' in anime, "Feld 'name' fehlt in einem Anime-Objekt"
        assert 'episode_count' in anime, "Feld 'episode_count' fehlt in einem Anime-Objekt"
        
        assert isinstance(anime['id'], int), "anime['id'] sollte ein Integer sein"
        assert isinstance(anime['name'], str), "anime['name'] sollte ein String sein"
        assert isinstance(anime['episode_count'], int), "anime['episode_count'] sollte ein Integer sein"
