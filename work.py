#!/usr/bin/env python3

import camelot
import pandas as pd

from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams  # Podešavanje parametara
from bs4 import BeautifulSoup

# python std lib
import os
from pathlib import Path
from io import StringIO
import glob
import re
import pickle
import sys

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


def preprocess_soup(soup):
    """Obrađuje BS4 objekte kako bi bili pogodniji za obradu"""
    for tag in soup.recursiveChildGenerator():
        if hasattr(tag, "attrs"):
            style = tag.attrs.get("style")
            if style:
                # inlinea style
                style = style_kv_obj(style)
                if style is not None:
                    for k, v in style.items():
                        tag.attrs[k] = v
                tag.attrs.pop("style")
    return soup


def pdf_soup(path):
    # Pretvorba iz PDFa u HTML pa u BS4 je dosta skupa, tako da pohranjujem
    # rezultate obrade za bržu iteraciju

    if not Path(path + ".html").is_file():
        print(f"Parsing {path} ... (not cached)")
        with open(path, "rb") as fin:
            output_string = StringIO()
            extract_text_to_fp(
                fin,
                output_string,
                laparams=LAParams(),
                output_type="html",
                codec=None,
            )

            soup = BeautifulSoup(output_string.getvalue(), "html.parser")
            print("Preprocessing...")
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
    pass


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


def find_dates(soup):
    spans = soup.find("span")
    for span in spans:
        content = span.text
        for kw in DATE_KEYWORDS:
            if kw in content.lower():
                print("FOund dates:", content)
                return parse_dates(content)
    raise Exception("Dates not found")


def apply_frame_cell(frame, key, name, f, soup):
    try:
        frame.loc[key, name] = f(soup)
    except Exception as e:
        print(f"Can't handle '{name}' in {key}:", e)


def handle_sample(path, soup):
    """Obrađuje jedan PDF dokument i vraća rezultate u obliku dictionarya"""
    document = pd.DataFrame(
        columns=["title", "authors", "received", "accepted", "published"]
    )

    key = os.path.splitext(os.path.basename(path))[0]

    apply_frame_cell(document, key, "title", find_title, soup)
    try:
        dates = find_dates(soup)
        document.loc[key, "received"] = dates["received"]
        document.loc[key, "accepted"] = dates["accepted"]
        document.loc[key, "published"] = dates["published"]
    except Exception as e:
        print(e)
        print(f"Can't handle 'dates' in {key}")

    return document


def run():
    for sample in glob.glob("./data/*.pdf"):
        # sekvencijalno obrađujemo uzorke jer su pohranjeni na HDDu, a i možda
        # budu zahtjevali previše radne memorije
        try:
            soup = pdf_soup(sample)
            document = handle_sample(sample, soup)

            document.to_csv(sample + ".out.csv")
            document.to_json(sample + ".out.json")
            document.to_excel(
                sample + ".out.xlsx"
            )  # grozan i nekonzistentan format ali ga normiji vole...
            document.to_pickle(sample + ".out.pkl")
        except Exception as e:
            print(str(e) + f"in {sample}.html")
            continue


if __name__ == "__main__":
    run()
