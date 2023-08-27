"""Collates the predictions of both models.

"""
from __future__ import annotations
__author__ = 'Paul Landes'
from typing import List, Tuple, Optional, Union, Set
from dataclasses import dataclass, field, InitVar
import logging
from pathlib import Path
from zensols.config import ConfigFactory, Configurable
from zensols.persist import (
    PersistableContainer, persisted, PersistedWork, Primeable
)
from zensols.nlp import LexicalSpan, FeatureDocument, FeatureDocumentParser
from zensols.deeplearn.model import ModelPacker, ModelFacade
from zensols.deeplearn.cli import FacadeApplication
from zensols.mimic import Section, NoteEvent, Note
from . import PredictedNote, AnnotationNoteFactory, MimicPredictedNote
from .model import PredictionError, EmptyPredictionError, SectionFacade

logger = logging.getLogger(__name__)


@dataclass
class SectionPredictor(PersistableContainer, Primeable):
    """Creates a complete prediction by collating the predictions of both the
    section ID (type) and header token models.  If :obj:`header_model_packer` is
    not set, then only section identifiers (types) and body spans are predicted.
    In this case, all header spans are left empty.

    Implementation note: when :obj:`auto_deallocate` is ``False`` you must wrap
    creations of this instance in :func:`~zensols.persist.dealloc` as this
    instance contains resources
    (:class:`~zensols.deeplearn.cli.app.FacadeApplication`) that need
    deallocation.  Their deallocation logic is invoked with this instance and
    deallocated by :class:`~zensols.persist.annotation.PersistableContainer`.

    """
    name: str = field()
    """The name of this object instance definition in the configuration."""

    config_factory: ConfigFactory = field()
    """The config factory used to help find the packed model."""

    section_id_model_packer: ModelPacker = field(default=None)
    """The packer used to create the section identifier model."""

    header_model_packer: Optional[ModelPacker] = field(default=None)
    """The packer used to create the header token identifier model."""

    model_config: Configurable = field(default=None)
    """Configuration that overwrites the packaged model configuration."""

    doc_parser: FeatureDocumentParser = field(default=None)
    """Used for parsing documents for predicton.  Default to using model's
    configured document parser.

    """
    min_section_body_len: int = field(default=1)
    """The minimum length of the body needed to make a section."""

    auto_deallocate: bool = field(default=True)
    """Whether or not to deallocate resources after every call to
    :meth:`predict`.  See class docs.

    """
    def __post_init__(self):
        self._section_id_app = PersistedWork('_section_id_app', self)
        self._header_app = PersistedWork('_header_app', self)

    @persisted('_section_id_app')
    def _get_section_id_app(self) -> SectionFacade:
        model_path: Path = self.section_id_model_packer.install_model()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'section ID model path: {model_path}')
        return FacadeApplication(
            config=self.config_factory.config,
            model_path=model_path,
            cache_global_facade=False,
            model_config_overwrites=self.model_config)

    @persisted('_header_app')
    def _get_header_app(self) -> SectionFacade:
        if self.header_model_packer is not None:
            model_path: Path = self.header_model_packer.install_model()
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'header model path: {model_path}')
            return FacadeApplication(
                config=self.config_factory.config,
                model_path=model_path,
                cache_global_facade=False,
                model_config_overwrites=self.model_config)

    def _merge_note(self, sn: PredictedNote, hn: PredictedNote):
        """Merge header tokens from ``hn`` to ``sn``."""
        def ff_chars(s: str, start: int, end: int, avoid: Set[str]) -> \
                Optional[int]:
            p: int = None
            for p in range(start, end + 1):
                c: str = s[p]
                if c not in avoid:
                    break
            return p

        avoid: Set[str] = set(': \n\t\r')
        ssec: Section
        for ssec in sn.sections.values():
            sspan: LexicalSpan = ssec.body_span
            hspans: List[LexicalSpan] = []
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'sec span: {ssec}: {ssec.body_doc}, ' +
                             f'lex: {ssec.lexspan}/{sspan}')
            hsec: Section
            for hsec in hn.sections.values():
                hspan: LexicalSpan = hsec.body_span
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'header span: {hsec}: {hsec.body_doc}, ' +
                                 f'overlap: {hspan.overlaps_with(sspan)}, ' +
                                 f'begin: {hspan.begin == sspan.begin}')
                if hspan.overlaps_with(sspan) and hspan.begin == sspan.begin:
                    # skip over the colon and space after
                    if len(hspan) > 1 and \
                       sn.text[hspan.end - 1:hspan.end] == ':':
                        hspan = LexicalSpan(hspan.begin, hspan.end - 1)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f'adding header span: {hspan}')
                    hspans.append(hspan)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'found {len(hspans)} overlapping header spans')
            if len(hspans) > 0:
                # skip leading space/colon for a tighter begin section boundary
                p: int = ff_chars(sn.text, hspans[-1].end, sspan.end, avoid)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'char skip: {p}')
                if p is None:
                    ssec.body_span = LexicalSpan(sspan.end, sspan.end)
                else:
                    ssec.body_span = LexicalSpan(p, sspan.end)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'adding {hspans} to {ssec}')
                ssec.header_spans = tuple(hspans)

    def _merge_notes(self, snotes: List[PredictedNote],
                     hnotes: List[PredictedNote]):
        """Merge header tokens from ``hnotes`` to ``snotes``."""
        sn: PredictedNote
        hn: PredictedNote
        for sn, hn in zip(snotes, hnotes):
            self._merge_note(sn, hn)

    @persisted('__validate_version', transient=True)
    def _validate_version(self, packer_name: str, facade: ModelFacade) -> bool:
        packer: ModelPacker = getattr(self, packer_name)
        model_pred: SectionPredictor = facade.config_factory(self.name)
        model_packer = getattr(model_pred, packer_name)
        if packer.version != model_packer.version:
            model_name: str = facade.model_settings.model_name
            logger.warning(
                f'API {model_name} version ({packer.version}) does not ' +
                f'match the trained model version ({model_packer.version})')
            return False
        return True

    def _trim_notes(self, notes: List[PredictedNote]):
        def filter_sec(sec: Section) -> bool:
            return len(sec.body_span) > self.min_section_body_len

        note: Note
        for note in notes:
            note.predicted_sections = list(
                filter(filter_sec, note.predicted_sections))

    def _predict_from_docs(self, docs: Tuple[FeatureDocument],
                           sid_fac: SectionFacade) -> List[PredictedNote]:
        head_app: FacadeApplication = self._get_header_app()
        snotes: List[PredictedNote] = sid_fac.predict(docs)
        if head_app is not None:
            head_fac: SectionFacade = head_app.get_cached_facade()
            self._validate_version('header_model_packer', head_fac)
            hnotes: List[PredictedNote] = head_fac.predict(docs)
            self._merge_notes(snotes, hnotes)
        self._trim_notes(snotes)
        return snotes

    def predict_from_docs(self, docs: Tuple[FeatureDocument]) -> \
            List[PredictedNote]:
        sid_fac: SectionFacade = self._get_section_id_app().get_cached_facade()
        self._validate_version('section_id_model_packer', sid_fac)
        return self._predict_from_docs(docs, sid_fac)

    def _predict(self, doc_texts: List[str]) -> List[PredictedNote]:
        sid_fac: SectionFacade = self._get_section_id_app().get_cached_facade()
        self._validate_version('section_id_model_packer', sid_fac)
        doc_parser: FeatureDocumentParser = \
            sid_fac.doc_parser if self.doc_parser is None else self.doc_parser
        docs: Tuple[FeatureDocument] = tuple(map(doc_parser, doc_texts))
        return self._predict_from_docs(docs, sid_fac)

    def predict(self, doc_texts: List[str]) -> List[PredictedNote]:
        """Collate the predictions of both the section ID (type) and header
        token models.

        :param doc_texts: the text of the medical note to segment

        :return: a list of the predictions as notes for each respective
                 ``doc_texts``

        """
        if self.auto_deallocate:
            try:
                return self._predict(doc_texts)
            finally:
                self.deallocate()
        else:
            return self._predict(doc_texts)

    def prime(self):
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'priming {type(self)}...')
        self.section_id_model_packer.install_model()
        self.header_model_packer.install_model()
        super().prime()

    def deallocate(self):
        super().deallocate()
        self._section_id_app.clear()
        self._header_app.clear()

    def __call__(self, docs: List[Union[str, FeatureDocument]]) -> \
            List[PredictedNote]:
        """See :meth:`predict` and :meth:`predict_from_docs`."""
        if len(docs) > 0 and isinstance(docs[0], FeatureDocument):
            return self.predict_from_docs(docs)
        else:
            return self.predict(docs)


