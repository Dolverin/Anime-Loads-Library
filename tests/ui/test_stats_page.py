"""
UI-Tests für die Statistikseite des Anime-Loads Dashboards.
Diese Tests überprüfen die Funktionalität der Statistikseite mit Charts und Datenvisualisierungen.
"""
import pytest
import re
from playwright.sync_api import Page, expect

def test_stats_page_title(navigate_to_stats, page: Page):
    """
    Testet, ob der Titel der Statistikseite korrekt ist.
    
    Args:
        navigate_to_stats: Fixture, die zur Statistikseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Prüfen, ob der Seitentitel korrekt ist
    expect(page).to_have_title("Statistiken - Anime-Loads Dashboard")
    
    # Prüfen, ob die Hauptüberschrift korrekt ist
    headline = page.locator("h1").first
    expect(headline).to_be_visible()
    expect(headline).to_contain_text("Statistiken")

def test_stats_page_charts_loaded(navigate_to_stats, page: Page):
    """
    Testet, ob die Charts auf der Statistikseite korrekt geladen werden.
    
    Args:
        navigate_to_stats: Fixture, die zur Statistikseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Alle Canvas-Elemente (Charts) auf der Seite finden
    charts = page.locator("canvas")
    
    # Es sollten mehrere Charts vorhanden sein
    chart_count = charts.count()
    assert chart_count > 0, "Keine Chart-Elemente auf der Statistikseite gefunden"
    
    # Prüfen, ob alle Canvas-Elemente sichtbar sind
    for i in range(chart_count):
        chart = charts.nth(i)
        expect(chart).to_be_visible(timeout=10000)
    
    # Prüfen, ob keine Fehlermeldungen angezeigt werden
    error_alerts = page.locator(".alert-danger")
    expect(error_alerts).to_have_count(0)

def test_stats_page_tabs(navigate_to_stats, page: Page):
    """
    Testet, ob die Tabs auf der Statistikseite funktionieren.
    
    Args:
        navigate_to_stats: Fixture, die zur Statistikseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Tabs finden
    tabs = page.locator(".nav-link")
    
    # Es sollten mehrere Tabs vorhanden sein
    tab_count = tabs.count()
    assert tab_count > 0, "Keine Tabs auf der Statistikseite gefunden"
    
    # Durch alle Tabs klicken und prüfen, ob der entsprechende Inhalt angezeigt wird
    for i in range(tab_count):
        tab = tabs.nth(i)
        tab_id = tab.get_attribute("href").split("#")[1]
        
        # Auf den Tab klicken
        tab.click()
        
        # Prüfen, ob der entsprechende Tab-Inhalt sichtbar ist
        tab_content = page.locator(f"#{tab_id}")
        expect(tab_content).to_be_visible()
        
        # Prüfen, ob der Tab als aktiv markiert ist
        expect(tab).to_have_class(re.compile(".*active.*"))

def test_stats_page_resolution_chart(navigate_to_stats, page: Page):
    """
    Testet den Auflösungs-Chart auf der Statistikseite.
    
    Args:
        navigate_to_stats: Fixture, die zur Statistikseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Zum Auflösungs-Tab navigieren (falls nicht automatisch aktiv)
    resolution_tab = page.locator(".nav-link").filter(has_text="Auflösungen")
    resolution_tab.click()
    
    # Auf den Auflösungs-Chart warten
    resolution_chart = page.locator("#resolutionChart")
    expect(resolution_chart).to_be_visible(timeout=10000)
    
    # Prüfen, ob die Legende des Charts angezeigt wird
    chart_legend = page.locator(".chart-container").filter(has_text="Auflösungen").locator(".chart-legend")
    
    # Es kann sein, dass die Chart-Bibliothek unterschiedliche Strukturen hat
    # daher prüfen wir auf verschiedene Möglichkeiten
    if chart_legend.count() > 0:
        expect(chart_legend).to_be_visible()
    else:
        # Wenn keine separate Legende, dann prüfen wir auf Canvas-Größe
        canvas_size = resolution_chart.evaluate("el => { return {width: el.width, height: el.height}; }")
        assert canvas_size["width"] > 0 and canvas_size["height"] > 0, "Chart-Canvas hat ungültige Größe"

def test_stats_page_codec_chart(navigate_to_stats, page: Page):
    """
    Testet den Codec-Chart auf der Statistikseite.
    
    Args:
        navigate_to_stats: Fixture, die zur Statistikseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Zum Codec-Tab navigieren
    codec_tab = page.locator(".nav-link").filter(has_text="Codecs")
    codec_tab.click()
    
    # Auf den Codec-Chart warten
    codec_chart = page.locator("#codecChart")
    expect(codec_chart).to_be_visible(timeout=10000)
    
    # Prüfen, ob der Chart-Container vorhanden ist
    chart_container = page.locator(".chart-container").filter(has_text="Codec-Verteilung")
    expect(chart_container).to_be_visible()
    
    # Prüfen, ob keine Fehlermeldungen angezeigt werden
    error_messages = chart_container.locator(".alert-danger")
    expect(error_messages).to_have_count(0)

def test_stats_page_responsive_layout(navigate_to_stats, page: Page):
    """
    Testet, ob die Statistikseite ein responsives Layout hat.
    
    Args:
        navigate_to_stats: Fixture, die zur Statistikseite navigiert
        page: Die Playwright-Page-Instanz
    """
    # Standardgröße beibehalten und Layout prüfen
    container = page.locator(".container")
    expect(container).to_be_visible()
    
    # Viewport auf Smartphone-Größe setzen
    page.set_viewport_size({"width": 480, "height": 720})
    
    # Kurz warten, damit das Layout angepasst werden kann
    page.wait_for_timeout(1000)
    
    # Prüfen, ob die Container noch sichtbar sind
    container = page.locator(".container")
    expect(container).to_be_visible()
    
    # Prüfen, ob die Tabs jetzt übereinander sind (Smartphone-Layout)
    tab_list = page.locator(".nav-tabs")
    tab_list_box = tab_list.bounding_box()
    
    # Die Breite der Tabs sollte kleiner sein als auf dem Desktop
    assert tab_list_box["width"] <= 480, "Tabs sind nicht responsive"
