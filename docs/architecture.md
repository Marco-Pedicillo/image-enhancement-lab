# Architettura — case_study_immobiliare

## Panoramica

**Image Enhancement Lab** è un prototipo Streamlit eseguito in locale che permette di confrontare due workflow di miglioramento delle fotografie immobiliari applicati alla **stessa immagine di partenza**. L'obiettivo principale è sperimentare e valutare metodi alternativi, non sviluppare un servizio di elaborazione fotografica pronto per la produzione.

Entrambi i workflow utilizzano elaborazioni **non generative**, ma differiscono nel **modo in cui valutano la fotografia e scelgono le correzioni**:

- **Workflow A — Traditional:** utilizza statistiche dell'immagine, regole deterministiche e trasformazioni OpenCV.
- **Workflow B — AI-Assisted:** utilizza l'API multimodale Google Gemini per analizzare la scena e proporre parametri di correzione entro limiti predefiniti; OpenCV modifica poi i pixel in locale.

Il modello AI **non genera stanze alternative, arredi o dettagli architettonici**. Tuttavia, anche le modifiche a luminosità e contrasto possono produrre rappresentazioni poco fedeli: la revisione umana rimane quindi necessaria.

## Stack tecnologico

| Componente | Tecnologia | Funzione |
| --- | --- | --- |
| Ambiente di esecuzione | Python 3.12, ambiente virtuale locale `.venv` | Esecuzione dell'applicazione |
| Interfaccia | Streamlit | Caricamento, confronto, valutazione umana e download |
| Elaborazione delle immagini | OpenCV, Pillow, NumPy | Trasformazioni fotometriche e gestione delle immagini |
| Analisi AI | Gemini 3.5 Flash-Lite tramite `google-genai` | Analisi della scena e suggerimento dei parametri |
| Gestione dati | Pandas, modulo Python `csv` | Tabelle di confronto e salvataggio degli esperimenti |
| Credenziali | `python-dotenv`, `.env` | Configurazione locale della chiave API |
| Configurazione | `.streamlit/config.toml` | Tema dell'interfaccia e impostazioni del server locale |

L'applicazione viene eseguita in locale. **Il Workflow B richiede una connessione Internet**, perché invia a Gemini un'anteprima ridotta della fotografia. Il progetto Gemini è stato utilizzato con il Free Tier, senza attivare la fatturazione API. Questo non garantisce un utilizzo gratuito illimitato e non costituisce una stima dei costi in produzione.

## Flusso di elaborazione

1. L'utente carica una fotografia in formato JPG o PNG.
2. L'app legge l'immagine, la converte in RGB e calcola un hash del file. Verifica anche la presenza del metadato PNG `PhotoLabProcessed`, quando disponibile.
3. Il pulsante **Run Experiment** esegue entrambi i workflow su copie separate della stessa immagine originale.
4. Output, tempi di elaborazione, stati, motivazioni e metadati disponibili del modello vengono mantenuti in `st.session_state` durante la sessione Streamlit.
5. L'interfaccia mostra **Original / Traditional / AI-Assisted**, insieme a metriche tecniche, indicatori di preservazione, decisioni e avvisi sulla qualità.
6. Il valutatore assegna a ogni immagine disponibile un punteggio da 1 a 5 per qualità visiva, naturalezza e fedeltà dell'immobile; può segnalare alterazioni potenzialmente ingannevoli e scegliere l'immagine preferita, inclusa quella originale.
7. Con **Save Evaluation**, l'app registra l'esperimento in `results/experiments.csv`: una riga per Original, Traditional e AI-Assisted, con lo stesso identificativo di esecuzione (`run_id`). Gli identificativi già salvati non vengono aggiunti nuovamente.

Gli errori dei workflow vengono mostrati esplicitamente e non vengono presentati come elaborazioni riuscite. I risultati rimangono disponibili nella sessione corrente; il CSV costituisce la registrazione persistente dell'esperimento. **Le immagini non vengono incorporate nel CSV.**

## Workflow A — Traditional Enhancement

**Implementazione:** `src/traditional.py`

1. Valuta l'esposizione tramite statistiche dell'immagine, tra cui la luminanza mediana e la percentuale di pixel scuri.
2. Decide se applicare una correzione o mantenere l'originale.
3. Quando necessario, applica l'attuale correzione deterministica e moderata basata su gamma e CLAHE nello spazio colore LAB.
4. Controlla che la modifica non sia trascurabile e che non aumentino eccessivamente le alte luci saturate; se le regole non vengono rispettate, mantiene l'originale.
5. Restituisce l'immagine e una decisione strutturata (`enhanced` oppure `skipped`), accompagnata da motivazione e dettagli dell'analisi.

Il metodo è un'**euristica sperimentale**, non un modello addestrato per valutare la qualità fotografica. Una luminanza complessiva bassa non indica necessariamente una sottoesposizione, e una correzione conservativa può lasciare un ambiente ancora troppo scuro.

> Durante lo sviluppo sono state provate anche correzioni del bilanciamento del bianco e metodi più intensi di schiarimento additivo delle ombre. Queste appartengono alla storia della sperimentazione, **non** alla pipeline finale descritta qui. Le soglie e i coefficienti esatti sono definiti nel codice sorgente corrente, che costituisce il riferimento per la riproducibilità.

## Workflow B — AI-Assisted Enhancement

