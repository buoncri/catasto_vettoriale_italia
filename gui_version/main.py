# Download Catasto Italiano con GUI
# idea of automatic download and extraction, plus hoping some improvements :-D
#
# May the force be with you ... always !


# Come usarlo
#     Prerequisiti:
#         Installa Python 3 (se non già installato).
#         Installa le librerie richieste usando pip:

#     pip install PyQt5 requests

# Esegui lo script:
#     python download_catasto_gui.py

# Funzionalità della GUI
#     Una finestra con un campo di input per inserire i nomi delle regioni.
#     Un pulsante per avviare il download ed elaborazione.
#     Una finestra di log che mostra l'avanzamento e il riepilogo finale.



import os
import requests
import zipfile
import shutil
from PyQt5.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QTextEdit,
    QFileDialog,
)
import sys

class DownloadCatastoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Download Catasto Italiano")
        self.resize(600, 400)
        
        layout = QVBoxLayout()

        # Istruzioni
        self.instructions_label = QLabel("Inserisci i nomi delle regioni separati da uno spazio (es. UMBRIA LAZIO):")
        layout.addWidget(self.instructions_label)

        # Input regioni
        self.region_input = QLineEdit()
        layout.addWidget(self.region_input)

        # Bottone per avviare il processo
        self.download_button = QPushButton("Scarica ed Elabora")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # Log per mostrare l'avanzamento del processo
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def log(self, message):
        """Aggiunge messaggi di log alla finestra di output."""
        self.log_output.append(message)
        QApplication.processEvents()

    def start_download(self):
        """Avvia il download ed elaborazione dei file."""
        regioni = self.region_input.text().upper().split()

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

        # Download ed elaborazione per ogni regione
        for regione in regioni:
            regione = regioni_speciali.get(regione, regione)
            self.log(f"Download vettoriale regionale: {regione}")

            # Scarica il file
            url = f"https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/GetDataset.php?dataset={regione}.zip"
            zip_path = f"{regione}.zip"
            try:
                response = requests.get(url)
                with open(zip_path, "wb") as f:
                    f.write(response.content)
                self.log(f"Scaricato: {zip_path}")
            except Exception as e:
                self.log(f"Errore durante il download di {regione}: {e}")
                continue

            # Sposta nella cartella sorgenti
            shutil.move(zip_path, f"catasto_italia/sorgenti/{zip_path}")

            # Estrazione del file ZIP
            extract_dir = f"{root_dir}/temp_extract/{regione}"
            with zipfile.ZipFile(f"catasto_italia/sorgenti/{zip_path}", "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            self.log(f"Estratto: {zip_path}")

        # Organizza i file GML
        self.log("Elaborazione file GML...")
        for root, _, files in os.walk(f"{root_dir}/temp_extract"):
            for file in files:
                if file.endswith("_ple.gml"):
                    shutil.move(os.path.join(root, file), f"{root_dir}/ple_files/{file}")
                    self.log(f"Spostato PLE: {file}")
                elif file.endswith("_map.gml"):
                    shutil.move(os.path.join(root, file), f"{root_dir}/map_files/{file}")
                    self.log(f"Spostato MAP: {file}")

        # Sposta le directory finali
        shutil.move(f"{root_dir}/ple_files", "catasto_italia/ple_files")
        shutil.move(f"{root_dir}/map_files", "catasto_italia/map_files")

        # Pulizia delle cartelle temporanee
        shutil.rmtree(root_dir)
        self.log("Pulizia cartelle temporanee completata.")

        # Riepilogo
        ple_count = len(os.listdir("catasto_italia/ple_files"))
        map_count = len(os.listdir("catasto_italia/map_files"))
        self.log("Elaborazione completata!")
        self.log("------------")
        self.log(f"File in ple_files: {ple_count}")
        self.log(f"File in map_files: {map_count}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadCatastoApp()
    window.show()
    sys.exit(app.exec_())
