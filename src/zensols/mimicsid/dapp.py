"""Distribution utility application.

"""
__author__ = 'Paul Landes'

from typing import Sequence
from dataclasses import dataclass, field
import logging
from pathlib import Path
import pandas as pd
from zensols.cli import ApplicationError
from zensols.mimic import NoteDocumentPreemptiveStash
from .anon import AnnotationResource

logger = logging.getLogger(__name__)


@dataclass
class DistApplication(object):
    """Utilities to train the models.

    """
    anon_resource: AnnotationResource = field()
    """Contains resources to acces the MIMIC-III MedSecId annotations."""

    preempt_stash: NoteDocumentPreemptiveStash = field()
    """A multi-processing stash used to preemptively parse notes."""

    def preempt_notes(self, input_file: Path = None, workers: int = None,
                      max_adm: int = None):
        """Preemptively document parse notes across multiple threads.

        :param input_file: a file of notes' unique ``row_id`` IDs

        :param workers: the number of processes to use to parse notes

        :param max_adm: the maximum number of admission notes to process

        """
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'preemting admissions with {workers} workers')
        row_ids: Sequence[str]
        if input_file is None:
            df: pd.DataFrame = self.anon_resource.note_ids
            row_ids = df['row_id'].to_list()
        else:
            try:
                with open(input_file) as f:
                    row_ids = tuple(map(str.strip, f.readlines()))
            except OSError as e:
                raise ApplicationError(
                    f'Could not preempt notes from file {input_file}: {e}') \
                    from e
        if max_adm is not None:
            row_ids = row_ids[:max_adm]
        self.preempt_stash.process_keys(row_ids, workers)