**Implementazione:** `src/ai_assisted.py`

1. Crea una copia ridimensionata dell'immagine per l'analisi visiva di Gemini, mantenendo l'originale a piena risoluzione per l'elaborazione OpenCV.
2. Chiede a Gemini se sia necessario un miglioramento e, in caso affermativo, richiede parametri strutturati in JSON e una breve motivazione.
3. Valida i tipi dei dati e limita i parametri numerici agli intervalli predefiniti prima di applicare qualsiasi correzione.
4. Applica con OpenCV correzioni controllate di gamma, CLAHE e schiarimento selettivo delle ombre; **non** viene eseguito editing generativo dell'immagine.
5. Valuta la candidata con un **Quality Gate** basato su regole, implementato in `src/quality_gate.py`. I controlli rilevano, ad esempio, perdite marcate di contrasto o gamma dinamica e aumenti del clipping delle alte luci.
6. Restituisce una decisione come `enhanced`, `skipped` o `rejected`, insieme ai parametri, agli avvisi e ai dati disponibili sull'utilizzo dei token.

**Eccezione sperimentale importante:** quando una candidata AI viene rifiutata, il prototipo può mostrare, **esclusivamente per la valutazione manuale**, una versione composta dal **70% della candidata e dal 30% dell'originale**. Si tratta di un *override sperimentale*, **non di un'immagine approvata dal Quality Gate**. Lo stato `rejected` e gli avvisi devono rimanere visibili e sono registrati nel CSV. L'immagine ottenuta tramite blending non viene raccomandata automaticamente per la pubblicazione.

Il Quality Gate verifica soltanto alcuni indicatori numerici. **Non può certificare la fedeltà dell'immobile**, la naturalezza fotografica o la superiorità effettiva della candidata.

## Valutazione e dati sperimentali

**Implementazione:** `src/metrics.py`, `src/experiments.py` e modulo *Human Evaluation* in `app.py`.

Le misurazioni automatiche comprendono:

- Luminosità media, contrasto globale e varianza del Laplaciano (indicatore limitato di nitidezza).
- Percentuale di pixel scuri e di alte luci prossime alla saturazione.
- Intervallo di luminanza basato sui percentili e contrasto locale calcolato per blocchi.
- Variazione delle regioni originariamente scure e differenza media RGB rispetto all'originale.
- Tempo totale di elaborazione di ogni workflow, inclusa la chiamata API nel Workflow B.

Queste metriche sono **indicatori diagnostici**, non misure oggettive definitive della qualità. Per esempio, una maggiore luminosità può corrispondere a neri slavati; una maggiore varianza del Laplaciano può riflettere un aumento del rumore. L'interpretazione richiede quindi il supporto della valutazione umana.

Il CSV registra identificativo dell'esperimento, hash e nome del file di input, workflow, stato e motivazione, tempo di elaborazione, modello e parametri, token disponibili, avvisi del Quality Gate, flag di override, metriche dell'immagine, valutazioni umane, immagine preferita e motivazione.

L'esperimento attuale comprende **sei fotografie**. I risultati hanno valore esplorativo e sono documentati in [`experiments.md`](experiments.md). La valutazione è stata condotta da una sola persona, conoscendo l'identità dei workflow. Non vengono avanzate conclusioni statistiche o causali sulle prestazioni degli annunci immobiliari.

## Responsabilità dei componenti

| File | Responsabilità |
| --- | --- |
| `app.py` | Interfaccia Streamlit, orchestrazione degli esperimenti, stato di sessione e valutazione umana |
| `src/traditional.py` | Analisi e miglioramento deterministici |
| `src/ai_assisted.py` | Richiesta a Gemini, validazione della risposta e correzione OpenCV guidata dall'AI |
| `src/quality_gate.py` | Controlli euristici sugli output candidati |
| `src/metrics.py` | Metriche fotografiche e confronto originale/output |
| `src/experiments.py` | Schema CSV, prevenzione dei duplicati e persistenza locale |
| `docs/` | Perimetro del prodotto, architettura e report degli esperimenti |

## Sicurezza, limiti e riproducibilità

- La chiave Gemini viene letta da `.env` e **non deve mai essere caricata su Git**; `.env.example` deve contenere soltanto un segnaposto.
- Devono essere utilizzate immagini che è lecito elaborare e condividere con il provider AI esterno. Nel Workflow B, l'anteprima ridotta viene trasmessa fuori dal dispositivo locale.
- L'app **non è pubblicata online**: viene avviata localmente con `streamlit run app.py`.
- Disponibilità dell'API, latenza e limiti del Free Tier dipendono dal provider. Il CSV conserva i dati di utilizzo dei token, quando restituiti, **non una stima validata del costo per immagine in produzione**.
- Le soglie del Quality Gate e l'override tramite blending sono sperimentali. Una candidata rifiutata non diventa automaticamente sicura soltanto perché la sua versione attenuata appare migliore.
- La persistenza CSV è adeguata a un piccolo prototipo con un solo utente, non a un sistema con scritture concorrenti in produzione. Non sono implementati autenticazione, monitoraggio operativo, audit trail completo o gestione automatizzata della conservazione delle immagini.
- Prima di un eventuale utilizzo in produzione sarebbero necessari un dataset più ampio e raccolto lecitamente, valutazioni cieche condotte da più persone, maggiore copertura dei test e sperimentazioni di prodotto su dati reali.
