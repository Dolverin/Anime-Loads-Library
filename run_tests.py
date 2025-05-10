#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hilfsskript zum einfachen Ausführen der API-Tests.
"""

import os
import sys
import argparse
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description='API-Tests für das Anime-Loads Dashboard ausführen')
    parser.add_argument('--verbose', '-v', action='store_true', help='Ausführliche Ausgabe')
    parser.add_argument('--test', '-t', default=None, 
                        help='Spezifischer Test, der ausgeführt werden soll (z.B. test_api_stats)')
    parser.add_argument('--module', '-m', default=None,
                        help='Spezifisches Testmodul, das ausgeführt werden soll (z.B. api_stats)')
    return parser.parse_args()

def run_tests(args):
    # Testverzeichnis ermitteln
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(current_dir, 'tests')
    
    # Befehl zusammenstellen
    command = [sys.executable, '-m', 'pytest']
    
    # Verbose-Option hinzufügen
    if args.verbose:
        command.append('-v')
    
    # Spezifisches Testmodul oder Testfunktion auswählen
    if args.module:
        command.append(f'tests/test_{args.module}.py')
    elif args.test:
        command.append(f'tests/test_{args.test}.py')
    else:
        command.append('tests/')
    
    # Tests ausführen
    try:
        print(f"Führe Befehl aus: {' '.join(command)}")
        subprocess.run(command, check=True)
        print("\n✅ Tests erfolgreich abgeschlossen!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Fehler beim Ausführen der Tests: {e}")
        sys.exit(1)

if __name__ == '__main__':
    args = parse_args()
    run_tests(args)
