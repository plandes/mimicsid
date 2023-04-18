"""Contains section ID model and prediction classes.

"""
__author__ = 'Paul Landes'

from typing import Tuple, Type, Any, List, Dict, Optional, ClassVar, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import pandas as pd
from zensols.persist import persisted
from zensols.nlp import FeatureToken, FeatureDocument, LexicalSpan
from zensols.mednlp import MedicalFeatureToken
from zensols.mimic import MimicTokenDecorator
from zensols.deeplearn.batch import DataPoint
from zensols.deeplearn.result import ResultsContainer
from zensols.deepnlp.classify import (
    ClassificationPredictionMapper, TokenClassifyModelFacade
)
from zensols.mimic import Section
from . import AnnotatedNote, AnnotatedSection, PredictedNote

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """A custom token type feature that identifies specifies whether the token
    is::

       * a separator
       * a space
       * a colon character (``:``)
       * if its upper, lower case or capitalized
       * if its punctuation (if not a colon)
       * all digits
       * anything else is ``MIX``

    """
    SEP = auto()
    SPACE = auto()
    COLON = auto()
    NEWLINE = auto()
    UPCASE = auto()
    DOWNCASE = auto()
    CAPITAL = auto()
    PUNCTUATION = auto()
    DIGIT = auto()
    MIX = auto()


@dataclass
class SectionDataPoint(DataPoint):
    """A data point for the section ID model.

    """
    TOKEN_TYPES: ClassVar[Tuple[str]] = tuple(
        map(lambda t: str(t.name), TokenType))
    """The list of types used as enumerated nominal values in labeled encoder
    vectorizer components.

    """
    note: AnnotatedNote = field(repr=False)
    """The note contained by this data point."""

    pred_doc: FeatureDocument = field(default=None)
    """The parsed document used for prediction when using this data point for
    prediction.

    """
    def __post_init__(self):
        if self.note is not None:
            assert isinstance(self.note, AnnotatedNote)

    @property
    def is_pred(self) -> bool:
        """Whether this data point is used for prediction."""
        return self.note is None

    @property
    def doc(self) -> FeatureDocument:
        """The document from where this data poign originates."""
        return self.pred_doc if self.is_pred else self.note.doc

    @property
    @persisted('_features', transient=True)
    def feature_dataframe(self) -> pd.DataFrame:
        """A dataframe used to create some of the features of this data point.

        """
        rows: List[Tuple[Any]] = []
        tok2sec: Dict[FeatureToken, Section] = None
        if self.note is not None:
            tok2sec = {}
            sec: AnnotatedSection
            for sec in self.note.sections.values():
                for tok in sec.header_tokens:
                    tok2sec[tok] = (sec, True)
                for tok in sec.body_tokens:
                    tok2sec[tok] = (sec, False)
        tok: FeatureToken
        for tok in self.doc.token_iter():
            entry: Optional[Tuple[Section, bool]] = None
            if tok2sec is not None:
                entry = tok2sec.get(tok)
            if entry is None:
                sec_name, is_header = FeatureToken.NONE, False
            else:
                sec_name, is_header = entry[0].name, entry[1]
            tt: TokenType
            norm: str = tok.norm
            ent: str = FeatureToken.NONE
            cui: Optional[str] = tok.cui_
            header_lab: str = 'y' if is_header else 'n'
            if cui == FeatureToken.NONE:
                cui = None
            if tok.ent_ != MedicalFeatureToken.CONCEPT_ENTITY_LABEL and \
               tok.ent_ != FeatureToken.NONE:
                ent = tok.ent_
            elif tok.mimic_ == MimicTokenDecorator.PSEUDO_TOKEN_FEATURE:
                ent = tok.onto_
            if tok.mimic_ == MimicTokenDecorator.SEPARATOR_TOKEN_FEATURE:
                tt = TokenType.SEP
            elif norm == ':':
                tt = TokenType.COLON
            elif tok.is_punctuation:
                tt = TokenType.PUNCTUATION
            elif tok.is_space:
                tt = {' ': TokenType.SPACE,
                      '\t': TokenType.SPACE,
                      '\n': TokenType.NEWLINE,
                      }[norm[0]]
            else:
                if norm.isupper():
                    tt = TokenType.UPCASE
                elif norm.islower():
                    tt = TokenType.DOWNCASE
                elif norm[0].isupper():
                    tt = TokenType.CAPITAL
                elif norm.isdigit():
                    tt = TokenType.DIGIT
                else:
                    tt = TokenType.MIX
            ts = tt.name
            rows.append((tok.norm, sec_name, header_lab, tok.idx, ts, ent, cui))
        return pd.DataFrame(
            rows, columns='norm sec_name is_header idx ttype ent cui'.split())

    @property
    def section_names(self) -> Tuple[str]:
        """The section names label (section types per the paper)."""
        return tuple(self.feature_dataframe['sec_name'])

    @property
    def headers(self) -> Tuple[str]:
        """The header label (section types per the paper)."""
        return tuple(self.feature_dataframe['is_header'])

    @property
    def idxs(self) -> Tuple[int]:
        """The index feature."""
        return tuple(self.feature_dataframe['idx'])

    @property
    def ttypes(self) -> Tuple[str]:
        """The token type feature, which is the string value of
        :class:`.TokeType`.

        """
        return tuple(self.feature_dataframe['ttype'])

    @property
    def ents(self) -> Tuple[str]:
        """The named entity feature."""
        return tuple(self.feature_dataframe['ent'])

    @property
    def cuis(self) -> Tuple[Optional[str]]:
        """The CUI feature."""
        return tuple(self.feature_dataframe['cui'])

    def __len__(self):
        return self.doc.token_len


