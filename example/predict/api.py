#!/usr/bin/env python

"""An example to show how to predict sections using the MedSecId pretrained
model.  This example uses the Zensols API to create and use the predictor
instance.

"""
__author__ = 'Paul Landes'

from zensols.nlp import FeatureToken
from zensols.mimic import Section
from zensols.mimicsid import PredictedNote, ApplicationFactory
from zensols.mimicsid.pred import SectionPredictor


def filter_interesting_tokens(t: FeatureToken) -> bool:
    return t.cui_ != FeatureToken.NONE or t.mimic_ != FeatureToken.NONE


def div(msg: str):
    print()
    print('_' * 20, msg, '_' * 20)


if (__name__ == '__main__'):
    # get the section predictor from the application context in the app
    section_predictor: SectionPredictor = ApplicationFactory.section_predictor()

    # read in a test note to predict
    with open('../../test-resources/note.txt') as f:
        content: str = f.read().strip()

    print(content)

    # predict the sections of read in note
    note: PredictedNote = section_predictor.predict([content])[0]
    div('section names and their content')
    note.write_human()

    # iterate through the note object graph
    div('all section IDs and names')
    sec: Section
    for sec in note.sections.values():
        print(sec.id, sec.name)

    div('concepts or special MIMIC tokens from the addendum section')
    sec = note.sections_by_name['addendum'][0]
    tok: FeatureToken
    for tok in filter(filter_interesting_tokens, sec.body_doc.token_iter()):
        print(tok, tok.mimic_, tok.cui_)
