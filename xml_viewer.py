import argparse
import os
import os.path
import glob
import json
import xml.etree.ElementTree as ElementTree

def view(year, phase, language, dirname):
    filename = f"ABSA{year % 2000}_Restaurants_{phase}_{language}.xml"

    path = f"data/{dirname}/{filename}"

    tree = ElementTree.parse(path)
    i = 0
    for sentence in tree.findall(".//sentence"):
        print(sentence.find(".//text").text + i.__str__())
        i = i + 1

def main():
    # parse CLI args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--year", default=2016, type=int, help="The year of the dataset (2015 or 2016)")
    parser.add_argument("--phase", default="Train", help="The phase of the dataset (Train or Test)")
    parser.add_argument("--language", default="English", type=str, help="The language of the dataset")
    parser.add_argument("--dirname", default="raw", type=str, help="The language of the dataset")
    args = parser.parse_args()

    year: int = args.year
    phase: str = args.phase
    language: str = args.language
    dirname: str = args.dirname

    view(year, phase, language, dirname)


if __name__ == "__main__":
    main()