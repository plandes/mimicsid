"""Use the MedSecId section annotations with MIMIC-III corpus parsing.

"""
__author__ = 'Paul Landes'

from typing import Tuple, List, Dict, Any, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
import logging
from io import StringIO, TextIOBase
from pathlib import Path
import pandas as pd
from zensols.util import loglevel, stdout
from zensols.persist import Stash
from zensols.config import ConfigFactory
from zensols.cli import ApplicationError
from zensols.deeplearn.cli import FacadeApplication
from zensols.mimic import (
    NoteFormat, Note, Corpus, HospitalAdmission,
    NoteDocumentPreemptiveStash,
)
from . import AnnotatedNote, AnnotationResource, NoteStash, PredictedNote
from .pred import SectionPredictor


logger = logging.getLogger(__name__)


@dataclass
class Application(FacadeApplication):
    """Use the MedSecId section annotations with MIMIC-III corpus parsing.

    """
    config_factory: ConfigFactory = field(default=None)
    """The config used to create facade instances."""

    corpus: Corpus = field(default=None)
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field(default=None)
    """Contains resources to acces the MIMIC-III MedSecId annotations."""

    note_stash: NoteStash = field(default=None)
    """A stash that returns :class:`~zensols.mimic.Note` instances by thier
    unique ``row_id`` keys.

    """
    preempt_stash: NoteDocumentPreemptiveStash = field(default=None)
    """A multi-processing stash used to preemptively parse notes."""

    def dump_ontology(self, out_file: Path = None):
        """Writes the ontology.

        :param out_file: the output path

        """
        out_file = Path('ontology.csv') if out_file is None else out_file
        self.anon_resource.ontology.to_csv(out_file)
        logger.info(f'wrote: {out_file}')

    def _write_note(self, note: Note, out_file: Path = None,
                    output_format: NoteFormat = NoteFormat.text):
        with stdout(out_file) as f:
            note.write_by_format(writer=f, note_format=output_format)
        if out_file.name != stdout.STANDARD_OUT_PATH:
            logger.info(f'wrote to {out_file}')

    def write_note(self, row_id: int, out_file: Path = None,
                   output_format: NoteFormat = NoteFormat.text):
        """Write an admission, note or section.

        :param row_id: the row ID of the note to write

        :param out_file: the output path

        :param output_format: the output format of the note

        """
        def summary_format(writer: TextIOBase):
            for s in note.sections.values():
                print(s, s.header_spans, len(s))

        if out_file is None:
            out_file = Path(stdout.STANDARD_OUT_PATH)
        note: Note = self.corpus.get_note_by_id(row_id)
        self._write_note(note, out_file, output_format)

    def write_admission(self, hadm_id: str, out_dir: Path = Path('.'),
                        output_format: NoteFormat = NoteFormat.text):
        """Write all the notes of an admission.

        :param hadm_id: the admission ID

        :param out_dir: the output directory

        :param output_format: the output format of the note

        """
        adm: HospitalAdmission = self.corpus.get_hospital_adm_by_id(hadm_id)
        out_dir = out_dir / 'adm' / hadm_id
        out_dir.mkdir(parents=True, exist_ok=True)
        note: Note
        for note in adm.notes:
            path: Path = out_dir / f'{note.normal_name}.{output_format.ext}'
            self._write_note(note, path, output_format)

    def admission_notes(self, hadm_id: str, out_file: Path = None,
                        keeps: str = None) -> pd.DataFrame:
        """Create a CSV of note information by admission.

        :param hadm_id: the admission ID

        :param out_file: the output path

        :param keeps: a comma-delimited list of column to keep in the output;
                      defaults to all columns

        """
        if out_file is None:
            out_file: Path = Path(f'notes-{hadm_id}.csv')
        adm: HospitalAdmission = self.corpus.hospital_adm_stash.get(hadm_id)
        rows: List[Dict[str, Any]] = []
        note: Note
        for note in adm.notes:
            is_anon: bool = isinstance(note, AnnotatedNote)
            dct: Dict[str, Any] = note.asdict()
            for k in 'text sections'.split():
                del dct[k]
            dct['is_anon'] = is_anon
            if is_anon:
                dct['age_type'] = note.age_type.name
            rows.append(dct)
        df = pd.DataFrame(rows)
        if keeps is not None:
            df = df[keeps.split(',')]
        df.to_csv(out_file)
        logger.info(f'wrote: {out_file}')
        return df

    def note_counts_by_admission(self, out_file: Path = None) -> pd.DataFrame:
        """Write the counts of each category and row IDs for each admission.

        :param out_file: the output path

        """
        out_file = Path('admissions.csv') if out_file is None else out_file
        df: pd.DataFrame = self.anon_resource.note_counts_by_admission
        df.to_csv(out_file, index=False)
        logger.info(f'wrote: {out_file}')
        return df

    def preempt_notes(self, input_file: Path = None, workers: int = None):
        """Preemptively document parse notes across multiple threads.

        :param input_file: a file of notes' unique ``row_id`` IDs

        :param workers: the number of processes to use to parse notes

        """
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'preemting admissions from {input_file} ' +
                        f'for {workers} workers')
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
        self.preempt_stash.process_keys(row_ids, workers)

    def clear(self):
        """Remove all admission, note and section cached (parsed) data.

        """
        stash: Stash = self.corpus.hospital_adm_stash
        logger.info('clearing admission cache')
        with loglevel('zensols'):
            stash.clear()


