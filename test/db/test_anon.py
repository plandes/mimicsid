from typing import Tuple
import unittest
import shutil
from pathlib import Path
from zensols.config import ImportIniConfig, ImportConfigFactory
from zensols.persist import Stash
from zensols.mimic import HospitalAdmission, Note
from zensols.mimic.regexnote import RadiologyNote, EchoNote
from zensols.mimicsid import AnnotatedNote


class TestAnnotationAccess(unittest.TestCase):
    def setUp(self):
        self.maxDiff = 999999
        self.hadm_id = '100139'
        target = Path('target')
        if 1:
            if target.is_dir():
                shutil.rmtree(target)

    def _get_corpus(self, name: str):
        config = ImportIniConfig(f'test-resources/{name}.conf')
        fac = ImportConfigFactory(config)
        return fac('mimic_corpus')

    def _get_notes(self, name: str) -> Tuple[Note]:
        corpus = self._get_corpus(name)
        stash: Stash = corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[self.hadm_id]
        rad_note: Note = adm.notes_by_category['Radiology'][0]
        echo_note: Note = adm.notes_by_id[63188]
        return rad_note, echo_note

    def test_without_anon(self):
        rad_note, echo_note = self._get_notes('without')
        self.assertEqual(RadiologyNote, type(rad_note))
        self.assertEqual(EchoNote, type(echo_note))
        sec = echo_note.sections_by_name['findings'][0]
        should = 'LEFT ATRIUM: Mild LA enlargement'
        self.assertEqual(should, sec.body[0:len(should)])
        should = 'left atrium.'
        self.assertEqual(should, sec.body[-len(should):])

    def test_with_anon(self):
        rad_note, echo_note = self._get_notes('with')
        self.assertEqual(RadiologyNote, type(rad_note))
        self.assertEqual(AnnotatedNote, type(echo_note))
        sec = echo_note.sections_by_name['findings'][0]
        should = 'LEFT ATRIUM: Mild LA enlargement'
        self.assertEqual(should, sec.body[0:len(should)])
        should = 'the MD caring for the patient.'
        self.assertEqual(should, sec.body[-len(should):])
