"""
Test-Modul für den API-Suchergebnisse-Endpunkt.
"""
import json
import pytest
from flask import url_for

def test_api_search_response_structure(client):
    """
    Testet, ob der API-Suchergebnisse-Endpunkt die erwartete Struktur zurückgibt.
    
    Args:
        client: Flask-Testclient.
    """
    # Einfache Suchanfrage mit leerem String (sollte alle Ergebnisse zurückgeben)
    response = client.get('/api/search?q=')
    
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
    required_fields = ['query', 'results', 'count']
    
    for field in required_fields:
        assert field in data, f"Feld '{field}' fehlt in der API-Antwort"
    
    # Prüfen, ob die Typen der Felder korrekt sind
    assert isinstance(data['query'], str), "query sollte ein String sein"
    assert isinstance(data['results'], dict), "results sollte ein Dictionary sein"
    assert isinstance(data['count'], int), "count sollte ein Integer sein"
    
    # Prüfen, ob die results die erwarteten Kategorien enthalten
    expected_categories = ['animes', 'seasons', 'episodes']
    for category in expected_categories:
        assert category in data['results'], f"Kategorie '{category}' fehlt in den Suchergebnissen"
        assert isinstance(data['results'][category], list), f"results[{category}] sollte eine Liste sein"

def test_api_search_with_query(client):
    """
    Testet die Suche mit einem konkreten Suchbegriff.
    
    Args:
        client: Flask-Testclient.
    """
    # Suchanfrage mit einem konkreten Begriff
    test_query = 'test'
    response = client.get(f'/api/search?q={test_query}')
    
    # Prüfen, ob die Anfrage erfolgreich war
    assert response.status_code == 200
    
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen, ob der Suchbegriff korrekt zurückgegeben wird
    assert data['query'] == test_query

def test_api_search_result_structure(client):
    """
    Testet die Struktur der Suchergebnisse.
    
    Args:
        client: Flask-Testclient.
    """
    response = client.get('/api/search?q=')
    
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen der Struktur von Anime-Ergebnissen (falls vorhanden)
    if data['results']['animes'] and len(data['results']['animes']) > 0:
        anime = data['results']['animes'][0]
        assert 'id' in anime, "Feld 'id' fehlt in einem Anime-Objekt"
        assert 'name' in anime, "Feld 'name' fehlt in einem Anime-Objekt"
        assert 'directory_path' in anime, "Feld 'directory_path' fehlt in einem Anime-Objekt"
        
        assert isinstance(anime['id'], int), "anime['id'] sollte ein Integer sein"
        assert isinstance(anime['name'], str), "anime['name'] sollte ein String sein"
        assert isinstance(anime['directory_path'], str), "anime['directory_path'] sollte ein String sein"
    
    # Prüfen der Struktur von Staffel-Ergebnissen (falls vorhanden)
    if data['results']['seasons'] and len(data['results']['seasons']) > 0:
        season = data['results']['seasons'][0]
        assert 'id' in season, "Feld 'id' fehlt in einem Season-Objekt"
        assert 'name' in season, "Feld 'name' fehlt in einem Season-Objekt"
        assert 'anime_id' in season, "Feld 'anime_id' fehlt in einem Season-Objekt"
        assert 'anime_name' in season, "Feld 'anime_name' fehlt in einem Season-Objekt"
        
        assert isinstance(season['id'], int), "season['id'] sollte ein Integer sein"
        assert isinstance(season['name'], str), "season['name'] sollte ein String sein"
        assert isinstance(season['anime_id'], int), "season['anime_id'] sollte ein Integer sein"
        assert isinstance(season['anime_name'], str), "season['anime_name'] sollte ein String sein"
    
    # Prüfen der Struktur von Episoden-Ergebnissen (falls vorhanden)
    if data['results']['episodes'] and len(data['results']['episodes']) > 0:
        episode = data['results']['episodes'][0]
        assert 'id' in episode, "Feld 'id' fehlt in einem Episode-Objekt"
        assert 'title' in episode, "Feld 'title' fehlt in einem Episode-Objekt"
        assert 'season_id' in episode, "Feld 'season_id' fehlt in einem Episode-Objekt"
        assert 'season_name' in episode, "Feld 'season_name' fehlt in einem Episode-Objekt"
        assert 'anime_id' in episode, "Feld 'anime_id' fehlt in einem Episode-Objekt"
        assert 'anime_name' in episode, "Feld 'anime_name' fehlt in einem Episode-Objekt"
        
        assert isinstance(episode['id'], int), "episode['id'] sollte ein Integer sein"
        assert isinstance(episode['title'], str), "episode['title'] sollte ein String sein"
        assert isinstance(episode['season_id'], int), "episode['season_id'] sollte ein Integer sein"
        assert isinstance(episode['season_name'], str), "episode['season_name'] sollte ein String sein"
        assert isinstance(episode['anime_id'], int), "episode['anime_id'] sollte ein Integer sein"
        assert isinstance(episode['anime_name'], str), "episode['anime_name'] sollte ein String sein"
