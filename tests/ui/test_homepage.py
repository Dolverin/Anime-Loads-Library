"""
UI-Tests für die Startseite des Anime-Loads Dashboards.
Diese Tests überprüfen grundlegende Funktionen der Startseite.
"""
import pytest
import re
from playwright.sync_api import Page, expect

def test_homepage_title(navigate_to_home, page: Page):
    """
    Testet, ob der Titel der Startseite korrekt ist.
    
    Args:
        navigate_to_home: Fixture, die zur Startseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Prüfen, ob der Seitentitel korrekt ist
    expect(page).to_have_title(re.compile("Startseite - Anime-Loads"))
    
    # Prüfen, ob die Hauptüberschrift korrekt ist
    headline = page.locator("h1").first
    expect(headline).to_be_visible()
    expect(headline).to_contain_text("Willkommen im Anime-Loads Dashboard")

def test_homepage_dashboard_cards(navigate_to_home, page: Page):
    """
    Testet, ob die Dashboard-Karten auf der Startseite korrekt angezeigt werden.
    
    Args:
        navigate_to_home: Fixture, die zur Startseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Prüfen, ob die Dashboard-Karten vorhanden sind
    cards = page.locator(".card")
    expect(cards).to_have_count(5, timeout=5000)  # Wir erwarten 5 Karten
    
    # Prüfen, ob die Hauptkarten-Titel korrekt sind
    expected_titles = [
        "Meine Anime-Sammlung",
        "Videoformate",
        "Auflösungen",
        "HDR-Formate",
        "Top Animes"
    ]
    
    for i, title in enumerate(expected_titles):
        if i < 4:  # Für die ersten 4 Karten
            card_title = page.locator(".card-title").nth(i)
            expect(card_title).to_contain_text(title)

def test_homepage_navigation_links(navigate_to_home, page: Page):
    """
    Testet, ob die Navigationslinks auf der Startseite funktionieren.
    
    Args:
        navigate_to_home: Fixture, die zur Startseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Auf "Alle Animes anzeigen" klicken
    page.locator("text=Alle Animes anzeigen").first.click()
    
    # Prüfen, ob wir zur Anime-Liste navigiert sind
    expect(page).to_have_url(re.compile(".*\/anime"))
    
    # Zurück zur Startseite navigieren
    page.go_back()
    
    # Auf "Detaillierte Statistiken" klicken
    page.locator("text=Detaillierte Statistiken").first.click()
    
    # Prüfen, ob wir zur Statistikseite navigiert sind
    expect(page).to_have_url(re.compile(".*\/stats"))

def test_homepage_charts_loaded(navigate_to_home, page: Page):
    """
    Testet, ob die Charts auf der Startseite korrekt geladen werden.
    
    Args:
        navigate_to_home: Fixture, die zur Startseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Warten, bis die Charts geladen sind (Canvas-Elemente)
    resolution_chart = page.locator("#resolutionChart")
    hdr_chart = page.locator("#hdrChart")
    
    # Prüfen, ob die Charts sichtbar sind
    expect(resolution_chart).to_be_visible(timeout=10000)
    expect(hdr_chart).to_be_visible(timeout=10000)
    
    # Prüfen, ob keine Fehlermeldungen angezeigt werden
    error_alerts = page.locator(".alert-danger")
    expect(error_alerts).to_have_count(0)

def test_homepage_top_animes_loaded(navigate_to_home, page: Page):
    """
    Testet, ob die Top-Animes-Liste auf der Startseite korrekt geladen wird.
    
    Args:
        navigate_to_home: Fixture, die zur Startseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Warten, bis die Top-Animes geladen sind
    top_animes_container = page.locator("#top-animes")
    expect(top_animes_container).to_be_visible()
    
    # Prüfen, ob keine Lade-Spinner mehr sichtbar sind
    spinners = page.locator(".spinner-border")
    expect(spinners).to_have_count(0, timeout=10000)
    
    # Es gibt entweder Anime-Einträge oder eine Info-Meldung
    anime_entries = page.locator("#top-animes .list-group-item")
    info_messages = page.locator("#top-animes .alert-info")
    
    # Entweder sollten Anime-Einträge oder eine Info-Meldung vorhanden sein
    has_entries = anime_entries.count() > 0
    has_info = info_messages.count() > 0
    
    assert has_entries or has_info, "Weder Anime-Einträge noch Info-Meldungen wurden gefunden"