class PredOutputType(Enum):
    """The types of prediction output formats."""
    text = auto()
    json = auto()


@dataclass
class PredictionApplication(object):
    """An application that predicts sections in file(s) on the file system, then
    dumps them back to the file system (or standard out).

    """
    config_factory: ConfigFactory = field(default=None)
    """The config factory used to help find the packed model."""

    note_stash: NoteStash = field(default=None)
    """A stash that returns :class:`~zensols.mimic.Note` instances by thier
    unique ``row_id`` keys.

    """
    section_predictor: SectionPredictor = field(default=None)
    """The section name that contains the name of the :class:`.SectionPredictor`
    to create from the ``config_factory``.

    """
    def predict_sections(self, input_path: Path,
                         output_path: Path = Path('preds'),
                         out_type: PredOutputType = PredOutputType.text,
                         file_limit: int = None):
        """Predict the section IDs of a medical notes by file name or all files
        in a directory.

        :param input_path: the path to the medical note(s) to annotate

        :param output_path: where to write the prediction(s) or - for standard
                            out

        :param out_type: the prediction output format

        :param file_limit: the max number of document to predict when the input
                           path is a directory

        """
        file_limit = sys.maxsize if file_limit is None else file_limit
        if input_path.is_dir():
            paths = list(input_path.iterdir())
            paths = paths[:file_limit]
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            paths = [input_path]
        docs: List[str] = []
        if not input_path.exists():
            raise ApplicationError(f'Input path does not exist: {input_path}')
        for path in paths:
            with open(path) as f:
                docs.append(f.read())
        ext = 'txt' if out_type == PredOutputType.text else 'json'
        notes: Tuple[PredictedNote] = self.section_predictor.predict(docs)
        for path, note in zip(paths, notes):
            path = path.parent / f'{path.stem}.{ext}'
            sio = StringIO()
            if out_type == PredOutputType.text:
                note.write_human(writer=sio)
            else:
                note.asjson(writer=sio, indent=4)
            if output_path.name == '-':
                print(sio.getvalue())
            else:
                fpath = output_path / f'{path.stem}-pred.{ext}'
                fpath.parent.mkdir(parents=True, exist_ok=True)
                with open(fpath, 'w') as f:
                    f.write(sio.getvalue())
                logger.info(f'wrote: {fpath}')
        return notes

    def repredict(self, row_id: int,
                  output_path: Path = Path('preds'),
                  out_type: PredOutputType = PredOutputType.text):
        """Predict the section IDs of an existing MIMIC III note.

        :param row_id: the row ID of the note to write

        :param output_path: where to write the prediction(s) or - for standard
                            out

        :param out_type: the prediction output format

        """
        out_path: Path = output_path / f'{row_id}.txt'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        note = self.note_stash[row_id]
        if isinstance(note, AnnotatedNote):
            fmt_path = out_path.parent / f'{row_id}-formatted.txt'
            with open(fmt_path, 'w') as f:
                note.write_human(writer=f)
            logger.info(f'wrote: {fmt_path}')
        with open(out_path, 'w') as f:
            f.write(note.text)
        return self.predict_sections(out_path)
