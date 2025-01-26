# 📦 Inventarium

Eine moderne Inventarverwaltung mit KI-Unterstützung und intuitiver Benutzeroberfläche.
Entwickelt von daMustermann.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![License](https://img.shields.io/badge/Lizenz-MIT-yellow)

## ✨ Features

- 🎨 Modernes, responsives Design mit Dark Mode
- 🤖 KI-gestützte Vorschläge für Artikelbeschreibungen
- 🔍 Integrierte Bildersuche für Artikel
- 📊 Detaillierte Statistiken und Visualisierungen
- 📱 Optimiert für Desktop und Mobile
- 🔄 Einfache Artikel-Verwaltung (Hinzufügen, Bearbeiten, Löschen)
- 📷 Bildverwaltung mit automatischer Optimierung
- 💾 Backup & Restore System für alle Daten
- 🔐 Sichere Speicherung von API-Keys und Einstellungen

## 🚀 Installation

### Windows

1. **Python installieren**
   - Laden Sie Python 3.8 oder höher von [python.org](https://python.org) herunter
   - Aktivieren Sie bei der Installation die Option "Add Python to PATH"

2. **Repository klonen**
   ```bash
   git clone https://github.com/IHR_USERNAME/Inventarium.git
   cd Inventarium
   ```

3. **Virtuelle Umgebung erstellen und aktivieren**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

4. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

### Linux/Raspberry Pi

1. **Erforderliche Pakete installieren**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git
   ```

2. **Repository klonen**
   ```bash
   git clone https://github.com/IHR_USERNAME/Inventarium.git
   cd Inventarium
   ```

3. **Virtuelle Umgebung erstellen und aktivieren**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Konfiguration

1. **Umgebungsvariablen einrichten**
   - Starten Sie die Anwendung
   - Gehen Sie zu "Einstellungen"
   - Tragen Sie Ihre API-Schlüssel ein:
     - GEMINI_API_KEY (für KI-Vorschläge)
     - GOOGLE_API_KEY und GOOGLE_CSE_ID (für Bildersuche)
   - Klicken Sie auf "Einstellungen speichern"

2. **Anwendung starten**

   **Entwicklungsserver (app.py)**
   ```bash
   python app.py
   ```
   - Vorteile:
     - Auto-Reload bei Code-Änderungen
     - Detaillierte Debug-Informationen
     - Interaktive Debugger-Konsole
   - Nachteile:
     - Nicht für Produktivbetrieb geeignet
     - Eingeschränkte Performance
     - Keine Sicherheitsoptimierungen
   - Verwendung:
     - Während der Entwicklung
     - Zum Testen von Änderungen
     - Für lokale Debugging-Zwecke

   **Produktionsserver (wsgi.py)**
   ```bash
   python wsgi.py
   ```
   - Vorteile:
     - Optimierte Performance
     - Multi-Threading Support
     - Robuste Fehlerbehandlung
     - Sicherheitsoptimierungen
   - Nachteile:
     - Kein Auto-Reload
     - Weniger Debug-Informationen
   - Verwendung:
     - Im Produktivbetrieb
     - Für den dauerhaften Einsatz
     - Wenn mehrere Benutzer zugreifen

   Die Anwendung ist unter `http://localhost:5000` erreichbar.

## 📱 Funktionen

### Artikel verwalten

- **Artikel hinzufügen**: 
  - Klicken Sie auf "Artikel hinzufügen"
  - Füllen Sie die Pflichtfelder aus
  - Nutzen Sie die KI für Beschreibungsvorschläge
  - Fügen Sie ein Bild hinzu (Upload oder Bildersuche)

- **Artikel bearbeiten**:
  - Klicken Sie auf einen Artikel
  - Wählen Sie "Bearbeiten"
  - Aktualisieren Sie die gewünschten Felder

- **Artikel löschen**:
  - Öffnen Sie die Artikeldetails
  - Klicken Sie auf "Löschen"
  - Bestätigen Sie die Aktion

### KI-Funktionen

- **Beschreibungsvorschläge**:
  - Geben Sie den Artikelnamen ein
  - Klicken Sie auf "KI-Vorschläge generieren"
  - Wählen Sie einen passenden Vorschlag aus

- **Bildersuche**:
  - Klicken Sie auf "Nach Bildern suchen"
  - Geben Sie Suchbegriffe ein
  - Wählen Sie ein passendes Bild aus

### Backup & Restore

- **Backup erstellen**:
  - Gehen Sie zu "Einstellungen"
  - Klicken Sie auf "Backup herunterladen"
  - Das Backup enthält:
    - Alle Datenbank-Einträge
    - Alle Bilder
    - Alle Einstellungen (.env Datei)

- **Backup wiederherstellen**:
  - Gehen Sie zu "Einstellungen"
  - Wählen Sie eine Backup-Datei aus
  - Klicken Sie auf "Wiederherstellen"
  - Das System wird automatisch neu geladen

### Statistiken

- Klicken Sie auf "Statistiken" für:
  - Gesamtübersicht der Artikel
  - Verteilung nach Kategorien
  - Verteilung nach Standorten
  - Systemstatistiken
  - Bildabdeckung
  - Speichernutzung

## 🎨 Design-Anpassung

- Dark Mode optimiert für bessere Lesbarkeit
- Responsive Design für alle Bildschirmgrößen
- Optimierte Darstellung auf mobilen Geräten
- Verbesserte Kontraste und Farbschema

## 🔧 Fehlerbehebung

### Häufige Probleme

1. **Datenbank-Fehler**
   - Stellen Sie sicher, dass der `instance` Ordner existiert
   - Überprüfen Sie die Schreibrechte

2. **API-Fehler**
   - Überprüfen Sie die API-Schlüssel in der `.env` Datei
   - Stellen Sie sicher, dass die APIs aktiviert sind

3. **Bildupload-Probleme**
   - Überprüfen Sie die Schreibrechte im `static/uploads` Ordner
   - Maximale Bildgröße beachten (10MB)

4. **Backup/Restore-Probleme**
   - Stellen Sie sicher, dass genügend Speicherplatz vorhanden ist
   - Überprüfen Sie die Schreibrechte für die .env Datei
   - Backup-Datei muss im ZIP-Format sein

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Weitere Details finden Sie in der [LICENSE](LICENSE) Datei.

## 🤝 Mitwirken

Beiträge sind willkommen! Bitte lesen Sie [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

## 📞 Support

Bei Fragen oder Problemen:
- Erstellen Sie ein Issue auf GitHub