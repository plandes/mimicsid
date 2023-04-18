"""Annotated section and note domain specific classes.

"""
__author__ = 'Paul Landes'

from typing import Dict, Any, List, ClassVar, Set, Iterable
from dataclasses import dataclass, field, InitVar
from enum import Enum, auto
import sys
from io import TextIOBase
import re
from zensols.persist import persisted, PersistableContainer
from zensols.nlp import LexicalSpan, FeatureDocument
from zensols.mimic import Note, Section, SectionContainer, SectionAnnotatorType


class AgeType(Enum):
    """An enumeration of all possible ages identified by the physicians per note
    in the annotation set.

    """
    adult = auto()
    newborn = auto()
    pediatric = auto()


@dataclass
class AnnotatedSection(Section):
    """A section that uses the MedSecId annotations for section demarcation
    (:obj:`header_span`, :obj:`header_spans` and :obj:`body_span`) and
    identification (:obj:`id`).

    Many of the header identifiers are found in multiple locations in the body
    of the text.  In other cases there are no header spans at all.  The
    :obj:`header_spans` field has all of them, and if there is at least one,
    the :obj:`header_span` is set to the first.

    See the MedSecId paper for details.

    """
    annotation: Dict[str, Any] = field(default=None, repr=False)
    """The raw annotation data parsed from the zip file containing the JSON."""


@dataclass
class AnnotatedNote(Note):
    """An annotated note that contains instances of :class:`.AnnotationSection`.
    It also contains the ``age type`` taken from the annotations.

    """
    _DICTABLE_ATTRIBUTES = Note._DICTABLE_ATTRIBUTES | {'age_type'}
    _POST_HEADER_REGEX = re.compile(r'^[:\s\n]+(.*)$', re.DOTALL)

    annotation: Dict[str, Any] = field(default=None, repr=False)
    """The annotation (JSON) parsed from the annotations zip file."""

    @property
    def age_type(self) -> AgeType:
        """The age type of the discharge note as annotated by the physicians.

        """
        atstr = self.annotation['age_type']
        return AgeType[atstr]

    def _get_section_annotator_type(self) -> SectionAnnotatorType:
        return SectionAnnotatorType.HUMAN

    def _create_sec(self, sid: int, anon: Dict[str, Any]) -> Section:
        body_span = LexicalSpan(**anon['body_span'])
        header_spans: List[LexicalSpan] = []
        header_span: LexicalSpan = None
        for hspan in anon.get('header_spans', ()):
            header_spans.append(LexicalSpan(**hspan))
        if len(header_spans) > 0:
            header_span = header_spans[-1]
            header_end = header_span.end
            body = self.text[header_end:body_span.end]
            m: re.Match = self._POST_HEADER_REGEX.match(body)
            if m is not None:
                header_end += m.start(1)
            body_span = LexicalSpan(header_end, body_span.end)
        return AnnotatedSection(
            id=sid,
            name=anon['id'],
            container=self,
            body_span=body_span,
            header_spans=header_spans,
            annotation=anon)

    def _get_sections(self) -> Iterable[Section]:
        an = self.annotation
        assert self.hadm_id == an['hadm_id']
        assert self.row_id == an['row_id']
        assert self.category == an['category']
        secs: List[Section] = []
        sec_anon: Dict[str, Any]
        for sid, sec_anon in enumerate(an['sections']):
            sec = self._create_sec(sid, sec_anon)
            sec._row_id = self.row_id
            secs.append(sec)
        return secs

    def write_fields(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        super().write_fields(depth, writer)
        self._write_line(f'age: {self.age_type.name}', depth, writer)


@dataclass
class PredictedNote(PersistableContainer, SectionContainer):
    """A note with predicted sections.

    """
    _PERSITABLE_PROPERTIES: ClassVar[Set[str]] = {'sections'}

    predicted_sections: List[Section] = field(repr=False)
    """The sections predicted by the model.

    """
    doc: InitVar[FeatureDocument] = field(repr=False)
    """The used document that was parsed for prediction."""

    def __post_init__(self, doc: FeatureDocument):
        self._doc = doc
        super().__init__()

    @property
    def _predicted_sections(self) -> List[Section]:
        return self._predicted_sections_val

    @_predicted_sections.setter
    def _predicted_sections(self, sections: List[Section]):
        self._predicted_sections_val = sections
        if hasattr(self, '_sections'):
            self._sections.clear()

    @property
    def text(self) -> str:
        """"The entire note text."""
        return self._get_doc().text

    @property
    @persisted('_truncated_text', transient=True)
    def truncted_text(self) -> str:
        return self._trunc(self.text, 70).replace('\n', ' ').strip()

    def _get_sections(self) -> Iterable[Section]:
        return self.predicted_sections

    def _get_doc(self) -> FeatureDocument:
        return self._doc

    def __setstate__(self, state: Dict[str, Any]):
        super().__setstate__(state)
        for sec in self.predicted_sections:
            sec.container = self

    def __str__(self):
        text = self.truncted_text
        if hasattr(self, 'row_id') and hasattr(self, 'category'):
            return f'{self.row_id}: ({self.category}): {text}'
        else:
            return text


PredictedNote.predicted_sections = PredictedNote._predicted_sections


@dataclass(init=False)
class MimicPredictedNote(Note):
    """A note that comes from the MIMIC-III corpus with predicted sections.
    This takes an instance of :class:`.PredictedNote` created by the model
    during inference.  It creates :class:`~zensols.mimic.note.Section`
    instances, and then discards the predicted note on pickling.

    This method avoids having to serialize the
    :class:`~zensols.nlp.container.FeatureDocument` (:obj:`.PredictedNote.doc`)
    twice.

    """
    _PERSITABLE_TRANSIENT_ATTRIBUTES: ClassVar[Set[str]] = \
        Note._PERSITABLE_TRANSIENT_ATTRIBUTES | {'_pred_note'}

    def __init__(self, *args, predicted_note: PredictedNote, **kwargs):
        self._pred_note = predicted_note
        super().__init__(*args, **kwargs)

    def _get_section_annotator_type(self) -> SectionAnnotatorType:
        return SectionAnnotatorType.MODEL

    def _get_sections(self) -> Iterable[Section]:
        def map_sec(ps: Section) -> Section:
            return Section(
                id=ps.id,
                name=ps.name,
                container=self,
                header_spans=ps.header_spans,
                body_span=ps.body_span)

        return map(map_sec, self._pred_note.predicted_sections)
