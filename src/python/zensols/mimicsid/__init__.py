"""MIMIC-III corpus parsing and section prediction with MedSecId.

"""
__author__ = 'Paul Landes'


def _silence_spacy_parser_warnings():
    import warnings
    warnings.filterwarnings(
        'ignore', message='remove_empty_sentences is deprecated.*')


_silence_spacy_parser_warnings()


from .domain import *
from .anon import *
from .app import *
from .cli import *
