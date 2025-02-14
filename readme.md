# Script di Download per il Catasto Italiano

## Panoramica
Questo repository contiene uno script Bash (`download_files.sh`) progettato per scaricare e processare file di dati vettoriali dal catasto italiano. Lo script supporta il download dei dati per regioni italiane specificate, l'estrazione dei contenuti e l'organizzazione dei file in cartelle specifiche per un'ulteriore analisi.

## Funzionalità
- Scarica i dati catastali vettoriali per le regioni italiane inserite dall'utente.
- Supporta nomi di regioni speciali (ad esempio, "EMILIA" diventa "EMILIA-ROMAGNA").
- Estrae e processa i file in cartelle organizzate.
- Separa i file nelle directory `ple_files` e `map_files`.
- Esegue automaticamente la pulizia dei file temporanei dopo il processo.

## Prerequisiti
Assicurati di avere i seguenti strumenti installati sul tuo sistema:
- Bash
- `wget`
- `unzip`

## Utilizzo
### Istruzioni passo-passo
1. Clona il repository o copia lo script `download_files.sh` sul tuo sistema locale.

2. Apri un terminale e vai alla directory contenente lo script.

3. Esegui lo script:
   ```bash
   ./download_files.sh
   ```

4. Quando richiesto, inserisci i nomi delle regioni separati da uno spazio (ad esempio, `UMBRIA LAZIO`).

5. Lo script eseguirà:
   - Il download dei file `.zip` corrispondenti per ogni regione.
   - L'estrazione dei contenuti in cartelle temporanee.
   - L'organizzazione dei file `.gml` nelle directory `ple_files` e `map_files`.
   - La pulizia delle cartelle temporanee.

### Esempio
```bash
Inserisci i nomi delle regioni separati da uno spazio (es. UMBRIA LAZIO): EMILIA LAZIO
```

### Riepilogo del Risultato
Al termine, lo script mostrerà il numero di file in ciascuna directory:
- **`ple_files`**: Contiene i file vettoriali catastali PLE.
- **`map_files`**: Contiene i file vettoriali catastali MAP.

Esempio di output:
```
Elaborazione completata!

Riepilogo:
------------
File in ple_files: 10
File in map_files: 12
```

## Struttura delle Directory
Dopo l'esecuzione, la directory `catasto_italia` avrà la seguente struttura:
```
catasto_italia/
  |-- ple_files/       # File vettoriali PLE
  |-- map_files/       # File vettoriali MAP
  |-- sorgenti/        # File ZIP scaricati originali
```

## Gestione delle Regioni Speciali
Lo script gestisce le seguenti abbreviazioni delle regioni:
- `EMILIA` viene convertito in `EMILIA-ROMAGNA`
- `FRIULI` viene convertito in `FRIULI-VENEZIA-GIULIA`

## Licenza
Questo progetto è concesso in licenza sotto la Licenza MIT. Consulta il file `LICENSE` per ulteriori dettagli.

## Disclaimer
I dati vengono scaricati dal servizio cartografico dell'Agenzia delle Entrate. Assicurati di rispettare eventuali termini e condizioni applicabili durante l'utilizzo dei dati.

## Ringraziamenti
- **Ispiratore**: Sam Altman & Co.

Che la forza sia con te... sempre!

