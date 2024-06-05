# Praktični zadatak

Kolegij: **Uvod u teorijsko računarstvo**

Nositelj predmeta: Prof. dr. sc. Sanda Martinčić-Ipšić

Asistent: Andrija Poleksić, mag. inf.

Autor koda: Tin Švagelj

Licenca: Apache 2.0/zlib/MIT

## Izvor podataka

Kao izvor podataka je korišten skup časopisa [`Climate Dynamics (2021)`](https://link.springer.com/journal/382) © Springer-Verlag GmbH Germany.

## Korišteni alati/biblioteke

- beautiful soup (`beautifulsoup4`)
- pdfminer (`pdfminer.six`)
- camelot (`camelot`)
- pandas (`pandas`)
- python std lib

### Utilities

- PyPDF2
  - za popravak "potrganih" PDFova
  - CI javlja grešku da su "/Root" dokumenta ne postoji (ne lokalno)
- psutil (`psutil`)
  - broj fizičkih jezgri procesora

### Radno okruženje

- pipenv (pip + virtualenv)
- VSCode (`code` + `code-marketplace` + `code-features-insiders`)
  - Python (Microsoft)
  - Cody

## Struktura spremljenih podataka

Podaci su spremljeni u `json`, `csv`, `xlsx` i `pkl` formatima.

## Korišteni materijali

- 