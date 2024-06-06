# Praktični zadatak
|||
|-:|:-:|
|Kolegij|**Uvod u teorijsko računarstvo**|
|Nositelj predmeta|Prof. dr. sc. Sanda Martinčić-Ipšić|
|Asistent|Andrija Poleksić, mag. inf.|

## Izvor podataka

Kao izvor podataka je korišten skup časopisa [`Climate Dynamics (2021)`](https://link.springer.com/journal/382) © Springer-Verlag GmbH Germany.

## Korišteni alati/biblioteke

- beautiful soup (`beautifulsoup4`)
- pdfminer (`pdfminer.six`)
- camelot (`camelot`)
- pandas (`pandas`)
- openpyxl (`openpyxl`)
  - podržka za `xlsx` format
- PyPDF2 (`pypdf2`)
  - za popravak "potrganih" PDFova
- psutil (`psutil`)
  - broj fizičkih jezgri procesora za idealnu paralelizaciju
- python std lib

Popis se može naći u [`Pipfile`](./Pipfile) datoteci (gornji nije nužno ažuran).

### Radno okruženje

- `pipenv` (pip + virtualenv)
- `flake8` linter
- VSCode (`code` + `code-marketplace` + `code-features-insiders`)
  - Python (Microsoft)
  - Cody

## Struktura spremljenih podataka

Podaci su spremljeni u `json`, `csv`, `xlsx` i `pkl` formatima.

Strukturirani formati koriste sljedeći format:
```json
{
  "title": "Naslov publikacije",
  "authors": [ "Popis", "imena", "autora" ],
  "received": "Datum zaprimanja publikacije",
  "accepted": "Datum prihvaćanja publikacije",
  "published": "Datum objave publikacije",
}
```

- Nestrukturirani formati pohranjuju strukture tako što odvajaju imena
  ugježđenih podataka točkom od vrhovnih imena.
  - Liste u nestrukturiranim podacima se tretiraju kao strukture sa `length`
    ključem, a indeksi su umetnuti kao ugježđena komponenta.

### Nedostaci

- Tekst nije uvijek ispravan jer konverzija iz PDF formata ne očuva dijakritičke znakove (npr. `é` postane `e´`)
  - Skripta podržava sve službene UNICODE simbole, u trenutku kada ekstrakcija
    teksta prestane odvajati modifikatore slova od slova, regularni izrazi za
    ekstrakciju informacija mogu biti precizniji. Radi se o ograničenju
    formata/alata na koje se skripta oslanja.

## Korišteni materijali

- Stack Overflow
  - Sve od najjednostavnijih stvari poput "bs4 check if attribute exists" do
    "how to parallelize a loop"
- Bing Copilot
  - Kada nisam bio siguran kako formulirati search query za tražilicu (tj. nisam
    dobivao rezultate)
  - Nisam generirao ni jednu cijelu funkciju njime jer mi je lakše debuggat
    svoje pogreške.
- Cody (mislim da koristi Claude 3 Opus)
  - Autocompletion na osnovu postojećeg koda i neke sitnice da ne tražim osnovne
    stvari poput `os.path.join` (jer ne koristim Python puno; a ne pamtim dobro
    stdlib jezika ako ih aktivno ne koristim)

Vjerujem da je to razumna razina oslanjanja na LLMove jer nadomještava "kopanje
po internetu".

## Licenca/License

Kod u repozitoriju je licenciran terenarnom Apache 2.0/zlib/MIT, koristite
željenu. PDF datoteke u `data/` direktoriju sadrže sukladne podatke o vlasništvu
i koriste se kao popratni materijal (za obradu), javno su dostupne (otvoreni
pristup).

Code in this repository is licensed under Apache 2.0/zlib/MIT terenary license,
adhere to whichever you prefer. PDF files in `data/` directory contain
respective copyright information and are used as a reference material (for
processing examples), they are publicly available (open access).

If you want PDFs in `data/` directory to be removed, feel free to contact me and
I'll aim to remove them as soon as practicable.
