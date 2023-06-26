import argparse
import os
import json
import xml.etree.ElementTree as ElementTree

import deep_translator
import translators as ts
from deep_translator import GoogleTranslator, DeeplTranslator
# requests = "~=2.27"
# python-lokalise-api = "~=1.6"
# python-dotenv = "~=0.20"
# googletrans = "==4.0.0rc1"
# translators = "~= 5.4"
# deep-translator = "~=1.9"


def make_symbols():
    symbols = ["[]", "{}", "<>", "%%", "^^", "``", "~~"]
    return symbols


def extract_marked_word(sentence: str, symbol: str):
    # print("extracting word from: " + sentence + "with symbol: " + symbol)
    substrings = sentence.split(symbol[0])
    substring1 = substrings[1]
    substrings2 = substring1.split(symbol[1])
    extraction = substrings2[0]
    return extraction


def mark_data(year:int, phase: str, language: str):
    print("Running marking")
    filename = f"ABSA{year % 2000}_Restaurants_{phase}_{language}.xml"
    filename_marked = f"ABSA{year % 2000}_Restaurants_{phase}_{language}Marked.xml"
    input_path = f"data/processed/{filename}"
    output_path = f"data/marked/{filename_marked}"
    tree = ElementTree.parse(input_path)
    symbols = make_symbols()

    for sentence in tree.findall(".//sentence"):
        text_element = sentence.find(".//text")
        aspects: list = []
        for opinion in sentence.findall(".//Opinion"):
            aspect = opinion.attrib['target']
            if not aspects.__contains__(aspect):
                aspects.append(aspect)

        for word in aspects:
            if text_element.text.__contains__(word):
                print(aspects[aspects.index(word)] + "at" + aspects.index(word).__str__())
                brackets = symbols[aspects.index(word)]
                first_bracket = brackets[0]
                second_bracket = brackets[1]

                # Mark the aspect word by replacing the original string with the word surrounded by brackets
                # Note: only the first occurrence is replaced to avoid double marking
                new_text = text_element.text.replace(word, first_bracket + word + second_bracket, 1)
                text_element.text = new_text

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path)
    print("Marking done")


def translate_data(year:int, phase: str, source_language: str, target_language: str):
    print("Running translation")
    filename = f"ABSA{year % 2000}_Restaurants_{phase}_{source_language}Marked.xml"
    filename_translated = f"ABSA{year % 2000}_Restaurants_{phase}_{target_language}Translated.xml"
    input_path = f"data/marked/{filename}"
    output_path = f"data/translated/{filename_translated}"
    tree = ElementTree.parse(input_path)

    target = ''
    if target_language == "Dutch":
        target = 'nl'
    elif target_language == "French":
        target = 'fr'
    elif target_language == "Spanish":
        target = 'es'

    translator = GoogleTranslator(source='auto', target=target)

    symbol_list = make_symbols()

    for sentence in tree.findall(".//sentence"):
            sentence_text = sentence.find(".//text").text
            # In case if the review only contains numeric values
            if sentence_text.isnumeric():
                continue

            translation = translator.translate(sentence_text)
            sentence.find(".//text").text = translation
            aspect_missing_list = []
            aspect_translated_list = []

            for symbol in symbol_list:
                first_symbol = symbol[0]

                # Preparing list of aspects in target language and collecting missing aspects
                if translation.__contains__(first_symbol):
                    aspect_translated = extract_marked_word(translation, symbol)
                    aspect_translated_list.append(aspect_translated)
                elif sentence_text.__contains__(first_symbol) and not translation.__contains__(first_symbol):
                    aspect_missing = extract_marked_word(sentence_text, symbol)
                    aspect_missing_list.append(aspect_missing)

            opinions = sentence.findall(".//Opinion")
            already_translated_aspects = []
            for opinion in opinions:
                original_aspect = opinion.attrib['target']
                if aspect_missing_list.__contains__(original_aspect):
                    opinion.attrib['text'] = translator.translate(original_aspect)
                elif already_translated_aspects.__contains__(opinion.attrib['target']):
                    for previous_aspect in already_translated_aspects:
                        if opinion.attrib['target'] == previous_aspect:
                            opinion.attrib['target'] = aspect_translated_list[already_translated_aspects.index(previous_aspect)]
                else:
                    print(aspect_translated_list.__str__())
                    print(len(already_translated_aspects))
                    # print(already_translated_aspects.__str__())
                    opinion.attrib['target'] = aspect_translated_list[len(already_translated_aspects)]
                    # print("target updated")
                    already_translated_aspects.append(original_aspect)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path)


