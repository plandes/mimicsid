#!/usr/bin/env python

from typing import Tuple
import spacy
from spacy import Language

sci_nlp: Language = spacy.load("en_ner_bionlp13cg_md")
labels: Tuple[str, ...] = sci_nlp.get_pipe('ner').labels
print(' '.join(sorted(labels)))
