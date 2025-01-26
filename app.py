from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from PIL import Image
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from googleapiclient.discovery import build
import requests
from io import BytesIO
import secrets
import json
import shutil
import zipfile

# Umgebungsvariablen laden
load_dotenv()

# Flask-Anwendung initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Stelle sicher, dass der Upload-Ordner existiert
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Datenbank initialisieren
db = SQLAlchemy(app)

# Gemini Konfiguration
genai.configure(api_key=os.getenv('GEMINI_API_KEY', ''))

# Inventar-Artikel-Modell definieren
class InventoryItem(db.Model):
    """
    Datenbankmodell für einen Inventarartikel.
    Enthält alle relevanten Informationen wie Name, Kategorie, Standort, etc.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    image_filename = db.Column(db.String(255))

    def __repr__(self):
        """Gibt eine String-Repräsentation des Artikels zurück"""
        return f'<InventoryItem {self.name}>'

def process_image(file):
    """
    Verarbeitet ein hochgeladenes Bild mit verbesserter Fehlerbehandlung
    """
    if not file:
        return None
        
    try:
        # Generiere einen eindeutigen Dateinamen
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename.rsplit('.', 1)[0]}.webp"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Öffne und verarbeite das Bild
        with Image.open(file) as img:
            # Konvertiere zu RGB wenn nötig
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            # Berechne neue Größe unter Beibehaltung des Seitenverhältnisses
            if img.height > 600:
                ratio = 600 / img.height
                new_width = int(img.width * ratio)
                img = img.resize((new_width, 600), Image.Resampling.LANCZOS)
            
            # Speichere als WebP mit optimierten Einstellungen
            img.save(
                filepath, 
                'WEBP', 
                quality=85, 
                method=6,
                lossless=False,
                exact=True
            )
        
        return filename
    except Exception as e:
        print(f"Fehler bei der Bildverarbeitung: {str(e)}")
        return None

def verify_image(item):
    """
    Überprüft ob das Bild eines Artikels existiert und aktualisiert die Datenbank wenn nötig
    
    Args:
        item: Der zu überprüfende InventoryItem-Eintrag
    
    Returns:
        bool: True wenn das Bild existiert oder eine URL ist, False sonst
    """
    if not item or not item.image_filename:
        return False
        
    # Prüfe ob es eine vollständige URL ist
    if item.image_filename.startswith(('http://', 'https://')):
        return True
        
    # Prüfe ob die Bilddatei existiert
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
    if not os.path.exists(image_path):
        # Setze image_filename auf None wenn die Datei nicht existiert
        item.image_filename = None
        db.session.add(item)
        db.session.commit()
        return False
        
    return True

# Startseiten-Route definieren
@app.route('/')
def index():
    """Zeigt die Hauptseite mit allen Inventarartikeln an"""
    items = InventoryItem.query.all()
    
    # Überprüfe alle Bilder
    for item in items:
        verify_image(item)
    
    return render_template('index.html', items=items)

# Route für die Detailansicht eines Artikels
@app.route('/item/<int:item_id>')
def item_details(item_id):
    """
    Zeigt die Detailansicht eines einzelnen Artikels an
    
    Args:
        item_id: Die ID des anzuzeigenden Artikels
    """
    item = InventoryItem.query.filter_by(id=item_id).first()
    
    # Überprüfe das Bild
    verify_image(item)
    
    return render_template('item_details.html', item=item)

# Route zum Hinzufügen eines neuen Artikels
@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    """
    Verarbeitet das Hinzufügen eines neuen Artikels.
    GET: Zeigt das Formular an
    POST: Verarbeitet die Formulardaten und speichert den neuen Artikel
    """
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        location = request.form['location']
        quantity = request.form['quantity']
        description = request.form['description']
        
        # Bildverarbeitung
        image_filename = None
        
        # Prüfe zuerst auf ein hochgeladenes Bild
        image_file = request.files.get('image')
        if image_file:
            image_filename = process_image(image_file)
        # Wenn kein Bild hochgeladen wurde, prüfe auf ein Bild aus der Bildsuche
        elif request.form.get('selected_image_url'):
            image_filename = request.form.get('selected_image_url')

        new_item = InventoryItem(
            name=name,
            category=category,
            location=location,
            quantity=quantity,
            description=description,
            image_filename=image_filename
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_item.html')

# Route zum Löschen eines Artikels
@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    """
    Löscht einen Artikel und sein zugehöriges Bild
    
    Args:
        item_id: Die ID des zu löschenden Artikels
    """
    item = InventoryItem.query.get(item_id)
    if item:
        # Lösche das Bild, falls vorhanden
        if item.image_filename:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('index'))

# Route zum Aktualisieren eines Artikels
@app.route('/update/<int:item_id>', methods=['POST'])
def update_item(item_id):
    """
    Aktualisiert die Daten eines bestehenden Artikels
    
    Args:
        item_id: Die ID des zu aktualisierenden Artikels
    """
    item = InventoryItem.query.get(item_id)
    if item:
        item.name = request.form['name']
        item.category = request.form['category']
        item.description = request.form['description']
        item.location = request.form['location']
        item.quantity = request.form['quantity']

        # Bildverwaltung
        delete_image = request.form.get('delete_image')
        image_file = request.files.get('image')
        selected_image_url = request.form.get('selected_image_url')

        # Wenn das Bild gelöscht werden soll
        if delete_image:
            if item.image_filename:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            item.image_filename = None
        
        # Wenn ein neues Bild hochgeladen wurde
        elif image_file:
            # Lösche altes Bild, falls vorhanden
            if item.image_filename:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Verarbeite neues Bild
            item.image_filename = process_image(image_file)
        
        # Wenn ein Bild aus der Bildsuche ausgewählt wurde
        elif selected_image_url:
            # Lösche altes Bild, falls vorhanden
            if item.image_filename:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            item.image_filename = selected_image_url

        db.session.commit()
    return redirect(url_for('item_details', item_id=item_id))

# Route zum Bearbeiten eines Artikels
@app.route('/edit_item', methods=['GET'])
def edit_item():
    """
    Zeigt das Formular zum Bearbeiten eines Artikels an
    
    Args:
        id: Die ID des zu bearbeitenden Artikels (aus Query-Parametern)
    """
    item_id = request.args.get('id')
    item = InventoryItem.query.get(item_id)
    
    # Überprüfe das Bild
    verify_image(item)
    
    return render_template('edit_item.html', item=item)

# Route für die Suche
@app.route('/search', methods=['GET'])
def search_items():
    """
    Durchsucht die Artikel nach dem angegebenen Suchbegriff
    in Name, Kategorie, Standort und Beschreibung
    """
    query = request.args.get('query', '').strip()
    if query:
        # Suche in allen relevanten Feldern mit LIKE
        items = InventoryItem.query.filter(
            db.or_(
                InventoryItem.name.ilike(f'%{query}%'),
                InventoryItem.category.ilike(f'%{query}%'),
                InventoryItem.location.ilike(f'%{query}%'),
                InventoryItem.description.ilike(f'%{query}%')
            )
        ).all()
    else:
        items = InventoryItem.query.all()
    
    # Überprüfe alle Bilder
    for item in items:
        verify_image(item)
    
    return render_template('index.html', items=items)

# Standard-Prompt definieren
DEFAULT_PROMPT = """Generiere 3 sachliche Produktbeschreibungen für den Artikel "{name}". 
Bleibe dabei EXAKT in der Produktkategorie des Artikels - generiere keine Vorschläge für andere Produkttypen.

