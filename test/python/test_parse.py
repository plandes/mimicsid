from typing import Dict, Any, List
import unittest
import os
from io import BytesIO, StringIO
import pickle
import yaml
import zensols.mimicsid
from zensols.mimicsid import (
    SectionFilterType, PredictedNote, ApplicationFactory,
    Section, SectionContainer,
)
from zensols.mimicsid.pred import SectionPredictor


class TestParse(unittest.TestCase):
    def setUp(self):
        zensols.mimicsid.suppress_warnings()
        self.maxDiff = 999999
        if 'MIMICSIDRC' in os.environ:
            del os.environ['MIMICSIDRC']

    def _predict(self, filter_type: SectionFilterType,
                 res: str, write: bool = False):
        section_predictor: SectionPredictor = \
            ApplicationFactory.section_predictor()
        section_predictor.auto_deallocate = False
        section_predictor.section_filter_type = filter_type
        with open(f'test-resources/should-{res}.yml') as f:
            should: Dict[str, Any] = yaml.load(f, yaml.FullLoader)
        with open('test-resources/note.txt') as f:
            content: str = f.read()
        note: PredictedNote = section_predictor.predict([content])[0]
        if write:
            print()
            note.write_human()
        return should, note

    def _assert(self, should, note: SectionContainer):
        self.assertTrue(isinstance(note, SectionContainer))
        should_secs: Dict[str, str] = should['sections']
        should_heads: List[str] = should['headers']
        self.assertEqual(len(should_secs), len(note.sections_by_name))
        name: str
        content: str
        headers: List[str]
        for (name, content), headers in zip(should_secs.items(), should_heads):
            self.assertTrue(name in note.sections_by_name, f'missing {name}')
            if name != 'unknown':
                self.assertEqual(1, len(note.sections_by_name[name]))
            sec: Section = note.sections_by_name[name][0]
            self.assertEqual(content.strip(), sec.body.strip())
            self.assertEqual(tuple(headers), sec.headers)

    def _test_pred(self, filter_type: SectionFilterType,
                   res: str, write: bool = False):
        should, note = self._predict(filter_type, res, write)
        self._assert(should, note)

    def test_predict_classified(self):
        self._test_pred(SectionFilterType.keep_classified, 'section-classified')

    def test_predict_non_empty(self):
        self._test_pred(SectionFilterType.keep_non_empty, 'section-non-empty')

    def test_predict_keep_all(self):
        self._test_pred(SectionFilterType.keep_all, 'section-all')

    def test_predict_sections_pickle(self):
        should, note = self._predict(SectionFilterType.keep_all, 'section-all')

        bio = BytesIO()
        pickle.dump(note, bio)
        bio.seek(0)
        note2 = pickle.load(bio)
        self._assert(should, note2)

        sio = StringIO()
        note.write(writer=sio)
        sio2 = StringIO()
        note2.write(writer=sio2)
        self.assertEqual(sio.getvalue(), sio2.getvalue())
