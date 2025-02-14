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

def download_and_process(regioni):
    total_regioni = len(regioni)
    processed_regioni = 0
    
    # Dizionario per gestire regioni speciali
    regioni_speciali = {
        "EMILIA": "EMILIA-ROMAGNA",
        "FRIULI": "FRIULI-VENEZIA-GIULIA",
    }

    # Creazione directory necessarie
    root_dir = "catasto_italia/tmp_folder"
    os.makedirs(f"{root_dir}/ple_files", exist_ok=True)
    os.makedirs(f"{root_dir}/map_files", exist_ok=True)
    os.makedirs(f"{root_dir}/temp_extract", exist_ok=True)
    os.makedirs("catasto_italia/sorgenti", exist_ok=True)

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

        # Sposta il file ZIP nella cartella sorgenti
        log_manager.append(f"Spostamento file Regione: {regione}")
        shutil.move(zip_path, f"catasto_italia/sorgenti/{zip_path}")

        # Estrai i file ZIP
        extract_dir = f"{root_dir}/temp_extract/{regione}"
        with zipfile.ZipFile(f"catasto_italia/sorgenti/{zip_path}", "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        log_manager.append(f"Estratto: {zip_path}")

    # Estrazione file provinciali e comunali
    log_manager.append("Elaborazione file provinciali e comunali...")
    for root, _, files in os.walk(f"{root_dir}/temp_extract"):
        for file in files:
            if file.endswith(".zip"):
                with zipfile.ZipFile(os.path.join(root, file), "r") as zip_ref:
                    zip_ref.extractall(root)
                log_manager.append(f"Estrazione file: {file}")

    # Organizza i file GML
    log_manager.append("Elaborazione file GML...")
    for root, _, files in os.walk(f"{root_dir}/temp_extract"):
        for file in files:
            if file.endswith("_ple.gml"):
                shutil.move(os.path.join(root, file), f"{root_dir}/ple_files/{file}")
                log_manager.append(f"Spostato PLE: {file}")
            elif file.endswith("_map.gml"):
                shutil.move(os.path.join(root, file), f"{root_dir}/map_files/{file}")
                log_manager.append(f"Spostato MAP: {file}")

    # Sposta le directory finali
    shutil.move(f"{root_dir}/ple_files", "catasto_italia/ple_files")
    shutil.move(f"{root_dir}/map_files", "catasto_italia/map_files")
    shutil.rmtree(root_dir)
    log_manager.append("Pulizia cartelle temporanee completata.")

    ple_count = len(os.listdir("catasto_italia/ple_files"))
    map_count = len(os.listdir("catasto_italia/map_files"))
    log_manager.append("Elaborazione completata!")
    log_manager.append("------------")
    log_manager.append(f"File in ple_files: {ple_count}")
    log_manager.append(f"File in map_files: {map_count}")


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
            "catasto_italia/ple_files",
            "catasto_italia/map_files",
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