@dataclass
class PredictionNoteFactory(AnnotationNoteFactory):
    """A note factory that predicts so that
    :class:`~zensols.mimic.adm.HospitalAdmissionDbStash` predicts missing
    sections.

    **Implementation note:** The :obj:`section_predictor_name` is used with the
    application context factory :obj:`config_factory` since declaring it in the
    configuration creates an instance cycle.

    """
    config_factory: ConfigFactory = field()
    """The factory to get the section predictor."""

    mimic_pred_note_section: str = field(default=None)
    """The section name holding the configuration of the
    :class:`.MimicPredictedNote` class.

    """
    section_predictor_name: InitVar[str] = field(default=None)
    """The name of the section predictor as an app config section name.  See
    class docs.

    """
    def __post_init__(self, section_predictor_name: str):
        self._section_predictor_name = section_predictor_name

    @property
    @persisted('_section_predictor')
    def section_predictor(self) -> SectionPredictor:
        """The section predictor (see class docs)."""
        sp: SectionPredictor = self.config_factory(self._section_predictor_name)
        # turn off deallocation to keep the same facade for all prediction calls
        sp.auto_deallocate = False
        return sp

    def prime(self):
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'priming {type(self)}...')
        self.section_predictor.prime()
        super().prime()

    def _create_missing_anon_note(self, note_event: NoteEvent,
                                  section: str) -> Note:
        sp: SectionPredictor = self.section_predictor
        note: Note = None
        try:
            if logger.isEnabledFor(logging.DEBUG):
                logger.info(f'predicting note: {note_event}')
            pred_note: PredictedNote = sp.predict_from_docs([note_event.doc])[0]
            if len(pred_note.sections) == 0:
                note = None
            else:
                note: MimicPredictedNote = self._event_to_note(
                    note_event,
                    section=self.mimic_pred_note_section,
                    params={'predicted_note': pred_note})
        except EmptyPredictionError as e:
            msg = f'nothing predicted: {note_event}: {e}--using regexs'
            # skip the stack trace since no classified tokens somewhat often
            logger.error(msg)
        except PredictionError as e:
            raise e
        except Exception as e:
            msg = f'could not predict note: {note_event}: {e}--using regexs'
            logger.error(msg, exc_info=True)
        if note is None:
            # the model does not perform well on short nursing notes because it
            # was not trained on them
            if logger.isEnabledFor(logging.INFO):
                logger.info(f'no sections predicted for {note_event.row_id}, ' +
                            'using regular expression prediction')
            try:
                note = self._create_from_note_event(note_event)
            except Exception as e:
                raise PredictionError('Failed twice to predict section: ' +
                                      f'{note_event}: {e}') from e
        else:
            if logger.isEnabledFor(logging.INFO):
                logger.info(f'predicted {len(note.sections)} ' +
                            f'for note: {note.row_id}')
        return note
