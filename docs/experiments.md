# Valutazione sperimentale

**Progetto:** Image Enhancement Lab — Case Study Immobiliare.it  
**Tipo di valutazione:** Confronto esplorativo su piccola scala  
**Dataset:** 6 fotografie di interni immobiliari  
**Fonte dei risultati:** `results/experiments.csv`

## 1. Obiettivo

Valutare se un workflow di miglioramento fotografico assistito dall'intelligenza artificiale offra vantaggi pratici rispetto a un workflow deterministico basato su OpenCV, considerando qualità visiva, naturalezza, fedeltà percepita dell'immobile, tempi di elaborazione e affidabilità.

L'esperimento verifica inoltre se sia preferibile conservare l'immagine originale quando il miglioramento non è necessario o potrebbe risultare controproducente.

L'obiettivo **non è dimostrare che l'AI superi sempre i metodi tradizionali**, ma identificare vantaggi e svantaggi dei due approcci e comprendere quando una modifica automatica debba essere accettata, evitata oppure sottoposta a revisione.

## 2. Workflow confrontati

| Variante | Descrizione |
|---|---|
| **Original** | Immagine originale non modificata, utilizzata come riferimento e considerata una possibile scelta finale. |
| **Traditional** | Analisi e correzione deterministica dell'immagine mediante Python e OpenCV. Può decidere di non applicare modifiche. |
| **AI-Assisted** | Gemini 3.5 Flash-Lite analizza una copia a risoluzione ridotta dell'immagine e suggerisce parametri di miglioramento entro intervalli prestabiliti. OpenCV applica le modifiche all'immagine originale a piena risoluzione. Il modello non genera nuovi contenuti immobiliari. |

Il workflow AI include un **Quality Gate sperimentale**, che controlla eventuali perdite eccessive di contrasto globale e locale, riduzioni della gamma dinamica e aumenti del clipping nelle alte luci.

Una candidata rifiutata può essere mostrata attraverso una combinazione composta dal **70% dell'immagine elaborata e dal 30% dell'originale**, per consentire una valutazione umana.

Questo comportamento rappresenta un **override sperimentale**, non un'approvazione del Quality Gate.

I warning registrati si riferiscono alla candidata prima del blending, mentre le metriche dell'output visualizzato si riferiscono all'immagine combinata.

## 3. Dataset e procedura sperimentale

Sono state valutate sei fotografie, denominate da `prova1.jpg` a `prova6.jpg`.

Le immagini sono state selezionate per una dimostrazione pratica e non costituiscono un campione casuale o un benchmark rappresentativo. Comprendono sia fotografie sulle quali è stato tentato un miglioramento, sia fotografie per le quali entrambi i workflow hanno deciso di non intervenire.

Per ciascuna fotografia è stata seguita la seguente procedura:

1. Caricamento dell'immagine originale nell'applicazione Streamlit locale.
2. Esecuzione dei workflow Traditional e AI-Assisted sulla stessa immagine.
3. Registrazione delle decisioni, dei tempi di elaborazione, delle metriche tecniche, dei parametri suggeriti dall'AI, dell'utilizzo dei token e degli eventuali warning del Quality Gate.
4. Confronto visivo tra immagine originale e due output elaborati.
5. Assegnazione di un punteggio da **1 (scarso) a 5 (eccellente)** per qualità visiva, naturalezza e fedeltà percepita dell'immobile.
6. Selezione dell'immagine preferita per un annuncio, eventuale inserimento di una motivazione e salvataggio della valutazione nel CSV locale.

Le sei valutazioni sono state effettuate da **un unico valutatore non in cieco**, che poteva conoscere il workflow associato a ciascuna immagine.

I punteggi soggettivi sono pertanto descrittivi e possono essere influenzati da bias di valutazione.

La fedeltà dell'immobile è stata giudicata visivamente rispetto alla fotografia di partenza; **non è stata verificata indipendentemente la corrispondenza con l'immobile reale**.

## 4. Metodologia di misurazione

