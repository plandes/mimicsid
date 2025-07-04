# MIMIC-III corpus parsing and section prediction with MedSecId

[![PyPI][pypi-badge]][pypi-link]
[![Python 3.11][python311-badge]][python311-link]
[![Build Status][build-badge]][build-link]

This repository contains the a Python package to automatically segment and
identify sections of clinical notes, such as electronic health record (EHR)
medical documents.  It also provides access to the MedSecId section annotations
with MIMIC-III corpus parsing from the paper [A New Public Corpus for Clinical
Section Identification: MedSecId].  See the [medsecid repository] to reproduce
the results from the paper.

This package provides the following:

* The same access to MIMIC-III data as provided in the [mimic package].
* Access to the annotated MedSecId notes as an easy to use Python object graph.
* The pretrained model inferencing, which produces a similar Python object
  graph to the annotations (provides the class `PredictedNote` instead of an
  `AnnotatedNote` class.


<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
## Table of Contents

- [Documentation](#documentation)
- [Installation](#installation)
- [Usage](#usage)
    - [Prediction Usage](#prediction-usage)
    - [Annotation Access](#annotation-access)
- [Models](#models)
    - [MedCAT Models](#medcat-models)
    - [Performance Metrics](#performance-metrics)
        - [Version 0.1.1](#version-011)
        - [Version 0.1.0](#version-010)
        - [Version 0.0.3](#version-003)
        - [Version 0.0.2](#version-002)
- [Differences from the Paper Repository](#differences-from-the-paper-repository)
    - [Model Differences](#model-differences)
- [Training](#training)
    - [Preprocessing Step](#preprocessing-step)
    - [Training and Testing](#training-and-testing)
- [Training Production Models](#training-production-models)
- [Citation](#citation)
- [Docker](#docker)
- [Changelog](#changelog)
- [Community](#community)
- [License](#license)

<!-- markdown-toc end -->


## Documentation

See the [full documentation](https://plandes.github.io/mimicsid/index.html).
The [API reference](https://plandes.github.io/mimicsid/api.html) is also
available.


## Installation

Because the this library has many dependencies and many moving parts, it is
best to create a new environment using [conda]:

```bash
wget https://github.com/plandes/mimicsid/raw/refs/heads/master/environment.yml
conda env create -f environment.yml
conda activate mimicsid
```

The library can also installed with pip from the [pypi] repository:
```bash
pip3 install zensols.mimicsid
```

The models used by the package are automatically downloaded on the first use.

If you only want to predict sections using the pretrained model, you need only
to [install](#obtaining) the package.  However, if you want to access the
annotated notes, you must install a Postgres MIMIC-III database as [mimic
package install section].


## Usage

This package provides models to predict sections of a medical note and access
to the MIMIC-III section annotations available on [Zenodo].  The first time it
is run it will take a while to download the annotation set and the pretrained
models.

See the [examples](example) for the complete code and additional documentation.


### Prediction Usage

The `SectionPredictor` class creates section annotation span IDs/types and
header token spans.  See the example below:

```python
from zensols.nlp import FeatureToken
from zensols.mimic import Section
from zensols.mimicsid import PredictedNote, ApplicationFactory
from zensols.mimicsid.pred import SectionPredictor

if (__name__ == '__main__'):
    # get the section predictor from the application context in the app
    section_predictor: SectionPredictor = ApplicationFactory.section_predictor()

    # read in a test note to predict
    with open('../../test-resources/note.txt') as f:
        content: str = f.read().strip()

    # predict the sections of read in note and print it
    note: PredictedNote = section_predictor.predict([content])[0]
    note.write()

    # iterate through the note object graph
    sec: Section
    for sec in note.sections.values():
        print(sec.id, sec.name)

    # concepts or special MIMIC tokens from the addendum section
    sec = note.sections_by_name['history-of-present-illness'][0]
    tok: FeatureToken
    for tok in sec.body_doc.token_iter():
        print(tok, tok.mimic_, tok.cui_)
```


### Annotation Access

Annotated notes are provided as a Python [Note class], which contains most of
the MIMIC-III data from the `NOTEEVENTS` table.  This includes not only the
text, but parsed `FeatureDocument` instances.  However, you must build a
Postgres database and provide a login to it in the application as detailed
below:

```python
from zensols.config import IniConfig
from zensols.mimic import Section
from zensols.mimicsid import ApplicationFactory
from zensols.mimic import Note
from zensols.mimicsid import AnnotatedNote, NoteStash

if (__name__ == '__main__'):
    # create a configuration with the Postgres database login
    config = IniConfig('db.conf')
    # get the `dict` like data structure that has notes by `row_id`
    note_stash: NoteStash = ApplicationFactory.note_stash(
        **config.get_options(section='mimic_postgres_conn_manager'))

    # get a note by `row_id`
    note: Note = note_stash[14793]

    # iterate through the note object graph
    sec: Section
    for sec in note.sections.values():
        print(sec.id, sec.name)
```


## Models

You can mix and match models across section vs. header models (see [Performance
Metrics](#performance-metrics)).  By default the package uses the best
performing models but you can select the model you want by adding a
configuration file and specifying it on the command line with `-c`:

```ini
[mimicsid_default]
section_prediction_model = bilstm-crf-tok-fasttext
header_prediction_model = bilstm-crf-tok-glove-300d
```

The resources live on [Zenodo] and are automatically downloaded on the first
time the program is used in the `~/.cache` directory (or similar home directory
on Windows).


### MedCAT Models

The dependency [mednlp package] package uses the [default MedCAT
model](https://github.com/plandes/mednlp#medcat-models).



### Performance Metrics

The distributed models add in the test set to the training set to improve the
performance for inferencing, which is why only the validation metrics are
given.  The validation set performance of the pretrained models are given
below, where:

* **wF1** is the weighted F1
* **mF1** is the micro F1
* **Mf1** is the macro F1
* **acc** is the accuracy

Fundamental API changes have necessitated subsequent versions of the model.
Each version of this package is tied to a model version.  While some minor
changes of each version might present language parsing differences such as
sentence chunking, metrics are most likely statistically insignificant.


#### Version 0.1.1

The version was released to accommodate for Zensols framework upgrades.

| Name                          | Type    | Id                                     |   wF1 |   mF1 |   MF1 |   acc |
|-------------------------------|---------|----------------------------------------|-------|-------|-------|-------|
| `BiLSTM-CRF_tok (fastText)`   | Section | bilstm-crf-tok-fasttext-section-type   | 0.921 | 0.929 | 0.787 | 0.929 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Section | bilstm-crf-tok-glove-300d-section-type | 0.939 | 0.944 | 0.841 | 0.944 |
| `BiLSTM-CRF_tok (fastText)`   | Header  | bilstm-crf-tok-fasttext-header         | 0.996 | 0.996 | 0.961 | 0.996 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Header  | bilstm-crf-tok-glove-300d-header       | 0.996 | 0.996 | 0.962 | 0.996 |



#### Version 0.1.0

Adding biomedical NER improved the `0.1.0` models (see [Model
Differences](#model-differences)).  In addition to the reported validation
scores of the production models below, the `BiLSTM-CRF_tok (GloVE 300D)`
section model achieved an improved weighted F1 of 0.9572, micro F1 of 0.959,
macro F1 of 0.8163.

| Name                          | Type    | Id                                     | wF1   | mF1   | MF1   | acc   |
|-------------------------------|---------|----------------------------------------|-------|-------|-------|-------|
| `BiLSTM-CRF_tok (fastText)`   | Section | bilstm-crf-tok-fasttext-section-type   | 0.923 | 0.933 | 0.764 | 0.933 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Section | bilstm-crf-tok-glove-300d-section-type | 0.936 | 0.941 | 0.810 | 0.941 |
| `BiLSTM-CRF_tok (fastText)`   | Header  | bilstm-crf-tok-fasttext-header         | 0.996 | 0.996 | 0.961 | 0.996 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Header  | bilstm-crf-tok-glove-300d-header       | 0.996 | 0.996 | 0.964 | 0.996 |


#### Version 0.0.3

The version was released to accommodate for Zensols framework upgrades.

| Name                          | Type    | Id                                     | wF1   | mF1   | MF1   | acc   |
|-------------------------------|---------|----------------------------------------|-------|-------|-------|-------|
| `BiLSTM-CRF_tok (fastText)`   | Section | bilstm-crf-tok-fasttext-section-type   | 0.911 | 0.917 | 0.792 | 0.917 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Section | bilstm-crf-tok-glove-300d-section-type | 0.929 | 0.933 | 0.810 | 0.933 |
| `BiLSTM-CRF_tok (fastText)`   | Header  | bilstm-crf-tok-fasttext-header         | 0.996 | 0.996 | 0.965 | 0.996 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Header  | bilstm-crf-tok-glove-300d-header       | 0.996 | 0.996 | 0.962 | 0.996 |


#### Version 0.0.2

The version was released to accommodate for Zensols framework upgrades.

| Name                          | Type    | Id                                     | wF1   | mF1   | MF1   | acc   |
|-------------------------------|---------|----------------------------------------|-------|-------|-------|-------|
| `BiLSTM-CRF_tok (fastText)`   | Section | bilstm-crf-tok-fasttext-section-type   | 0.918 | 0.925 | 0.797 | 0.925 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Section | bilstm-crf-tok-glove-300d-section-type | 0.917 | 0.922 | 0.809 | 0.922 |
| `BiLSTM-CRF_tok (fastText)`   | Header  | bilstm-crf-tok-fasttext-header         | 0.996 | 0.996 | 0.959 | 0.996 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Header  | bilstm-crf-tok-glove-300d-header       | 0.996 | 0.996 | 0.962 | 0.996 |


## Differences from the Paper Repository

The paper [medsecid repository] has quite a few differences, mostly around
reproducibility.  However, this repository is designed to be a package used for
research that applies the model.  To reproduce the results of the paper, please
refer to the [medsicid repository].  To use the best performing model
(BiLSTM-CRF token model) from that paper, then use this repository.

Perhaps the largest difference is that this repository has a pretrained model
and code for header tokens.  This is a separate model whose header token
predictions are "merged" with the section ID/type predictions.

The differences in performance between the section ID/type models and metrics
reported involve several factors.  The primary difference being that released
models were trained on the test data with only validation performance metrics
reported to increase the pretrained model performance.  Other changes include:

* Uses the [mednlp package], which uses [MedCAT] to parse clinical medical
  text.  This includes changes such as fixing misspellings and expanding
  acronyms.
* Uses the [mimic package], which builds on the [mednlp package] and parses
  [MIMIC-III] text by configuring the [spaCy] tokenizer to deal with pseudo
  tokens (i.e. `[**First Name**]`).  This is a significant change given how
  these tokens are treated between the models and term mapping (`Pt.` becomes
  `patient`).  This was changed so the model will work well on non-MIMIC data.
* Feature sets differences such as provided by the [Zensols Deep NLP package].
* Model changes include LSTM hidden layer parameter size and activation
  function.
* White space tokens are removed in [medsecid repository] and added back in
  this package to give additional cues to the model on when to break a
  section.  However, this might have had the opposite effect.

There are also changes in the Python interpreter and libraries used:

* Python version 3.9 to 3.11.
* PyTorch was upgraded from 1.9.1 to 2.1.2
* [spaCy] was upgraded from 3.0.7 to 3.6.1
* HuggingFace Transformers 4.11.3 to 4.35.2
* scispaCy 0.4.0 to 0.5.3


### Model Differences

Starting with [Version 0.1.0](#version-010), named entities include those
predicted from the scispaCy biomedical NER (`en_ner_bionlp13cg_md`) trained
model.  Compressed model files are also smaller in size.


## Training

This document explains how to create and package models for distribution.


### Preprocessing Step

1. To train the model, first install the MIMIC-III Postgres database per the [mimic
   package] instructions in the *Installation* section.
1. Copy the system configuration file:
   ```bash
   cp config/system-template.conf config/system.conf
   ```
1. Add the MIMIC-III Postgres credentials and database configuration to
   `config/system.conf`.
1. Vectorize the batches using the preprocessing script:
   `./src/bin/preprocess.sh`.  This also creates cached hospital admission and
   spaCy data parse files.


### Training and Testing

To get performance metrics on the test set by training on the training, use the
command: `./dist traintest -c config/glove300.conf` for the section ID
model.  The configuration file can be any of those in the `models` directory.
For the header model use:

```bash
./dist traintest -c config/glove300.conf --override mimicsid_default.model_type=header
```


## Training Production Models

TL;DR: if you're feeling lucky:

1. Update the new *model* version in:
   * [resources/default.conf](resources/default.conf) for property
     `msid_model:version`.
   * [dist-resources/app.conf][dist-resources/app.conf] for property
     `deeplearn_model_packer:version`
1. Run detached from the console since it will take about a day to train all
   four models: `nohup src/bin/all.sh > train.log 2>&1 &`
1. Recreate the environment file: `make envfile`

However, there are many moving parts and libraries with many things that can go
wrong.  More in-depth training instructions follow.

To train models used in your projects, train the model on both the training and
test sets.  This still leaves the validation set to inform when to save for
epochs where the loss decreases:

1. Update the version in the `deeplearn_model_packer` section in file
   `dist-resources/app.conf`.
1. Update the same version in the `msid_model` section in file
   `resources/default.conf`.
1. Preprocess the data (see the [preprocessing](#preprocessing-step) section).
1. **Important**: Remember to remove the passwords and database configuration
   in `config/system.conf`:
   ```bash
   cp config/system.conf config/system-sensitive-data.conf
   cat /dev/null > config/system.conf
   ```
1. Run the script that trains the models and packages them: `src/bin/package.sh`.
1. Revert the configuration files:
   ```bash
   git checkout -- dist-resources/app.conf resources/default.conf
   ```


## Citation

If you use this project in your research please use the following BibTeX entry:

```bibtex
@inproceedings{landes-etal-2022-new,
    title = "A New Public Corpus for Clinical Section Identification: {M}ed{S}ec{I}d",
    author = "Landes, Paul  and
      Patel, Kunal  and
      Huang, Sean S.  and
      Webb, Adam  and
      Di Eugenio, Barbara  and
      Caragea, Cornelia",
    booktitle = "Proceedings of the 29th International Conference on Computational Linguistics",
    month = oct,
    year = "2022",
    address = "Gyeongju, Republic of Korea",
    publisher = "International Committee on Computational Linguistics",
    url = "https://aclanthology.org/2022.coling-1.326",
    pages = "3709--3721"
}
```

Also please cite the [Zensols Framework]:

```bibtex
@inproceedings{landes-etal-2023-deepzensols,
    title = "{D}eep{Z}ensols: A Deep Learning Natural Language Processing Framework for Experimentation and Reproducibility",
    author = "Landes, Paul  and
      Di Eugenio, Barbara  and
      Caragea, Cornelia",
    editor = "Tan, Liling  and
      Milajevs, Dmitrijs  and
      Chauhan, Geeticka  and
      Gwinnup, Jeremy  and
      Rippeth, Elijah",
    booktitle = "Proceedings of the 3rd Workshop for Natural Language Processing Open Source Software (NLP-OSS 2023)",
    month = dec,
    year = "2023",
    address = "Singapore, Singapore",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.nlposs-1.16",
    pages = "141--146"
}
```


## Docker

A [docker](docker/app/README.md) image is now available as well.

To use the docker image, do the following:

1. Create (or obtain) the [Postgres docker image]
1. Clone this repository `git clone --recurse-submodules
   https://github.com/plandes/mimicsid`
1. Set the working directory to the repo: `cd mimicsid`
1. Copy the configuration from the installed [mimicdb] image configuration:
   `make -C docker/mimicdb SRC_DIR=<cloned mimicdb directory> cpconfig`
1. Start the container: `make -C docker/app up`
1. Test sectioning a document: `make -C docker/app testdumpsec`
1. Log in to the container: `make -C docker/app devlogin`
1. Output a note to a temporary file: `mimic note 1118471 > note.txt`
1. Predict the sections on the note: `mimicsid predict note.txt`
1. Look at the section predictions: `cat preds/note-pred.txt`


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## Community

Please star this repository and let me know how and where you use this API.
Contributions as pull requests, feedback and any input is welcome.


## License

[MIT License](LICENSE.md)

Copyright (c) 2022 - 2025 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.mimicsid/
[pypi-link]: https://pypi.python.org/pypi/zensols.mimicsid
[pypi-badge]: https://img.shields.io/pypi/v/zensols.mimicsid.svg
[python311-badge]: https://img.shields.io/badge/python-3.11-blue.svg
[python311-link]: https://www.python.org/downloads/release/python-3110
[build-badge]: https://github.com/plandes/mimicsid/workflows/CI/badge.svg
[build-link]: https://github.com/plandes/mimicsid/actions

[MedCat]: https://github.com/CogStack/MedCAT
[spaCy]: https://spacy.io
[conda]: https://docs.anaconda.com/miniconda/

[mednlp package]: https://github.com/plandes/mednlp
[mimic package]: https://github.com/plandes/mimic
[mimic package install section]: https://github.com/plandes/mimic#installation
[medsecid repository]: https://github.com/uic-nlp-lab/medsecid
[Zensols Deep NLP package]: https://github.com/plandes/deepnlp
[Zensols Framework]: https://github.com/plandes/deepnlp

[annotation example]: example/anon/anon.py
[A New Public Corpus for Clinical Section Identification: MedSecId]: https://aclanthology.org/2022.coling-1.326.pdf
[Zenodo]: https://zenodo.org/records/10971167

[Postgres docker image]: https://github.com/plandes/mimicdb#installation
[mimicdb]: https://github.com/plandes/mimicdb

[Note class]: https://plandes.github.io/mimic/api/zensols.mimic.html#zensols.mimic.note.Note
