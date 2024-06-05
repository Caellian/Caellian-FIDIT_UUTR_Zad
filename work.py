#!/usr/bin/env python3

import camelot
import pandas as pd

import PyPDF2
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams  # Podešavanje parametara
from bs4 import BeautifulSoup
import psutil

# python std lib
import os
from pathlib import Path
from io import StringIO
import glob
import re
import pickle
from datetime import datetime
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

# sys.setrecursionlimit(8000)

DEBUG = True


def map_style_val(name, value):
    """Ovisno o imenu CSS atributa mapira/čisti njegovu vrijednost"""
    if name == "font-size":
        if value.endswith("px"):
            return value[:-2]
        else:
            raise Exception(f"Unknown font-size unit: {value}")
    return value


def style_kv_obj(style):
    """Mapira CSS style u Python objekte"""
    if not style or len(style) == 0:
        return None
    if style is object:
        # već obrađeno
        return style
    style = filter(
        lambda x: not len(x) == 0, map(lambda x: x.strip(), style.split(";"))
    )
    return {
        k.strip(): map_style_val(k.strip(), v.strip())
        for k, v in map(lambda x: x.split(":"), style)
    }


# preprocessanje da daljnji style string searchevi imaju bolje performanse
# inlinea style atribute na HTML tagove samo, no može se dodati još obrade tu
# poput odjeljivanja stranica i sl.
def preprocess_soup(soup):
    """Obrađuje BS4 objekte kako bi bili pogodniji za obradu"""
    for tag in soup.recursiveChildGenerator():
        if hasattr(tag, "attrs"):
            style = tag.attrs.get("style")
            if style:
                style = style_kv_obj(style)
                if style is not None:
                    for k, v in style.items():
                        tag.attrs[k] = v
                tag.attrs.pop("style")
    return soup


