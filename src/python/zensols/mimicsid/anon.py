"""Stashes that use annotated sections when available.

"""
__author__ = 'Paul Landes'

from typing import Dict, Any, ClassVar, Iterable, Set, List, Tuple, Union
from dataclasses import dataclass, field
import logging
import json
import re
from pathlib import Path
from io import BytesIO
from frozendict import frozendict
import pandas as pd
from zensols.util import time
from zensols.config import Dictable
from zensols.install import Installer
from zensols.persist import (
    persisted, PersistedWork,
    Stash, ReadOnlyStash, ZipStash, PrimeableStash, DelegateStash
)
from zensols.mimic import (
    Note, NoteFactory, NoteEvent, HospitalAdmission,
    NoteEventPersister, Corpus,
)
from . import AnnotatedNote

logger = logging.getLogger(__name__)


@dataclass
class AnnotationResource(Dictable):
    """This class providess access to the ``.zip`` file that contains the JSON
    section identification annotations.  It also has the ontology provided as a
    Pandas dataframe.

    """
    _DICTABLE_ATTRIBUTES: ClassVar[str] = {'corpus_path'}
    _ROOT_ZIP_DIR: ClassVar[str] = 'section-id-annotations'
    _ANN_ENTRY: ClassVar[str] = 'annotations'
    _ONTOLOGY_ENTRY: ClassVar[str] = 'ontology.csv'
    _KEY_REGEX: ClassVar[str] = re.compile(_ANN_ENTRY + r'/(\d+)-(\d+)-([^.]+)')

    installer: Installer = field(repr=False)
    """Used to download the annotation set as a zip file and provide the
    location to the downloaded file.

    """
    @property
    def corpus_path(self) -> Path:
        """The path to the annotations ``.zip`` file (see class docs)."""
        return self.installer.get_singleton_path()

    @persisted('_stash')
    def _get_stash(self) -> ZipStash:
        """"Return the stash containing the section annotations."""
        self.installer()
        path: Path = self.corpus_path
        return ZipStash(path, root=self._ROOT_ZIP_DIR)

    @property
    @persisted('_ontology')
    def ontology(self) -> pd.DataFrame:
        """A dataframe representing the note to section ontology.  It contains
        the relation from notes to sections along with their respective
        descriptions.

        """
        csv_data: bytearray = self._get_stash().get(self._ONTOLOGY_ENTRY)
        return pd.read_csv(BytesIO(csv_data))

    @property
    @persisted('_note_ids')
    def note_ids(self) -> pd.DataFrame:
        """Return a dataframe of hospital admission and corresponding note IDs.

        """
        rows = []
        for k in self._get_stash().keys():
            m: re.Match = self._KEY_REGEX.match(k)
            if m is not None:
                rows.append(m.groups())
        return pd.DataFrame(rows, columns='hadm_id row_id category'.split())

    @staticmethod
    def category_to_id(name: str) -> str:
        """Return the ID form for the category name."""
        return name.replace(' ', '-').replace('/', '-').lower()

    def get_annotation(self, note_event: NoteEvent) -> Dict[str, Any]:
        """Get the raw annotation as Python dict of dics for a
        :class:`~zensols.mimic.NoteEvent`.

        """
        ne = note_event
        cat = self.category_to_id(ne.category)
        path = f'{self._ANN_ENTRY}/{ne.hadm_id}-{ne.row_id}-{cat}.json'
        item: bytearray = self._get_stash().get(path)
        if item is not None:
            return json.load(BytesIO(item))

    @property
    @persisted('_note_counts_by_admission')
    def note_counts_by_admission(self) -> pd.DataFrame:
        """The counts of each category and row IDs for each admission.

        """
        df: pd.DataFrame = self.note_ids
        cats: List[str] = sorted(df['category'].drop_duplicates().tolist())
        cols: List[str] = ['hadm_id'] + cats + ['total', 'row_ids']
        rows: List[Tuple[str, int]] = []
        for hadm_id, dfg in df.groupby('hadm_id'):
            cnts = dfg.groupby('category').size()
            row: List[Union[str, int]] = [hadm_id]
            row.extend(map(lambda c: cnts[c] if c in cnts else 0, cats))
            row.append(cnts.sum())
            rows.append(row)
            row.append(','.join(dfg['row_id']))
        df = pd.DataFrame(rows, columns=cols)
        return df.sort_values('total', ascending=False)


