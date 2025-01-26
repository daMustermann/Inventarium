"""
Produktions-WSGI-Server mit Waitress

Dieser Server bietet:
- Verbesserte Performance durch Multi-Threading
- Robuste Fehlerbehandlung
- Sicherheitsoptimierungen
- Geeignet für Produktivbetrieb
- Erreichbar im lokalen Netzwerk

Verwendung:
    python wsgi.py
"""

from waitress import serve
from app import app, init_db

# Datenbank initialisieren
init_db()

if __name__ == '__main__':
    print("Starting Waitress production server...")
    print("Server is running at:")
    print("- Local:   http://127.0.0.1:5000")
    print("- Network: http://0.0.0.0:5000")
    print("Use Ctrl+C to stop")
    
    # Konfiguration für Waitress
    serve(app,
          host='0.0.0.0',           # Auf allen Netzwerkinterfaces verfügbar
          port=5000,                # Port
          threads=4,                # Anzahl der Threads
          channel_timeout=120,      # Timeout in Sekunden
          cleanup_interval=30,      # Aufräumintervall
          ident='Inventarium')      # Server-Identifikation
