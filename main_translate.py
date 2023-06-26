import argparse
import os
import os.path
import glob
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
    symbols = ["[]", "{}", "<>", "%%", "^^", "``", "~~", "○○"]
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
    input_path = f"data/raw/{filename}"
    output_path = f"data/marked/{filename_marked}"
    tree = ElementTree.parse(input_path)
    symbols = make_symbols()

    for sentence in tree.findall(".//sentence"):
        text_element = sentence.find(".//text")
        sentence_text = text_element.text
        opinions = sentence.findall(".//Opinion")
        sorted_opinions = sorted(opinions, key= lambda x: int(x.attrib['from']))
        opinions.sort(key=lambda x: int(x.attrib['from']))

        last_start = ''
        k = 0
        for sorted_opinion in opinions:
            symbol = symbols[k]
            start = int(sorted_opinion.attrib['from'])
            end = int(sorted_opinion.attrib['to'])

            if sorted_opinion.attrib['target'] == "NULL":
                continue

            print("target: " + sorted_opinion.attrib['target'] + " start: " + sorted_opinion.attrib['from'] + " last: " + last_start)
            if not sorted_opinion.attrib['from'] == last_start:
                start = start + 2*k
                end = end + 2*k

                sentence_text = sentence_text[:start] + symbol[0] + sentence_text[start:end] + symbol[1] + sentence_text[end:]

                sentence.find(".//text").text = sentence_text
                last_start = start.__str__()
                k += 1

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

    symbols = make_symbols()

    for sentence in tree.findall(".//sentence"):
            sentence_text = sentence.find(".//text").text
            # In case if the review only contains numeric values
            if sentence_text.isnumeric():
                continue

            translation = translator.translate(sentence_text)
            sentence.find(".//text").text = translation
            sentence_text = translation
            previous_positions = []
            previous_opinions = []
            double_opinions = []

            opinions = sentence.findall(".//Opinion")
            for opinion in opinions:
                position = [opinion.attrib['from'], opinion.attrib['to']]
                if previous_positions.__contains__(position):
                    opinion.attrib['from'] = "same as " + previous_positions.index(position).__str__()
                    double_opinions.append(opinion)
                else:
                    previous_opinions.append(opinion)
                    previous_positions.append(position)

            i = 0
            # Update aspect text with translation and update position
            for opinion in sentence.findall(".//Opinion"):
                if opinion.attrib['target'] == "NULL":
                    continue

                symbol = symbols[i]
                if double_opinions.__contains__(opinion):
                    continue

                # If brackets still in translation, extract aspect and update position
                elif sentence_text.__contains__(symbol[0]) and symbol.__contains__(symbol[1]):
                    aspect = extract_marked_word(sentence_text, symbol)
                    opinion.attrib['target'] = aspect
                    start = sentence_text.find(symbol[0]) + 1
                    end = sentence_text.rfind(symbol[1])
                    opinion.attrib['from'] = start.__str__()
                    opinion.attrib['to'] = end.__str__()

                    previous_positions.append([start.__str__(), end.__str__()])
                    previous_opinions.append(opinion)
                    i += 1

                else:
                    # sentence.findall(".//Opinion").remove(opinion)
                    opinion.attrib['target'] = "NULL"

                    i += 1

            for double in double_opinions:
                brother_index = int(double.attrib['from'][8])
                brother = previous_opinions[brother_index]
                double.attrib['target'] = brother.attrib['target']
                double.attrib['from'] = brother.attrib['from']
                double.attrib['to'] = brother.attrib['to']

    # #Removing NULL opinions
    # # remove implicit targets
    # n_null_removed = 0
    # for opinions in tree.findall(".//Opinions"):
    #     for opinion in opinions.findall('./Opinion[@target="NULL"]'):
    #         opinions.remove(opinion)
    #         n_null_removed += 1
    #
    # # calculate descriptive statistics for remaining opinions
    # n = 0
    # n_positive = 0
    # n_negative = 0
    # n_neutral = 0
    # for opinion in tree.findall(".//Opinion"):
    #     n += 1
    #
    #     if opinion.attrib['polarity'] == "positive":
    #         n_positive += 1
    #     elif opinion.attrib['polarity'] == "negative":
    #         n_negative += 1
    #     elif opinion.attrib['polarity'] == "neutral":
    #         n_neutral += 1
    #
    # if n == 0:
    #     print(f"\n{filename} does not contain any opinions")
    # else:
    #     print(f"\n{filename}")
    #     print(f"  Removed {n_null_removed} opinions with target NULL")
    #     print(f"  Total number of opinions remaining: {n}")
    #     print(f"  Fraction positive: {100 * n_positive / n:.3f} %")
    #     print(f"  Fraction negative: {100 * n_negative / n:.3f} %")
    #     print(f"  Fraction neutral: {100 * n_neutral / n:.3f} %")

    tree.write(output_path)