| Dimensione | Misura | Interpretazione e limiti |
|---|---|---|
| Qualità visiva, naturalezza e fedeltà percepita | Valutazioni umane da 1 a 5 | Soggettive, senza riferimenti indipendenti o valutatori multipli. |
| Immagine preferita | Una scelta per fotografia | Conteggio delle preferenze; eventuali qualità equivalenti non implicano selezioni multiple. |
| Tempo di elaborazione | Secondi per workflow | Il tempo AI comprende la chiamata al modello remoto e l'elaborazione locale. |
| Affidabilità | `enhanced`, `skipped`, `rejected`, `error` | Indica gli esiti del processamento, non garantisce la qualità fotografica. |
| Metriche tecniche | Luminosità, contrasto, indicatore di nitidezza, frazione di ombre, clipping delle alte luci, gamma dinamica e contrasto locale | Indicatori diagnostici, non un punteggio automatico di qualità. Valori più alti non sono sempre migliori. |
| Conservazione dell'immagine | Variazione nelle regioni scure e differenza RGB media | Misura l'entità delle modifiche, non la loro correttezza o desiderabilità. |
| Utilizzo API e costi | Token di input/output Gemini; progetto Free Tier | I token sono registrati, ma non è stato misurato un costo monetario per immagine né il consumo energetico. |

La metrica di nitidezza utilizza la varianza della risposta di un filtro Laplaciano, che può aumentare anche in presenza di rumore.

Il parametro `shadow_fraction` rappresenta la proporzione di pixel in scala di grigi al di sotto di una soglia prestabilita: non costituisce una valutazione semantica dei dettagli nelle ombre.

## 5. Risultati

### 5.1 Immagine preferita

| Immagine preferita | Fotografie | Percentuale |
|---|---:|---:|
| Original | 2 | 33,3% |
| Traditional | 2 | 33,3% |
| AI-Assisted | 2 | 33,3% |

Le preferenze registrate per ogni fotografia sono:

| Fotografia | Immagine preferita | Motivazione registrata |
|---|---|---|
| `prova1.jpg` | AI-Assisted | Più luminosa |
| `prova2.jpg` | Traditional | Qualità migliore |
| `prova3.jpg` | Original | Non ha bisogno di miglioramenti |
| `prova4.jpg` | AI-Assisted | Bordi migliori |
| `prova5.jpg` | Traditional | Nessuna motivazione registrata |
| `prova6.jpg` | Original | Miglioramenti non necessari |

Nessuna delle tre alternative ha ottenuto una maggioranza delle preferenze.

In due fotografie è stata preferita l'immagine originale, confermando l'utilità di consentire al sistema di **non applicare modifiche quando non necessarie**.

### 5.2 Valutazioni qualitative medie

| Criterio (scala 1–5) | Original | Traditional | AI-Assisted |
|---|---:|---:|---:|
| Qualità visiva | 3,50 | 4,50 | 4,50 |
| Naturalezza | 3,83 | **4,50** | 4,17 |
| Fedeltà percepita dell'immobile | 4,17 | 4,50 | **4,67** |
| **Media complessiva dei criteri** | **3,83** | **4,50** | **4,44** |

Il workflow Traditional ha ottenuto una media descrittiva complessiva leggermente superiore.

Tuttavia, le differenze sono ridotte e il campione è troppo limitato per sostenere conclusioni di superiorità statisticamente significativa.

Il workflow AI-Assisted ha ricevuto la valutazione media più alta per la **fedeltà percepita dell'immobile**, ma questo risultato non dimostra una maggiore accuratezza rispetto alle caratteristiche reali della proprietà.

### 5.3 Tempi di elaborazione ed esiti

| Misura | Traditional | AI-Assisted |
|---|---:|---:|
| Tempo medio di elaborazione | **0,632 s** | **3,541 s** |
| Immagini migliorate (`enhanced`) | 4/6 | 3/6 |
| Elaborazioni saltate (`skipped`) | 2/6 | 2/6 |
| Candidate rifiutate (`rejected`) | 0/6 | 1/6 |
| Errori (`error`) | 0/6 | 0/6 |

Nei sei esperimenti, AI-Assisted ha richiesto mediamente un tempo di elaborazione circa **5,6 volte superiore** rispetto a Traditional.

