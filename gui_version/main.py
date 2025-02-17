import os
import subprocess
import zipfile
import shutil
import threading
import pickle
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='template')

class LogManager:
    _instance = None
    _log_file = "log_storage.pkl"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance.messages = []
            cls._instance.progress = 0
            if os.path.exists(cls._log_file):
                with open(cls._log_file, 'rb') as f:
                    cls._instance.messages = pickle.load(f)
        return cls._instance
    
    def append(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.messages.append(f"[{timestamp}] {message}")
        with open(self._log_file, 'wb') as f:
            pickle.dump(self.messages, f)
    
    def clear(self):
        self.messages = []
        if os.path.exists(self._log_file):
            os.remove(self._log_file)
    
    def set_progress(self, value):
        self.progress = value
    
    def get_logs(self):
        return self.messages

log_manager = LogManager()


def download_with_progress(url, zip_path):
    try:
        log_manager.append(f"Tentativo di download da: {url}")
        
        # Usa wget per il download
        wget_command = [
            'wget',
            '--user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"',
            '--referer=https://www.agenziaentrate.gov.it/',
            '--progress=bar:force',
            '-O', zip_path,
            url
        ]
        
        # Esegui wget
        process = subprocess.Popen(
            wget_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Aspetta il completamento
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Wget error: {stderr}")
            
        # Verifica il file
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
            raise Exception("Download fallito: file vuoto o mancante")
            
        file_size = os.path.getsize(zip_path)
        log_manager.append(f"Download completato: {file_size/1024/1024:.2f} MB")
        
        # Verifica ZIP
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.testzip()
        except zipfile.BadZipFile:
            raise Exception("Il file scaricato non è un file ZIP valido")
            
        return True
        
    except Exception as e:
        log_manager.append(f"Errore durante il download: {str(e)}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise


def extract_all_zips(root_dir):
    """
    Estrae ricorsivamente tutti i file ZIP contenuti in root_dir.
    Restituisce True se l'estrazione ha modificato la struttura (cioè se sono stati processati ZIP).
    """
    extraction_done = False
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".zip"):
                zip_path = os.path.join(root, file)
                try:
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        contents = zip_ref.namelist()
                        log_manager.append(f"Contenuto ZIP: {contents}")
                        zip_ref.extractall(root)
                        log_manager.append(f"Estratto contenuto di: {file}")
                    os.remove(zip_path)
                    log_manager.append(f"Rimosso ZIP: {file}")
                    extraction_done = True
                except Exception as e:
                    log_manager.append(f"Errore nell'estrazione di {file}: {str(e)}")
    return extraction_done

def process_gml(root_dir, fogli_dir, mappali_dir):
    """
    Cerca in root_dir tutti i file GML e li copia nelle directory di destinazione.
    Restituisce il totale dei file GML processati.
    """
    total_gml = 0
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".gml"):
                file_path = os.path.join(root, file)
                try:
                    if "_ple.gml" in file:
                        dest = os.path.join(fogli_dir, file)
                        shutil.copy2(file_path, dest)
                        total_gml += 1
                        log_manager.append(f"Copiato foglio: {file}")
                    elif "_map.gml" in file:
                        dest = os.path.join(mappali_dir, file)
                        shutil.copy2(file_path, dest)
                        total_gml += 1
                        log_manager.append(f"Copiato mappale: {file}")
                except Exception as e:
                    log_manager.append(f"Errore nella copia di {file}: {str(e)}")
    return total_gml

def download_and_process(regioni):
    total_regioni = len(regioni)
    processed_regioni = 0
    
    # Dizionario per gestire regioni speciali
    regioni_speciali = {
        "EMILIA": "EMILIA-ROMAGNA",
        "FRIULI": "FRIULI-VENEZIA-GIULIA",
        "AOSTA": "VALLE-AOSTA",
        "VALLE D'AOSTA": "VALLE-AOSTA",
        "VALDAOSTA": "VALLE-AOSTA",
    }

    # Creazione directory necessarie
    root_dir = "catasto_italia/tmp_folder"
    os.makedirs(f"{root_dir}/temp_extract", exist_ok=True)
    os.makedirs("catasto_italia/sorgenti", exist_ok=True)
    os.makedirs("catasto_italia/fogli", exist_ok=True)
    os.makedirs("catasto_italia/mappali", exist_ok=True)

    for regione in regioni:
        regione = regioni_speciali.get(regione, regione)
        log_manager.append(f"Download vettoriale regionale: {regione}")

        url = f"https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/GetDataset.php?dataset={regione}.zip"
        zip_path = f"{regione}.zip"
        try:
            response = download_with_progress(url, zip_path)
            log_manager.append(f"Scaricato: {zip_path}")
            processed_regioni += 1
            log_manager.set_progress(int((processed_regioni / total_regioni) * 100))
        except Exception as e:
            log_manager.append(f"Errore durante il download di {regione}: {e}")
            continue

        # Sposta il file ZIP Regionale nella cartella sorgenti
        log_manager.append(f"Spostamento file Regione: {regione}")
        shutil.move(zip_path, f"catasto_italia/sorgenti/{zip_path}")

        # Estrai i file ZIP
        extract_dir = f"{root_dir}/temp_extract/{regione}"
        with zipfile.ZipFile(f"catasto_italia/sorgenti/{zip_path}", "r") as zip_ref:
            log_manager.append(f"Inizio unzip file: {zip_ref.filename}")
            zip_ref.extractall(extract_dir)
        log_manager.append(f"Estratto: {zip_path}")

    # Estrazione ricorsiva dei file ZIP provinciali/comunali
    log_manager.append("Elaborazione file provinciali e comunali...")
    extraction_done = True
    while extraction_done:
        extraction_done = extract_all_zips(f"{root_dir}/temp_extract")

    # Processa i file GML
    log_manager.append("Ricerca file GML in tutte le directory...")
    total_gml = process_gml(f"{root_dir}/temp_extract", "catasto_italia/fogli", "catasto_italia/mappali")
    log_manager.append(f"Totale file GML processati: {total_gml}")

    # Pulizia directory temporanee
    try:
        shutil.rmtree(root_dir)
        log_manager.append("Pulizia cartelle temporanee completata")
    except Exception as e:
        log_manager.append(f"Errore durante la pulizia: {str(e)}")

    # Verifica finale
    try:
        fogli_count = len(os.listdir("catasto_italia/fogli"))
        mappali_count = len(os.listdir("catasto_italia/mappali"))
        log_manager.append("Elaborazione completata!")
        log_manager.append("------------")
        log_manager.append(f"Fogli catastali trovati: {fogli_count}")
        log_manager.append(f"Mappali catastali trovati: {mappali_count}")
    except Exception as e:
        log_manager.append(f"Errore nel conteggio finale: {str(e)}")


@app.route("/logs", methods=["GET"])
def get_logs():
    return jsonify(logs=log_manager.get_logs(), progress=log_manager.progress)


@app.route("/clear_logs", methods=["POST"])
def clear_logs():
    log_manager.clear()
    return jsonify(success=True)


@app.route("/cleanup", methods=["POST"])
def cleanup_directories():
    try:
        # Lista delle directory da cancellare
        dirs_to_clean = [
            "catasto_italia/tmp_folder",
            "catasto_italia/fogli",
            "catasto_italia/mappali",
            "catasto_italia/sorgenti"
        ]
        
        # Cancella le directory se esistono
        for dir_path in dirs_to_clean:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                log_manager.append(f"Directory cancellata: {dir_path}")
        
        # Cancella anche la directory principale se vuota
        if os.path.exists("catasto_italia") and not os.listdir("catasto_italia"):
            os.rmdir("catasto_italia")
            log_manager.append("Directory principale catasto_italia cancellata")
            
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        regioni = request.form.getlist("regioni")
        threading.Thread(target=download_and_process, args=(regioni,)).start()
        return jsonify(success=True)
    return render_template("index.html", log_messages=log_manager.get_logs())



if __name__ == "__main__":
    app.run(debug=False)