def aspect_code_switching(year: int, phase: str, source: str, target: str):
    print("Running ACS")
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
                    # Make sure current aspect is equal to the one in the sentence
                    if opinion.attrib['target'] == "NULL":
                        continue

                    if opinion.attrib['target'] == source_aspect:
                        opinion.attrib['target'] = target_aspect

                # Replacing in target data
                # Replace target text with marked source aspect
                sentence_target.find(".//text").text = sentence_target.find(".//text").text.replace(target_aspect, source_aspect)

                # Replace target labels with source labels
                for opinion in sentence_target.findall(".//Opinion"):
                    if opinion.attrib['target'] == "NULL":
                        continue

                    if opinion.attrib['target'] == target_aspect:
                        opinion.attrib['target'] = source_aspect

    # Update positions in source to target data
    for sentence_source in tree_source.findall(".//sentence"):
        source_text = sentence_source.find(".//text").text
        previous_positions = []
        double_opinions = []
        new_positions = []
        for opinion in sentence_source.findall(".//Opinion"):
            if opinion.attrib["target"] == "NULL":
                continue
            position = [opinion.attrib['from'], opinion.attrib['to']]
            if previous_positions.__contains__(position):
                opinion.attrib['from'] = previous_positions.index(position).__str__()
                double_opinions.append(opinion)
            else:
                previous_positions.append(position)
        k = 0
        for opinion in sentence_source.findall(".//Opinion"):
            if opinion.attrib['target'] == "NULL":
                continue

            symbol = symbols[k]
            if not double_opinions.__contains__(opinion):
                new_start = source_text.find(symbol[0]) + 1
                new_end = source_text.rfind(symbol[1])
                opinion.attrib['from'] = new_start.__str__()
                opinion.attrib['to'] = new_end.__str__()
                new_positions.append([new_start.__str__(), new_end.__str__()])
                k += 1

        for double in double_opinions:
            brother_index = int(double.attrib['from'])
            brother_position = new_positions[brother_index]
            double.attrib['from'] = brother_position[0]
            double.attrib['to'] = brother_position[1]

    # Update positions in target to source data
    for sentence_target in tree_target.findall(".//sentence"):
        target_text = sentence_target.find(".//text").text
        previous_positions = []
        double_opinions = []
        new_positions = []
        for opinion in sentence_target.findall(".//Opinion"):
            if opinion.attrib['target'] == "NULL":
                continue

            position = [opinion.attrib['from'], opinion.attrib['to']]
            if previous_positions.__contains__(position):
                opinion.attrib['from'] = previous_positions.index(position).__str__()
                double_opinions.append(opinion)
            else:
                previous_positions.append(position)
        k = 0
        for opinion in sentence_target.findall(".//Opinion"):
            if opinion.attrib['target'] == "NULL":
                continue

            symbol = symbols[k]
            if not double_opinions.__contains__(opinion):
                new_start = target_text.find(symbol[0]) + 1
                new_end = target_text.rfind(symbol[1])
                opinion.attrib['from'] = new_start.__str__()
                opinion.attrib['to'] = new_end.__str__()
                new_positions.append([new_start.__str__(), new_end.__str__()])
                k += 1

        for double in double_opinions:
            brother_index = int(double.attrib['from'])
            brother_position = new_positions[brother_index]
            double.attrib['from'] = brother_position[0]
            double.attrib['to'] = brother_position[1]
    tree_source.write(st_path)
    tree_target.write(ts_path)


def remove_symbols(filename):
    tree = ElementTree.parse(filename)
    symbols = make_symbols()
    for sentence in tree.findall(".//sentence"):
        text_element = sentence.find(".//text")
        sentence_text = text_element.text
        already_changed = []
        opinions = sentence.findall(".//Opinion")
        # Find corresponding opinion

        opinions.sort(key=lambda x: int(x.attrib['from']))

        last_from = ''
        last_to = ''
        k = 0
        for opinion in opinions:
            if opinion.attrib['from'] != last_from and opinion.attrib['to'] != last_to:
                # Determine new aspect boundaries
                last_from = opinion.attrib['from']
                last_to = opinion.attrib['to']

                print("marked: " + opinion.attrib['from'])
                from_int = int(opinion.attrib['from']) - 1 - 2 * k
                to_int = int(opinion.attrib['to']) - 1 - 2 * k
                print("adjusted: " + from_int.__str__())
                opinion.attrib['from'] = from_int.__str__()
                opinion.attrib['to'] = to_int.__str__()


                k += 1
            else:
                # Same boundaries as previous
                opinion.attrib['from'] = from_int.__str__()
                opinion.attrib['to'] = to_int.__str__()

        # Remove symbols
        for symbol in symbols:
            sentence_text = sentence_text.replace(symbol[0], "", 1)
            sentence_text = sentence_text.replace(symbol[1], "", 1)

        sentence.find(".//text").text = sentence_text

    tree.write(filename)


def join_datasets(year, phase, source, target):
    filename_source = f"ABSA{year % 2000}_Restaurants_{phase}_{source}Marked.xml"
    filename_target = f"ABSA{year % 2000}_Restaurants_{phase}_{target}Translated.xml"
    filename_st = f"ABSA{year % 2000}_Restaurants_{phase}_{source}to{target}ACS.xml"
    filename_ts = f"ABSA{year % 2000}_Restaurants_{phase}_{target}to{source}ACS.xml"

    filename_acs = f"ABSA{year % 2000}_Restaurants_{phase}_XACSfor{target}.xml"

    source_path = f"data/processed/{filename_source}"
    target_path = f"data/processed/{filename_target}"
    st_path = f"data/processed/{filename_st}"
    ts_path = f"data/processed/{filename_ts}"

    acs_path = f"data/processed/{filename_acs}"
    xml_files = [source_path, target_path, st_path, ts_path]

    root = ElementTree.Element("Reviews")
    forest = ElementTree.ElementTree(root)

    for file in xml_files:
        tree = ElementTree.parse(file)
        reviews = tree.findall(".//Review")
        root.extend(reviews)

    forest.write(acs_path)


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

    # mark_data(year, phase, source)
    # translate_data(year, phase, source, target)
    # remove_symbols(f"data/processed/ABSA{year % 2000}_Restaurants_{phase}_{target}.xml")

    aspect_code_switching(year, phase, source, target)
    # join_datasets(year, phase, source, target)


if __name__ == "__main__":
    main()