def aspect_code_switching(year:int, phase:str, source:str, target:str):
    print("Runnning ACS")
    filename_source = f"ABSA{year % 2000}_Restaurants_{phase}_{source}Marked.xml"
    filename_target = f"ABSA{year % 2000}_Restaurants_{phase}_{target}Translated.xml"
    filename_st = f"ABSA{year % 2000}_Restaurants_{phase}_{source}to{target}ACS.xml"
    filename_ts = f"ABSA{year % 2000}_Restaurants_{phase}_{target}to{source}ACS.xml"

    source_path = f"data/marked/{filename_source}"
    target_path = f"data/translated/{filename_target}"
    st_path = f"data/acs/{filename_st}"
    ts_path = f"data/acs/{filename_ts}"

    tree_source = ElementTree.parse(source_path)
    tree_target = ElementTree.parse(target_path)
    symbols = make_symbols()
    all_source_sentences = tree_source.findall(".//sentence")

    for sentence_source in all_source_sentences:
        source_text = sentence_source.find(".//text").text

        sentence_target = tree_target.findall(".//sentence")[all_source_sentences.index(sentence_source)]
        target_text = sentence_target.find(".//text").text

        # Switch each source aspect with each corresponding target aspect
        for symbol in symbols:

            # Only operates when sentence contains marking for aspect in source and target text
            if source_text.__contains__(symbol[0]) and target_text.__contains__(symbol[0]):
                source_aspect = extract_marked_word(source_text, symbol)
                target_aspect = extract_marked_word(target_text, symbol)

                # Replacing in source data
                # Replace source text with marked target aspect
                sentence_source.find(".//text").text = sentence_source.find(".//text").text.replace(source_aspect, target_aspect)

                # Replace source labels with target labels
                for opinion in sentence_source.findall(".//Opinion"):
                    if opinion.attrib['target'] == source_aspect:
                        opinion.attrib['target'] = target_aspect

                # Replacing in target data
                # Replace target text with marked source aspect
                sentence_target.find(".//text").text = sentence_target.find(".//text").text.replace(target_aspect, source_aspect)

                # Replace target labels with source labels
                for opinion in sentence_target.findall(".//Opinion"):
                    if opinion.attrib['target'] == target_aspect:
                        opinion.attrib['target'] = source_aspect

    tree_source.write(st_path)
    tree_target.write(ts_path)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--year", default=2016, type=int, help="The year of the dataset (2015 or 2016)")
    parser.add_argument("--phase", default="Train", help="The phase of the dataset (Train or Test)")
    parser.add_argument("--source", default="English", type=str, help="The language of the dataset")
    parser.add_argument("--target", default="Dutch", type=str, help="The target language")

    args = parser.parse_args()

    year: int = args.year
    phase: str = args.phase
    source: str = args.source
    target: str = args.target

    mark_data(year, phase, source)
    translate_data(year, phase, source, target)
    aspect_code_switching(year, phase, source, target)

    # ts = GoogleTranslator(source='auto', target='nl')
    # what = ts.translate("The restaurant has a Family [feel], not least with regard to the {portions} which are enormous; the (veal) alone could have single-handedly solve")
    # print(what)
    # word = extract_marked_word(what, "[]")
    # print(word)


if __name__ == "__main__":
    main()
