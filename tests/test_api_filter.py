"""
Test-Modul für den API-Filter-Endpunkt.
"""
import json
import pytest
from flask import url_for

def test_api_filter_response_structure(client):
    """
    Testet, ob der API-Filter-Endpunkt die erwartete Struktur zurückgibt.
    
    Args:
        client: Flask-Testclient.
    """
    # Einfache Filteranfrage ohne Parameter (sollte alle Episoden zurückgeben)
    response = client.get('/api/filter')
    
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
    required_fields = ['episodes', 'count', 'filters']
    
    for field in required_fields:
        assert field in data, f"Feld '{field}' fehlt in der API-Antwort"
    
    # Prüfen, ob die Typen der Felder korrekt sind
    assert isinstance(data['episodes'], list), "episodes sollte eine Liste sein"
    assert isinstance(data['count'], int), "count sollte ein Integer sein"
    assert isinstance(data['filters'], dict), "filters sollte ein Dictionary sein"
    
    # Prüfen, ob die Count-Angabe mit der tatsächlichen Anzahl der Episoden übereinstimmt
    assert data['count'] == len(data['episodes']), "count sollte der Länge der episodes-Liste entsprechen"

def test_api_filter_episode_structure(client):
    """
    Testet die Struktur der Episoden in der Filterantwort.
    
    Args:
        client: Flask-Testclient.
    """
    response = client.get('/api/filter')
    
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Wenn keine Episoden zurückgegeben werden, können wir die Struktur nicht prüfen
    if not data['episodes'] or len(data['episodes']) == 0:
        pytest.skip("Keine Episoden in der Filterantwort gefunden, Strukturprüfung übersprungen")
    
    # Prüfen der Struktur der ersten Episode
    episode = data['episodes'][0]
    
    # Prüfen, ob die wichtigsten Felder vorhanden sind
    expected_fields = [
        'id', 'title', 'file_path', 'file_size', 'episode_number',
        'season_id', 'season_name', 'anime_id', 'anime_name',
        'resolution_width', 'resolution_height', 'video_codec'
    ]
    
    for field in expected_fields:
        assert field in episode, f"Feld '{field}' fehlt in einem Episode-Objekt"
    
    # Prüfen, ob die Typen der kritischen Felder korrekt sind
    assert isinstance(episode['id'], int), "episode['id'] sollte ein Integer sein"
    assert isinstance(episode['title'], str), "episode['title'] sollte ein String sein"
    assert isinstance(episode['file_path'], str), "episode['file_path'] sollte ein String sein"
    assert isinstance(episode['file_size'], (int, float)), "episode['file_size'] sollte numerisch sein"
    assert isinstance(episode['season_id'], int), "episode['season_id'] sollte ein Integer sein"
    assert isinstance(episode['season_name'], str), "episode['season_name'] sollte ein String sein"
    assert isinstance(episode['anime_id'], int), "episode['anime_id'] sollte ein Integer sein"
    assert isinstance(episode['anime_name'], str), "episode['anime_name'] sollte ein String sein"
    
    # Auflösungsfelder können None sein, daher prüfen wir auf (int, type(None))
    assert isinstance(episode['resolution_width'], (int, type(None))), "episode['resolution_width'] sollte ein Integer oder None sein"
    assert isinstance(episode['resolution_height'], (int, type(None))), "episode['resolution_height'] sollte ein Integer oder None sein"

def test_api_filter_with_anime_id(client):
    """
    Testet die Filterung nach Anime-ID.
    
    Args:
        client: Flask-Testclient.
    """
    # Zunächst alle Episoden abrufen
    response_all = client.get('/api/filter')
    
    try:
        data_all = json.loads(response_all.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Wenn keine Episoden vorhanden sind, können wir nicht nach Anime-ID filtern
    if not data_all['episodes'] or len(data_all['episodes']) == 0:
        pytest.skip("Keine Episoden gefunden, Filtertest übersprungen")
    
    # Die erste Anime-ID aus den Ergebnissen verwenden
    anime_id = data_all['episodes'][0]['anime_id']
    
    # Nach dieser Anime-ID filtern
    response_filtered = client.get(f'/api/filter?anime_id={anime_id}')
    
    assert response_filtered.status_code == 200
    
    try:
        data_filtered = json.loads(response_filtered.data)
    except json.JSONDecodeError:
        pytest.fail("Die gefilterte Antwort ist kein gültiges JSON")
    
    # Sicherstellen, dass alle gefilterten Episoden die richtige Anime-ID haben
    for episode in data_filtered['episodes']:
        assert episode['anime_id'] == anime_id, f"Episode hat falsche Anime-ID: {episode['anime_id']} statt {anime_id}"

def test_api_filter_with_resolution(client):
    """
    Testet die Filterung nach Auflösung.
    
    Args:
        client: Flask-Testclient.
    """
    # Filtern nach HD-Auflösung (mindestens 1280px breit)
    response = client.get('/api/filter?resolution_min=1280')
    
    assert response.status_code == 200
    
    try:
        data = json.loads(response.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Prüfen, ob alle zurückgegebenen Episoden mindestens HD-Auflösung haben
    for episode in data['episodes']:
        # Manche Episoden könnten keine Auflösungsdaten haben, diese überspringen wir
        if episode['resolution_width'] is not None:
            assert episode['resolution_width'] >= 1280, f"Episode hat eine Auflösung unter HD: {episode['resolution_width']}px"

def test_api_filter_with_multiple_parameters(client):
    """
    Testet die Filterung mit mehreren Parametern.
    
    Args:
        client: Flask-Testclient.
    """
    # Zunächst alle Episoden abrufen
    response_all = client.get('/api/filter')
    
    try:
        data_all = json.loads(response_all.data)
    except json.JSONDecodeError:
        pytest.fail("Die Antwort ist kein gültiges JSON")
    
    # Wenn keine Episoden vorhanden sind, können wir nicht filtern
    if not data_all['episodes'] or len(data_all['episodes']) == 0:
        pytest.skip("Keine Episoden gefunden, Filtertest übersprungen")
    
    # Filter mit mehreren Parametern erstellen (Limit und Sort)
    response_filtered = client.get('/api/filter?limit=5&sort=file_size&order=desc')
    
    assert response_filtered.status_code == 200
    
    try:
        data_filtered = json.loads(response_filtered.data)
    except json.JSONDecodeError:
        pytest.fail("Die gefilterte Antwort ist kein gültiges JSON")
    
    # Prüfen, ob maximal 5 Ergebnisse zurückgegeben werden
    assert len(data_filtered['episodes']) <= 5, f"Es wurden mehr als 5 Episoden zurückgegeben: {len(data_filtered['episodes'])}"
    
    # Prüfen, ob die Ergebnisse nach Dateigröße sortiert sind (absteigend)
    if len(data_filtered['episodes']) >= 2:
        for i in range(len(data_filtered['episodes']) - 1):
            assert data_filtered['episodes'][i]['file_size'] >= data_filtered['episodes'][i+1]['file_size'], \
                "Episoden sind nicht nach Dateigröße absteigend sortiert"
