# Guida all'avvio — Image Enhancement Lab

Questa guida descrive come eseguire localmente il prototipo sviluppato per il case study Immobiliare.it.

## 1. Requisiti

- Python 3.12
- Git
- Connessione Internet per il workflow AI-Assisted
- Chiave API Gemini per utilizzare il workflow AI-Assisted

Il progetto è stato sviluppato e testato su Windows 11 con Visual Studio Code e PowerShell.

## 2. Scaricare il progetto

Clonare la repository privata GitHub (è necessario disporre dei permessi di accesso):

```powershell
git clone https://github.com/Marco-Pedicillo/image-enhancement-lab.git
cd image-enhancement-lab
```

## 3. Creare l'ambiente Python

Aprire PowerShell nella cartella principale del progetto ed eseguire:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Le dipendenze saranno installate nell'ambiente virtuale locale.

## 4. Configurare Gemini

Nella cartella principale è presente `.env.example`. Creare una copia denominata `.env`:

```powershell
Copy-Item .env.example .env
```

Aprire `.env` e inserire la propria chiave:

```env
GEMINI_API_KEY=INSERIRE_LA_PROPRIA_CHIAVE
```

La chiave può essere generata attraverso [Google AI Studio](https://aistudio.google.com/apikey), secondo le condizioni e le quote disponibili.

**Non pubblicare `.env` né condividere la chiave API.** Il file è escluso dalla repository tramite `.gitignore`.

## 5. Avviare l'applicazione

Dalla cartella principale del progetto:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py 
```

Aprire nel browser:

`http://localhost:8501`

L'applicazione funziona localmente e non richiede alcun deployment pubblico.

## 6. Provare il prototipo

1. Caricare una fotografia JPG o PNG, ad esempio una delle immagini in `data/samples/`.
2. Premere **Run Experiment** per eseguire entrambi i workflow.
3. Confrontare Original, Traditional e AI-Assisted, verificando metriche, tempi, decisioni ed eventuali warning.
4. Compilare **Human Evaluation**, selezionare l'immagine preferita e premere **Save Evaluation**.
5. Consultare i risultati salvati in `results/experiments.csv`.

**Nota:** il CSV incluso nella repository contiene già i sei esperimenti del case study. Ulteriori valutazioni vengono aggiunte localmente allo stesso file; per conservarne una copia immutata, duplicarlo prima di effettuare nuovi test.

## 7. Limitazioni e note di sicurezza

- Il workflow Traditional elabora le immagini localmente; AI-Assisted richiede una chiave Gemini valida e una connessione Internet.
- Senza chiave API è possibile consultare il codice, la documentazione e i risultati salvati; l'esecuzione completa del workflow AI-Assisted non è disponibile.
- Il workflow AI invia a Google una copia ridimensionata della fotografia: utilizzare esclusivamente immagini autorizzate.
- Il Quality Gate è sperimentale e non garantisce la fedeltà della rappresentazione immobiliare.
- Le quote e l'eventuale fatturazione Gemini dipendono dalla configurazione del progetto API utilizzato.

Per maggiori dettagli consultare [Architettura](architecture.md) e [Valutazione sperimentale](experiments.md).