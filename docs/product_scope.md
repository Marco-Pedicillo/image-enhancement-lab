# Product Scope — case_study_immobiliare

## Problema e utente di riferimento

Fotografie con esposizione inadeguata o scarsa visibilità degli ambienti possono rendere gli annunci immobiliari più difficili da valutare. Il miglioramento automatico può aiutare, ma una fotografia più gradevole non è necessariamente una **rappresentazione fedele dell'immobile**.

L'utente principale è un **operatore di agenzia immobiliare che prepara le fotografie per gli annunci**. Il prototipo è rivolto anche a valutatori e team di prodotto che desiderano confrontare diverse strategie di miglioramento.

## Obiettivo dell'MVP

Realizzare un **laboratorio sperimentale locale e funzionante** che consenta di caricare una fotografia di interni, confrontare l'elaborazione tradizionale e quella assistita dall'AI sullo stesso input, consultare indicatori quantitativi, valutare gli output e salvare i risultati per analisi successive.

Il prodotto deve consentire anche di **mantenere la fotografia originale**. L'obiettivo è supportare decisioni più consapevoli, non garantire un miglioramento di ogni immagine caricata.

## Funzionalità implementate

- Caricamento e conversione RGB di fotografie di interni in formato JPG/PNG.
- **Workflow A — Traditional:** elaborazione deterministica dell'esposizione e del contrasto con OpenCV; valutazione euristica della necessità di intervenire.
- **Workflow B — AI-Assisted:** Gemini 3.5 Flash-Lite analizza la fotografia e suggerisce parametri entro limiti prefissati; OpenCV applica localmente correzioni non generative.
- Esecuzione tramite un unico comando **Run Experiment**, con confronto affiancato tra Original, Traditional e AI-Assisted.
- Indicatori tecnici di luminosità, contrasto, nitidezza stimata, ombre, alte luci, gamma dinamica, contrasto locale e variazioni dei pixel, oltre ai tempi di elaborazione.
- **Quality Gate** basato su regole, che può rifiutare candidate AI problematiche e mostrare le relative segnalazioni.
- **Override sperimentale**, indicato esplicitamente nell'interfaccia, che può mostrare una candidata AI rifiutata dopo una fusione con l'originale (*blending*) per la **revisione manuale**. Tale output **non è approvato dal Quality Gate** e non viene raccomandato automaticamente.
- Valutazioni umane su scala 1–5 di qualità visiva, naturalezza e fedeltà dell'immobile; segnalazione di possibili alterazioni ingannevoli; scelta dell'immagine preferita e motivazione.
- Salvataggio locale in CSV con separatore `;`, con tre record per esperimento, comprendenti decisioni, metriche, avvisi e informazioni disponibili sull'utilizzo dell'API.
- Download degli output ed esecuzione locale tramite Streamlit.

## Funzionalità escluse

- Aggiunta o rimozione di mobili, *virtual staging*, nuovi oggetti o elementi architettonici.
- Modifiche a planimetrie, posizione di porte e finestre, dimensioni degli ambienti o viste esterne.
- Correzione automatica completa di ogni difetto fotografico, come prospettiva, rumore, sfocatura o inclinazione della fotocamera.
- Account utente, infrastruttura database, integrazione con Immobiliare.it, pubblicazione online o scalabilità per la produzione.
- Affermazioni su incrementi di conversioni, contatti ricevuti o ricavi degli annunci.

## Principi di prodotto, rischi e mitigazioni

| Rischio | Mitigazione nel prototipo | Limite residuo |
| --- | --- | --- |
| Rappresentazione ingannevole dell'immobile | Trasformazioni non generative con parametri limitati, confronto prima/dopo e valutazione umana della fedeltà | Le metriche sui pixel non garantiscono una rappresentazione veritiera |
| Elaborazione eccessiva ed effetto slavato | Limiti ai parametri, avvisi su clipping e perdita di contrasto, possibilità di conservare l'originale | Alcuni output guidati dall'AI risultano ancora poco naturali; l'override può mostrare una candidata rifiutata |
| Modifiche non necessarie | Valutazione preliminare della fotografia e stato `skipped` | Le euristiche possono interpretare male ambienti intenzionalmente scuri o fotografie già adeguate |
| Errori API o disponibilità limitata | Errori e stati espliciti; esecuzione del workflow tradizionale separata | Il Workflow B richiede una connessione e un servizio esterno |
| Privacy e diritti sulle immagini | Utilizzo di fotografie di test autorizzate e chiave API conservata localmente | Gemini riceve una versione ridotta delle fotografie analizzate dal Workflow B |
| Interpretazione errata dei punteggi | Metriche e criteri umani distinti, senza presentare un unico punteggio come qualità oggettiva | I giudizi sono soggettivi; gli esperimenti attuali sono stati valutati da una sola persona non in cieco |

## Criteri di successo e risultati disponibili

- **Funzionalità:** entrambi i workflow possono essere eseguiti e confrontati sulla stessa immagine; output, tempi e decisioni sono visualizzati e i risultati sono esportabili in CSV.
- **Misurabilità:** gli stessi indicatori diagnostici sono calcolati per gli output disponibili e affiancati a una valutazione umana strutturata.
- **Trasparenza:** errori, candidate AI rifiutate, override manuali e conservazione dell'originale sono distinguibili.
- **Verifica sperimentale:** il prototipo è stato testato su **sei fotografie**. Original, Traditional e AI-Assisted sono stati preferiti **due volte ciascuno**; questo risultato **non dimostra** la superiorità generale di un metodo.

Lo studio è esplorativo: non dimostra che il workflow AI produca risultati costantemente migliori, né che il miglioramento delle fotografie aumenti le prestazioni reali degli annunci. Risultati e limiti sono descritti in [`experiments.md`](experiments.md).

## Componenti reali e componenti sperimentali

**Reali:** elaborazione locale delle immagini, chiamate effettive a Gemini, misurazione dei tempi, metriche quantitative, valutazioni umane e persistenza su CSV.

**Sperimentali o non validati per la produzione:** soglie euristiche del Quality Gate, blending delle candidate AI rifiutate, valutazioni soggettive di un unico revisore ed eventuali stime dei costi operativi su larga scala. Non sono simulati miglioramenti dei contatti o delle conversioni degli annunci.

## Possibili sviluppi successivi (fuori dall'MVP)

Valutare un dataset più ampio, diversificato e acquisito nel rispetto dei diritti d'uso, coinvolgendo più revisori con valutazione in cieco; calibrare i parametri di miglioramento e le regole di rifiuto; ampliare i test automatici e i casi di errore; analizzare costi, latenza e requisiti di privacy in produzione; solo successivamente, considerare esperimenti A/B sull'interazione degli utenti con gli annunci.
