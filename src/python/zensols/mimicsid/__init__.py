"""MIMIC-III corpus parsing and section prediction with MedSecId.

"""
__author__ = 'Paul Landes'


def _silence_zennlp_parser_warnings():
    """The pretrained model uses a deprecated API."""
    import warnings
    warnings.filterwarnings(
        'ignore', message='remove_empty_sentences is deprecated.*')


_silence_zennlp_parser_warnings()


from .domain import *
from .anon import *
from .app import *
from .cli import *
