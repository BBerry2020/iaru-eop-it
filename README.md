# Etica e procedure operative per il radioamatore – 4ª edizione

Traduzione italiana **non ufficiale**, per uso personale, di
*International Amateur Radio Union – Ethics and Operating Procedures for the Radio Amateur*,
Fourth Edition, Revision 4.2.0 (2026), © IARU Region 1.

> Questa traduzione è stata realizzata a titolo personale, per studio e consultazione.
> Non è una traduzione ufficiale dell'IARU e non è stata revisionata, approvata né certificata
> dall'ARI – Associazione Radioamatori Italiani. In caso di differenze fa fede l'edizione originale
> in lingua inglese: [Codes of Conduct | International Amateur Radio Union (IARU)](https://www.iaru-r1.org/on-the-air/eop/).

## Contenuto

| Percorso | Che cosa contiene |
| --- | --- |
| `dist/` | Il PDF impaginato, pronto da leggere o stampare |
| `src/eop-it.md` | Il testo tradotto in Markdown (sorgente) |
| `build/` | Modello LaTeX, script di conversione, immagini e caratteri per rigenerare il PDF |

## Rigenerare il PDF

Servono Python 3, pandoc 3 e XeLaTeX (TeX Live con `polyglossia` e i pattern di sillabazione italiani).

```sh
./build/build.sh
```

### File per la stampa in brossura (16,5×24 cm)

`./build/build-stampa.sh [dorso in mm]` genera in `dist/stampa-165x240/` l'interno (pagine singole)
e la copertina (2 pagine: esterno con dorso, interno bianco), con 3 mm di abbondanza,
in CMYK FOGRA51 (PSO Coated v3) e PDF/X-3, secondo le linee guida di 4graph.
Servono anche Ghostscript e il profilo `PSOcoated_v3.icc` (pacchetto `icc-profiles` su Debian/Ubuntu).

## Licenze

- **Testo originale:** © 2026 International Amateur Radio Union Region 1, licenza
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.it).
  Autori: Ahmad AlHoli 9K2DB, Marco Colombo IU2DXF, Frode Igland LA6VQ, Ian Suart GM4AUP;
  autore e curatore Rafal Lukawiecki EI6LA.
- **Traduzione italiana:** © 2026 i contributori di questo repository, licenza
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.it), come richiesto dalla licenza dell'originale.
- **Immagine di copertina:** © 2025 Silvano Ancelotti, licenza
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0); modificata rimuovendo il testo originale e il logo IARU.
- **Figure interne:** dall'edizione originale (immagini di EI6LA e IU2DXF), CC BY-SA 4.0.
- **Caratteri:** Source Serif e Source Sans, © Adobe, SIL Open Font License 1.1 (vedi `build/fonts/`).

La traduzione è stata realizzata con l'ausilio di strumenti di intelligenza artificiale.
Le note del traduttore sono segnalate con [N.d.T.]. Segnalazioni e correzioni sono benvenute tramite issue o pull request.