def repaired_pdf(path):
    """
    Pokušava popraviti dani PDF dokument i vraća putanju na popravljeni file.
    """
    # https://github.com/pdfminer/pdfminer.six/issues/476
    repaired_filename = f"{path.replace('.pdf', '_repaired.pdf')}"

    with open(path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        # Create a new PDF
        with open(repaired_filename, "wb") as new_file:
            writer = PyPDF2.PdfWriter()

            # Copy content from old to new
            for i in range(len(reader.pages)):
                writer.add_page(reader.pages[i])

            writer.write(new_file)
    return repaired_filename


def pdf_soup(path):
    """
    Učitava PDF dokument u BS4 objekte, provodeći preprocessanje ako je
    potrebno.

    Također popravlja PDF ako se nije uspješno otvorio.
    """
    # Pretvorba iz PDFa u HTML pa u BS4 je dosta skupa, tako da pohranjujem
    # rezultate obrade za bržu iteraciju

    if not Path(path + ".html").is_file():
        print(f"Parsing {path} ... (not cached)")
        output_string = StringIO()
        try:
            fin = open(path, "rb")
            extract_text_to_fp(
                fin,
                output_string,
                laparams=LAParams(),
                output_type="html",
                codec=None,
            )
        except PDFSyntaxError as err:
            print(f"Error parsing '{path}': ", err)
            print(f"Trying to repair '{path}' PDF...")

            fin = open(repaired_pdf(path), "rb")
            extract_text_to_fp(
                fin,
                output_string,
                laparams=LAParams(),
                output_type="html",
                codec=None,
            )
            return None
        finally:
            fin.close()

        soup = BeautifulSoup(output_string.getvalue(), "html.parser")
        print(f"Preprocessing {path} ...")
        soup = preprocess_soup(soup)
        with open(path + ".html", "w") as fout:
            fout.write(soup.prettify())
        print("Done")
        return soup

    else:
        print(f"Loading cached {path}.html ...")
        with open(path + ".html", "r") as fin:
            soup = BeautifulSoup(fin.read(), "html.parser")
            print("Done")
            return soup


RE_WHITESPACE = re.compile(r"[\n\t\s]+")


def normalize_str(content):
    return RE_WHITESPACE.sub(" ", content.strip())


# RE_TITLE_FONT = re.compile(r"(Times|AdvPS|MyriadPro|STIX|MathPack|FranklinGothic)")

# Podešava minimalnu veličinu fonta naslova; obično se samo page# nalazi prije
MIN_TITLE_FONT_SIZE = 15


def is_title(tag):
    if not tag.name == "span":
        return False

    size = tag.get("font-size")
    if size is None or int(size) < MIN_TITLE_FONT_SIZE:
        return False

    # Font je velik wildcart, vjerujem da je "prvi veliki tekst" dovoljno
    # font = tag.get("font-family")
    # if font is None or not bool(RE_TITLE_FONT.search(font)):
    #     return False

    return True


def find_title(soup):
    els = soup.find(is_title)
    if els is not None:
        return normalize_str(els.text)
    raise Exception("Title not found")


def find_authors(soup):
    raise Exception("Author not found")


def parse_dates(content):
    result = {}
    content = map(lambda it: it.strip(), content.split("/"))

    for c in content:
        phase = "published"
        if c.startswith("Received"):
            phase = "received"
        elif c.startswith("Accepted"):
            phase = "accepted"
        elif c.startswith("Published"):
            phase = "published"
        result[phase] = c.split(":", 1)[1].strip()

    return result


DATE_KEYWORDS = [
    "received",
    "accepted",
    "published",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def find_dates(soup):
    for span in soup.find_all("span"):
        content = span.text
        for kw in DATE_KEYWORDS:
            if kw in content.lower():
                line = next(filter(lambda it: kw in it.lower(), content.split("\n")))
                return parse_dates(line)
    raise Exception("Dates not found")


def apply_frame_cell(frame, key, soup, name, f):
    """
    Aplikator funkcije f na frame[key, name], koji javi pogrešku ako f ne
    uspije.
    """
    try:
        frame.loc[key, name] = f(soup)
    except Exception as e:
        print(f"Can't handle '{name}' in {key}.pdf.html: ", e)


def apply_frame_cells(frame, key, soup, cell_map):
    """
    apply_frame_cell samo radi na skupu parova imena i parsera
    """
    for k, v in cell_map.items():
        apply_frame_cell(frame, key, soup, k, v)


def handle_sample(path):
    """Obrađuje jedan PDF dokument i vraća rezultate u obliku DataFramea"""
    soup = pdf_soup(path)
    key = os.path.splitext(os.path.basename(path))[0]

    try:
        if Path(f"./out/{key}.gen.csv").is_file():
            print(f"Skipping {key} (already processed)")
            return (key, None)

        document = pd.DataFrame(
            columns=["title", "authors", "received", "accepted", "published"]
        )

        # ovdje je isto dobro mjesto za branchanje i paralelnu obradu, no već
        # smo iskoristili sve fizičke coreove branchanjem na osnovu ulaznih
        # datoteka
        apply_frame_cells(
            document, key, soup, {"title": find_title, "authors": find_authors}
        )
        # šteta apstrakcije kada postoje ovakve stvari
        try:
            dates = find_dates(soup)
            document.loc[key, "received"] = dates["received"]
            document.loc[key, "accepted"] = dates["accepted"]
            document.loc[key, "published"] = dates["published"]
        except Exception as e:
            print(f"Can't handle 'dates' in {key}.pdf.html: ", e)

        return (key, document)
    except Exception as e:
        print(f"{key} failed: ", e)
        return (key, None)


# Dozvoljava podešavanje parametara kroz environment variables
OUT_DIR = os.environ.get("OUT_DIR", "./out")
IN_DIR = os.environ.get("IN_DIR", "./data")

WORKER_COUNT = os.environ.get("WORKER_COUNT", psutil.cpu_count(logical=False))
# Možemo koristiti i argparse pa postaviti os.environ vrijednosti, no nije bitno
# za ovaj zadatak


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    tasks = glob.iglob(os.path.join(IN_DIR, "*.pdf"))

    # obrada zadataka u batchevima veličine WORKER_COUNT
    with ProcessPoolExecutor(max_workers=WORKER_COUNT) as executor:
        futures = {executor.submit(handle_sample, task): task for task in tasks}
        for future in as_completed(futures):
            name, doc = future.result()
            if doc is not None:
                doc.to_csv(os.path.join(OUT_DIR, name + ".gen.csv"))
                doc.to_json(os.path.join(OUT_DIR, name + ".gen.json"))
                doc.to_excel(os.path.join(OUT_DIR, name + ".gen.xlsx"))
                doc.to_pickle(os.path.join(OUT_DIR, name + ".gen.pkl"))


if __name__ == "__main__":
    run()
