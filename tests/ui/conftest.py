"""
Konfigurationsdatei für Playwright-UI-Tests.
Diese Datei enthält Fixtures und Konfigurationen für die UI-Tests mit Playwright.
"""
import os
import sys
import pytest
import time
from playwright.sync_api import Playwright, Page, BrowserContext, Browser, sync_playwright

# Pfad zum Hauptverzeichnis des Projekts hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import der Hauptanwendung für das Starten eines Testservers
from simple_dashboard import app

# Standard-Port für den Test-Server
TEST_PORT = 5050
BASE_URL = f"http://localhost:{TEST_PORT}"

# Globale Variable für den Server-Prozess
server_process = None

@pytest.fixture(scope="session")
def start_test_server():
    """
    Startet den Flask-Server für Tests.
    Wird einmal pro Testsession ausgeführt.
    """
    import multiprocessing
    
    def run_server():
        app.run(host="localhost", port=TEST_PORT, debug=False)
    
    # Server in einem separaten Prozess starten
    global server_process
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()
    
    # Kurz warten, damit der Server Zeit hat zu starten
    time.sleep(2)
    
    yield
    
    # Server nach den Tests beenden
    if server_process and server_process.is_alive():
        server_process.terminate()
        server_process.join(timeout=1)

@pytest.fixture(scope="session")
def browser_context_args():
    """
    Konfiguration für den Browser-Kontext.
    """
    return {
        "viewport": {
            "width": 1280,
            "height": 720
        },
        "ignore_https_errors": True,
        "java_script_enabled": True,
    }

@pytest.fixture(scope="session")
def browser_type_launch_args():
    """
    Konfiguration für den Browser-Start.
    """
    return {
        "headless": True,
        "slow_mo": 50,
    }

@pytest.fixture(scope="function")
def page(browser: Browser, start_test_server):
    """
    Erstellt eine neue Seite für jeden Test.
    Stellt sicher, dass der Testserver läuft.
    """
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)  # 10 Sekunden Timeout
    
    yield page
    
    context.close()

@pytest.fixture(scope="function")
def navigate_to_home(page: Page):
    """
    Navigiert zur Startseite und stellt sicher, dass sie geladen wurde.
    """
    page.goto(BASE_URL)
    page.wait_for_selector("h1")  # Warten auf eine Überschrift
    
    return page

@pytest.fixture(scope="function")
def navigate_to_anime_list(page: Page):
    """
    Navigiert zur Anime-Liste und stellt sicher, dass sie geladen wurde.
    """
    page.goto(f"{BASE_URL}/anime")
    page.wait_for_selector(".card")  # Warten auf eine Karten-Komponente
    
    return page

@pytest.fixture(scope="function")
def navigate_to_stats(page: Page):
    """
    Navigiert zur Statistikseite und stellt sicher, dass sie geladen wurde.
    """
    page.goto(f"{BASE_URL}/stats")
    page.wait_for_selector("canvas")  # Warten auf ein Canvas-Element (Chart)
    
    return page
