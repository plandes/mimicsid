# MIMIC-III corpus parsing and section prediction with MedSecId

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7150451.svg)](https://doi.org/10.5281/zenodo.7150451)
[![PyPI][pypi-badge]][pypi-link]
[![Python 3.9][python39-badge]][python39-link]
[![Python 3.10][python310-badge]][python310-link]

This repository contains the a Python package to automatically segment and
identify sections of medical notes.  It also provides access to the MedSecId
section annotations with MIMIC-III corpus parsing from the paper [A New Public
Corpus for Clinical Section Identification: MedSecId].  See the [medsecid
repository] to reproduce the results from the paper.

This package provides the following:

* The same access to MIMIC-III data as provided in the [mimic package].
* Access to the annotated MedSecId notes as an easy to use Python object graph.
* The pretrained model inferencing, which produces a similar Python object
  graph to the annotations (provides the class `PredictedNote` instead of an
  `AnnotatedNote` class.


<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
## Table of Contents

- [Obtaining](#obtaining)
- [Documentation](#documentation)
- [Installation](#installation)
- [Usage](#usage)
    - [Prediction Usage](#prediction-usage)
    - [Annotation Access](#annotation-access)
- [Differences from the Paper Repository](#differences-from-the-paper-repository)
- [Training](#training)
    - [Preprocessing Step](#preprocessing-step)
    - [Training and Testing](#training-and-testing)
- [Training Usable Models](#training-usable-models)
- [Models](#models)
    - [Performance Metrics](#performance-metrics)
- [Citation](#citation)
- [Changelog](#changelog)
- [License](#license)

<!-- markdown-toc end -->



## Obtaining

The easiest way to install the command line program is via the `pip` installer:
```bash
pip3 install zensols.mimicsid
```

Binaries are also available on [pypi].


## Documentation

See the [full documentation](https://plandes.github.io/mimicsid/index.html).
The [API reference](https://plandes.github.io/mimicsid/api.html) is also
available.


## Installation

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
    sec = note.sections_by_name['addendum'][0]
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

There are also changes in the libraries used:

* PyTorch was upgraded from 1.9.1 to 1.12.1
* [spaCy] was upgraded from 3.0.7 to 3.2.4
* Python version 3.9 to 3.10.


## Training

This document explains how to create and package models for distribution.


### Preprocessing Step

1. To train the model, first install the MIMIC-III Postgres database per the [mimic
   package] instructions in the *Installation* section.
2. Add the MIMIC-III Postgres credentials and database configuration to
   `etc/batch.conf`.
3. Comment out the line `resource(zensols.mimicsid): resources/model/adm.conf`
   in `resources/app.conf`.
4. Vectorize the batches using the preprocessing script:
   `$ ./src/bin/preprocess.sh`.  This also creates cached hospital admission and
   spaCy data parse files.


### Training and Testing

To get performance metrics on the test set by training on the training, use the
command: `./mimicsid traintest -c models/glove300.conf` for the section ID
model.  The configuration file can be any of those in the `models` directory.
For the header model use:

```bash
./mimicsid traintest -c models/glove300.conf --override mimicsid_default.model_type=header
```


## Training Production Models

To train models used in your projects, train the model on both the training and
test sets.  This still leaves the validation set to inform when to save for
epochs where the loss decreases:

1. Update the `deeplearn_model_packer:version` in `resources/app.conf`.
2. Preprocess (see the [preprocessing](#preprocessing-step)) section.
3. Run the script that trains the models and packages them: `src/bin/package.sh`.
4. Check for errors and verify models: `$ ./src/bin/verify-model.py`.
5. Don't forget to revert files `etc/batch.conf` and `resources/app.conf`.


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


### Performance Metrics

The distributed models add in the test set to the training set to improve the
performance for inferencing, which is why only the validation metrics are
given.  Only version 0.0.2 results are given.  The validation set performance
of the pretrained models are given below, where:

* **wF1** is the weighted F1
* **mF1** is the micro F1
* **Mf1** is the macro F1
* **acc** is the accuracy

| Name                          | Type    | Id                                     | wF1   | mF1   | MF1   | acc   |
|-------------------------------|---------|----------------------------------------|-------|-------|-------|-------|
| `BiLSTM-CRF_tok (fastText)`   | Section | bilstm-crf-tok-fasttext-section-type   | 0.918 | 0.925 | 0.797 | 0.925 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Section | bilstm-crf-tok-glove-300d-section-type | 0.917 | 0.922 | 0.809 | 0.922 |
| `BiLSTM-CRF_tok (fastText)`   | Header  | bilstm-crf-tok-fasttext-header         | 0.996 | 0.996 | 0.959 | 0.996 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Header  | bilstm-crf-tok-glove-300d-header       | 0.996 | 0.996 | 0.962 | 0.996 |


The model version 0.0.3 validation results:

| Name                          | Type    | Id                                     | wF1   | mF1   | MF1   | acc   |
|-------------------------------|---------|----------------------------------------|-------|-------|-------|-------|
| `BiLSTM-CRF_tok (fastText)`   | Section | bilstm-crf-tok-fasttext-section-type   | 0.918 | 0.925 | 0.797 | 0.925 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Section | bilstm-crf-tok-glove-300d-section-type | 0.917 | 0.922 | 0.809 | 0.922 |
| `BiLSTM-CRF_tok (fastText)`   | Header  | bilstm-crf-tok-fasttext-header         | 0.996 | 0.996 | 0.959 | 0.996 |
| `BiLSTM-CRF_tok (GloVE 300D)` | Header  | bilstm-crf-tok-glove-300d-header       | 0.996 | 0.996 | 0.962 | 0.996 |



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
@article{Landes_DiEugenio_Caragea_2021,
  title={DeepZensols: Deep Natural Language Processing Framework},
  url={http://arxiv.org/abs/2109.03383},
  note={arXiv: 2109.03383},
  journal={arXiv:2109.03383 [cs]},
  author={Landes, Paul and Di Eugenio, Barbara and Caragea, Cornelia},
  year={2021},
  month={Sep}
}
```


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## License

[MIT License](LICENSE.md)

Copyright (c) 2022 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.mimicsid/
[pypi-link]: https://pypi.python.org/pypi/zensols.mimicsid
[pypi-badge]: https://img.shields.io/pypi/v/zensols.mimicsid.svg
[python39-badge]: https://img.shields.io/badge/python-3.9-blue.svg
[python39-link]: https://www.python.org/downloads/release/python-390
[python310-badge]: https://img.shields.io/badge/python-3.10-blue.svg
[python310-link]: https://www.python.org/downloads/release/python-3100

[MedCat]: https://github.com/CogStack/MedCAT
[spaCy]: https://spacy.io

[mednlp package]: https://github.com/plandes/mednlp
[mimic package]: https://github.com/plandes/mimic
[mimic package install section]: https://github.com/plandes/mimic#installation
[medsecid repository]: https://github.com/uic-nlp-lab/medsecid
[Zensols Deep NLP package]: https://github.com/plandes/deepnlp
[Zensols Framework]: https://github.com/plandes/deepnlp

[annotation example]: example/anon/anon.py
[A New Public Corpus for Clinical Section Identification: MedSecId]: https://aclanthology.org/2022.coling-1.326.pdf
[Zenodo]: https://zenodo.org/record/7150451#.Yz30BS2B3Bs

[Note class]: https://plandes.github.io/mimic/api/zensols.mimic.html#zensols.mimic.note.Note
