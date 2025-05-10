#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hilfsskript zum Ausführen der UI-Tests mit Playwright.
"""

import os
import sys
import argparse
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description='UI-Tests für das Anime-Loads Dashboard ausführen')
    parser.add_argument('--headed', action='store_true', help='Tests mit sichtbarem Browser ausführen')
    parser.add_argument('--slow', action='store_true', help='Tests langsamer ausführen (nützlich für Debugging)')
    parser.add_argument('--test', '-t', default=None, 
                        help='Spezifischer Test, der ausgeführt werden soll (z.B. test_homepage)')
    return parser.parse_args()

def run_tests(args):
    # Testverzeichnis ermitteln
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(current_dir, 'tests', 'ui')
    
    # Befehl zusammenstellen
    command = [sys.executable, '-m', 'pytest']
    
    # Optionen hinzufügen
    command.append('-v')  # Immer ausführliche Ausgabe für UI-Tests
    
    if args.headed:
        command.append('--headed')
    
    if args.slow:
        command.append('--slowmo=500')
    
    # Spezifischen Test auswählen oder alle UI-Tests ausführen
    if args.test:
        command.append(f'tests/ui/test_{args.test}.py')
    else:
        command.append('tests/ui/')
    
    # Tests ausführen
    try:
        print(f"Führe UI-Tests aus: {' '.join(command)}")
        # Prüfen, ob Playwright installiert ist
        try:
            subprocess.run([sys.executable, '-m', 'playwright', 'install'], check=True)
            print("Playwright-Browser erfolgreich installiert/aktualisiert.")
        except subprocess.CalledProcessError:
            print("Fehler bei der Installation der Playwright-Browser.")
            return
        
        # UI-Tests ausführen
        subprocess.run(command, check=True)
        print("\n✅ UI-Tests erfolgreich abgeschlossen!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Fehler beim Ausführen der UI-Tests: {e}")
        sys.exit(1)

if __name__ == '__main__':
    args = parse_args()
    run_tests(args)
