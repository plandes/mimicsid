"""MIMIC-III corpus parsing and section prediction with MedSecId.

"""
__author__ = 'Paul Landes'


def suppress_warnings():
    """The pretrained model uses a deprecated API."""
    import warnings
    import zensols.mednlp
    warnings.filterwarnings(
        'ignore', message='remove_empty_sentences is deprecated.*')
    zensols.mednlp.surpress_warnings()


suppress_warnings()


from .domain import *
from .compat import *
from .app import *
from .cli import *
