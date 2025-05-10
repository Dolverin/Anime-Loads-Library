"""
UI-Tests für die Anime-Liste-Seite des Anime-Loads Dashboards.
Diese Tests überprüfen Funktionen der Anime-Übersichtsseite.
"""
import pytest
import re
from playwright.sync_api import Page, expect

def test_anime_list_title(navigate_to_anime_list, page: Page):
    """
    Testet, ob der Titel der Anime-Liste-Seite korrekt ist.
    
    Args:
        navigate_to_anime_list: Fixture, die zur Anime-Liste navigiert
        page: Die Playwright-Page-Instanz
    """
    # Prüfen, ob der Seitentitel korrekt ist
    expect(page).to_have_title(re.compile("Animes - Anime-Loads"))
    
    # Prüfen, ob die Hauptüberschrift korrekt ist
    headline = page.locator("h1").first
    expect(headline).to_be_visible()
    expect(headline).to_contain_text("Animes")

def test_anime_list_search_field(navigate_to_anime_list, page: Page):
    """
    Testet, ob das Suchfeld auf der Anime-Liste-Seite funktioniert.
    
    Args:
        navigate_to_anime_list: Fixture, die zur Anime-Liste navigiert
        page: Die Playwright-Page-Instanz
    """
    # Prüfen, ob das Suchfeld vorhanden ist
    search_field = page.locator("#animeSearchInput")
    expect(search_field).to_be_visible()
    
    # Einen Suchwert eingeben
    test_search = "Test"
    search_field.fill(test_search)
    
    # Prüfen, ob der Wert korrekt gesetzt wurde
    expect(search_field).to_have_value(test_search)
    
    # Auf die Enter-Taste drücken
    search_field.press("Enter")
    
    # Die Filterfunktion ist client-seitig, daher sollte die URL gleich bleiben
    expect(page).to_have_url(re.compile(".*\/anime"))

def test_anime_list_cards(navigate_to_anime_list, page: Page):
    """
    Testet, ob die Anime-Karten korrekt angezeigt werden.
    
    Args:
        navigate_to_anime_list: Fixture, die zur Anime-Liste navigiert
        page: Die Playwright-Page-Instanz
    """
    # Auf Anime-Karten warten
    anime_cards = page.locator(".anime-card")
    
    # Entweder sollte es Anime-Karten oder eine Info-Meldung geben
    cards_count = anime_cards.count()
    info_messages = page.locator(".alert-info")
    
    if cards_count > 0:
        # Prüfen, ob die Animes angezeigt werden
        first_card = anime_cards.first
        expect(first_card).to_be_visible()
        
        # Prüfen, ob jede Karte einen Namen hat
        anime_names = page.locator(".anime-card .card-title")
        expect(anime_names.first).to_be_visible()
        
        # Prüfen, ob die Staffel- und Episodenanzahl angezeigt wird
        season_count = page.locator(".anime-card .season-count").first
        episode_count = page.locator(".anime-card .episode-count").first
        
        expect(season_count).to_be_visible()
        expect(episode_count).to_be_visible()
    else:
        # Wenn keine Animes gefunden wurden, sollte eine Info-Meldung angezeigt werden
        expect(info_messages).to_have_count(1)
        expect(info_messages.first).to_contain_text("Keine Animes gefunden")

def test_anime_list_card_navigation(navigate_to_anime_list, page: Page):
    """
    Testet, ob die Navigation durch Klick auf eine Anime-Karte funktioniert.
    
    Args:
        navigate_to_anime_list: Fixture, die zur Anime-Liste navigiert
        page: Die Playwright-Page-Instanz
    """
    # Auf Anime-Karten warten
    anime_cards = page.locator(".anime-card")
    
    # Wenn keine Anime-Karten vorhanden sind, Test überspringen
    if anime_cards.count() == 0:
        pytest.skip("Keine Anime-Karten gefunden zum Testen der Navigation")
    
    # Den Namen des ersten Animes speichern
    first_anime_name = page.locator(".anime-card .card-title").first.text_content()
    
    # Auf die erste Anime-Karte klicken
    anime_cards.first.click()
    
    # Prüfen, ob wir zur Detailseite des Animes navigiert sind
    expect(page).to_have_url(re.compile(".*\/anime\/\\d+"))
    
    # Prüfen, ob der Name des Animes in der Überschrift der Detailseite enthalten ist
    detail_headline = page.locator("h1").first
    expect(detail_headline).to_contain_text(first_anime_name)

def test_anime_list_breadcrumbs(navigate_to_anime_list, page: Page):
    """
    Testet, ob die Breadcrumb-Navigation korrekt funktioniert.
    
    Args:
        navigate_to_anime_list: Fixture, die zur Anime-Liste navigiert
        page: Die Playwright-Page-Instanz
    """
    # Prüfen, ob die Breadcrumbs vorhanden sind
    breadcrumbs = page.locator(".breadcrumb")
    expect(breadcrumbs).to_be_visible()
    
    # Prüfen, ob die Breadcrumb-Links korrekt sind
    home_link = page.locator(".breadcrumb-item a").first
    expect(home_link).to_contain_text("Startseite")
    
    # Auf den Startseite-Link klicken
    home_link.click()
    
    # Prüfen, ob wir zur Startseite navigiert sind
    expect(page).to_have_url(re.compile(".*\/$"))