@dataclass
class AnnotationNoteFactory(NoteFactory):
    """Override to replace section with MedSecId annotations if they exist.

    """
    anon_resource: AnnotationResource = field(default=None)
    """Contains the annotations and ontolgy/metadata note to section data."""

    annotated_note_section: str = field(default=None)
    """The section to use for creating new annotated section, for those that
    found in the annotation set.

    """
    def _create_missing_anon_note(self, note_event: NoteEvent) -> Note:
        return super().__call__(note_event)

    def _create_note(self, note_event: NoteEvent, anon: Dict[str, Any]) -> Note:
        if anon is not None:
            note = self._event_to_note(
                note_event,
                section=self.annotated_note_section,
                params={'annotation': anon})
        else:
            note = self._create_missing_anon_note(note_event)
        return note

    def __call__(self, note_event: NoteEvent) -> Note:
        anon: Dict[str, Any] = self.anon_resource.get_annotation(note_event)
        return self._create_note(note_event, anon)


@dataclass
class AnnotatedNoteStash(ReadOnlyStash, PrimeableStash):
    """A stash that returns :class:`~zensols.mimic.Note` instances by thier
    unique ``row_id`` keys.

    """
    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field()
    """Contains the annotations and ontolgy/metadata note to section data."""

    row_hadm_map_path: Path = field()
    """The path to the note to admission ID mapping cached file."""

    def __post_init__(self):
        super().__post_init__()
        self._row_hadm_map = PersistedWork(
            self.row_hadm_map_path, self, mkdir=True, recover_empty=True)

    @property
    @persisted('_row_hadm_map')
    def row_to_hadm_ids(self) -> Dict[str, str]:
        """A mapping of row to hospital admission IDs."""
        with time('calc key diff'):
            df: pd.DataFrame = self.anon_resource.note_ids
            rows: Dict[str, str] = dict(
                df['row_id hadm_id'.split()].itertuples(index=False))
        return frozendict(rows)

    def prime(self):
        stash: Stash = self.corpus.hospital_adm_stash
        df: pd.DataFrame = self.anon_resource.note_ids
        hadm_ids: Set[str] = set(df['hadm_id'].drop_duplicates())
        remaining: Set[str] = hadm_ids - set(stash.keys())
        if len(remaining) > 0:
            if logger.isEnabledFor(logging.INFO):
                logger.info(f'priming {len(remaining)} admissions')
            with time(f'wrote {len(remaining)} admissions'):
                for hadm_id in remaining:
                    stash[hadm_id]

    def clear(self):
        self._row_hadm_map.clear()

    def load(self, row_id: str) -> AnnotatedNote:
        row_to_hadm: Dict[str, str] = self.row_to_hadm_ids
        stash: Stash = self.corpus.hospital_adm_stash
        hadm_id: str = row_to_hadm.get(row_id)
        if hadm_id is not None:
            adm: HospitalAdmission = stash[hadm_id]
            note: AnnotatedNote = adm[int(row_id)]
            if isinstance(note, AnnotatedNote):
                return note
            else:
                logger.warning('No annotation found for hadm_id: ' +
                               f'{hadm_id}, row_id: {row_id}')

    def keys(self) -> Iterable[str]:
        return self.anon_resource.note_ids['row_id'].tolist()

    def exists(self, row_id: str) -> bool:
        return any(self.anon_resource.note_ids['row_id'] == row_id)

    def __len__(self) -> int:
        return len(self.anon_resource.note_ids)


@dataclass
class NoteStash(DelegateStash):
    """Creates notes of type :class:`~zensols.mimic.Note` or
    :class:`.AnnotatedNote` depending on if the note was annotated.

    """
    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    def load(self, row_id: str) -> Note:
        note: Note = self.delegate.load(row_id)
        if note is None:
            np: NoteEventPersister = self.corpus.note_event_persister
            hadm_id: int = np.get_hadm_id(str(row_id))
            if hadm_id is not None:
                adm: HospitalAdmission = self.corpus.hospital_adm_stash[hadm_id]
                note = adm[int(row_id)]
        return note

    def get(self, name: str, default: Any = None) -> Any:
        return Stash.get(self, name, default)
