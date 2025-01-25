from waitress import serve
from app import app

if __name__ == '__main__':
    # Konfiguration für Waitress
    serve(app,
          host='127.0.0.1',          # Localhost
          port=5000,                 # Port
          threads=4,                 # Anzahl der Threads
          channel_timeout=120,       # Timeout in Sekunden
          cleanup_interval=30,       # Aufräumintervall
          ident='Inventarium')       # Server-Identifikation 
