# Script per scaricare e processare file catastali regionali
# Funziona su Windows 10 e versioni successive
#
#
# Come usarlo:
# 
#     Salva lo script come file .ps1, ad esempio download_files.ps1.
#     Esegui il file in PowerShell:
#         Apri PowerShell come amministratore (necessario per i permessi di esecuzione).
#         Esegui il comando per abilitare l'esecuzione degli script:

# Set-ExecutionPolicy RemoteSigned

# Lancia lo script:

# .\download_files.ps1


# Pulizia schermo
Clear-Host

Write-Output "Download dei file vettoriali del catasto italiano"

# Chiedi i nomi delle regioni
$regioni = Read-Host "Inserisci i nomi delle regioni separati da uno spazio (es. UMBRIA LAZIO)"
$regioni = $regioni.ToUpper()

# Gestione dei casi speciali
$regioni_speciali = @{
    "EMILIA" = "EMILIA-ROMAGNA"
    "FRIULI" = "FRIULI-VENEZIA-GIULIA"
}

# Creazione directory
$root_dir = "catasto_italia\tmp_folder"
New-Item -ItemType Directory -Force -Path "$root_dir\ple_files", "$root_dir\map_files", "$root_dir\temp_extract", "catasto_italia\sorgenti" | Out-Null

# Scarica ed elabora i file per ogni regione
foreach ($regione in $regioni.Split(" ")) {
    $regione = if ($regioni_speciali.ContainsKey($regione)) { $regioni_speciali[$regione] } else { $regione }
    
    # Scarica il file ZIP
    $url = "https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/GetDataset.php?dataset=${regione}.zip"
    Write-Output "Download vettoriale regionale: $regione"
    $zipPath = "${regione}.zip"
    Invoke-WebRequest -Uri $url -OutFile $zipPath
    
    # Sposta nella cartella sorgenti
    Move-Item $zipPath "catasto_italia\sorgenti\" -Force
    
    # Estrai i file ZIP
    Write-Output "Estrazione file regionale per $regione..."
    Expand-Archive -Path "catasto_italia\sorgenti\$zipPath" -DestinationPath "$root_dir\temp_extract\$regione" -Force
}

# Estrazione dei file provinciali e comunali
Write-Output "Estrazione file provinciali e comunali..."
Get-ChildItem -Recurse -Filter *.zip -Path "$root_dir\temp_extract" | ForEach-Object {
    Write-Output "Estraendo file: $($_.Name)"
    Expand-Archive -Path $_.FullName -DestinationPath $_.DirectoryName -Force
}

# Organizzazione dei file GML
Write-Output "Elaborazione file GML..."
Get-ChildItem -Recurse -Filter *.gml -Path "$root_dir\temp_extract" | ForEach-Object {
    $filename = $_.Name
    Write-Output "Analizzando: $filename"
    
    if ($filename -like "*_ple.gml") {
        Write-Output "Spostando PLE: $filename"
        Move-Item $_.FullName "$root_dir\ple_files\" -Force
    } elseif ($filename -like "*_map.gml") {
        Write-Output "Spostando MAP: $filename"
        Move-Item $_.FullName "$root_dir\map_files\" -Force
    }
}

# Sposta le directory ple_files e map_files
Move-Item "$root_dir\ple_files" "catasto_italia\" -Force
Move-Item "$root_dir\map_files" "catasto_italia\" -Force

# Pulizia delle directory temporanee
Write-Output "Pulizia cartelle temporanee..."
Remove-Item -Recurse -Force "$root_dir"

# Esito finale
Write-Output "`nElaborazione completata!"
Write-Output "Riepilogo:"
Write-Output "------------"
$ple_count = (Get-ChildItem -Recurse -File -Path "catasto_italia\ple_files").Count
Write-Output "File in ple_files: $ple_count"
$map_count = (Get-ChildItem -Recurse -File -Path "catasto_italia\map_files").Count
Write-Output "File in map_files: $map_count"