Der Titel sollte enthalten:
- Exakter Herstellername (hier: {name} - behalte diesen bei)
- Genaue Modellbezeichnung 
- Wichtigste technische Spezifikation

Die Beschreibung sollte enthalten:
- Technische Hauptmerkmale
- Spezifische Leistungsdaten
- Besondere Funktionen
- Kompatibilität/Anschlüsse

WICHTIG:
- Behalte den originalen Herstellernamen bei
- Generiere nur Varianten des GLEICHEN Produkts
- Keine anderen Produkte oder Hersteller vorschlagen
- Nur verifizierbare technische Fakten
- Keine Werbesprache oder Übertreibungen"""

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Einstellungen für die APIs verwalten"""
    if request.method == 'POST':
        # Aktuelle Werte laden
        env_content = {
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
            'GEMINI_MODEL': os.getenv('GEMINI_MODEL', 'gemini-1.0-pro'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY', ''),
            'GOOGLE_CSE_ID': os.getenv('GOOGLE_CSE_ID', ''),
            'CUSTOM_PROMPT': os.getenv('CUSTOM_PROMPT', DEFAULT_PROMPT)
        }
        
        # Neue Werte nur übernehmen, wenn sie nicht leer sind
        new_api_key = request.form.get('api_key', '').strip()
        new_model = request.form.get('model', '').strip()
        new_google_api_key = request.form.get('google_api_key', '').strip()
        new_google_cse_id = request.form.get('google_cse_id', '').strip()
        new_prompt = request.form.get('custom_prompt', '').strip()

        # Aktualisiere die Werte nur wenn sie nicht leer sind
        if new_api_key:
            env_content['GEMINI_API_KEY'] = new_api_key
        if new_model:
            env_content['GEMINI_MODEL'] = new_model
        if new_google_api_key:
            env_content['GOOGLE_API_KEY'] = new_google_api_key
        if new_google_cse_id:
            env_content['GOOGLE_CSE_ID'] = new_google_cse_id
        if new_prompt:
            env_content['CUSTOM_PROMPT'] = new_prompt
        
        # .env Datei aktualisieren
        with open('.env', 'w', encoding='utf-8') as f:
            for key, value in env_content.items():
                f.write(f'{key}={value}\n')
        
        # Umgebungsvariablen aktualisieren
        os.environ.update(env_content)
        
        # Gemini neu konfigurieren wenn ein neuer API Key gesetzt wurde
        if new_api_key:
            genai.configure(api_key=env_content['GEMINI_API_KEY'])
        
        flash('Einstellungen wurden gespeichert', 'success')
        return redirect(url_for('settings'))
    
    # Aktuelle Werte für die Anzeige laden
    return render_template('settings.html', 
                         api_key=os.getenv('GEMINI_API_KEY', ''),
                         current_model=os.getenv('GEMINI_MODEL', 'gemini-1.0-pro'),
                         google_api_key=os.getenv('GOOGLE_API_KEY', ''),
                         google_cse_id=os.getenv('GOOGLE_CSE_ID', ''),
                         custom_prompt=os.getenv('CUSTOM_PROMPT', DEFAULT_PROMPT),
                         default_prompt=DEFAULT_PROMPT)

@app.route('/generate_description', methods=['POST'])
def generate_description():
    """Generiert sachliche Vorschläge für Titel und Beschreibung mit Gemini"""
    try:
        import json
        data = request.get_json()
        name = data.get('name', '')
        
        if not os.getenv('GEMINI_API_KEY'):
            return jsonify({
                'error': 'Bitte konfigurieren Sie zuerst den Gemini API-Key in den Einstellungen.'
            }), 400
        
        # Gemini-Modell initialisieren
        model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.0-pro'))
        
        # Benutzerdefinierten Prompt laden oder Standard-Prompt verwenden
        user_prompt = os.getenv('CUSTOM_PROMPT', DEFAULT_PROMPT)
        
        # Technischen Teil des Prompts hinzufügen
        prompt = f"""{user_prompt.format(name=name)}

[
    {{
        "title": "{name} - Technische Details",
        "description": "• Technische Spezifikation\\n• Hauptmerkmal\\n• Besonderheit",
        "consumables": ["Benötigtes Zubehör 1", "Benötigtes Zubehör 2"]
    }}
]

WICHTIG: Antworte NUR mit dem JSON-Array. Behalte den Herstellernamen '{name}' in ALLEN Vorschlägen bei."""

        # Generierung durchführen
        response = model.generate_content(prompt)
        
        # Antwort bereinigen
        text = response.text.strip()
        print(f"Raw response: {text}")
        
        # JSON extrahieren (alles zwischen der ersten [ und letzten ])
        start = text.find('[')
        end = text.rfind(']') + 1
        
        if start >= 0 and end > start:
            json_text = text[start:end]
            print(f"Extracted JSON: {json_text}")
            
            try:
                # JSON parsen und validieren
                suggestions = json.loads(json_text)
                if isinstance(suggestions, list):
                    return jsonify(suggestions)
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {str(e)}")
        
        # Fallback mit originalem Produktnamen
        return jsonify([
            {
                "title": f"{name} - Standard Edition",
                "description": "• Originalprodukt\n• Standardausführung\n• Technische Details ergänzen",
                "consumables": []
            },
            {
                "title": f"{name} - Professional Version",
                "description": "• Originalprodukt\n• Professionelle Ausführung\n• Technische Details ergänzen",
                "consumables": []
            },
            {
                "title": f"{name} - Premium Ausführung",
                "description": "• Originalprodukt\n• Premium Edition\n• Technische Details ergänzen",
                "consumables": []
            }
        ])
            
    except Exception as e:
        print(f"Error in generate_description: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/search_images', methods=['POST'])
def search_images():
    """Sucht nach passenden Bildern für einen Artikel"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not os.getenv('GOOGLE_CSE_ID') or not os.getenv('GOOGLE_API_KEY'):
            return jsonify({
                'error': 'Bitte konfigurieren Sie den Google Custom Search API-Key in den Einstellungen.'
            }), 400
            
        service = build(
            "customsearch", "v1",
            developerKey=os.getenv('GOOGLE_API_KEY')
        )
        
        result = service.cse().list(
            q=query,
            cx=os.getenv('GOOGLE_CSE_ID'),
            searchType='image',
            num=5,
            imgSize='LARGE',
            safe='active'
        ).execute()
        
        images = []
        for item in result.get('items', []):
            image_url = item.get('link')
            thumbnail_url = item.get('image', {}).get('thumbnailLink')
            title = item.get('title', '')
            
            try:
                response = requests.head(image_url, timeout=2)
                if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                    images.append({
                        'url': image_url,
                        'thumbnail': thumbnail_url,
                        'title': title
                    })
            except:
                continue
                
        return jsonify(images)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def download_and_process_image(url):
    """
    Lädt ein Bild von einer URL herunter und verarbeitet es mit verbesserter Fehlerbehandlung
    """
    try:
        response = requests.get(url, timeout=5, stream=True)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_gcp{os.urandom(12).hex()}.webp"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            with Image.open(img_data) as img:
                # Konvertiere zu RGB wenn nötig
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Berechne neue Größe
                if img.height > 600:
                    ratio = 600 / img.height
                    new_width = int(img.width * ratio)
                    img = img.resize((new_width, 600), Image.Resampling.LANCZOS)
                
                # Speichere als WebP mit optimierten Einstellungen
                img.save(
                    filepath, 
                    'WEBP', 
                    quality=85, 
                    method=6,
                    lossless=False,
                    exact=True
                )
                
                return filename
    except Exception as e:
        print(f"Fehler beim Herunterladen/Verarbeiten des Bildes: {str(e)}")
        return None

@app.route('/save_image_from_url', methods=['POST'])
def save_image_from_url():
    """Speichert ein Bild von einer URL"""
    try:
        data = request.get_json()
        image_url = data.get('url')
        
        if not image_url:
            return jsonify({'error': 'Keine Bild-URL angegeben'}), 400
            
        filename = download_and_process_image(image_url)
        if filename:
            return jsonify({'filename': filename})
        else:
            return jsonify({'error': 'Bild konnte nicht verarbeitet werden'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/statistics')
def statistics():
    """Zeigt Statistiken über das Inventar"""
    try:
        # Grundlegende Statistiken in einer Query
        stats = db.session.query(
            db.func.count(InventoryItem.id).label('total_items'),
            db.func.sum(InventoryItem.quantity).label('total_quantity'),
            db.func.count(InventoryItem.image_filename).label('items_with_images')
        ).first()
        
        total_items = stats[0]
        total_quantity = stats[1] or 0
        items_with_images = stats[2]
        items_without_images = total_items - items_with_images
        
        # Kategorien und Standorte in einer Query
        categories = db.session.query(
            InventoryItem.category,
            db.func.count(InventoryItem.id).label('count'),
            db.func.sum(InventoryItem.quantity).label('total_quantity')
        ).group_by(InventoryItem.category).all()
        
        locations = db.session.query(
            InventoryItem.location,
            db.func.count(InventoryItem.id).label('count'),
            db.func.sum(InventoryItem.quantity).label('total_quantity')
        ).group_by(InventoryItem.location).all()
        
        # Dateigrößen effizient berechnen
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'inventory.db')
        db_size = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0
        
        total_image_size = sum(
            os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], f))
            for f in os.listdir(app.config['UPLOAD_FOLDER'])
            if f.endswith('.webp')
        ) / (1024 * 1024) if os.path.exists(app.config['UPLOAD_FOLDER']) else 0
        
        # Chartdaten vorbereiten
        category_data = {
            'labels': [cat[0] for cat in categories],
            'counts': [cat[1] for cat in categories],
            'quantities': [cat[2] for cat in categories]
        }
        
        location_data = {
            'labels': [loc[0] for loc in locations],
            'counts': [loc[1] for loc in locations],
            'quantities': [loc[2] for loc in locations]
        }
        
        image_stats = {
            'with_images': items_with_images,
            'without_images': items_without_images
        }
        
        return render_template('statistics.html',
                             total_items=total_items,
                             total_quantity=total_quantity,
                             category_data=category_data,
                             location_data=location_data,
                             image_stats=image_stats,
                             db_size=round(db_size, 2),
                             total_image_size=round(total_image_size, 2))
    except Exception as e:
        return f"Fehler beim Laden der Statistiken: {str(e)}", 500

@app.route('/static/uploads/<path:filename>')
def serve_image(filename):
    """
    Optimierte Auslieferung von Bildern mit korrekten Headers und verbesserter Fehlerbehandlung
    """
    try:
        if not filename:
            print("Kein Dateiname angegeben")
            return '', 404
            
        # Sicherheitscheck für den Dateinamen
        if '..' in filename or filename.startswith('/'):
            print("Ungültiger Dateipfad")
            return '', 404
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_path = os.path.abspath(file_path)
        
        # Prüfe ob der Pfad im Upload-Ordner liegt
        if not file_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            print("Pfad außerhalb des Upload-Ordners")
            return '', 404
            
        if not os.path.exists(file_path):
            print(f"Datei nicht gefunden: {filename}")
            # Bereinige die Datenbank
            items = InventoryItem.query.filter_by(image_filename=filename).all()
            for item in items:
                item.image_filename = None
                db.session.add(item)
            db.session.commit()
            return '', 404
            
        if not os.path.isfile(file_path):
            print(f"Pfad ist keine Datei: {filename}")
            return '', 404
            
        try:
            # Prüfe ob es ein gültiges Bild ist
            with Image.open(file_path) as img:
                format = img.format.lower()
                if format not in ['webp', 'jpeg', 'jpg', 'png']:
                    print(f"Ungültiges Bildformat: {format}")
                    return '', 404
        except Exception as e:
            print(f"Fehler beim Bildlesen: {str(e)}")
            return '', 404

        # Setze explizit den MIME-Type basierend auf der Dateiendung
        mime_type = 'image/webp'
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.lower().endswith('.png'):
            mime_type = 'image/png'

        # Hole den Datei-Zeitstempel
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime)

        # Prüfe If-Modified-Since Header
        if_modified_since = request.headers.get('If-Modified-Since')
        if if_modified_since:
            try:
                if_modified_since = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                if last_modified <= if_modified_since:
                    return '', 304
            except ValueError:
                pass

        response = send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            mimetype=mime_type,
            as_attachment=False,
            max_age=43200,  # 12 Stunden Cache
            conditional=True,
            last_modified=last_modified
        )
        
        # Optimierte Cache-Header
        response.headers['Cache-Control'] = 'public, max-age=43200, must-revalidate'
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['Accept-Ranges'] = 'bytes'
        
        return response
        
    except Exception as e:
        print(f"Fehler beim Laden des Bildes {filename}: {str(e)}")
        return '', 404

@app.route('/backup', methods=['POST'])
def create_backup():
    """Erstellt ein Backup der Datenbank und Bilder"""
    try:
        # Erstelle einen temporären BytesIO-Buffer für das ZIP
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Exportiere Datenbank-Einträge als JSON
            items = InventoryItem.query.all()
            items_data = []
            for item in items:
                items_data.append({
                    'name': item.name,
                    'category': item.category,
                    'location': item.location,
                    'quantity': item.quantity,
                    'description': item.description,
                    'image_filename': item.image_filename
                })
            
            # Speichere JSON in ZIP
            zip_file.writestr('inventory.json', json.dumps(items_data, indent=2))
            
            # Füge Bilder hinzu
            for item in items:
                if item.image_filename and not item.image_filename.startswith(('http://', 'https://')):
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
                    if os.path.exists(image_path):
                        zip_file.write(image_path, f"images/{item.image_filename}")
            
            # Füge .env Datei hinzu wenn sie existiert
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            if os.path.exists(env_path):
                zip_file.write(env_path, '.env')

        # Setze Pointer auf Anfang des Buffers
        zip_buffer.seek(0)
        
        # Generiere Dateinamen mit Zeitstempel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"inventarium_backup_{timestamp}.zip"
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/restore', methods=['POST'])
def restore_backup():
    """Stellt ein Backup wieder her"""
    try:
        if 'backup_file' not in request.files:
            return jsonify({'error': 'Keine Backup-Datei hochgeladen'}), 400
            
        backup_file = request.files['backup_file']
        if not backup_file.filename.endswith('.zip'):
            return jsonify({'error': 'Ungültiges Dateiformat. Nur ZIP-Dateien erlaubt.'}), 400
            
        # Erstelle temporären Ordner für die Wiederherstellung
        temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_restore')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Extrahiere ZIP
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Lade JSON-Daten
            with open(os.path.join(temp_dir, 'inventory.json'), 'r') as f:
                items_data = json.load(f)
            
            # Lösche bestehende Daten
            InventoryItem.query.delete()
            
            # Lösche bestehende Bilder
            for file in os.listdir(app.config['UPLOAD_FOLDER']):
                if file.endswith(('.webp', '.jpg', '.jpeg', '.png')):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
                    except:
                        pass
            
            # Stelle Bilder wieder her
            if os.path.exists(os.path.join(temp_dir, 'images')):
                for image in os.listdir(os.path.join(temp_dir, 'images')):
                    src = os.path.join(temp_dir, 'images', image)
                    dst = os.path.join(app.config['UPLOAD_FOLDER'], image)
                    shutil.copy2(src, dst)
            
            # Stelle .env Datei wieder her wenn vorhanden
            env_src = os.path.join(temp_dir, '.env')
            if os.path.exists(env_src):
                env_dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                shutil.copy2(env_src, env_dst)
                # Lade neue Umgebungsvariablen
                load_dotenv()
            
            # Stelle Datenbankeinträge wieder her
            for item_data in items_data:
                item = InventoryItem(**item_data)
                db.session.add(item)
            
            db.session.commit()
            
            return jsonify({'message': 'Backup erfolgreich wiederhergestellt'})
            
        finally:
            # Aufräumen
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Datenbank beim Start initialisieren
def init_db():
    with app.app_context():
        db.create_all()
        print("Datenbank wurde initialisiert.")

# Anwendung starten
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