Questi tempi dipendono dall'ambiente di esecuzione, dalla rete e dal servizio remoto utilizzato; non devono quindi essere interpretati come benchmark di produzione.

Nel caso di `prova2.jpg`, la candidata AI è stata rifiutata per:

- Perdita eccessiva del contrasto globale.
- Perdita eccessiva del contrasto locale.
- Riduzione eccessiva della gamma dinamica.

L'applicazione ha mostrato una versione attenuata della candidata tramite blending, come override sperimentale per la revisione manuale.

Tale output non deve essere interpretato come un'immagine che ha superato i controlli del Quality Gate.

## 6. Interpretazione e decisione di prodotto

L'esperimento **non identifica un workflow universalmente superiore**.

Entrambi i metodi di miglioramento sono stati preferiti in due fotografie su sei, mentre in altri due casi è stata preferita l'immagine originale.

Questo risultato supporta una progettazione che consenta esplicitamente di **mantenere la fotografia invariata** quando la qualità iniziale è già adeguata.

La componente AI può offrire un'analisi contestuale della scena e suggerimenti adattivi, ma la maggiore complessità e latenza non si sono tradotte, nei sei test, in un chiaro vantaggio complessivo nelle preferenze.

Il Quality Gate ha individuato una candidata problematica. Tuttavia, le sue soglie sono euristiche e il comportamento di override richiede una revisione umana.

**Raccomandazione preliminare di prodotto:** mantenere Traditional come soluzione di riferimento rapida, offrire AI-Assisted come alternativa sperimentale facoltativa per i casi più difficili e prevedere sempre una decisione umana prima di utilizzare una fotografia elaborata in un annuncio reale.

Le candidate rifiutate dal Quality Gate non devono essere pubblicate automaticamente.

## 7. Limiti e sviluppi futuri

- **Dataset piccolo e non rappresentativo:** sei immagini non permettono di stabilire prestazioni affidabili su immobili, condizioni di illuminazione, fotocamere e risoluzioni differenti.
- **Un solo valutatore non in cieco:** la conoscenza del metodo utilizzato potrebbe influenzare i punteggi. Non è stata misurata la concordanza tra valutatori.
- **Assenza di immagini di riferimento:** la fedeltà percepita è stata valutata rispetto alla fotografia originale, non confrontando l'output con l'immobile fisico o con un'esposizione di riferimento verificata.
- **Metriche e Quality Gate euristici:** le soglie possono rifiutare modifiche accettabili oppure non rilevare artefatti indesiderati.
- **Trattamento particolare degli output AI rifiutati:** l'immagine ottenuta tramite blending è un override successivo al rifiuto. Le relative metriche non dimostrano l'accettazione da parte del Quality Gate.
- **Evidenze limitate su tempi e costi:** è stata eseguita una sola elaborazione per fotografia. Non sono disponibili misure di ripetibilità, consumo energetico o un modello economico validato per l'utilizzo delle API in produzione.
- **Elaborazione AI esterna:** l'analisi Gemini richiede una connessione Internet e comporta l'invio di una copia ridimensionata dell'immagine a un servizio esterno. È necessario utilizzare fotografie autorizzate e non riservate.

In un eventuale sviluppo successivo sarebbe opportuno:

1. Ampliare e diversificare il dataset utilizzando fotografie con diritti d'uso adeguati.
2. Coinvolgere più valutatori e randomizzare o nascondere le etichette dei workflow durante la valutazione.
3. Ripetere le misurazioni dei tempi per stimarne la variabilità.
4. Calibrare le regole di miglioramento e i criteri di accettazione.
5. Introdurre verifiche esplicite sui requisiti di privacy e consenso.
6. Stimare i costi delle API, introdurre monitoraggio del servizio e implementare controlli di sicurezza prima di un'eventuale distribuzione in produzione.

Un'eventuale sperimentazione di prodotto dovrebbe inoltre verificare se il miglioramento fotografico produca benefici misurabili sul coinvolgimento degli utenti negli annunci immobiliari.

---

*Tutti i risultati numerici riportati derivano dai sei esperimenti registrati in `results/experiments.csv`. Nessun output del modello o punteggio di valutazione è stato simulato per questo report.*