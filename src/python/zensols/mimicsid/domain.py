"""Annotated section and note domain specific classes.

"""
__author__ = 'Paul Landes'

from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
from io import TextIOBase
import re
from zensols.nlp import LexicalSpan, FeatureDocument
from zensols.mimic import Note, Section, SectionContainer


class AgeType(Enum):
    """An enumeration of all possible ages identified by the physicians per note
    in the annotation set.

    """
    adult = auto()
    newbon = auto()
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

    def _get_sections(self) -> List[Section]:
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
class PredictedSection(Section):
    """A section with spans and ID/type predicted by the model.

    """
    doc: FeatureDocument = field(repr=False)
    """The note document in :class:`.PredictedNote`."""

    def _get_body_doc(self) -> FeatureDocument:
        return self._narrow_doc(self.doc)


@dataclass
class PredictedNote(SectionContainer):
    """A note with predicted sections.

    """
    doc: FeatureDocument = field(repr=False)
    """The used document that was parsed for prediction."""

    predicted_sections: List[Section] = field(repr=False)
    """The sections predicted by the model.

    """
    @property
    def text(self) -> str:
        """"The entire note text."""
        return self.doc.text

    def _get_sections(self) -> List[Section]:
        return self.predicted_sections

    def _get_doc(self) -> FeatureDocument:
        return self.doc