@dataclass
class SectionPredictionMapper(ClassificationPredictionMapper):
    """Predict sections from a :class:`~zensols.nlp.FeatureDocument` as a list
    of :class:`.PredictedNote` instances.  It does this by creating data points
    of type :class:`.SectionDataPoint` that are used by the model.

    """
    def _create_tok_list(self, doc: FeatureDocument, labels: Tuple[str],
                         tok_lists: List[Tuple[str, List[FeatureToken]]]):
        """Create token lists for each document.  This coallates a section label
        with the respective list of tokens from which they were predicted.

        :param doc: the document used for prediction

        :param labels: the predicted labels for ``doc``

        :tok_lists: the coallated label/token list to populate

        """
        def add_tok_list(lab: str, tok_list: List[FeatureToken]):
            """Strip front and back newlines."""
            for beg, tok in enumerate(tok_list):
                if tok.norm != '\n':
                    break
            for end, tok in enumerate(reversed(tok_list)):
                if tok.norm != '\n':
                    break
            end = len(tok_list) - end
            tok_lists.append((lab, tok_list[beg:end]))

        tok_list: List[FeatureToken] = None
        last_lab: str = None
        label: str
        tok: FeatureToken
        for label, tok in zip(labels, doc.token_iter()):
            if last_lab != label:
                if tok_list is not None:
                    add_tok_list(last_lab, tok_list)
                tok_list = [tok]
            else:
                tok_list.append(tok)
            last_lab = label
        if tok_list is not None and len(tok_list) > 0:
            add_tok_list(last_lab, tok_list)

    def _create_secions(self, tok_lists: Tuple[str, List[FeatureToken]],
                        doc: FeatureDocument, secs: List[AnnotatedSection]):
        """Create sections from token lists.

        :param tok_lists: the token lists created in :meth:`_create_tok_list`

        :param doc: the document used for prediction

        :param secs: the list to populate with creeated sections

        """
        # remove token lists with no classified section
        tok_lists = tuple(
            filter(lambda x: x[0] != FeatureToken.NONE, tok_lists))
        for sid, (label, toks) in enumerate(tok_lists):
            span: LexicalSpan = None
            if len(toks) == 1:
                span = toks[0].lexspan
            else:
                begin = toks[0].lexspan.begin
                end = toks[-1].lexspan.end
                span = LexicalSpan(begin, end)
            assert span is not None
            secs.append(Section(
                id=sid,
                name=label,
                container=None,
                header_spans=(),
                body_span=span))

    def _collate(self, docs: Tuple[FeatureDocument],
                 classes: Tuple[Tuple[str]]) -> List[PredictedNote]:
        """Collate predictions with feature tokens.

        :param docs: he documents used for prediction

        :param classes: the predicted classes
        """
        notes: List[PredictedNote] = []
        doc_tok_lists: List[Tuple[str, List[FeatureToken]]] = []
        # create token lists that have the section label with respective tokens
        labels: List[str]
        doc: FeatureDocument
        for labels, doc in zip(classes, docs):
            tok_lists: List[Tuple[str, List[FeatureToken]]] = []
            doc_tok_lists.append(tok_lists)
            self._create_tok_list(doc, labels, tok_lists)
        # create predicted notes
        tok_lists: Tuple[str, List[FeatureToken]]
        doc: FeatureDocument
        for doc, tok_lists in zip(docs, doc_tok_lists):
            secs: List[AnnotatedSection] = []
            self._create_secions(tok_lists, doc, secs)
            pn = PredictedNote(
                predicted_sections=secs,
                doc=doc)
            sec: Section
            for sec in secs:
                sec.container = pn
            notes.append(pn)
        return notes

    def _create_features(self, data: Union[FeatureDocument, str]) -> \
            Tuple[FeatureDocument]:
        if isinstance(data, FeatureDocument):
            self._docs.append(data)
            return [data]
        else:
            return super()._create_features(data)

    def _create_data_point(self, cls: Type[DataPoint],
                           feature: Any) -> DataPoint:
        return cls(None, self.batch_stash, note=None, pred_doc=feature)

    def map_results(self, result: ResultsContainer) -> List[PredictedNote]:
        docs: Tuple[FeatureDocument] = tuple(self._docs)
        classes: Tuple[Tuple[str]] = tuple(self._map_classes(result))
        return self._collate(docs, classes)


@dataclass
class SectionFacade(TokenClassifyModelFacade):
    """The application model facade.  This only adds the ``zensols.install``
    package to the CLI output logging.

    """
    def _configure_cli_logging(self, info_loggers: List[str],
                               debug_loggers: List[str]):
        super()._configure_cli_logging(info_loggers, debug_loggers)
        if not self.progress_bar:
            info_loggers.append('zensols.install')
