@REM # Script per scaricare e processare file catastali regionali
@REM # Funziona su Windows 10 e versioni successive
@REM #
@REM #
@REM Come usarlo:
@REM     Salva il file come download_files.bat.
@REM     Esegui il file facendo doppio clic o lanciandolo dal prompt dei comandi (cmd).
@REM     Segui le istruzioni per inserire i nomi delle regioni.






@echo off
:: Script di download per dati catastali regionali

:: Pulizia schermo
cls
echo Download dei file vettoriali del catasto italiano

:: Chiedi le regioni all'utente
set /p regioni="Inserisci i nomi delle regioni separati da uno spazio (es. UMBRIA LAZIO): "

:: Creazione directory
set "root_dir=catasto_italia\tmp_folder"
mkdir "%root_dir%\ple_files"
mkdir "%root_dir%\map_files"
mkdir "%root_dir%\temp_extract"
mkdir "catasto_italia\sorgenti"

:: Download dei file per ogni regione
for %%R in (%regioni%) do (
    set "regione=%%R"
    set "regione=%regione:~0,1%%regione:~1%"
    set "regione=!regione:~0,1!!regione:~1!"
    if /i "!regione!"=="EMILIA" set "regione=EMILIA-ROMAGNA"
    if /i "!regione!"=="FRIULI" set "regione=FRIULI-VENEZIA-GIULIA"
    
    echo Download vettoriale regionale: !regione!
    set "url=https://wfs.cartografia.agenziaentrate.gov.it/inspire/wfs/GetDataset.php?dataset=!regione!.zip"
    
    :: Scarica il file
    powershell -Command "Invoke-WebRequest -Uri !url! -OutFile '!regione!.zip'"
    
    :: Sposta il file nella cartella sorgenti
    move "!regione!.zip" "catasto_italia\sorgenti\"
    
    :: Estrazione del file ZIP
    powershell -Command "Expand-Archive -Path 'catasto_italia\sorgenti\!regione!.zip' -DestinationPath '%root_dir%\temp_extract\!regione!' -Force"
)

:: Estrazione file provinciali e comunali
echo Estrazione file provinciali e comunali...
for /r "%root_dir%\temp_extract" %%F in (*.zip) do (
    echo Estrazione file: %%~nxF
    powershell -Command "Expand-Archive -Path '%%F' -DestinationPath '%%~dpF' -Force"
)

:: Organizzazione dei file GML
echo Elaborazione file GML...
for /r "%root_dir%\temp_extract" %%G in (*.gml) do (
    echo Analizzando: %%~nxG
    if "%%~nxG"=="*_ple.gml" move "%%G" "%root_dir%\map_files"  # Invertito
    if "%%~nxG"=="*_map.gml" move "%%G" "%root_dir%\ple_files"  # Invertito
)

:: Sposta le cartelle finali
move "%root_dir%\ple_files" "catasto_italia\"
move "%root_dir%\map_files" "catasto_italia\"

:: Pulizia cartelle temporanee
echo Pulizia cartelle temporanee...
rmdir /s /q "%root_dir%"

:: Riepilogo
echo Elaborazione completata!
echo.
echo Riepilogo:
echo ------------
dir /b "catasto_italia\ple_files" | find /c /v ""
dir /b "catasto_italia\map_files" | find /c /v ""
