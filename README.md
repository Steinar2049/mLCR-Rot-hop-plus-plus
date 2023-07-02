# mLCR-Rot-hop++

Source code for a neural approach with hierarchical rotary attention for Multilingual- and Cross-lingual Aspect-Based Sentiment
Classification.

## Installation

### Data

First, create a `data/raw` directory and download
the [SemEval 2015](http://alt.qcri.org/semeval2015/task12/index.php?id=data-and-tools), [SemEval 2016](http://alt.qcri.org/semeval2016/task5/index.php?id=data-and-tools)
datasets. Then rename the SemEval datasets to end up with the following files:

- `data/raw`
    - `ABSA15_Restaurants_Test.xml`
    - `ABSA15_Restaurants_Train.xml`
    - `ABSA16_Restaurants_Test.xml`
    - `ABSA16_Restaurants_Train.xml`

### Setup environment

Create a conda environment with Python version 3.10, the required packages and their versions are listed
in `requirements.txt`, note that you may need to install some packages using `conda install` instead of `pip install`
depending on your platform.

## Usage

To view the available cli args for a program, run `python [FILE] --help`. These CLI args can for example be used to pick
the year of the dataset. Note that the files include an ontology reasoner, and an ontology injection method, which can be used to enhance the final performance of the models. This research did not utilize an ontology reasoner nor the injection method. For descriptions to use this method, see https://github.com/wesselvanree/LCR-Rot-hop-ont-plus-plus.git.

- `main_clean.py`: remove opinions that contain implicit targets and invalid targets due to translation or Aspect-Code-Switching
- `main_translate.py`: contains all functions needed to create Multilingual datasets, a description of how to run each model is given below. Our version uses Google API for translation.
- `main_embed.py`: generate embeddings, these embeddings are used by the other programs. To generate all embeddings for a given year, run `python main_preprocess.py --all`
- `main_hyperparam.py`: run hyperparameter optimization
- `main_train.py`: train the model for a given set of hyperparameters
- `main_validate.py`: validate a trained model.

## Models
### mLCR-Rot-hop++
Run `main_clean.py` on the English train and test datasets, which is selected by passing either "Train" or "Test" as parameter inputs for the variable "phase". Second, create embeddings, which is done with `main_embed.py` Then, run `main_hyperparam.py`, which provides a checkpoint file in the "data" folder, which contains the hyperparameter values needed to be changed in `main\_train.py`. After updating the hyperparameters manually, run `main_train.py`, which gives a model as output, ready to be tested. Last, validate the model with `main_validate.py`, which outputs the performance measures.

To run the original LCR-Rot-hop++ of [ref], the original BERT embeddings are preferred. Therefore, it is necessary to go to the "bert_encoder" directory under the "model" directory. There, the "tokenizer" and "model" on line 10 and 11 need to be given "bert-base-cased"  as input instead of "bert-base-multilingual-cased". Afterward, the procedure is identical to described above.

### mLCR-Rot-hop-XX++
For these models, the same procedure as in mLCR-Rot-hop++ can be followed. However, the data corresponding to the language XX should be used for training and testing.

### MLCR-Rot-hop++
To run MLCR-Rot-hop++, the English, Dutch, French, Spanish cleaned training data files have to be combined. This is done by the "MLCR-Rot-hop++" function in `main_translate.py` After combining all into the multilingual dataset, the rest of the procedure is the same as for mLCR-Rot-hop++.

### mLCR-Rot-hop-XXen++
For this model translation is necessary. Hence, the english training data first needs to be marked with the `mark_data.py` function in `main_translate.py`. Then the translation is done by running the `translate_data.py` function and specifying the target language as an input parameter. After runnning translation the markings need to be removed. That is done by the function "remove_symbols". After that the file has to be cleaned again by `main_clean.py` to remove opinions for which the translation failed. Then it can be run the same as the other models above.

### mLCR-Rot-hop-ACSxx
To run the model, which implements Aspect-Code-Switching, the same marked data created in the process for mLCR-Rot-hop-XXen and translated data, with markings, are used. The function Aspect-Code-Switching needs to be called and creates two more datasets with markings. Then all markings need to be removed per dataset with the function "remove_symbols". Afterward, all files need to be cleaned again to remove any failed switches. Then the function "join_datasets_ACS" needs to be called to combine the four datasets for one ACS model with xx as target language.

### SLCR-Rot-hop++
For this model, the original LCR-Rot-hop++ trained model is used. The only requirement is to now perform translation on the English test data, which is done in the same way as for mLCR-Rot-hop-XXen. After translating, removing symbols, and cleaning, the data has to be embedded using `main_embed.py`.
The model can then be validated using these embeddings by running `main_validate.py` while specifying the language of the test data and that it is translated by writing the language and then "Translated". For, example DutchTranslated.


## Acknowledgements
This repository is based on the source code of https://github.com/wesselvanree/LCR-Rot-hop-ont-plus-plus.git.
The `model.bert_encoder` module uses code from:

- Liu, W., Zhou, P., Zhao, Z., Wang, Z., Ju, Q., Deng, H., Wang, P.: K-BERT: Enabling language representation with
  knowledge graph. In: 34th AAAI Conference on Artificial Intelligence. vol. 34, pp. 2901–2908. AAAI Press (2020)
- https://github.com/Felix0161/KnowledgeEnhancedABSA 
