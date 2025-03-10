#!/bin/bash
# idea of automatic download and extraction, plus hoping some improvements :-D
# May the force be with you ... always !

# Pulisci lo schermo con vetril
clear

echo "Download dei file vettoriali del catasto italiano"

# Chiedi l'input delle regioni
read -p "Inserisci i nomi delle regioni separati da uno spazio (es. UMBRIA LAZIO): " regioni
regioni=$(echo "$regioni" | tr '[:lower:]' '[:upper:]')

# Gestisci i casi speciali
declare -A regioni_speciali
regioni_speciali=( ["EMILIA"]="EMILIA-ROMAGNA" ["FRIULI"]="FRIULI-VENEZIA-GIULIA" )

# Crea la root directory e le cartelle di destinazione
root_dir="catasto_italia/tmp_folder"
mkdir -p "$root_dir/ple_files"
mkdir -p "$root_dir/map_files"
mkdir -p "$root_dir/temp_extract"
mkdir -p "catasto_italia/sorgenti"

# Scarica ed elabora i file per ogni regione
for regione in $regioni; do
    regione=${regioni_speciali[$regione]:-$regione}
    
    # Scarica il file corrispondente
    url="https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/GetDataset.php?dataset=${regione}.zip"
    echo "Download vettoriale regionale: $regione"
    wget -O "${regione}.zip" "$url"
    
    # Sposta il file zip nella cartella sorgenti
    mv "${regione}.zip" "catasto_italia/sorgenti/"
    
    # Elaborazione file regionale
    echo "Elaborazione file regionale per $regione..."
    unzip -o "catasto_italia/sorgenti/${regione}.zip" -d "$root_dir/temp_extract/${regione}"
done

# Elaborazione file provinciali
echo
echo "Elaborazione file provinciali ..."
find "$root_dir/temp_extract" -name '*.zip' | while read F; do
    echo "Estraendo comune: $(basename "$F")"
    unzip -o "$F" -d "$(dirname "$F")"
done

# Elaborazione file comunali
echo
echo "Elaborazione file comunali..."
find "$root_dir/temp_extract" -name '*.zip' | while read F; do
    echo "Estraendo file: $(basename "$F")"
    unzip -o "$F" -d "$(dirname "$F")"
done

# Sposta tutti i file GML reperiti nelle cartelle di destinazione
echo
echo "Elaborazione file GML..."
find "$root_dir/temp_extract" -name '*.gml' | while read G; do
    filename=$(basename "$G")
    echo "Analizzando: $filename"
    
    if [[ "$filename" == *_ple.gml ]]; then
        echo "Spostando PLE: $filename"
        mv "$G" "$root_dir/map_files/"  # Invertito
    elif [[ "$filename" == *_map.gml ]]; then
        echo "Spostando MAP: $filename"
        mv "$G" "$root_dir/ple_files/"  # Invertito
    fi
done    

# Sposta le carte ple_files e map_files nella dir_italia
mv "$root_dir/ple_files" "catasto_italia/"
mv "$root_dir/map_files" "catasto_italia/"

# Eliminazione cartelle temporanee
echo
echo "Pulizia cartelle temporanee..."
rm -rf "$root_dir"

# Esito finale
echo
echo "Elaborazione completata!"
echo
echo "Riepilogo:"
echo "------------"
PLE_COUNT=$(find "catasto_italia/ple_files" -type f | wc -l)
echo "File in ple_files: $PLE_COUNT"

MAP_COUNT=$(find "catasto_italia/map_files" -type f | wc -l)
echo "File in map_files: $MAP_COUNT"
